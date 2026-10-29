import base64
import io
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from defusedxml import ElementTree
from pypdf import PdfReader

from .db import digest_hash
from .fetch import CheckError, MAX_BYTES, canonical

PARSER_VERSION='html-1/pdf-1/feed-1'
EFFECTIVE_UNKNOWN='Effective date not established from the monitored content.'


@dataclass
class Extracted:
    text: str
    metadata: dict=field(default_factory=dict)
    entries: list=field(default_factory=list)
    links: list=field(default_factory=list)
    warnings: list=field(default_factory=list)
    format: str='html'


def config_hash(source):
    return digest_hash(json.dumps({k:source.get(k,'') for k in ['scope','selector','expected','ignore_selectors','url']},sort_keys=True)+PARSER_VERSION)


def clean(s):
    return re.sub(r'\s+',' ',s).strip()


def date_metadata(text):
    sentences=re.split(r'(?<=[.!?])\s+|\n',text)
    effective=[s for s in sentences if re.search(r'\b(effective|takes? effect|comes? into force)\b',s,re.I) and re.search(r'\b\d{1,4}\b',s)]
    return {'effective_wording':'\n'.join(effective[:10]) or EFFECTIVE_UNKNOWN}


def html_extract(raw,url,source):
    soup=BeautifulSoup(raw,'html.parser')
    visible=clean(soup.get_text(' ',strip=True))
    title=clean(soup.title.get_text()) if soup.title else ''
    challenge=r'(verify (you are|that you are) human|access denied|just a moment|checking your browser|captcha|sign in to continue|enable javascript and cookies)'
    if re.search(challenge,title+' '+visible[:1500],re.I):
        raise CheckError('Challenge, access restriction, or login page detected','failed or blocked')
    meta={}
    for key,names in {'publication':['dcterms.issued','datePublished','article:published_time'],'modified':['dcterms.modified','dateModified','article:modified_time']}.items():
        for name in names:
            tag=soup.find('meta',attrs={'name':name}) or soup.find('meta',attrs={'property':name})
            if tag and tag.get('content'): meta[key]=tag['content'];break
    modified=soup.select_one('#wb-dtmd time, .date-modified time')
    if modified: meta['modified']=modified.get('datetime') or clean(modified.get_text())
    if source.get('selector'):
        try: nodes=soup.select(source['selector'])
        except Exception as exc: raise CheckError('Invalid section/list selector','extraction uncertain') from exc
        if not nodes: raise CheckError('Selected section was not found','extraction uncertain')
        root=BeautifulSoup('<main></main>','html.parser').main
        for node in nodes: root.append(node)
    else:
        if source.get('scope')=='selected section': raise CheckError('Selected section requires a CSS selector','extraction uncertain')
        root=soup.find('main') or soup.find(attrs={'role':'main'}) or soup.find('article')
        if not root: raise CheckError('No reliable main/article content found; configure a section selector','extraction uncertain')
    for node in root.select('script,style,noscript,nav,footer,form,iframe,object,embed,svg,#wb-dtmd,.date-modified,.cookie-banner,[role="navigation"]'):
        node.decompose()
    for selector in source.get('ignore_selectors','').splitlines():
        if selector.strip():
            try:
                for node in root.select(selector.strip()): node.decompose()
            except Exception as exc: raise CheckError('Invalid noise selector','extraction uncertain') from exc
    links=[]; entries=[]; seen=set()
    for a in root.find_all('a',href=True):
        href=a['href']; label=clean(a.get_text(' ',strip=True))
        if not href or href.startswith('#'): continue
        target=urljoin(url,href)
        if urlsplit(target).scheme not in ('http','https'): continue
        target=canonical(target)
        links.append({'title':label or target,'url':target})
        if source.get('scope')=='listing entries' and target not in seen:
            parent=a.find_parent(['tr','li','article'])
            if parent:
                dt=parent.find('time')
                publication=(dt.get('datetime') or clean(dt.get_text())) if dt else None
                entries.append({'key':target,'url':target,'title':label or target,'publication':publication,'context':clean(parent.get_text(' ',strip=True))})
                seen.add(target)
        a.replace_with((label or target)+' ['+target+']')
    # Preserve block order and row/header context; whitespace alone is normalized.
    for tag in list(root.find_all(['h1','h2','h3','h4','h5','h6','p','li','tr','div','section','br'])):
        if tag.name=='li': tag.insert_before('\n• ')
        elif re.fullmatch('h[1-6]',tag.name): tag.insert_before('\n'+'#'*int(tag.name[1])+' ')
        else: tag.insert_before('\n')
        tag.insert_after('\n')
    for cell in root.find_all(['td','th']): cell.insert_after(' | ')
    text='\n'.join(line for line in (clean(s) for s in root.get_text().splitlines()) if line)
    if len(text)<80:
        raise CheckError('Empty or suspiciously short content; possible dynamic shell','extraction uncertain')
    expected=source.get('expected','').strip()
    if expected and expected.casefold() not in text.casefold():
        raise CheckError('Expected content marker is missing','extraction uncertain')
    if source.get('scope')=='listing entries':
        if not entries: raise CheckError('No identifiable listing entries; configure listing container','extraction uncertain')
        # Stable URL identity means inserting/reordering a row does not change all entries.
        text='\n'.join(e['title']+' ['+e['url']+'] '+(e['publication'] or '')+' '+e['context'] for e in sorted(entries,key=lambda e:e['key']))
    meta.update(date_metadata(text))
    return Extracted(text,meta,entries,links)


