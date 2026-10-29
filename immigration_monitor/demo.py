"""Deterministic fictional end-to-end demonstration, without network requests."""
from .db import now
from .extract import extract
from .fetch import Response, CheckError
from .monitor import run_checks
from .notifications import make_digest


def demo(store):
    if store.one('SELECT id FROM sources LIMIT 1'):
        raise ValueError('Demo requires a separate empty data directory')
    url='https://www.canada.ca/fictional-demo-not-a-real-page'
    with store.connect() as db:
        id=db.execute('INSERT INTO sources(title,url,agency,tags,source_type,next_due) VALUES (?,?,?,?,?,?)',
            ('FICTIONAL DEMO — Employer Requirements',url,'Fictional example, not government guidance','fictional, demo','public guidance',now())).lastrowid
    class FixtureFetcher:
        value=None
        def fetch(self,url,headers=None):
            if isinstance(self.value,Exception):raise self.value
            return Response(200,url,self.value,{'content-type':'text/html'})
    fetcher=FixtureFetcher();out=[]
    for step,word in [('baseline','must'),('wording change','must not'),('failed check',None),('recovery','may')]:
        fetcher.value=CheckError('FICTIONAL simulated timeout') if word is None else f'<html><main><h1>FICTIONAL Employer Requirements</h1><p>This is fictional test content, not official guidance. Employers {word} submit a sample document for this demonstration.</p></main></html>'.encode()
        result=run_checks(store,source_id=id,fetcher=fetcher,extractor=extract)
        out.append({'step':step,'result':result['sources'][0][1]})
    first=store.one("SELECT id FROM events WHERE kind='content_changed' ORDER BY id LIMIT 1")
    # Exercise the actual browser review route with its CSRF token.
    from .web import create_app
    client=create_app(store).test_client();client.get('/')
    with client.session_transaction() as session:token=session['csrf']
    result=client.post(f"/events/{first['id']}/review",data={'csrf':token,'state':'Reviewed','interpretation':'FICTIONAL: wording reviewed; no legal conclusion.','follow_up':'FICTIONAL: consult the saved source evidence.'})
    if result.status_code!=302:raise RuntimeError('Demo review failed')
    digest=make_digest(store,force=True)
    with store.connect() as db:db.execute('UPDATE sources SET paused=1 WHERE id=?',(id,))
    return {'label':'FICTIONAL demo — no live sources fetched','steps':out,'review_event':first['id'],'digest_id':digest,'source_paused':True}
