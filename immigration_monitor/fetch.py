"""Bounded fetching with exact-host approval, public DNS checks and pinned direct sockets."""
import http.client
import ipaddress
import os
import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from urllib.request import getproxies

import requests

USER_AGENT = 'ImmigrationSourceMonitor/0.1 (+local personal research; respectful official-source monitoring)'
MAX_BYTES = 15 * 1024 * 1024
TIMEOUT = 20
MAX_SECONDS = 45


class CheckError(Exception):
    def __init__(self, detail, status='failed or blocked', metadata=None, retry_at=None):
        super().__init__(detail)
        self.status = status
        self.metadata = metadata or {}
        self.retry_at = retry_at


def canonical(url):
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',p.query,''))


def validate_url(url, approved, resolve=True):
    try:
        p = urlsplit(url)
        host = (p.hostname or '').lower()
        if p.scheme not in ('http','https') or not host or p.username or p.password or p.port not in (None,80,443):
            raise ValueError()
        if any(c.isspace() or ord(c)<32 for c in url) or '\\' in url or host.endswith('.'):
            raise ValueError()
        if host not in approved:
            raise CheckError('Host is not explicitly approved: '+host)
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global or ip.is_multicast or ip.is_reserved:
                raise ValueError()
        except ValueError:
            if host.replace('.','').isdigit() or ':' in host or host in ('localhost','metadata.google.internal'):
                raise CheckError('Non-public address is forbidden')
        if not resolve:
            return host, []
        addresses = sorted({a[4][0] for a in socket.getaddrinfo(host,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)})
        if not addresses or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast or ipaddress.ip_address(ip).is_reserved for ip in addresses):
            raise CheckError('DNS resolved to a non-public address')
        return host, addresses
    except CheckError:
        raise
    except (ValueError, OSError) as exc:
        raise CheckError('Unsafe URL or DNS lookup failed') from exc


@dataclass
class Response:
    status: int
    url: str
    body: bytes = b''
    headers: dict = field(default_factory=dict)
    redirects: list = field(default_factory=list)


def retry_after(value):
    if not value:
        return None
    try:
        if value.isdigit():
            return (datetime.now(timezone.utc)+timedelta(seconds=int(value))).isoformat()
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (ValueError,OverflowError):
        return None