def pdf_extract(raw):
    try:
        reader=PdfReader(io.BytesIO(raw),strict=False)
        if reader.is_encrypted: raise CheckError('Encrypted PDF is not supported','extraction uncertain')
        if len(reader.pages)>400: raise CheckError('PDF exceeds 400-page processing limit','extraction uncertain')
        pages=[]; warnings=['PDF layout and table reading order require visual verification against the saved original.']
        for i,page in enumerate(reader.pages,1):
            text=page.extract_text() or ''
            if len(clean(text))<20:
                raise CheckError(f'PDF page {i} has insufficient text; image-only or unreliable extraction (no OCR)','extraction uncertain')
            pages.append(f'[Page {i}]\n'+text.strip())
        if not pages: raise CheckError('Empty PDF','extraction uncertain')
        text='\n\n'.join(pages)
        return Extracted(text,date_metadata(text),warnings=warnings,format='pdf')
    except CheckError: raise
    except Exception as exc: raise CheckError('PDF could not be reliably extracted','extraction uncertain') from exc


def feed_extract(raw,url):
    try: root=ElementTree.fromstring(raw)
    except Exception as exc: raise CheckError('Feed XML is invalid or unsafe','extraction uncertain') from exc
    entries=[]
    for item in root.iter():
        if item.tag.split('}')[-1] not in ('entry','item'): continue
        fields={child.tag.split('}')[-1]:child for child in item}
        title=clean(''.join(fields['title'].itertext())) if 'title' in fields else ''
        link=fields.get('link')
        target=(link.get('href') or link.text) if link is not None else None
        if not title or not target: continue
        target=canonical(urljoin(url,target))
        if urlsplit(target).scheme not in ('https','http'): continue
        date=next((fields[k].text for k in ['published','pubDate','updated'] if k in fields),None)
        summary=' '.join(clean(''.join(fields[k].itertext())) for k in ['summary','description','content'] if k in fields)
        entries.append({'key':target,'url':target,'title':title,'publication':date,'context':summary})
    if not entries: raise CheckError('Feed contains no identifiable entries','extraction uncertain')
    text='\n'.join(e['title']+' ['+e['url']+'] '+(e['publication'] or '')+' '+e['context'] for e in sorted(entries,key=lambda e:e['key']))
    return Extracted(text,date_metadata(text),entries,[{'title':e['title'],'url':e['url']} for e in entries],format='feed')


def extract(raw,url,source,content_type=''):
    if len(raw)>MAX_BYTES: raise CheckError('Input too large','extraction uncertain')
    if raw.startswith(b'%PDF'): return pdf_extract(raw)
    if 'pdf' in content_type: raise CheckError('Expected PDF signature is missing','extraction uncertain')
    if any(t in content_type for t in ('rss','atom','xml')) or raw.lstrip().startswith(b'<?xml'):
        return feed_extract(raw,url)
    return html_extract(raw,url,source)


def bounded_extract(raw,url,source,content_type=''):
    payload=json.dumps({'raw':base64.b64encode(raw).decode(),'url':url,'source':dict(source),'content_type':content_type})
    try:
        run=subprocess.run([sys.executable,'-m','immigration_monitor.extract'],input=payload,text=True,capture_output=True,timeout=25)
        result=json.loads(run.stdout)
        if 'error' in result: raise CheckError(result['error'],result['status'])
        return Extracted(**result)
    except (subprocess.TimeoutExpired,ValueError) as exc:
        raise CheckError('Extraction process exceeded limits or failed','extraction uncertain') from exc


if __name__=='__main__':
    try:
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(20,20))
        except ImportError: pass
        data=json.load(sys.stdin)
        print(json.dumps(asdict(extract(base64.b64decode(data['raw']),data['url'],data['source'],data['content_type']))))
    except CheckError as exc:
        print(json.dumps({'error':str(exc),'status':exc.status}))
