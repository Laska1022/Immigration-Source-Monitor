"""Narrow adapter for the official page/data pair observed in LIVE_SOURCE_NOTES.

Exact originals are retained in a bounded ZIP, including incomplete observations.
The adapter never follows a replacement data endpoint without a code review.
"""
import io
import json
import re
import zipfile
from datetime import date
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from .db import digest_hash, now
from .fetch import CheckError, MAX_BYTES, canonical

PAGE_URL='https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html'
DATA_URL='https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json'
MIME='application/vnd.ism.express-entry+zip'
ADAPTER_VERSION='express-entry-1'


def handles(url):
    return canonical(url)==PAGE_URL


def uncertain(message):
    return CheckError(message,'extraction uncertain')


def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('Non-finite JSON number')
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    except (ValueError,UnicodeError,RecursionError) as exc:raise uncertain('Express Entry JSON is invalid or ambiguous') from exc


def references(raw,url):
    """Read WET URL declarations, not arbitrary links or text mentioning an API."""
    soup=BeautifulSoup(raw,'html.parser'); found=[]
    def urls(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key=='url' and isinstance(item,str):yield item
                elif isinstance(item,(dict,list)):yield from urls(item)
        elif isinstance(value,list):
            for item in value:yield from urls(item)
        elif isinstance(value,str) and value.startswith(('https://','http://','/')):yield value
    for node in soup.select('[data-wb-json],[data-wb-jsonmanager]'):
        for attr in ('data-wb-json','data-wb-jsonmanager'):
            value=node.get(attr)
            if not value:continue
            if value.lstrip().startswith(('{','[','"')):value=strict_json(value)
            for target in urls(value):found.append(canonical(urljoin(url,target)))
    if not found or any(target!=DATA_URL for target in found):
        raise uncertain('Express Entry data reference is missing or changed; no replacement endpoint was followed')
    return soup


def _artifact(name,response,original_url):
    return {'name':name,'original_url':original_url,'final_url':response.url,
            'retrieved_utc':now(),'status':response.status,'sha256':digest_hash(response.body),
            'headers':{k:v for k,v in response.headers.items() if k in ('content-type','etag','last-modified','date','content-length')}}


def _pack(artifacts,bodies,complete):
    out=io.BytesIO()
    manifest={'adapter_version':ADAPTER_VERSION,'complete':complete,'artifacts':artifacts}
    with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as z:
        for name,body in bodies.items():z.writestr(zipfile.ZipInfo(name),body)
        z.writestr(zipfile.ZipInfo('manifest.json'),json.dumps(manifest,sort_keys=True))
    if len(out.getvalue())>MAX_BYTES:raise uncertain('Combined Express Entry observation exceeds size limit')
    return out.getvalue(),manifest


def prepare_response(response,source,fetcher):
    """Mutate the response so the existing failure path can retain partial evidence."""
    if not handles(source['url']):return response
    if response.status!=200 or canonical(response.url)!=PAGE_URL:
        raise uncertain('Express Entry requires a full page and full JSON observation on every check')
    page=response.body
    artifacts=[_artifact('page.html',response,source['url'])];bodies={'page.html':page}
    response.body,response.capture_metadata=_pack(artifacts,bodies,False)
    response.headers={**response.headers,'content-type':MIME}
    references(page,response.url)
    data=fetcher.fetch(DATA_URL)  # deliberately unconditional: the HTML ETag cannot validate JSON
    artifacts.append(_artifact('rounds.json',data,DATA_URL));bodies['rounds.json']=data.body
    response.body,response.capture_metadata=_pack(artifacts,bodies,False)
    if data.status!=200 or canonical(data.url)!=DATA_URL:
        raise uncertain('Express Entry JSON needs a full response from the verified endpoint')
    response.body,response.capture_metadata=_pack(artifacts,bodies,True)
    return response


def unpack(raw,require_complete=True):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist()
            if sorted(names) not in (['manifest.json','page.html'],['manifest.json','page.html','rounds.json']):
                raise ValueError('Unexpected artifact members')
            if sum(i.file_size for i in z.infolist())>MAX_BYTES or any(i.compress_type!=zipfile.ZIP_STORED for i in z.infolist()):
                raise ValueError('Artifact limits exceeded')
            manifest=strict_json(z.read('manifest.json'))
            if manifest.get('adapter_version')!=ADAPTER_VERSION:raise ValueError('Unknown adapter version')
            if require_complete and (manifest.get('complete') is not True or 'rounds.json' not in names):raise ValueError('Incomplete capture')
            artifacts=manifest.get('artifacts',[])
            if sorted(a['name'] for a in artifacts)!=sorted(set(names)-{'manifest.json'}):raise ValueError('Artifact manifest mismatch')
            for a in artifacts:
                if digest_hash(z.read(a['name']))!=a['sha256']:raise ValueError('Artifact hash mismatch')
                expected=PAGE_URL if a['name']=='page.html' else DATA_URL
                if canonical(a['original_url'])!=expected or canonical(a['final_url'])!=expected:raise ValueError('Artifact source mismatch')
                if require_complete and a['status']!=200:raise ValueError('Unsuccessful artifact')
            return manifest,{name:z.read(name) for name in names if name!='manifest.json'}
    except (ValueError,TypeError,KeyError,zipfile.BadZipFile) as exc:
        raise uncertain('Invalid or incomplete Express Entry evidence bundle') from exc


def validate_data(raw):
    data=strict_json(raw)
    if not isinstance(data,dict) or not isinstance(data.get('classes'),(str,dict,list)) or not data['classes']:
        raise uncertain('Express Entry classes metadata is missing or invalid')
    rounds=data.get('rounds')
    if not isinstance(rounds,list) or not 1<=len(rounds)<=10000:
        raise uncertain('Express Entry rounds array is empty or exceeds limits')
    seen=set()
    required={'drawNumber','drawNumberURL','drawDate','drawName','drawSize','drawCRS'}
    for row in rounds:
        if not isinstance(row,dict) or not required.issubset(row):raise uncertain('Express Entry round is missing required fields')
        for key in required:
            if isinstance(row[key],bool) or not isinstance(row[key],(str,int)) or not str(row[key]).strip():
                raise uncertain('Express Entry round contains an invalid required value: '+key)
        if any(not isinstance(row[k],str) for k in ('drawNumberURL','drawDate','drawName')):
            raise uncertain('Express Entry link, date and name must be strings')
        if not re.fullmatch(r'\d+',str(row['drawNumber'])) or int(row['drawNumber']) in seen:
            raise uncertain('Express Entry round identity is invalid or duplicated')
        seen.add(int(row['drawNumber']))
        try:date.fromisoformat(row['drawDate'])
        except (ValueError,TypeError):raise uncertain('Express Entry round date is invalid')
        for key in ('drawSize','drawCRS'):
            if not re.fullmatch(r'\d+|\d{1,3}(?:,\d{3})+',str(row[key])):
                raise uncertain('Express Entry count/score is not a recognized number: '+key)
        target=urlsplit(urljoin(PAGE_URL,row['drawNumberURL']))
        if target.scheme!='https' or target.hostname!='www.canada.ca' or target.username or target.password or target.port not in (None,443):
            raise uncertain('Express Entry round link is not an approved official HTTPS link')
        distribution={f'dd{i}' for i in range(1,19)}
        if distribution.intersection(row):
            if not distribution.issubset(row) or not row.get('drawDistributionAsOn'):
                raise uncertain('Express Entry distribution data is incomplete')
            if any(isinstance(row[k],bool) or not re.fullmatch(r'\d+|\d{1,3}(?:,\d{3})+',str(row[k])) for k in distribution):
                raise uncertain('Express Entry distribution count is invalid')
    latest=max(rounds,key=lambda row:int(row['drawNumber']))
    if not all(f'dd{i}' in latest for i in range(1,19)):
        raise uncertain('Latest Express Entry round has no complete distribution data')
    return data


def extract_bundle(raw,url,source):
    from .extract import html_extract, date_metadata
    manifest,bodies=unpack(raw)
    references(bodies['page.html'],url)
    data=validate_data(bodies['rounds.json'])
    # Static wording and complete data are compared together. No browser scripts run.
    result=html_extract(bodies['page.html'],url,source,verified_rounds=True)
    sections=[result.text,'# Official Express Entry JSON data',
              '## Classes metadata',json.dumps(data['classes'],ensure_ascii=False,sort_keys=True,indent=2)]
    for row in sorted(data['rounds'],key=lambda row:int(row['drawNumber']),reverse=True):
        sections.extend(['## Round '+str(row['drawNumber']),json.dumps(row,ensure_ascii=False,sort_keys=True,indent=2)])
    for key in sorted(set(data)-{'classes','rounds'}):
        sections.extend(['## Additional JSON field: '+key,json.dumps(data[key],ensure_ascii=False,sort_keys=True,indent=2)])
    result.text='\n'.join(sections)
    result.format='express-entry-bundle'
    result.metadata.update(manifest)
    result.metadata.update(date_metadata(result.text))
    result.metadata['round_ids']=sorted(int(row['drawNumber']) for row in data['rounds'])
    result.warnings.append('HTML and JSON were retrieved separately; their exact observation times are recorded. Distribution keys are preserved verbatim; no eligibility interpretation is made.')
    return result
