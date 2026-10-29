"""Fictional examples matching documented field names, never live evidence."""
import copy
import io
import json
import zipfile

import pytest

from immigration_monitor.db import now, digest_hash
from immigration_monitor.express_entry import PAGE_URL, DATA_URL, prepare_response, unpack, validate_data
from immigration_monitor.extract import bounded_extract, extract
from immigration_monitor.fetch import CheckError, Response
from immigration_monitor.monitor import run_checks

PAGE=('''<!doctype html><html><title>Fictional Express Entry rounds</title><main>
<h1>Fictional Express Entry rounds of invitations</h1>
<p>This fixture is invented test data, not an official invitation round or immigration instruction.</p>
<div data-wb-jsonmanager='{"url":"'''+DATA_URL+'''","name":"rounds"}'></div>
<p>Invitations: <span data-json-replace="#rounds/0/drawSize"></span></p>
<table><thead><tr><th>Fictional round</th><th>Score</th><th>Invitations</th></tr></thead><tbody></tbody></table>
</main></html>''').encode()


def dataset():
    rows=[]
    for n in [2,1]:
        row={'drawNumber':str(n),'drawNumberURL':f'https://www.canada.ca/fictional-round-{n}',
             'drawDate':f'2026-01-0{n}','drawDateFull':f'January {n}, 2026','drawName':'FICTIONAL test class',
             'drawSize':'1,000','drawCRS':'500','drawDistributionAsOn':'2026-01-01',
             'mitext':'Fictional ministerial instructions','DrawText1':'Fictional text','drawText2':'Fictional condition',
             'drawDateTime':'12:00 UTC','drawCutOff':'2025-01-01T00:00:00Z'}
        row.update({f'dd{i}':str(i*10) for i in range(1,19)})
        rows.append(row)
    return {'classes':'table fictional-fixture','rounds':rows}


class PairFetcher:
    def __init__(self,data=None,page=PAGE):self.data=dataset() if data is None else data;self.page=page;self.calls=[]
    def fetch(self,url,headers=None):
        self.calls.append((url,headers))
        if url==PAGE_URL:return Response(200,url,self.page,{'content-type':'text/html','etag':'"unchanged-page"'})
        assert url==DATA_URL
        if isinstance(self.data,Exception):raise self.data
        if isinstance(self.data,Response):return self.data
        body=self.data if isinstance(self.data,bytes) else json.dumps(self.data).encode()
        return Response(200,url,body,{'content-type':'application/json','etag':'"json"'})


@pytest.fixture
def ee_source(store):
    with store.connect() as db:
        return db.execute('INSERT INTO sources(title,url,agency,tags,source_type,scope,expected,next_due) VALUES (?,?,?,?,?,?,?,?)',
            ('FICTIONAL Express Entry',PAGE_URL,'IRCC','Express Entry','public guidance','main content','rounds',now())).lastrowid


def run(store,id,fetcher,extractor=extract):return run_checks(store,source_id=id,fetcher=fetcher,extractor=extractor)


def test_compound_baseline_preserves_originals_and_checks_both_every_time(store,ee_source):
    f=PairFetcher();assert run(store,ee_source,f)['sources'][0][1]=='baseline created'
    v=store.one('SELECT * FROM versions')
    manifest,bodies=unpack(v['raw'])
    assert bodies['page.html']==PAGE and bodies['rounds.json']==json.dumps(dataset()).encode()
    assert all(a['retrieved_utc'] and a['sha256']==digest_hash(bodies[a['name']]) for a in manifest['artifacts'])
    assert json.loads(v['metadata'])['round_ids']==[1,2]
    assert 'drawDistributionAsOn' in v['text'] and 'dd18' in v['text']
    assert not store.rows('SELECT * FROM events')
    f.calls=[];assert run(store,ee_source,f)['sources'][0][1]=='checked successfully; unchanged'
    assert f.calls==[(PAGE_URL,{}),(DATA_URL,None)]


@pytest.mark.parametrize('field,value',[('drawDate','2026-01-03'),('drawSize','1,001'),('drawCRS','501'),('dd9','999'),('drawCutOff','2025-02-01T00:00:00Z'),('drawNumberURL','https://www.canada.ca/fictional-revised-link'),('drawText2','Fictional condition must not apply')])
def test_round_changes_and_reversions(store,ee_source,field,value):
    run(store,ee_source,PairFetcher());changed=dataset();changed['rounds'][1][field]=value
    assert run(store,ee_source,PairFetcher(changed))['sources'][0][1]=='change detected'
    assert run(store,ee_source,PairFetcher())['sources'][0][1]=='change detected'
    assert len(store.rows("SELECT * FROM events WHERE kind='content_changed'"))==2


