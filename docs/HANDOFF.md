# Handoff

Status: READY (publishing agent verifies the remote after each push).
Continuation: `codex/immigration-monitor`; current checkpoint is the tip commit containing this file. Do not merge into a stable branch without approval.

Milestone: P02 core evidence engine complete against deterministic fixtures; P03 UI next.

Implemented: hash-locked Python dependencies; SQLite source registry, immutable raw/extracted versions, attempts, separate reviews/candidates/notification schema; safe bounded fetching, robots checks, conditional requests and daily full checks; HTML/feed/PDF extraction in a time-limited worker; stable listing identities; failure/recovery, quiet edits, metadata edits, PDF-byte review, parser rebaseline and reversion events; one-hop article capture/candidates; process locking and one catch-up run. Exact nine starter URLs are in `immigration_monitor/starter_sources.json`.

Files: `db.py`, `fetch.py`, `extract.py`, `monitor.py`, `tests/test_monitor.py`. Test fixtures are fictional, generated in tests.

Verified: `/workspace/ism-venv/bin/python -m pytest -q` → **28 passed** (Linux). Dependency imports passed. Initial foundation SHA `6c0f61c05df2cf0c8a81757a651256696a07f0ab` was confirmed remotely.

Next, in order: P03 Flask loopback UI/source CRUD/candidate approvals/inbox/diff/history/export; P04 persistent digests/SMTP states and Windows scripts; P05 consistent backup/restore/security tests; P06 live URL verification plus fictional demo; P07 docs and acceptance validation. No web application or CLI launcher exists yet.

Decisions/limits: raw evidence is stored as SQLite blobs so a consistent database backup captures all evidence. Failed 200 captures are retained without advancing baselines. Default direct fetches pin public DNS IPs while verifying TLS hostname. An explicitly trusted outbound proxy (`ISM_TRUSTED_PROXY=1`) delegates DNS/egress enforcement to that proxy; never enable for an untrusted proxy. Unexpected redirects require review. PDFs always warn about table/layout fidelity; no OCR. Discovery is bounded and candidates require approval; no whole-site crawling.

Environment: Python 3.11+, `python -m pip install --require-hashes -r requirements.txt`. Dev venv currently `/workspace/ism-venv` (not portable; recreate). Git network commands need configured proxy/network permission. Official-source domains are not in the managed network allowlist yet. Windows/real SMTP/live coverage unverified. No credentials stored. Data must be outside repository.

Unpublished work: none intended at this checkpoint; verify remote SHA. If push fails, mark NEEDS_PUBLISHING and export a Git bundle. Remote was originally empty, so GitHub may select the development branch as its initial default; no stable branch has been created or merged.
