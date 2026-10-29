import difflib
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from filelock import FileLock, Timeout

from .db import now, digest_hash
from .extract import PARSER_VERSION, EFFECTIVE_UNKNOWN, bounded_extract, config_hash
from .fetch import CheckError, Fetcher, canonical
from .express_entry import handles as compound_source, prepare_response

UNHEALTHY={'failed or blocked','extraction uncertain','source unavailable or redirected'}


def future(seconds,stamp=None):
    return (datetime.fromisoformat(stamp or now())+timedelta(seconds=seconds)).isoformat(timespec='seconds')


def changed_excerpts(old,new):
    if len(old)+len(new)>200000:
        return old[:12000],new[:12000],['Large monitored content (excerpts truncated; compare saved originals)']
    oldlines=old.splitlines(); newlines=new.splitlines(); removed=[];added=[];sections=[]
    matcher=difflib.SequenceMatcher(None,oldlines,newlines,autojunk=True)
    for tag,a,b,c,d in matcher.get_opcodes():
        if tag=='equal': continue
        removed.extend(oldlines[max(0,a-1):min(len(oldlines),b+1)])
        added.extend(newlines[max(0,c-1):min(len(newlines),d+1)])
        heading=next((s.lstrip('# ') for s in reversed(newlines[:c+1]) if s.startswith('#')),'Monitored content')
        if heading not in sections: sections.append(heading)
    return '\n'.join(removed)[:12000], '\n'.join(added)[:12000],sections


def priority(old,new,rules):
    # Only changed tokens, not unchanged context, influence review aids.
    if len(old)+len(new)>200000:return 'Large content change: manual review required; automatic keyword analysis omitted'
    a=old.split();b=new.split();tokens=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=True).get_opcodes():
        if tag!='equal': tokens.extend(a[i:j]+b[k:l])
    changed=' '.join(tokens); hits=[]
    if rules.get('numbers') and re.search(r'\d',changed): hits.append('Changed number/date/amount')
    for word in rules.get('keywords',[]):
        if word and word.casefold() in changed.casefold(): hits.append('Keyword: '+word)
    return '; '.join(hits)


def event(db,source,kind,stamp,old_id,new_id,summary,old_text='',new_text='',meta=None,rules=None):
    old_excerpt,new_excerpt,sections=changed_excerpts(old_text,new_text)
    evidence={'title':source['title'],'agency':source['agency'],'url':source['url'],'tags':source['tags'],
        'old_excerpt':old_excerpt,'new_excerpt':new_excerpt,'sections':sections,
        'effective_wording':EFFECTIVE_UNKNOWN}
    evidence.update(meta or {})
    for key,version in [('old_raw_hash',old_id),('new_raw_hash',new_id)]:
        row=db.execute('SELECT raw_hash FROM versions WHERE id=?',(version,)).fetchone() if version else None
        evidence[key]=row[0] if row else None
    if kind=='document_bytes_changed':
        evidence['old_excerpt']=old_text[:3000]
        evidence['new_excerpt']=new_text[:3000]
        evidence['sections']=['PDF file bytes; extracted text identical']
    cur=db.execute('INSERT INTO events(source_id,kind,detected,previous_observed,old_version,new_version,summary,priority,evidence) VALUES (?,?,?,?,?,?,?,?,?)',
        (source['id'],kind,stamp,source['last_success'],old_id,new_id,summary,priority(old_text,new_text,rules or {}) if kind in ('content_changed','new_entry','document_bytes_changed') else '',json.dumps(evidence)))
    db.execute('INSERT INTO reviews(event_id,updated) VALUES (?,?)',(cur.lastrowid,stamp))
    return cur.lastrowid


