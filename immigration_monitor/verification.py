import json
from pathlib import Path

from .db import now, digest_hash
from .extract import bounded_extract
from .fetch import Fetcher, CheckError


def verify_sources(output):
    seeds=json.loads(Path(__file__).with_name('starter_sources.json').read_text())
    fetcher=Fetcher({'www.canada.ca','www.welcomebc.ca'})
    results=[]
    for source in seeds:
        item={'title':source['title'],'url':source['url'],'checked_utc':now(),
            'method':'Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)',
            'result':'not checked','redirects':[],'limitations':[]}
        try:
            r=fetcher.fetch(source['url'])
            item.update(final_url=r.url,http_status=r.status,redirects=r.redirects,raw_sha256=digest_hash(r.body))
            ex=bounded_extract(r.body,r.url,source,r.headers.get('content-type',''))
            item.update(result='fetch and extraction passed',extracted_characters=len(ex.text),limitations=ex.warnings)
            if 'documents' in source['url']:
                item['guide_candidates']=[link for link in ex.links if 'guide' in link['title'].lower()]
            if 'rounds-invitations' in source['url']:
                item['limitations'].append('Dynamic rounds data requires separate verification; generic HTML success does not establish coverage of each invitation round.')
        except CheckError as exc:
            item.update(result=exc.status,detail=str(exc),response_metadata=exc.metadata)
            item['limitations'].append('No verified current content or replacement URL. A failed prerequisite does not establish no change.')
        results.append(item)
        print(source['title']+': '+item['result'],flush=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'generated_utc':now(),'results':results},indent=2,ensure_ascii=False)+'\n')
    md=['# Starter-source verification','',f'Checked UTC: {now()}','',
        'Live checks are separate from deterministic fixture tests. A blocked result is not a passed test. No replacement URLs were invented. Discovered BC guides require approval in Sources & health before monitoring.','']
    for item in results:
        md.extend(['## '+item['title'],item['url'],'', '- Result: '+item['result'],'- Checked UTC: '+item['checked_utc'],'- Extraction method: '+item['method'],
            '- Detail: '+item.get('detail','Valid extracted content captured'),'- Redirect evidence: '+json.dumps(item.get('response_metadata',{}).get('redirects',item['redirects'])),'- Limitations: '+' '.join(item['limitations']),''])
    output.with_suffix('.md').write_text('\n'.join(md))
