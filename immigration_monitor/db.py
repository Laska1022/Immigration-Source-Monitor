import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def data_dir():
    base = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share'))
    path = Path(os.environ.get('ISM_DATA_DIR', base / 'ImmigrationSourceMonitor')).expanduser().resolve()
    repo = Path(__file__).resolve().parent.parent
    if path == repo or repo in path.parents:
        raise ValueError('Runtime data must be outside the repository.')
    path.mkdir(parents=True, exist_ok=True)
    return path


SCHEMA = '''
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hosts(host TEXT PRIMARY KEY, agency TEXT NOT NULL, approved_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources(
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE, agency TEXT NOT NULL,
 tags TEXT NOT NULL DEFAULT '', group_name TEXT NOT NULL DEFAULT '', source_type TEXT NOT NULL,
 scope TEXT NOT NULL DEFAULT 'main content', selector TEXT NOT NULL DEFAULT '',
 expected TEXT NOT NULL DEFAULT '', ignore_selectors TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
 frequency INTEGER NOT NULL DEFAULT 21600 CHECK(frequency>=900), paused INTEGER NOT NULL DEFAULT 0,
 removed INTEGER NOT NULL DEFAULT 0, last_attempt TEXT, last_success TEXT, next_due TEXT,
 health TEXT NOT NULL DEFAULT 'never checked', detail TEXT NOT NULL DEFAULT '', baseline_id INTEGER,
 etag TEXT, http_modified TEXT, full_checked TEXT, retry_until TEXT, parent_id INTEGER, link_label TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS versions(
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id), retrieved TEXT NOT NULL,
 original_url TEXT NOT NULL, final_url TEXT NOT NULL, raw BLOB NOT NULL, raw_hash TEXT NOT NULL,
 text TEXT NOT NULL, text_hash TEXT NOT NULL, metadata TEXT NOT NULL, config_hash TEXT NOT NULL,
 extraction_version TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS immutable_versions_update BEFORE UPDATE ON versions BEGIN SELECT RAISE(ABORT,'Evidence is immutable'); END;
CREATE TRIGGER IF NOT EXISTS immutable_versions_delete BEFORE DELETE ON versions BEGIN SELECT RAISE(ABORT,'Evidence is immutable'); END;
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id),
 attempted TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL, version_id INTEGER, metadata TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id),
 kind TEXT NOT NULL, detected TEXT NOT NULL, previous_observed TEXT, old_version INTEGER, new_version INTEGER,
 summary TEXT NOT NULL, priority TEXT NOT NULL DEFAULT '', evidence TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS reviews(event_id INTEGER PRIMARY KEY REFERENCES events(id), state TEXT NOT NULL DEFAULT 'New',
 interpretation TEXT NOT NULL DEFAULT '', follow_up TEXT NOT NULL DEFAULT '', updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entries(source_id INTEGER NOT NULL, entry_key TEXT NOT NULL, title TEXT NOT NULL,
 url TEXT NOT NULL, publication TEXT, first_seen TEXT NOT NULL, PRIMARY KEY(source_id,entry_key));
CREATE TABLE IF NOT EXISTS candidates(id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL REFERENCES sources(id),
 title TEXT NOT NULL, url TEXT NOT NULL, kind TEXT NOT NULL, publication TEXT, discovered TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending', source_id INTEGER, raw BLOB, text TEXT, metadata TEXT NOT NULL DEFAULT '{}',
 capture_status TEXT NOT NULL DEFAULT 'not captured', UNIQUE(parent_id,url));
CREATE TABLE IF NOT EXISTS digests(id INTEGER PRIMARY KEY, day TEXT NOT NULL UNIQUE, created TEXT NOT NULL,
 body TEXT NOT NULL, coverage TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS deliveries(id INTEGER PRIMARY KEY, digest_id INTEGER NOT NULL UNIQUE REFERENCES digests(id),
 state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, detail TEXT NOT NULL DEFAULT '',
 message_id TEXT NOT NULL, updated TEXT NOT NULL);
PRAGMA user_version=1;
'''
DEFAULTS = {
    'timezone': 'Europe/Istanbul', 'digest_time': '09:00', 'email_enabled': False,
    'smtp_host': '', 'smtp_port': 587, 'smtp_mode': 'starttls', 'smtp_user': '',
    'email_to': '', 'email_from': '',
    'network_cooldowns': {},
    'priority_rules': {'numbers': True, 'keywords': ['deadline', 'eligible', 'eligibility', 'not', 'open', 'closed', 'must', 'required']},
}


class Store:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'monitor.sqlite3'
        with self.connect() as db:
            db.executescript(SCHEMA)
            for key, value in DEFAULTS.items():
                db.execute('INSERT OR IGNORE INTO settings VALUES (?,?)', (key, json.dumps(value)))
            for host, agency in [('www.canada.ca','IRCC / Canada'), ('www.welcomebc.ca','British Columbia')]:
                db.execute('INSERT OR IGNORE INTO hosts VALUES (?,?,?)', (host,agency,now()))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=30000')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def rows(self, sql, args=()):
        with self.connect() as db:
            return [dict(r) for r in db.execute(sql, args)]

    def one(self, sql, args=()):
        rows = self.rows(sql,args)
        return rows[0] if rows else None

    def settings(self):
        return {r['key']:json.loads(r['value']) for r in self.rows('SELECT * FROM settings')}

    def set_settings(self, values):
        with self.connect() as db:
            for key,value in values.items():
                if key not in DEFAULTS:
                    raise ValueError('Unknown setting')
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(key,json.dumps(value)))

    def seed(self):
        seeds = json.loads(Path(__file__).with_name('starter_sources.json').read_text())
        with self.connect() as db:
            for s in seeds:
                db.execute('INSERT OR IGNORE INTO sources(title,url,agency,tags,source_type,scope,selector,expected,next_due) VALUES (?,?,?,?,?,?,?,?,?)',
                    (s['title'],s['url'],s['agency'],s['tags'],s['source_type'],s['scope'],s.get('selector',''),s['expected'],now()))


def digest_hash(data):
    return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()