def test_round_reordering_is_not_a_change_but_new_round_is(store,ee_source):
    run(store,ee_source,PairFetcher());data=dataset();data['rounds'].reverse()
    assert run(store,ee_source,PairFetcher(data))['sources'][0][1]=='checked successfully; unchanged'
    new=copy.deepcopy(data['rounds'][0]);new['drawNumber']='3';new['drawDate']='2026-01-03';data['rounds'].append(new)
    assert run(store,ee_source,PairFetcher(data))['sources'][0][1]=='change detected'


@pytest.mark.parametrize('bad',[b'not json',b'{"rounds":[],"rounds":[]}',{'classes':[],'rounds':[]},CheckError('Simulated JSON timeout'),Response(304,DATA_URL)])
def test_bad_data_cannot_replace_valid_baseline(store,ee_source,bad):
    run(store,ee_source,PairFetcher());baseline=store.one('SELECT baseline_id FROM sources')['baseline_id']
    run(store,ee_source,PairFetcher(bad))
    assert store.one('SELECT baseline_id FROM sources')['baseline_id']==baseline
    assert store.one('SELECT health FROM sources')['health'] in ('failed or blocked','extraction uncertain')
    failed=store.one('SELECT * FROM versions ORDER BY id DESC LIMIT 1')
    manifest,bodies=unpack(failed['raw'],require_complete=False)
    assert bodies['page.html']==PAGE
    if not isinstance(bad,Exception):assert 'rounds.json' in bodies
    assert json.loads(failed['metadata'])['valid'] is False
    assert run(store,ee_source,PairFetcher())['sources'][0][1]=='checked successfully; unchanged'
    assert store.one("SELECT id FROM events WHERE kind='recovered'")


@pytest.mark.parametrize('mutation',[lambda d:d['rounds'][0].pop('drawCRS'),lambda d:d['rounds'][0].pop('dd1'),lambda d:d['rounds'][0].update(drawDate='yesterday'),lambda d:d['rounds'][0].update(drawSize=True),lambda d:d['rounds'][0].update(drawNumberURL='http://127.0.0.1/'),lambda d:d['rounds'].append(d['rounds'][0])])
def test_required_schema_and_unique_identity(mutation):
    data=dataset();mutation(data)
    with pytest.raises(CheckError):validate_data(json.dumps(data))


def test_historical_round_disappearance_held_for_review(store,ee_source):
    run(store,ee_source,PairFetcher());baseline=store.one('SELECT baseline_id FROM sources')['baseline_id']
    data=dataset();data['rounds'].pop()
    assert run(store,ee_source,PairFetcher(data))['sources'][0][1]=='extraction uncertain'
    assert store.one('SELECT baseline_id FROM sources')['baseline_id']==baseline


def test_changed_reference_is_not_followed(store,ee_source):
    f=PairFetcher(page=PAGE.replace(DATA_URL.encode(),b'https://www.canada.ca/unreviewed-data.json'))
    assert run(store,ee_source,f)['sources'][0][1]=='extraction uncertain'
    assert f.calls==[(PAGE_URL,{})]
    assert store.one('SELECT baseline_id FROM sources')['baseline_id'] is None


def test_unrelated_dynamic_placeholder_still_rejected(store,ee_source):
    f=PairFetcher(page=PAGE.replace(b'</main>',b'<div data-ajax-replace="/unknown-policy.html"></div></main>'))
    assert run(store,ee_source,f)['sources'][0][1]=='extraction uncertain'


def test_bounded_worker_download_and_backup(store,ee_source,tmp_path):
    from immigration_monitor.web import create_app
    from immigration_monitor.backup import create_backup,restore_backup
    from immigration_monitor.db import Store
    assert run(store,ee_source,PairFetcher(),extractor=bounded_extract)['sources'][0][1]=='baseline created'
    client=create_app(store).test_client();response=client.get('/versions/1/raw')
    assert 'evidence-1.zip' in response.headers['Content-Disposition']
    assert b'page.html' in response.data and b'rounds.json' in response.data
    other=Store(tmp_path/'restored');restore_backup(other,create_backup(store))
    assert other.one('SELECT raw FROM versions')['raw']==store.one('SELECT raw FROM versions')['raw']
    assert unpack(other.one('SELECT raw FROM versions')['raw'])[0]['complete'] is True


def test_tampered_bundle_cannot_be_extracted():
    f=PairFetcher();r=f.fetch(PAGE_URL);prepare_response(r,{'url':PAGE_URL},f)
    original=zipfile.ZipFile(io.BytesIO(r.body));out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name in original.namelist():z.writestr(name,b'{}' if name=='rounds.json' else original.read(name))
    with pytest.raises(CheckError):extract(out.getvalue(),PAGE_URL,{},r.headers['content-type'])
