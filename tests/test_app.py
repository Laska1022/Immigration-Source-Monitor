import hashlib
import io
import json
import sqlite3
import zipfile

import pytest

from immigration_monitor.backup import create_backup, restore_backup, validate_backup
from immigration_monitor.db import Store
from immigration_monitor.demo import demo
from immigration_monitor.notifications import make_digest, deliver_pending
from immigration_monitor.web import create_app
from immigration_monitor.fetch import CheckError
from conftest import page,check


def client_for(store):
    app=create_app(store);app.config['TESTING']=True
    client=app.test_client();client.get('/')
    with client.session_transaction() as s:token=s['csrf']
    return client,token


def test_ui_routes_review_export_security(store,source):
    check(store,source,page());check(store,source,page('must not',extra='<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'))
    client,token=client_for(store)
    for url in ['/','/sources','/sources/new',f'/sources/{source}/edit','/history','/settings','/backup','/events/1']:
        response=client.get(url);assert response.status_code==200,(url,response.data)
        assert "script-src 'none'" in response.headers['Content-Security-Policy']
    assert b'<script>alert(1)</script>' not in client.get('/events/1').data
    assert b'&lt;script&gt;' in client.get('/events/1').data
    assert client.post('/events/1/review',data={'state':'Reviewed'}).status_code==400
    assert client.post('/events/1/review',data={'csrf':token,'state':'Reviewed'},headers={'Origin':'https://evil.test'}).status_code==403
    assert client.get('/',headers={'Host':'evil.test'}).status_code==400
    response=client.post('/events/1/review',data={'csrf':token,'state':'Reviewed','interpretation':'My separate note','follow_up':'Revisit source'})
    assert response.status_code==302
    assert store.one('SELECT state FROM reviews')['state']=='Reviewed'
    for format in ['md','html']:
        exported=client.post('/export',data={'csrf':token,'event_id':'1','format':format})
        assert exported.status_code==200
        assert b'My separate note' in exported.data
        assert b'<script>alert(1)</script>' not in exported.data if format=='html' else True
    assert client.get('/versions/1/raw').headers['Content-Disposition'].startswith('attachment;')
    assert client.get('/versions/1/metadata').status_code==200
    assert client.get('/versions/1/../../etc/passwd').status_code==404


def test_source_management(store):
    client,token=client_for(store)
    data={'csrf':token,'title':'A new source','url':'https://www.canada.ca/new','agency':'IRCC','source_type':'public guidance','scope':'main content','frequency_hours':'6','tags':'IEC','group_name':'Work permits'}
    assert client.post('/sources/new',data=data).status_code==302
    assert store.one('SELECT group_name FROM sources')['group_name']=='Work permits'
    id=store.one('SELECT id FROM sources')['id']
    assert client.post(f'/sources/{id}/action',data={'csrf':token,'action':'pause'}).status_code==302
    assert store.one('SELECT paused FROM sources')['paused']==1
    data.update(scope='selected section',selector='main',expected='guidance')
    assert client.post(f'/sources/{id}/edit',data=data).status_code==302
    assert client.post(f'/sources/{id}/action',data={'csrf':token,'action':'remove','confirm':'yes'}).status_code==302
    assert store.one('SELECT removed FROM sources')['removed']==1
    assert client.post(f'/sources/{id}/action',data={'csrf':token,'action':'restore'}).status_code==302
    assert store.one('SELECT removed FROM sources')['removed']==0
    data['url']='http://127.0.0.1/secret'
    assert client.post('/sources/new',data=data).status_code==400


def test_guides_approval_no_automatic_monitor(store,source):
    check(store,source,page(extra='<p><a href="https://www.canada.ca/skills.pdf">Skills Immigration Program Guide</a></p>'))
    assert len(store.rows('SELECT * FROM sources'))==1
    c=store.one('SELECT * FROM candidates');assert c['state']=='pending'
    client,token=client_for(store)
    assert client.post(f"/candidates/{c['id']}",data={'csrf':token,'action':'approve'}).status_code==302
    child=store.one('SELECT * FROM sources WHERE parent_id=?',(source,))
    assert child['url'].endswith('skills.pdf')
    assert child['baseline_id'] is None
    assert 'no earlier version' in child['notes']


def test_digest_coverage_email_restart_and_uncertainty(store,source):
    check(store,source,page());check(store,source,CheckError('simulated timeout'))
    store.set_settings({'email_enabled':True,'email_to':'fixture@example.invalid','email_from':'fixture@example.invalid','smtp_host':'smtp.example.invalid'})
    id=make_digest(store,force=True);assert make_digest(store,force=True)==id
    body=store.one('SELECT body FROM digests')['body']
    assert '0 checked successfully; 1 failed;' in body
    assert 'Could not verify' in body
    calls=[]
    deliver_pending(store,sender=lambda settings,body,message_id:calls.append(message_id))
    deliver_pending(Store(store.root),sender=lambda *args:calls.append('duplicate'))
    assert len(calls)==1
    with store.connect() as db:db.execute("UPDATE deliveries SET state='sending'")
    deliver_pending(store,sender=lambda *args:calls.append('duplicate'))
    assert len(calls)==1
    assert store.one('SELECT state FROM deliveries')['state']=='uncertain'


def test_delivery_failure_separate_from_source(store,source):
    check(store,source,page());store.set_settings({'email_enabled':True})
    make_digest(store,force=True)
    def bad(*args):raise ValueError('Simulated SMTP rejection')
    deliver_pending(store,sender=bad)
    assert store.one('SELECT health FROM sources')['health']=='baseline created'
    assert store.one('SELECT state FROM deliveries')['state']=='failed'
    deliver_pending(store,sender=lambda *args:pytest.fail('Automatic resend after failure'))


