import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from filelock import FileLock

from .db import now, SCHEMA

MAX_RESTORE=2*1024*1024*1024


def create_backup(store):
    # SQLite online backup is consistent even while the UI is reading/writing.
    folder=store.root/'backups';folder.mkdir(exist_ok=True)
    import uuid
    name='ism-'+now().replace(':','').replace('+','_')+'-'+uuid.uuid4().hex[:8]+'.zip'
    target=folder/name
    with tempfile.TemporaryDirectory(dir=store.root) as tmp:
        copy=Path(tmp)/'monitor.sqlite3'
        with store.connect() as source, sqlite3.connect(copy) as dest:source.backup(dest)
        digest=hashlib.sha256(copy.read_bytes()).hexdigest()
        manifest={'format':1,'created':now(),'sha256':digest,'credentials_included':False,'note':'Includes public evidence and private annotations. Protect this backup.'}
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.write(copy,'monitor.sqlite3');archive.writestr('manifest.json',json.dumps(manifest))
    return target


def validate_backup(path):
    with zipfile.ZipFile(path) as archive:
        if sorted(archive.namelist())!=['manifest.json','monitor.sqlite3']:
            raise ValueError('Unexpected archive members; paths and extra files are forbidden')
        info=archive.getinfo('monitor.sqlite3')
        if info.file_size>MAX_RESTORE or archive.getinfo('manifest.json').file_size>10000:
            raise ValueError('Backup exceeds restore limits')
        if info.compress_size and info.file_size/info.compress_size>1000:
            raise ValueError('Suspicious compression ratio')
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('format')!=1:raise ValueError('Unsupported backup format')
        data=archive.read('monitor.sqlite3')
        if hashlib.sha256(data).hexdigest()!=manifest.get('sha256'):raise ValueError('Backup checksum mismatch')
        return data


def restore_backup(store,path):
    # Stop the app/checker first. Operation and delivery locks protect other processes.
    data=validate_backup(path)
    with FileLock(str(store.root/'ui.lock'),timeout=0),FileLock(str(store.root/'operation.lock'),timeout=0),FileLock(str(store.root/'delivery.lock'),timeout=0):
        with tempfile.TemporaryDirectory(dir=store.root) as tmp:
            candidate=Path(tmp)/'restore.sqlite3';candidate.write_bytes(data)
            with sqlite3.connect(candidate) as db:
                db.execute('PRAGMA trusted_schema=OFF')
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
                if db.execute('PRAGMA user_version').fetchone()[0]!=1:raise ValueError('Unsupported schema version')
                tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                expected={'settings','hosts','sources','versions','attempts','events','reviews','entries','candidates','digests','deliveries'}
                if tables!=expected:raise ValueError('Unexpected database schema')
                with sqlite3.connect(':memory:') as reference:
                    reference.executescript(SCHEMA)
                    expected_schema=reference.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name").fetchall()
                actual_schema=db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name").fetchall()
                if actual_schema!=expected_schema:raise ValueError('Untrusted or incompatible database schema')
                if db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Broken evidence references')
                # Verify immutable evidence itself, not merely the archive checksum.
                for raw,raw_hash,text,text_hash in db.execute('SELECT raw,raw_hash,text,text_hash FROM versions'):
                    if hashlib.sha256(raw).hexdigest()!=raw_hash or hashlib.sha256(text.encode()).hexdigest()!=text_hash:
                        raise ValueError('Evidence hash mismatch')
                # Restoring an old outbox must never automatically resend old messages.
                db.execute("UPDATE deliveries SET state='uncertain',detail='Restored queue: reconcile mailbox before retry' WHERE state!='sent'")
                db.execute("UPDATE settings SET value='false' WHERE key='email_enabled'")
                db.commit()
            safety=create_backup(store)
            os.replace(candidate,store.path)
    return safety
