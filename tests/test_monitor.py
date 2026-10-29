import io
import json
import socket

import pytest
from filelock import FileLock
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from immigration_monitor.db import now
from immigration_monitor.extract import extract, bounded_extract
from immigration_monitor.fetch import CheckError, Response, validate_url, Fetcher
from immigration_monitor.monitor import run_checks, coverage
from conftest import FakeFetcher, page, check, URL


def kinds(store): return [r['kind'] for r in store.rows('SELECT kind FROM events')]


def pdf(text='Fictional PDF guidance: employers must supply documentation for the program.',producer='one'):
    writer=PdfWriter();p=writer.add_blank_page(612,792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    p[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(f'BT /F1 12 Tf 40 700 Td ({text}) Tj ET'.encode())
    p[NameObject('/Contents')]=writer._add_object(stream)
    writer.add_metadata({'/Producer':producer});out=io.BytesIO();writer.write(out);return out.getvalue()


def test_baseline_identical_navigation(store,source):
    assert check(store,source,page())['sources'][0][1]=='baseline created'
    check(store,source,page());check(store,source,page(nav='Completely new navigation'))
    assert kinds(store)==[]
    assert len(store.rows('SELECT * FROM versions'))==3


@pytest.mark.parametrize('before,after',[
    ('must','must not'),('January 1, 2026','January 2, 2026'),('$500','$501'),
    ('<table><tr><th>NOC</th><th>Amount</th></tr><tr><td>21231</td><td>500</td></tr></table>',
     '<table><tr><th>NOC</th><th>Amount</th></tr><tr><td>21231</td><td>501</td></tr></table>'),
    ('<a href="/old">Guide</a>','<a href="/new">Guide</a>')])
def test_small_changes(store,source,before,after):
    check(store,source,page(extra='<p>'+before+'</p>'))
    check(store,source,page(extra='<p>'+after+'</p>'))
    assert kinds(store)==['content_changed']


def test_failures_recovery_reversion(store,source):
    check(store,source,page());baseline=store.one('SELECT baseline_id FROM sources')['baseline_id']
    check(store,source,CheckError('timeout'));check(store,source,CheckError('timeout'))
    assert store.one('SELECT baseline_id FROM sources')['baseline_id']==baseline
    assert kinds(store)==['unhealthy']
    check(store,source,page('must not'))
    assert kinds(store)==['unhealthy','content_changed','recovered']
    check(store,source,page())
    assert kinds(store)[-1]=='content_changed'
    assert coverage(store)['failed']==0


@pytest.mark.parametrize('body',[
    b'<html><title>Just a moment</title><main>Verify you are human</main></html>',
    b'<html><main><div id="app"></div><script src="app.js"></script></main></html>',
    b'<html><p>A shell with no main content</p></html>'])
def test_reject_bad_200(store,source,body):
    check(store,source,page());old=store.one('SELECT baseline_id FROM sources')['baseline_id']
    check(store,source,body)
    assert store.one('SELECT baseline_id FROM sources')['baseline_id']==old
    assert store.one('SELECT health FROM sources')['health'] in ['extraction uncertain','failed or blocked']
    assert store.one('SELECT COUNT(*) AS n FROM versions')['n']==2  # failed raw retained


def test_listing_stable_identity(store,source):
    with store.connect() as db: db.execute("UPDATE sources SET scope='listing entries' WHERE id=?",(source,))
    rows=lambda order: page(extra='<ul>'+''.join(f'<li><time datetime="2026-01-0{i}">January {i}</time><a href="/entry/{i}">Fictional announcement number {i}</a></li>' for i in order)+'</ul>')
    check(store,source,rows([1,2]));check(store,source,rows([3,1,2]));check(store,source,rows([2,3,1]))
    assert kinds(store)==['new_entry']
    assert json.loads(store.one('SELECT evidence FROM events')['evidence'])['publication']=='2026-01-03'


def test_pdf_bytes_and_text(store,source):
    check(store,source,pdf());check(store,source,pdf(producer='two'))
    assert kinds(store)==['document_bytes_changed']
    check(store,source,pdf(text='Fictional PDF guidance: employers must not supply documentation for the program.'))
    assert kinds(store)[-1]=='content_changed'
    version=store.one('SELECT * FROM versions ORDER BY id DESC LIMIT 1')
    assert '[Page 1]' in version['text']
    assert json.loads(version['metadata'])['warnings']


def test_image_pdf_uncertain():
    w=PdfWriter();w.add_blank_page(10,10);out=io.BytesIO();w.write(out)
    with pytest.raises(CheckError,match='insufficient text'): extract(out.getvalue(),URL,{})


def test_config_parser_rebaseline(store,source,monkeypatch):
    import immigration_monitor.extract as module
    check(store,source,page())
    monkeypatch.setattr(module,'PARSER_VERSION','next-version')
    check(store,source,page('must not'))
    assert kinds(store)==['internal_rebaseline']
    check(store,source,page('may'))
    assert kinds(store)[-1]=='content_changed'


def test_conditional_and_full_validation(store,source):
    check(store,source,Response(304,URL))
    assert store.one('SELECT health FROM sources')['health']=='extraction uncertain'
    check(store,source,page())
    check(store,source,Response(304,URL))
    assert store.one('SELECT health FROM sources')['health']=='checked successfully; unchanged'
    with store.connect() as db: db.execute("UPDATE sources SET full_checked='2000-01-01T00:00:00+00:00'")
    check(store,source,Response(304,URL))
    assert store.one('SELECT health FROM sources')['health']=='extraction uncertain'


def test_overlap_catchup_restart(store,source):
    with store.connect() as db: db.execute("UPDATE sources SET next_due='2000-01-01T00:00:00+00:00'")
    f=FakeFetcher(page())
    with FileLock(str(store.root/'operation.lock')):
        assert run_checks(store,fetcher=f,extractor=extract)['status']=='already running'
    assert len(f.calls)==0
    run_checks(store,fetcher=f,extractor=extract)
    run_checks(store,fetcher=f,extractor=extract)
    assert len(f.calls)==1
    assert len(store.rows('SELECT * FROM attempts'))==1


@pytest.mark.parametrize('url',['file:///etc/passwd','http://127.0.0.1/a','http://169.254.169.254/','https://user:pass@www.canada.ca/','https://www.canada.ca:8000/','https://evil.test/','https://www.canada.ca\\@evil.test/'])
def test_unsafe_urls(url):
    with pytest.raises(CheckError): validate_url(url,{'www.canada.ca','127.0.0.1','169.254.169.254'})


def test_private_dns(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('10.0.0.1',443))])
    with pytest.raises(CheckError,match='non-public'):validate_url(URL,{'www.canada.ca'})