def save_version(db,source,r,ex,stamp,uncertain=None):
    meta={'response':{k:v for k,v in r.headers.items() if k in ['content-type','etag','last-modified','content-length','date']},
        'redirects':r.redirects,'entries':ex.entries if ex else [],'links':ex.links if ex else [],'warnings':ex.warnings if ex else [uncertain],
        'format':ex.format if ex else 'unknown','valid':bool(ex)}
    meta.update(r.capture_metadata)
    if ex: meta.update(ex.metadata)
    text=ex.text if ex else ''
    cur=db.execute('INSERT INTO versions(source_id,retrieved,original_url,final_url,raw,raw_hash,text,text_hash,metadata,config_hash,extraction_version) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (source['id'],stamp,source['url'],r.url,r.body,digest_hash(r.body),text,digest_hash(text),json.dumps(meta),config_hash(source),PARSER_VERSION))
    return cur.lastrowid


def discover(db,source,ex,stamp,baseline,new_keys,current_version=None):
    for entry in ex.entries:
        db.execute('INSERT OR IGNORE INTO entries VALUES (?,?,?,?,?,?)',(source['id'],entry['key'],entry['title'],entry['url'],entry['publication'],stamp))
    approved={r[0] for r in db.execute('SELECT host FROM hosts')}
    # Compare consecutive observations, not candidate existence. This preserves
    # link reversions and avoids suppressing an alert when discovery ran first.
    previous=db.execute('SELECT text,metadata FROM versions WHERE id=?',(source['baseline_id'],)).fetchone() if source['baseline_id'] else None
    if previous and not baseline:
        old_meta=json.loads(previous['metadata'])
        for child in db.execute('SELECT * FROM sources WHERE parent_id=? AND removed=0',(source['id'],)).fetchall():
            label=child['link_label']
            if not label:continue
            targets={link['url'] for link in ex.links if link['title']==label}
            if 'links' in old_meta:
                old_targets={link['url'] for link in old_meta['links'] if link['title']==label}
            else:
                # Older immutable captures predate structured links metadata.
                old_targets=set(re.findall(re.escape(label)+r'\s*\[([^\]]+)\]',previous['text']))
            if targets==old_targets:continue
            event(db,source,'download_link_changed',stamp,source['baseline_id'],current_version,
                  'Download link changed for '+label+'; review the observed destinations.',
                  '\n'.join(sorted(old_targets)) or '(No matching link in previous observation)',
                  '\n'.join(sorted(targets)) or '(No matching link in current observation)',meta={**ex.metadata,'warnings':ex.warnings})
            for target in targets-old_targets:
                if urlsplit(target).hostname in approved and target!=child['url']:
                    db.execute('INSERT OR IGNORE INTO candidates(parent_id,title,url,kind,discovered) VALUES (?,?,?,?,?)',
                               (source['id'],label,target,'replacement guide',stamp))
    for link in ex.links:
        if urlsplit(link['url']).hostname not in approved:continue
        guide=bool(re.search(r'(skills immigration.*guide|application guide|program guide)',link['title'],re.I))
        article=source['source_type']=='announcement' and link['url'] in new_keys and not baseline
        if guide or article:
            publication=next((e['publication'] for e in ex.entries if e['url']==link['url']),None)
            db.execute('INSERT OR IGNORE INTO candidates(parent_id,title,url,kind,publication,discovered) VALUES (?,?,?,?,?,?)',
                (source['id'],link['title'],link['url'],'guide' if guide else 'announcement',publication,stamp))


def superseded(source,current):
    return config_hash(source)!=config_hash(current) or source['baseline_id']!=current['baseline_id']


def record_superseded(db,source,response,attempted,stamp,detail=''):
    status='configuration changed; awaiting check'
    explanation='Check superseded by a source edit or newer baseline; current source state was preserved.'
    if detail:explanation+=' '+detail
    version=save_version(db,source,response,None,stamp,explanation) if response and response.body else None
    db.execute('INSERT INTO attempts(source_id,attempted,status,detail,version_id) VALUES (?,?,?,?,?)',
               (source['id'],attempted,status,explanation,version))
    return status


def check_one(store,source,fetcher,extractor=bounded_extract):
    stamp=now(); attempted=stamp; old=store.one('SELECT * FROM versions WHERE id=?',(source['baseline_id'],)) if source['baseline_id'] else None
    r=None; version_id=None
    if source.get('retry_until') and source['retry_until']>stamp: return 'deferred by Retry-After'
    headers={}
    full_due=not source['full_checked'] or source['full_checked']<future(-86400,stamp)
    if old and not full_due and old['config_hash']==config_hash(source) and not compound_source(source['url']):
        if source['etag']: headers['If-None-Match']=source['etag']
        elif source['http_modified']: headers['If-Modified-Since']=source['http_modified']
    rules=store.settings()['priority_rules']
    try:
        r=fetcher.fetch(source['url'],headers)
        prepare_response(r,source,fetcher)
        if r.status==304:
            if not old or not headers or old['final_url']!=r.url:
                raise CheckError('304 without a valid corresponding conditional baseline','extraction uncertain')
            ex=None; status='checked successfully; unchanged'
        else:
            ex=extractor(r.body,r.url,source,r.headers.get('content-type',''))
            if old and old['config_hash']==config_hash(source) and ex.format=='express-entry-bundle':
                previous_ids=set(json.loads(old['metadata']).get('round_ids',[]))
                if previous_ids-set(ex.metadata['round_ids']):
                    raise CheckError('Express Entry historical rounds disappeared; incomplete data or an archive change requires review','extraction uncertain')
            if old and old['config_hash']==config_hash(source) and len(ex.text)<len(old['text'])*0.45:
                raise CheckError('Suspiciously incomplete extraction: more than 55% of previous text missing; inspect saved capture before adjusting scope','extraction uncertain')
            status='baseline created' if old is None else 'checked successfully; unchanged'
        stamp=now()  # completed observation, not the earlier request start
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=dict(db.execute('SELECT * FROM sources WHERE id=?',(source['id'],)).fetchone())
            if superseded(source,current):return record_superseded(db,source,r,attempted,stamp)
            if ex:
                version_id=save_version(db,source,r,ex,stamp)
                baseline=old is None
                rebaseline=old is not None and old['config_hash']!=config_hash(source)
                known={row[0] for row in db.execute('SELECT entry_key FROM entries WHERE source_id=?',(source['id'],))}
                new_entries=[e for e in ex.entries if e['key'] not in known]
                if rebaseline:
                    status='internal rebaseline'
                    event(db,source,'internal_rebaseline',stamp,old['id'],version_id,'Extraction/configuration changed; internal rebaseline, not an official content-change claim.')
                elif old:
                    oldmeta=json.loads(old['metadata'])
                    text_changed=old['text_hash']!=digest_hash(ex.text)
                    raw_changed=old['raw_hash']!=digest_hash(r.body)
                    if ex.entries:
                        for e in new_entries:
                            event(db,source,'new_entry',stamp,old['id'],version_id,'New listing entry observed: '+e['title'], '',e['title']+' ['+e['url']+']',
                                {**ex.metadata,'publication':e['publication'],'entry_url':e['url']},rules)
                        oldmap={e['key']:e for e in oldmeta.get('entries',[])}
                        newmap={e['key']:e for e in ex.entries}
                        # New entries have their own events. Compare retained/removed entries for quiet edits.
                        text_changed=any(k not in newmap or newmap[k]!=v for k,v in oldmap.items()) or any(k in known and k not in oldmap for k in newmap)
                        if new_entries: status='change detected'
                    if text_changed:
                        _,_,sections=changed_excerpts(old['text'],ex.text)
                        event(db,source,'content_changed',stamp,old['id'],version_id,'Text changed in '+', '.join(sections[:3])+'.',old['text'],ex.text,{**ex.metadata,'warnings':ex.warnings},rules)
                        status='change detected'
                    elif ex.format=='pdf' and raw_changed:
                        event(db,source,'document_bytes_changed',stamp,old['id'],version_id,'PDF bytes changed with identical extracted text; manual visual review required.',old['text'],ex.text,{**ex.metadata,'warnings':ex.warnings},rules)
                        status='change detected'
                    elif oldmeta.get('modified')!=ex.metadata.get('modified'):
                        event(db,source,'metadata_changed',stamp,old['id'],version_id,'Page-level modified date changed; substantive extracted content is unchanged.',meta=ex.metadata)
                discover(db,source,ex,stamp,baseline or rebaseline,{e['key'] for e in new_entries},version_id)
            if source['health'] in UNHEALTHY:
                event(db,source,'recovered',stamp,old['id'] if old else None,version_id,'Source recovered; compared against the last valid baseline.')
            db.execute('UPDATE sources SET last_attempt=?,last_success=?,next_due=?,health=?,detail=?,baseline_id=?,etag=?,http_modified=?,full_checked=?,retry_until=NULL WHERE id=?',
                (attempted,stamp,future(current['frequency'],stamp),status,'; '.join(ex.warnings) if ex else '',version_id or source['baseline_id'],
                 r.headers.get('etag') if ex else source['etag'],r.headers.get('last-modified') if ex else source['http_modified'],stamp if ex else source['full_checked'],source['id']))
            db.execute('INSERT INTO attempts(source_id,attempted,status,detail,version_id,metadata) VALUES (?,?,?,?,?,?)',
                (source['id'],attempted,status,'',version_id,json.dumps({'http_status':r.status,'final_url':r.url})))
        return status
    except Exception as exc:
        if not isinstance(exc,CheckError):exc=CheckError('Internal check failure ('+type(exc).__name__+'); baseline retained')
        stamp=now()
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=dict(db.execute('SELECT * FROM sources WHERE id=?',(source['id'],)).fetchone())
            if superseded(source,current):return record_superseded(db,source,r,attempted,stamp,str(exc))
            if r and r.body: version_id=save_version(db,source,r,None,stamp,str(exc))
            if source['health'] not in UNHEALTHY:
                event(db,source,'unhealthy',stamp,old['id'] if old else None,version_id,'Source could not be checked: '+str(exc),meta={'warnings':[str(exc)]})
            next_due=max(future(current['frequency'],stamp),exc.retry_at or '')
            db.execute('UPDATE sources SET last_attempt=?,next_due=?,health=?,detail=?,retry_until=? WHERE id=?',
                (attempted,next_due,exc.status,str(exc),exc.retry_at,source['id']))
            db.execute('INSERT INTO attempts(source_id,attempted,status,detail,version_id,metadata) VALUES (?,?,?,?,?,?)',
                (source['id'],attempted,exc.status,str(exc),version_id,json.dumps(exc.metadata)))
        return exc.status


def capture_articles(store,fetcher,extractor=bounded_extract):
    # One hop only, five per run. A persistent round-robin cursor prevents a
    # permanently blocked early batch from starving every later discovery.
    cursor=store.settings().get('article_capture_cursor',0)
    for c in store.rows("SELECT c.* FROM candidates c JOIN sources s ON s.id=c.parent_id WHERE c.kind='announcement' AND c.capture_status!='captured' AND s.removed=0 AND s.paused=0 ORDER BY CASE WHEN c.id>? THEN 0 ELSE 1 END,c.id LIMIT 5",(cursor,)):
        if not store.one('SELECT id FROM sources WHERE id=? AND removed=0 AND paused=0',(c['parent_id'],)):continue
        try:
            r=fetcher.fetch(c['url'])
            ex=extractor(r.body,r.url,{'scope':'main content'},r.headers.get('content-type',''))
            with store.connect() as db:
                article_meta={'original_url':c['url'],'final_url':r.url,'retrieved':now(),
                    'raw_hash':digest_hash(r.body),'text_hash':digest_hash(ex.text),'parser':PARSER_VERSION,
                    'config_hash':config_hash({'scope':'main content'}),
                    'response':{k:v for k,v in r.headers.items() if k in ['content-type','etag','last-modified','date']},
                    'warnings':ex.warnings,**ex.metadata}
                db.execute('UPDATE candidates SET raw=?,text=?,metadata=?,capture_status=? WHERE id=?',
                    (r.body,ex.text,json.dumps(article_meta),'captured',c['id']))
                for alert in db.execute("SELECT id,evidence FROM events WHERE source_id=? AND kind='new_entry'",(c['parent_id'],)).fetchall():
                    evidence=json.loads(alert['evidence'])
                    if evidence.get('entry_url')==c['url']:
                        evidence['article_capture']=article_meta
                        if not evidence.get('publication'):evidence['publication']=ex.metadata.get('publication')
                        if ex.metadata.get('effective_wording')!=EFFECTIVE_UNKNOWN:
                            evidence['effective_wording']=ex.metadata['effective_wording']
                        db.execute('UPDATE events SET evidence=? WHERE id=?',(json.dumps(evidence),alert['id']))
                approved={row[0] for row in db.execute('SELECT host FROM hosts')}
                for link in ex.links[:100]:
                    if urlsplit(link['url']).hostname in approved and re.search(r'(instructions|manual|guide|requirements)',link['title'],re.I):
                        db.execute('INSERT OR IGNORE INTO candidates(parent_id,title,url,kind,discovered) VALUES (?,?,?,?,?)',
                            (c['parent_id'],link['title'],link['url'],'instruction',now()))
        except Exception as exc:
            detail=str(exc) if isinstance(exc,CheckError) else 'Article capture failed ('+type(exc).__name__+')'
            with store.connect() as db:
                db.execute('UPDATE candidates SET capture_status=? WHERE id=?',(detail,c['id']))
        store.set_settings({'article_capture_cursor':c['id']})


def run_checks(store,source_id=None,force=False,fetcher=None,extractor=bounded_extract,lock_timeout=0):
    try:
        with FileLock(str(store.root/'operation.lock'),timeout=lock_timeout):
            fetcher=fetcher or Fetcher([r['host'] for r in store.rows('SELECT host FROM hosts')],store=store)
            sql='SELECT * FROM sources WHERE removed=0 AND paused=0';params=[]
            if source_id is not None: sql+=' AND id=?';params.append(source_id)
            elif not force: sql+=' AND (next_due IS NULL OR next_due<=?)';params.append(now())
            results=[]
            for selected in store.rows(sql+' ORDER BY id',params):
                # The user may edit or pause later sources while earlier ones fetch.
                source=store.one('SELECT * FROM sources WHERE id=? AND removed=0 AND paused=0',(selected['id'],))
                if not source:continue
                results.append((source['id'],check_one(store,source,fetcher,extractor)))
            capture_articles(store,fetcher,extractor)
            return {'status':'completed','sources':results}
    except Timeout:
        return {'status':'already running','sources':[]}


def coverage(store,at=None):
    stamp=at or now(); rows=store.rows('SELECT * FROM sources WHERE removed=0 AND paused=0')
    return {'checked_successfully':sum(bool(s['last_success']) and s['health'] in ('baseline created','checked successfully; unchanged','change detected','internal rebaseline') for s in rows),
        'failed':sum(s['health'] in UNHEALTHY for s in rows),
        'overdue':sum(not s['next_due'] or s['next_due']<stamp for s in rows),
        'never_checked':sum(s['last_attempt'] is None for s in rows),'total':len(rows)}