def test_daily_schedule_timezone(store,source):
    check(store,source,page())
    assert make_digest(store,at='2026-01-01T05:59:00+00:00') is None  # 08:59 Istanbul
    assert make_digest(store,at='2026-01-01T06:00:00+00:00') is not None
    assert len(store.rows('SELECT * FROM digests'))==1


def test_backup_restore_roundtrip(store,source,tmp_path):
    check(store,source,page());check(store,source,page('must not'))
    with store.connect() as db:db.execute("UPDATE reviews SET state='Reviewed',interpretation='Private fictional note'")
    store.set_settings({'timezone':'America/Toronto','email_enabled':True})
    make_digest(store,force=True)
    (store.root/'smtp-password.dpapi').write_text('fixture-not-a-real-secret')
    backup=create_backup(store)
    with zipfile.ZipFile(backup) as z:assert sorted(z.namelist())==['manifest.json','monitor.sqlite3']
    other=Store(tmp_path/'restored');restore_backup(other,backup)
    assert other.rows('SELECT * FROM versions')==store.rows('SELECT * FROM versions')
    assert other.rows('SELECT * FROM sources')==store.rows('SELECT * FROM sources')
    assert other.rows('SELECT * FROM reviews')==store.rows('SELECT * FROM reviews')
    assert other.rows('SELECT * FROM attempts')==store.rows('SELECT * FROM attempts')
    assert other.settings()['timezone']=='America/Toronto'
    assert other.settings()['email_enabled'] is False
    assert other.one('SELECT state FROM deliveries')['state']=='uncertain'
    assert not (other.root/'smtp-password.dpapi').exists()


def test_bad_backup_paths_and_hash(store,tmp_path):
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('../monitor.sqlite3','attack');z.writestr('manifest.json','{}')
    with pytest.raises(ValueError,match='members'):validate_backup(bad)
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('monitor.sqlite3','invalid');z.writestr('manifest.json',json.dumps({'format':1,'sha256':'wrong'}))
    with pytest.raises(ValueError,match='checksum'):restore_backup(store,bad)
    assert store.one('PRAGMA integrity_check')['integrity_check']=='ok'


def test_fictional_demo(store):
    result=demo(store)
    assert [s['result'] for s in result['steps']]==['baseline created','change detected','failed or blocked','change detected']
    assert store.one('SELECT state FROM reviews WHERE event_id=?',(result['review_event'],))['state']=='Reviewed'
    assert 'FICTIONAL' in store.one('SELECT body FROM digests')['body']
    assert store.one('SELECT paused FROM sources')['paused']==1


def test_restore_rejects_extra_trigger(store,source,tmp_path):
    check(store,source,page());backup=create_backup(store)
    extracted=validate_backup(backup);dbpath=tmp_path/'tampered.sqlite3';dbpath.write_bytes(extracted)
    with sqlite3.connect(dbpath) as db:db.execute('CREATE TRIGGER malicious AFTER INSERT ON settings BEGIN DELETE FROM sources; END')
    data=dbpath.read_bytes();bad=tmp_path/'tampered.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('monitor.sqlite3',data);z.writestr('manifest.json',json.dumps({'format':1,'sha256':hashlib.sha256(data).hexdigest()}))
    with pytest.raises(ValueError,match='schema'):restore_backup(store,bad)


def test_digest_event_watermark_no_same_second_loss(store,source):
    check(store,source,page());check(store,source,page('must not'))
    first=make_digest(store,force=True,at='2099-01-01T06:00:00+00:00')
    stamp=store.one('SELECT created FROM digests WHERE id=?',(first,))['created']
    check(store,source,page('may'))
    with store.connect() as db:db.execute('UPDATE events SET detected=? WHERE id=(SELECT MAX(id) FROM events)',(stamp,))
    second=make_digest(store,force=True,at='2099-01-02T06:00:00+00:00')
    assert 'may' in store.one('SELECT body FROM digests WHERE id=?',(second,))['body']


def test_backup_restore_refuses_active_ui(store,source):
    from filelock import FileLock,Timeout
    check(store,source,page());backup=create_backup(store)
    with FileLock(str(store.root/'ui.lock')):
        with pytest.raises(Timeout):restore_backup(store,backup)


def test_failed_capture_does_not_render_false_deletions(store,source):
    check(store,source,page());check(store,source,b'<html><main>empty</main></html>')
    client,token=client_for(store)
    body=client.get('/events/1').data
    assert b'does not establish that earlier content was removed' in body
    assert b'<del>' not in body


def test_starter_registry_is_idempotent_and_unverified(store):
    store.seed();store.seed()
    sources=store.rows('SELECT * FROM sources')
    assert len(sources)==9
    assert all(s['baseline_id'] is None and s['last_success'] is None and s['health']=='never checked' for s in sources)


def test_live_report_command_does_not_pass_blocked_sources(tmp_path,monkeypatch):
    import immigration_monitor.verification as verification
    class Blocked:
        def __init__(self,*args,**kwargs):pass
        def fetch(self,*args,**kwargs):raise CheckError('Simulated network restriction')
    monkeypatch.setattr(verification,'Fetcher',Blocked)
    path=tmp_path/'report.json'
    assert verification.verify_sources(path) is False
    results=json.loads(path.read_text())['results']
    assert len(results)==9 and all(r['result']=='failed or blocked' for r in results)