def test_robots_and_redirect(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))])
    f=Fetcher({'www.canada.ca'},delay=0)
    monkeypatch.setattr(f,'_request',lambda u,h:Response(200,u,b'User-agent: *\nDisallow: /'))
    with pytest.raises(CheckError,match='robots'): f.fetch(URL)
    f.robots={}
    monkeypatch.setattr(f,'_request',lambda u,h:Response(404,u) if u.endswith('robots.txt') else Response(302,u,headers={'location':'http://127.0.0.1/'}))
    with pytest.raises(CheckError,match='redirect'):f.fetch(URL)


def test_modified_date_separate_and_immutable(store,source):
    a=page().replace(b'</main>',b'<div id="wb-dtmd"><time>2026-01-01</time></div></main>')
    b=a.replace(b'2026-01-01',b'2026-01-02')
    check(store,source,a);check(store,source,b)
    assert kinds(store)==['metadata_changed']
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        with store.connect() as db:db.execute("UPDATE versions SET text='altered'")


def test_bounded_extractor():
    result=bounded_extract(page(),URL,{})
    assert 'Fictional Employer' in result.text
    assert bounded_extract(pdf(),URL,{}).format=='pdf'


def test_feed():
    body=b'<rss><channel><item><title>Fictional announcement</title><link>https://www.canada.ca/test</link><pubDate>2026-01-01</pubDate><description>Test summary</description></item></channel></rss>'
    result=extract(body,URL,{},'application/rss+xml')
    assert result.entries[0]['publication']=='2026-01-01'
