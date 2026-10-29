import json
import os
import smtplib
import ssl
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from filelock import FileLock, Timeout

from .db import now
from .monitor import coverage


def make_digest(store,force=False,at=None):
    settings=store.settings();stamp=at or now()
    local=datetime.fromisoformat(stamp).astimezone(ZoneInfo(settings['timezone']))
    if not force and local.strftime('%H:%M')<settings['digest_time']: return None
    day=local.date().isoformat()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT id FROM digests WHERE day=?',(day,)).fetchone()
        if existing:return existing['id']
        prior=db.execute('SELECT created,coverage FROM digests ORDER BY id DESC LIMIT 1').fetchone()
        after_id=json.loads(prior['coverage']).get('last_event_id',0) if prior else 0
        events=db.execute('SELECT * FROM events WHERE id>? AND detected<=? ORDER BY id',(after_id,stamp)).fetchall()
        cov=coverage(store,stamp)
        cov['last_event_id']=events[-1]['id'] if events else after_id
        failed_articles=db.execute("SELECT COUNT(*) FROM candidates WHERE kind='announcement' AND capture_status!='captured'").fetchone()[0]
        body=['Immigration Source Monitor — daily digest',day+' ('+settings['timezone']+')',
            'Coverage as of '+stamp+' (latest observations, not a guarantee of continuous coverage):',
            f"{cov['checked_successfully']} checked successfully; {cov['failed']} failed; {cov['overdue']} overdue; {cov['never_checked']} never checked.",
            'Overdue can overlap other counts. Paused/removed sources are excluded.',
            f'{failed_articles} discovered announcement articles have not been captured successfully.', '']
        content_events=[e for e in events if e['kind'] not in ('metadata_changed','internal_rebaseline')]
        if not content_events:
            body.append('No new change or health events were recorded in this digest interval. Consult the coverage and source-health details; this is not proof that all sources were checked or unchanged.')
        for e in events:
            evidence=json.loads(e['evidence'])
            body.extend([e['summary'],f"{evidence.get('title','')} — {evidence.get('agency','')}",evidence.get('entry_url') or evidence.get('url',''),
                'Tags: '+evidence.get('tags',''), 'Previous raw SHA-256: '+str(evidence.get('old_raw_hash')), 'New raw SHA-256: '+str(evidence.get('new_raw_hash')), 'Previous successful observation: '+str(e['previous_observed']),
                'Detected: '+e['detected'], 'Publication: '+str(evidence.get('publication','not stated')),
                'Modified: '+str(evidence.get('modified','not stated')),evidence.get('effective_wording',''),
                'Review aids (not legal conclusions): '+(e['priority'] or 'none'),
                'OLD:\n'+evidence.get('old_excerpt',''), 'NEW:\n'+evidence.get('new_excerpt',''),
                'Uncertainty: '+'; '.join(evidence.get('warnings',[])),f"Saved comparison: open event {e['id']} in the local application.", ''])
        for source in db.execute("SELECT title,url,health,detail FROM sources WHERE removed=0 AND paused=0 AND health IN ('failed or blocked','extraction uncertain','source unavailable or redirected')"):
            body.extend(['Could not verify: '+source['title'],source['url'],source['health']+': '+source['detail'],''])
        body.append('Evidence monitor only. No eligibility or legal conclusions. A running, connected computer is required. Catch-up cannot reconstruct every intermediate change.')
        digest_id=db.execute('INSERT INTO digests(day,created,body,coverage) VALUES (?,?,?,?)',(day,stamp,'\n'.join(body),json.dumps(cov))).lastrowid
        if settings['email_enabled']:
            db.execute('INSERT INTO deliveries(digest_id,message_id,updated) VALUES (?,?,?)',(digest_id,'<'+str(uuid.uuid4())+'@immigration-source-monitor.local>',stamp))
        return digest_id


def smtp_delivery(settings,body,message_id):
    password=os.environ.get('ISM_SMTP_PASSWORD')
    if settings['smtp_user'] and not password:
        raise ValueError('ISM_SMTP_PASSWORD is not configured in this process')
    if not settings['smtp_host'] or not settings['email_to'] or not settings['email_from']:
        raise ValueError('SMTP host, sender and recipient are required')
    message=EmailMessage()
    message['Subject']='Immigration Source Monitor — daily evidence digest'
    message['From']=settings['email_from'];message['To']=settings['email_to'];message['Message-ID']=message_id
    message.set_content(body)
    context=ssl.create_default_context()
    client=None;data_started=False
    try:
        if settings['smtp_mode']=='ssl':
            client=smtplib.SMTP_SSL(settings['smtp_host'],settings['smtp_port'],timeout=30,context=context)
        else:
            client=smtplib.SMTP(settings['smtp_host'],settings['smtp_port'],timeout=30)
            client.ehlo();client.starttls(context=context);client.ehlo()
        if settings['smtp_user']:client.login(settings['smtp_user'],password)
        data_started=True
        client.send_message(message,to_addrs=[settings['email_to']])
    except (smtplib.SMTPRecipientsRefused,smtplib.SMTPSenderRefused,smtplib.SMTPAuthenticationError,smtplib.SMTPDataError) as exc:
        raise ValueError('SMTP rejected delivery ('+type(exc).__name__+'); check configuration') from exc
    except (OSError,smtplib.SMTPException) as exc:
        if data_started:raise RuntimeError('Delivery outcome uncertain; verify recipient mailbox before any manual retry') from exc
        raise ValueError('SMTP connection failed ('+type(exc).__name__+')') from exc
    finally:
        if client:
            try:client.quit()
            except (OSError,smtplib.SMTPException):pass


def deliver_pending(store,sender=smtp_delivery):
    if not store.settings()['email_enabled']:return {'status':'disabled'}
    try:
        with FileLock(str(store.root/'delivery.lock'),timeout=0):
            with store.connect() as db:
                # SMTP has no exactly-once contract. A crash after DATA may have sent mail.
                db.execute("UPDATE deliveries SET state='uncertain',detail='Interrupted during send; verify mailbox before retry',updated=? WHERE state='sending'",(now(),))
            for item in store.rows("SELECT d.*,g.body FROM deliveries d JOIN digests g ON g.id=d.digest_id WHERE d.state='pending' ORDER BY d.id"):
                with store.connect() as db: db.execute("UPDATE deliveries SET state='sending',attempts=attempts+1,updated=? WHERE id=?",(now(),item['id']))
                try:
                    sender(store.settings(),item['body'],item['message_id'])
                    state,detail='sent','SMTP server accepted message; inbox receipt is not guaranteed'
                except ValueError as exc:state,detail='failed',str(exc)
                except Exception:state,detail='uncertain','Outcome uncertain; verify recipient mailbox before retry'
                with store.connect() as db:db.execute('UPDATE deliveries SET state=?,detail=?,updated=? WHERE id=?',(state,detail,now(),item['id']))
            return {'status':'processed'}
    except Timeout:return {'status':'already running'}
