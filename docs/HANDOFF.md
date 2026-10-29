# Handoff

Status: READY (remote SHA verified after publication).
Continuation branch: `codex/immigration-monitor`. Use the latest tip containing this handoff; no stable-branch merge authorized. The originally empty repository may use this development branch as GitHub's default.

Milestone: local application implemented; P06 live-source verification blocked; P07 operator documentation/validation in progress.

Implemented: Python/Flask/Waitress loopback UI, source CRUD/grouping/pause/removal with retained history, explicit host registry, approval-gated guides/instructions, inbox/review notes, side-by-side and inline diffs, history/search/download/export, health/overdue coverage, settings and digest archive, consistent backup and checked restore. Independent CLI checker uses SQLite/file locks, six-hour defaults, one catch-up, persistent health transitions and notification outbox. SMTP is opt-in; interrupted sends become uncertain, never automatically resent. Windows setup/launcher/task/DPAPI password scripts are supplied. Full core evidence behavior was implemented in prior checkpoint `7b9ff1258ff3a9844fa8df678700c2e56f776e33`.

Checks: `/workspace/ism-venv/bin/python -m pytest -q` → **37 passed** on Linux. `compileall` passed. CLI fictional demo at `/tmp/ism-demo-acceptance` completed baseline → wording edit → simulated failure → recovery → reviewed alert → digest. UI server starts on loopback under escalated execution (sandbox denies binding); actual HTTP smoke is next. Windows/real SMTP are NOT tested.

Live report: `docs/source-verification.json` and `.md`, all nine starter URLs blocked. Local DNS is unavailable; explicitly trusted proxy mode delegates resolution/egress enforcement to the managed proxy. Both government-host robots probes return **CONNECT 403 Forbidden**. No government page content, redirects, current guide links, or dynamic Express Entry data has been verified. An environment draft adds only `www.canada.ca` and `www.welcomebc.ca`; it is saved but NOT applied/published. User must review/save/publish in environment settings. Do not bypass restrictions or invent replacement URLs. After policy activation, rerun live verification and inspect official data requests. BC guide candidates must be approved in the app; none were fabricated.

Next priorities:
1. Finish README, security/limitations/Windows/backup instructions and exact validation report; perform local HTTP smoke.
2. Add edge-case tests for Retry-After, dynamic populated-shell rejection, restored-schema validation and digest boundaries; inspect correctness/security; fix verified defects.
3. When official-host access is enabled, run `ISM_TRUSTED_PROXY=1 python -m immigration_monitor verify-sources --output docs/source-verification.json`. Inspect dynamic pages and only implement adapters using observed official endpoints; do not claim current live coverage until verified. Discover BC guides, leave approval to user.
4. Test Windows scripts on Windows and opt-in SMTP with the user's chosen provider when available. No credentials should be put in Git.

Environment: recreate with Python 3.11+ and `python -m pip install --require-hashes -r requirements.txt`. Run `python -m immigration_monitor init`, `serve`, `check`. Runtime data defaults outside checkout; `ISM_DATA_DIR` can select another external folder. `/workspace/ism-venv` and `/tmp/ism-demo-acceptance` are current-task only, not shared project memory. `docs/PROJECT_SPEC.md` is authoritative. No Docker/cloud host/AI needed.

Important decisions/limits: immutable raw blobs are in SQLite for consistent backup. Failed captures never replace baselines. Direct HTTP sockets pin validated public IPs and verify TLS hostname; trusted proxies own DNS/address enforcement, so opt-in `ISM_TRUSTED_PROXY=1` is only for a managed/trusted egress proxy. Redirects require review. PDF pages with no reliable text fail; all PDF table/layout extraction needs visual verification. Dynamic empty placeholders and unverified Express Entry round tables are uncertain, not unchanged. SMTP has no exactly-once delivery guarantee; manual uncertain-message reconciliation is required. Backup restores disable email and hold unsent deliveries; scheduler registration/DPAPI credentials are separate. Large diffs use bounded previews and retained full originals. No retention deletion exists; history is kept.

Unpublished work: none intended after this checkpoint's push; confirm `git ls-remote origin refs/heads/codex/immigration-monitor`. If push fails, mark NEEDS_PUBLISHING and export a Git bundle. Continue the existing implementation; do not restart it.
