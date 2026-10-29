import difflib
import hmac
import html
import io
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for

from .backup import create_backup, validate_backup
from .db import Store, now
from .fetch import CheckError, canonical, validate_url
from .monitor import coverage, UNHEALTHY
from .notifications import make_digest

TYPES=['announcement','public guidance','operational instructions','legislation','document index','downloadable guide']
SCOPES=['main content','selected section','listing entries','selected linked document']
STATES=['New','Reviewed','Action needed','Archived']


def create_app(store=None):
    store=store or Store()
    app=Flask(__name__)
    key=store.root/'session.key'
    if not key.exists():
        try:
            with key.open('x') as f:f.write(secrets.token_hex(32))
            key.chmod(0o600)
        except FileExistsError:pass
    app.secret_key=key.read_text()
    app.config.update(MAX_CONTENT_LENGTH=128*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',TRUSTED_HOSTS=['localhost','127.0.0.1','[::1]'])
    app.config['STORE']=store

    @app.before_request
    def protect():
        if 'csrf' not in session:session['csrf']=secrets.token_hex(32)
        if request.method=='POST':
            if not hmac.compare_digest(request.form.get('csrf',''),session['csrf']):abort(400,'Invalid form token; reload the page')
            origin=request.headers.get('Origin')
            if origin and origin!=request.host_url.rstrip('/'):abort(403)

    @app.after_request
    def headers(response):
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'none'; style-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Cache-Control']='no-store'
        return response

    @app.context_processor
    def common():
        return dict(csrf=session.get('csrf'),coverage=coverage(store),settings=store.settings(),states=STATES,types=TYPES,scopes=SCOPES,unhealthy=UNHEALTHY,utc_now=now())

    @app.template_filter('localtime')
    def localtime(value):
        if not value:return '—'
        try:return datetime.fromisoformat(value).astimezone(ZoneInfo(store.settings()['timezone'])).strftime('%Y-%m-%d %H:%M %Z')
        except ValueError:return value

    @app.errorhandler(ValueError)
    @app.errorhandler(CheckError)
    def bad_input(exc):return render_template('message.html',title='Please review this input',message=str(exc)),400

    def source_or_404(id):
        source=store.one('SELECT * FROM sources WHERE id=?',(id,))
        if not source:abort(404)
        return source

    @app.get('/')
    def inbox():
        state=request.args.get('state','New')
        sql="SELECT e.*,r.state,r.interpretation,r.follow_up,s.title,s.health FROM events e JOIN reviews r ON r.event_id=e.id JOIN sources s ON s.id=e.source_id WHERE e.kind NOT IN ('metadata_changed','internal_rebaseline')"
        params=[]
        if state in STATES:sql+=' AND r.state=?';params.append(state)
        events=store.rows(sql+' ORDER BY e.id DESC LIMIT 250',params)
        return render_template('inbox.html',events=events,state=state)

    @app.get('/sources')
    def sources():
        return render_template('sources.html',sources=store.rows('SELECT * FROM sources WHERE removed=0 ORDER BY group_name,agency,title'),hosts=store.rows('SELECT * FROM hosts'),candidates=store.rows("SELECT c.*,s.title AS parent_title FROM candidates c JOIN sources s ON s.id=c.parent_id WHERE c.state='pending' ORDER BY c.id DESC LIMIT 200"))

    @app.post('/sources/seed')
    def seed():store.seed();flash('Starter sources added. They are unverified until a successful check.');return redirect(url_for('sources'))

    @app.route('/sources/new',methods=['GET','POST'])
    @app.route('/sources/<int:id>/edit',methods=['GET','POST'])
    def edit_source(id=None):
        source=source_or_404(id) if id else {}
        if request.method=='POST':
            fields={k:request.form.get(k,'').strip() for k in ['title','url','agency','tags','group_name','source_type','scope','selector','expected','ignore_selectors','notes']}
            if any(len(v)>6000 for v in fields.values()):raise ValueError('A source field is too long')
            if not fields['title'] or not fields['agency']:raise ValueError('Title and agency are required')
            if fields['source_type'] not in TYPES or fields['scope'] not in SCOPES:raise ValueError('Unknown source type or scope')
            if fields['scope']=='selected section' and not fields['selector']:raise ValueError('Selected section requires a CSS selector')
            if fields['selector'] or fields['ignore_selectors']:
                import soupsieve
                for selector in [fields['selector']]+fields['ignore_selectors'].splitlines():
                    if selector:
                        try:soupsieve.compile(selector)
                        except Exception as exc:raise ValueError('Invalid CSS selector') from exc
            fields['url']=canonical(fields['url'])
            validate_url(fields['url'],{h['host'] for h in store.rows('SELECT host FROM hosts')},resolve=False)
            hours=float(request.form.get('frequency_hours',6))
            if not 0.25<=hours<=720:raise ValueError('Check frequency must be 0.25–720 hours')
            fields['frequency']=int(hours*3600)
            with store.connect() as db:
                duplicate=db.execute('SELECT id FROM sources WHERE url=? AND id!=?',(fields['url'],id or -1)).fetchone()
                if duplicate:raise ValueError('This URL already has a source, possibly removed. Edit or restore that source from history.')
                if id:
                    changed=any(fields[k]!=source[k] for k in ['url','scope','selector','expected','ignore_selectors'])
                    db.execute('UPDATE sources SET '+','.join(k+'=?' for k in fields)+',next_due=? WHERE id=?',[*fields.values(),now(),id])
                    if changed:db.execute("UPDATE sources SET health='configuration changed; awaiting check',etag=NULL,http_modified=NULL,full_checked=NULL WHERE id=?",(id,))
                else:
                    db.execute('INSERT INTO sources('+','.join(fields)+',next_due) VALUES ('+','.join('?' for _ in fields)+',?)',[*fields.values(),now()])
            flash('Source saved. First success creates a baseline; extraction changes create an internal rebaseline.')
            return redirect(url_for('sources'))
        return render_template('source_form.html',source=source)

    @app.post('/hosts')
    def approve_host():
        host=request.form.get('host','').strip().lower()
        agency=request.form.get('agency','').strip()
        if not agency or request.form.get('official')!='yes':raise ValueError('Confirm ownership by an official government agency')
        validate_url('https://'+host+'/',{host})
        with store.connect() as db:db.execute('INSERT OR IGNORE INTO hosts VALUES (?,?,?)',(host,agency,now()))
        flash('Exact host approved. Linked sites and subdomains are not automatically approved.')
        return redirect(url_for('sources'))

    @app.post('/sources/<int:id>/action')
    def source_action(id):
        source=source_or_404(id);action=request.form.get('action')
        with store.connect() as db:
            if action=='pause':db.execute('UPDATE sources SET paused=1-paused WHERE id=?',(id,))
            elif action=='remove':
                if request.form.get('confirm')!='yes':raise ValueError('Confirm removal from monitoring; evidence is retained')
                db.execute('UPDATE sources SET removed=1,paused=1 WHERE id=?',(id,))
            elif action=='restore':db.execute('UPDATE sources SET removed=0,paused=0,next_due=? WHERE id=?',(now(),id))
            elif action=='check':
                if source['paused'] or source['removed']:raise ValueError('Resume the source before checking')
                db.execute('UPDATE sources SET next_due=? WHERE id=?',(now(),id))
            else:raise ValueError('Unknown action')
        if action=='check':launch_check(id)
        return redirect(url_for('sources'))

    def launch_check(id=None):
        command=[sys.executable,'-m','immigration_monitor','check']
        if id:command+=['--source',str(id)]
        env=os.environ.copy();env['ISM_DATA_DIR']=str(store.root)
        flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
        subprocess.Popen(command,cwd=Path(__file__).resolve().parent.parent,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**flags)
        flash('Check requested. Refresh Sources and health to see recorded results. An existing run is allowed to finish first.')

    @app.post('/check')
    def check_due():launch_check();return redirect(url_for('sources'))

    @app.post('/candidates/<int:id>')
    def candidate_action(id):
        c=store.one('SELECT * FROM candidates WHERE id=?',(id,))
        if not c:abort(404)
        action=request.form.get('action')
        if action=='approve':
            validate_url(c['url'],{h['host'] for h in store.rows('SELECT host FROM hosts')},resolve=False)
            parent=source_or_404(c['parent_id'])
            with store.connect() as db:
                db.execute('INSERT OR IGNORE INTO sources(title,url,agency,tags,source_type,scope,next_due,parent_id,link_label,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (c['title'],c['url'],parent['agency'],parent['tags'],'downloadable guide' if 'guide' in c['kind'] else 'operational instructions',
                     'selected linked document' if 'guide' in c['kind'] else 'main content',now(),parent['id'],c['title'],'Newly discovered source: no earlier version is available. Approved in onboarding.'))
                sid=db.execute('SELECT id FROM sources WHERE url=?',(c['url'],)).fetchone()[0]
                db.execute("UPDATE candidates SET state='approved',source_id=? WHERE id=?",(sid,id))
            flash('Approved for independent monitoring. First success is a baseline, not a recent-change claim.')
        elif action=='dismiss':
            with store.connect() as db:db.execute("UPDATE candidates SET state='dismissed' WHERE id=?",(id,))
        else:raise ValueError('Unknown candidate action')
        return redirect(url_for('sources'))

    @app.get('/events/<int:id>')
    def comparison(id):
        e=store.one('SELECT e.*,r.state,r.interpretation,r.follow_up FROM events e JOIN reviews r ON r.event_id=e.id WHERE e.id=?',(id,))
        if not e:abort(404)
        old=store.one('SELECT * FROM versions WHERE id=?',(e['old_version'],)) or {'text':''}
        new=store.one('SELECT * FROM versions WHERE id=?',(e['new_version'],)) or {'text':''}
        a=old['text'];b=new['text'];tokens=[];diff_rows=[]
        large=len(a)+len(b)>200000
        if not large:
            aw=re.findall(r'\S+|\s+',a);bw=re.findall(r'\S+|\s+',b)
            for tag,i,j,k,l in difflib.SequenceMatcher(None,aw,bw,autojunk=True).get_opcodes():
                if tag=='equal':tokens.append(('equal',''.join(bw[k:l])))
                else:
                    if i!=j:tokens.append(('delete',''.join(aw[i:j])))
                    if k!=l:tokens.append(('insert',''.join(bw[k:l])))
            al=a.splitlines();bl=b.splitlines()
            for tag,i,j,k,l in difflib.SequenceMatcher(None,al,bl,autojunk=True).get_opcodes():diff_rows.append((tag,'\n'.join(al[i:j]),'\n'.join(bl[k:l])))
        return render_template('comparison.html',event=e,evidence=json.loads(e['evidence']),old=old,new=new,tokens=tokens,diff_rows=diff_rows,large=large)

    @app.post('/events/<int:id>/review')
    def review(id):
        if not store.one('SELECT id FROM events WHERE id=?',(id,)):abort(404)
        state=request.form.get('state')
        if state not in STATES:raise ValueError('Invalid review state')
        note=request.form.get('interpretation','');follow=request.form.get('follow_up','')
        if max(len(note),len(follow))>20000:raise ValueError('Note exceeds 20,000 characters')
        with store.connect() as db:db.execute('UPDATE reviews SET state=?,interpretation=?,follow_up=?,updated=? WHERE event_id=?',(state,note,follow,now(),id))
        return redirect(url_for('comparison',id=id))

    @app.get('/versions/<int:id>/<kind>')
    def download_version(id,kind):
        version=store.one('SELECT * FROM versions WHERE id=?',(id,))
        if not version:abort(404)
        if kind=='text':data=version['text'].encode();name=f'evidence-{id}.txt';mime='text/plain'
        elif kind=='raw':
            data=version['raw'];name=f'evidence-{id}'+('.pdf' if data.startswith(b'%PDF') else '.bin');mime='application/octet-stream'
        elif kind=='metadata':data=json.dumps({k:v for k,v in version.items() if k not in ['raw','text']},indent=2).encode();name=f'evidence-{id}.json';mime='application/json'
        else:abort(404)
        return send_file(io.BytesIO(data),as_attachment=True,download_name=name,mimetype=mime)

    @app.get('/candidates/<int:id>/evidence')
    def candidate_evidence(id):
        c=store.one('SELECT * FROM candidates WHERE id=?',(id,))
        if not c:abort(404)
        return render_template('message.html',title=c['title'],message=c['capture_status']+'\n'+c['metadata']+'\n\n'+(c['text'] or 'No article captured.'))

    @app.get('/history')
    def history():
        query=request.args.get('q','')[:200];page=max(1,int(request.args.get('page',1)))
        events=store.rows('SELECT e.*,r.state,s.title FROM events e JOIN reviews r ON r.event_id=e.id JOIN sources s ON s.id=e.source_id WHERE s.title LIKE ? OR e.evidence LIKE ? OR r.interpretation LIKE ? OR r.follow_up LIKE ? ORDER BY e.id DESC LIMIT 100 OFFSET ?',('%'+query+'%',)*4+((page-1)*100,))
        attempts=store.rows('SELECT a.*,s.title FROM attempts a JOIN sources s ON s.id=a.source_id WHERE s.title LIKE ? ORDER BY a.id DESC LIMIT 100 OFFSET ?',('%'+query+'%',(page-1)*100))
        versions=store.rows('SELECT v.id,v.source_id,v.retrieved,v.raw_hash,v.text_hash,v.extraction_version,s.title FROM versions v JOIN sources s ON s.id=v.source_id WHERE s.title LIKE ? OR v.text LIKE ? ORDER BY v.id DESC LIMIT 100 OFFSET ?',('%'+query+'%','%'+query+'%',(page-1)*100))
        return render_template('history.html',events=events,attempts=attempts,versions=versions,query=query,page=page,removed=store.rows('SELECT * FROM sources WHERE removed=1'))

    @app.post('/export')
    def export():
        ids=request.form.getlist('event_id')
        if not ids or len(ids)>250 or any(not x.isdigit() for x in ids):raise ValueError('Select 1–250 evidence events')
        rows=store.rows('SELECT e.*,r.state,r.interpretation,r.follow_up FROM events e JOIN reviews r ON r.event_id=e.id WHERE e.id IN ('+','.join('?' for _ in ids)+') ORDER BY e.id',ids)
        parts=['# Immigration Source Monitor — selected evidence\n\nPublic captured evidence and separately labelled private notes. No legal conclusions.']
        for row in rows:
            ev=json.loads(row['evidence'])
            parts.append('\n\n## '+ev.get('title','')+'\nAgency: '+ev.get('agency','')+'\nOfficial link: '+ev.get('url','')+'\nTags: '+ev.get('tags','')+'\n'+row['summary']+'\nPrevious observation: '+str(row['previous_observed'])+'\nDetected UTC: '+row['detected']+'\nPublication: '+str(ev.get('publication','not stated'))+'\nModified: '+str(ev.get('modified','not stated'))+'\n'+ev.get('effective_wording','')+'\nUncertainty: '+'; '.join(ev.get('warnings',[]))+'\n\nOLD:\n'+ev.get('old_excerpt','')+'\n\nNEW:\n'+ev.get('new_excerpt','')+'\n\nPRIVATE USER INTERPRETATION ('+row['state']+'):\n'+row['interpretation']+'\nFOLLOW-UP:\n'+row['follow_up'])
        content='\n'.join(parts)
        if request.form.get('format')=='html':
            content='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src &apos;none&apos;"><title>Selected immigration source evidence</title><body><pre>'+html.escape(content)+'</pre></body></html>'
            name='selected-evidence.html';mime='text/html'
        else:name='selected-evidence.md';mime='text/markdown'
        return send_file(io.BytesIO(content.encode()),as_attachment=True,download_name=name,mimetype=mime)

    @app.route('/settings',methods=['GET','POST'])
    def settings_page():
        if request.method=='POST':
            tz=request.form.get('timezone','')
            try:ZoneInfo(tz)
            except (KeyError,ValueError) as exc:raise ValueError('Unknown IANA timezone') from exc
            time=request.form.get('digest_time','')
            if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',time):raise ValueError('Use a valid HH:MM digest time')
            values={k:request.form.get(k,'').strip() for k in ['smtp_host','smtp_user','email_to','email_from','smtp_mode']}
            values.update(timezone=tz,digest_time=time,email_enabled=request.form.get('email_enabled')=='yes',smtp_port=int(request.form.get('smtp_port',587)),priority_rules={'numbers':request.form.get('numbers')=='yes','keywords':[v.strip() for v in request.form.get('keywords','').split(',') if v.strip()]})
            if values['smtp_mode'] not in ('ssl','starttls') or not 1<=values['smtp_port']<=65535:raise ValueError('Use TLS or STARTTLS with a valid SMTP port')
            for key in ['email_to','email_from']:
                if values[key] and not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+',values[key]):raise ValueError('Provide one plain email address per field')
            if values['email_enabled'] and not all(values[k] for k in ['smtp_host','email_to','email_from']):raise ValueError('Email requires host, sender, and one recipient')
            store.set_settings(values);flash('Settings saved. Keywords only prioritize; all content changes remain recorded.')
            return redirect(url_for('settings_page'))
        return render_template('settings.html',digests=store.rows('SELECT * FROM digests ORDER BY id DESC LIMIT 30'),deliveries=store.rows('SELECT * FROM deliveries ORDER BY id DESC LIMIT 30'),password_present=bool(os.environ.get('ISM_SMTP_PASSWORD')))

    @app.post('/digest')
    def digest():make_digest(store,force=True);return redirect(url_for('settings_page'))

    @app.post('/deliveries/<int:id>/retry')
    def retry_delivery(id):
        if request.form.get('confirm')!='yes':raise ValueError('Confirm you checked the recipient mailbox before retrying')
        with store.connect() as db:db.execute("UPDATE deliveries SET state='pending',detail='User requested retry',updated=? WHERE id=? AND state IN ('failed','uncertain')",(now(),id))
        flash('Queued for the next checker run. A retry can duplicate a message if the original was accepted.')
        return redirect(url_for('settings_page'))

    @app.route('/backup',methods=['GET','POST'])
    def backup_page():
        if request.method=='POST':
            if request.form.get('action')=='create':
                path=create_backup(store);return send_file(path,as_attachment=True,download_name=path.name)
            upload=request.files.get('backup')
            if not upload:raise ValueError('Choose a backup ZIP')
            folder=store.root/'restore-staging';folder.mkdir(exist_ok=True)
            path=folder/(secrets.token_hex(8)+'.zip');upload.save(path)
            try:validate_backup(path)
            except Exception:
                path.unlink(missing_ok=True);raise ValueError('Backup failed validation; no runtime data changed')
            return render_template('message.html',title='Backup staged; restore requires closing the application',message='Close the launcher and stop scheduled checks, then run from the repository:\n.venv\\Scripts\\python.exe -m immigration_monitor restore --file "'+str(path)+'" --confirm\nA safety backup is created before replacement. Email is disabled after restore; credentials and Windows task registration are separate.')
        size=sum(p.stat().st_size for p in store.root.rglob('*') if p.is_file())
        return render_template('backup.html',size=size,root=store.root)

    return app