class Fetcher:
    def __init__(self, approved, delay=2.0):
        self.approved = set(approved)
        self.delay = delay
        self.last = {}
        self.robots = {}

    def _validate(self, url):
        trusted = os.environ.get('ISM_TRUSTED_PROXY') == '1' and bool(getproxies().get(urlsplit(url).scheme))
        return validate_url(url, self.approved, resolve=not trusted)

    def _request(self, url, headers):
        host, ips = self._validate(url)
        elapsed = time.monotonic()-self.last.get(host,0)
        if elapsed < self.delay:
            time.sleep(self.delay-elapsed)
        self.last[host] = time.monotonic()
        p = urlsplit(url)
        start = time.monotonic()
        proxies = getproxies()
        if proxies.get(p.scheme):
            # Explicitly trusted managed egress proxies own destination resolution.
            # Arbitrary inherited proxies cannot silently disable direct DNS pinning.
            if os.environ.get('ISM_TRUSTED_PROXY') != '1':
                raise CheckError('Outbound proxy is configured. Review proxy trust before setting ISM_TRUSTED_PROXY=1; direct sockets remain DNS-pinned.')
            try:
                with requests.get(url,headers=headers,timeout=(TIMEOUT,TIMEOUT),allow_redirects=False,stream=True) as r:
                    chunks=[]; size=0
                    for chunk in r.iter_content(65536):
                        size+=len(chunk)
                        if size>MAX_BYTES or time.monotonic()-start>MAX_SECONDS:
                            raise CheckError('Response exceeded size or time limit')
                        chunks.append(chunk)
                    return Response(r.status_code,url,b''.join(chunks),{k.lower():v for k,v in r.headers.items()})
            except requests.RequestException as exc:
                raise CheckError('Network request failed ('+type(exc).__name__+')') from exc
        conn = None
        try:
            port = p.port or (443 if p.scheme=='https' else 80)
            if p.scheme=='https':
                conn = http.client.HTTPSConnection(host,port,timeout=TIMEOUT,context=ssl.create_default_context())
            else:
                conn = http.client.HTTPConnection(host,port,timeout=TIMEOUT)
            # Pin the validated address while HTTPS still verifies the original hostname.
            conn._create_connection = lambda address, timeout=TIMEOUT, source_address=None: socket.create_connection((ips[0],port),timeout,source_address)
            conn.request('GET',urlunsplit(('','',p.path or '/',p.query,'')),headers=headers)
            r=conn.getresponse(); chunks=[]; size=0
            while True:
                chunk=r.read(65536)
                if not chunk: break
                size+=len(chunk)
                if size>MAX_BYTES or time.monotonic()-start>MAX_SECONDS:
                    raise CheckError('Response exceeded size or time limit')
                chunks.append(chunk)
            return Response(r.status,url,b''.join(chunks),{k.lower():v for k,v in r.getheaders()})
        except (OSError,http.client.HTTPException) as exc:
            raise CheckError('Network request failed ('+type(exc).__name__+')') from exc
        finally:
            if conn: conn.close()

    def _robots_allowed(self,url):
        p=urlsplit(url); origin=f'{p.scheme}://{p.netloc}'
        if origin not in self.robots:
            r=self._request(origin+'/robots.txt',{'User-Agent':USER_AGENT,'Accept-Encoding':'identity'})
            if r.status in (404,410):
                parser=RobotFileParser(); parser.parse([])
            elif r.status==200 and b'<html' not in r.body.lower() and len(r.body)<1024*1024:
                parser=RobotFileParser(); parser.parse(r.body.decode('utf-8',errors='replace').splitlines())
            else:
                raise CheckError('Robots rules could not be verified (HTTP '+str(r.status)+')',metadata={'robots_url':r.url,'status':r.status},retry_at=retry_after(r.headers.get('retry-after')))
            self.robots[origin]=parser
        parser=self.robots[origin]
        if not parser.can_fetch(USER_AGENT,url):
            raise CheckError('Blocked by robots rules')
        delay=parser.crawl_delay(USER_AGENT) or parser.crawl_delay('*')
        rate=parser.request_rate(USER_AGENT) or parser.request_rate('*')
        if delay: self.delay=max(self.delay,float(delay))
        if rate: self.delay=max(self.delay,rate.seconds/rate.requests)
        if self.delay>60:
            raise CheckError('Robots requests a long crawl delay; manual review required')

    def fetch(self,url,headers=None):
        original=canonical(url); current=original; redirects=[]
        base={'User-Agent':USER_AGENT,'Accept-Encoding':'identity','Accept':'text/html, application/pdf, application/atom+xml, application/rss+xml, application/json;q=0.8'}
        base.update(headers or {})
        for hop in range(6):
            self._validate(current)
            self._robots_allowed(current)
            for attempt in range(2):
                try:
                    r=self._request(current,base)
                    break
                except CheckError as exc:
                    if attempt or 'Network request failed' not in str(exc): raise
                    time.sleep(2)
            if r.status in (301,302,303,307,308):
                target=canonical(urljoin(current,r.headers.get('location','')))
                redirects.append({'from':current,'to':target,'status':r.status})
                try: self._validate(target)
                except CheckError as exc:
                    raise CheckError('Unapproved or unsafe redirect; baseline retained','source unavailable or redirected',{'redirects':redirects}) from exc
                if urlsplit(current).scheme=='https' and urlsplit(target).scheme!='https':
                    raise CheckError('HTTPS downgrade redirect rejected','source unavailable or redirected',{'redirects':redirects})
                current=target
                base.pop('If-None-Match',None); base.pop('If-Modified-Since',None)
                continue
            r.redirects=redirects
            if r.status not in (200,304):
                status='source unavailable or redirected' if r.status in (404,410) else 'failed or blocked'
                raise CheckError('HTTP '+str(r.status)+'; no conclusion about policy withdrawal',status,
                    {'status':r.status,'final_url':r.url,'redirects':redirects},retry_after(r.headers.get('retry-after')))
            # Redirects require explicit source URL review. Never silently change identity.
            if redirects:
                raise CheckError('Redirect observed; review final URL before approving it','source unavailable or redirected',{'final_url':r.url,'redirects':redirects})
            return r
        raise CheckError('Too many redirects','source unavailable or redirected',{'redirects':redirects})
