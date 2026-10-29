"""Reproductions of bugs found during the continuation audit."""
import json
import pytest

from conftest import check, page, FakeFetcher, URL
from immigration_monitor.fetch import CheckError, Response
from immigration_monitor.monitor import run_checks
from immigration_monitor.web import create_app


def approve_first_guide(store):
    c=store.one('SELECT * FROM candidates');client=create_app(store).test_client();client.get('/')
    with client.session_transaction() as session:token=session['csrf']
    assert client.post(f"/candidates/{c['id']}",data={'csrf':token,'action':'approve'}).status_code==302
    return c


def guide_page(path):return page(extra=f'<p><a href="{path}">Skills Immigration Program Guide</a></p>')


def test_download_replacement_event_is_not_swallowed_by_candidate_discovery(store,source):
    check(store,source,guide_page('/first.pdf'));approve_first_guide(store)
    check(store,source,guide_page('/second.pdf'))
    events=store.rows("SELECT * FROM events WHERE kind='download_link_changed'")
    assert len(events)==1
    evidence=json.loads(events[0]['evidence'])
    assert '/first.pdf' in evidence['old_excerpt'] and '/second.pdf' in evidence['new_excerpt']
    assert events[0]['new_version']==store.one('SELECT baseline_id FROM sources WHERE id=?',(source,))['baseline_id']
    check(store,source,guide_page('/second.pdf'))
    assert len(store.rows("SELECT * FROM events WHERE kind='download_link_changed'"))==1
    check(store,source,guide_page('/first.pdf'))
    assert len(store.rows("SELECT * FROM events WHERE kind='download_link_changed'"))==2
    assert len(store.rows('SELECT * FROM sources'))==2  # replacement remains approval-gated


def test_configuration_rebaseline_is_not_a_download_change(store,source):
    check(store,source,guide_page('/first.pdf'));approve_first_guide(store)
    with store.connect() as db:db.execute("UPDATE sources SET expected='Fictional' WHERE id=?",(source,))
    check(store,source,guide_page('/second.pdf'))
    assert not store.rows("SELECT * FROM events WHERE kind='download_link_changed'")


@pytest.mark.parametrize('failure',[False,True])
def test_source_edit_during_fetch_cannot_overwrite_current_health_or_baseline(store,source,failure):
    check(store,source,page());before=store.one('SELECT * FROM sources WHERE id=?',(source,))
    class EditingFetcher:
        def fetch(self,url,headers=None):
            with store.connect() as db:
                db.execute("UPDATE sources SET url=?,health='configuration changed; awaiting check',next_due='2000-01-01T00:00:00+00:00',etag=NULL,http_modified=NULL,full_checked=NULL WHERE id=?",(URL+'-edited',source))
            if failure:raise CheckError('Simulated timeout after source edit')
            return Response(200,url,page('must not'),{'content-type':'text/html'})
    result=run_checks(store,source_id=source,fetcher=EditingFetcher())
    after=store.one('SELECT * FROM sources WHERE id=?',(source,))
    assert result['sources'][0][1]=='configuration changed; awaiting check'
    assert after['health']=='configuration changed; awaiting check'
    assert after['baseline_id']==before['baseline_id']
    assert after['last_success']==before['last_success']
    assert after['etag'] is None and after['next_due']=='2000-01-01T00:00:00+00:00'
    assert not store.rows('SELECT * FROM events')
    attempt=store.one('SELECT * FROM attempts ORDER BY id DESC LIMIT 1')
    assert 'superseded' in attempt['detail']


def test_successful_observation_time_is_after_fetch(store,source,monkeypatch):
    import immigration_monitor.monitor as monitor
    times=iter(['2026-01-01T00:00:00+00:00','2026-01-01T00:00:20+00:00'])
    monkeypatch.setattr(monitor,'now',lambda:next(times))
    from immigration_monitor.extract import extract
    current=store.one('SELECT * FROM sources WHERE id=?',(source,))
    monitor.check_one(store,current,FakeFetcher(page()),extract)
    assert store.one('SELECT retrieved FROM versions')['retrieved']=='2026-01-01T00:00:20+00:00'


def test_paused_queued_source_is_not_fetched(store,source):
    with store.connect() as db:
        second=db.execute('INSERT INTO sources(title,url,agency,source_type) VALUES (?,?,?,?)',('Second fixture',URL+'/second','Test','public guidance')).lastrowid
    class PausingFetcher(FakeFetcher):
        def fetch(self,url,headers=None):
            with store.connect() as db:db.execute('UPDATE sources SET paused=1 WHERE id=?',(second,))
            return super().fetch(url,headers)
    f=PausingFetcher(page())
    from immigration_monitor.extract import extract
    run_checks(store,force=True,fetcher=f,extractor=extract)
    assert [url for url,_ in f.calls]==[URL]
    assert store.one('SELECT last_attempt FROM sources WHERE id=?',(second,))['last_attempt'] is None


def test_replacement_links_use_legacy_evidence_and_render_excerpts(store,source):
    check(store,source,guide_page('/first.pdf'));approve_first_guide(store)
    # Simulate a pre-upgrade version by producing its older metadata at insertion.
    with store.connect() as db:
        s=dict(db.execute('SELECT * FROM sources WHERE id=?',(source,)).fetchone())
        # Keep immutable rows intact: insert a valid old-format observation.
        prior=dict(db.execute('SELECT * FROM versions WHERE id=?',(s['baseline_id'],)).fetchone())
        meta=json.loads(prior['metadata']);meta.pop('links')
        cols=[k for k in prior if k!='id'];values=[json.dumps(meta) if k=='metadata' else prior[k] for k in cols]
        id=db.execute('INSERT INTO versions('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',values).lastrowid
        db.execute('UPDATE sources SET baseline_id=? WHERE id=?',(id,source))
    check(store,source,guide_page('/second.pdf'))
    e=store.one("SELECT id FROM events WHERE kind='download_link_changed'")
    body=create_app(store).test_client().get(f"/events/{e['id']}").data
    assert b'Observed download links' in body and b'/first.pdf' in body and b'/second.pdf' in body


def test_failed_articles_do_not_starve_later_discoveries_across_restarts(store,source):
    from immigration_monitor.db import Store,now
    from immigration_monitor.monitor import capture_articles
    from immigration_monitor.extract import extract
    with store.connect() as db:
        for i in range(7):
            db.execute('INSERT INTO candidates(parent_id,title,url,kind,discovered) VALUES (?,?,?,?,?)',
                       (source,f'Fictional article {i}',f'https://www.canada.ca/article-{i}','announcement',now()))
    class Routes:
        def __init__(self):self.calls=[]
        def fetch(self,url,headers=None):
            self.calls.append(url)
            if int(url.rsplit('-',1)[1])<5:raise CheckError('Simulated permanent block')
            return Response(200,url,page(),{'content-type':'text/html'})
    f=Routes();capture_articles(store,f,extract)
    assert len(f.calls)==5
    f.calls=[];capture_articles(Store(store.root),f,extract)
    assert len(f.calls)<=5
    assert store.one("SELECT COUNT(*) AS n FROM candidates WHERE capture_status='captured'")['n']==2
