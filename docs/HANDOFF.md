# Handoff

**Status: READY** — the publishing agent verifies the remote SHA after pushing this checkpoint. READY means published continuation, not full live-release acceptance.

Continuation branch: **`codex/immigration-monitor`**. Checkpoint identity: the latest commit containing this file (`git log -1`). No PR is required/created; no stable-branch merge authorized. The repository was originally empty, so GitHub may use this development branch as its initial default.

## Current milestone

Local application implemented; **P06 live-source validation is blocked**. P07's docs/local validation are complete; final release acceptance awaits P06 and Windows verification. Continue this implementation rather than replacing the stack or repeating completed fixture work.

Implemented: Python/Flask/Waitress loopback UI; SQLite immutable versions and retained failed captures; source CRUD/grouping/pause/soft removal; approved exact-host registry; selected sections/listings/independent PDFs; approval-gated candidates and bounded one-hop article capture; diff/review/history/export; six-hour independent checker and locks/catch-up; persistent first-unhealthy/recovery events; opt-in SMTP queue with explicit uncertain outcomes; timezone daily digest/coverage; backup/validated restore; Windows setup/launcher/scheduler/DPAPI password scripts; complete operator/security/limitation docs.

Important code: `db.py` schema; `fetch.py` network controls; `extract.py` bounded parsing (`html-2/pdf-1/feed-1`); `monitor.py` observation state machine; `notifications.py` digest/outbox; `backup.py` checked restore; `web.py` browser routes; `__main__.py` CLI. `starter_sources.json` contains exactly the nine requested URLs. No guide URLs were invented.

## Verified results

Latest resumption (2026-10-29): remote lookup/fetch confirmed published `fdddae33273798442d8187d8d41e3239711fd7b7` before work. Fresh hash-locked install, `pip check`, all 55 tests, and six-screen HTTP smoke passed; the saved install script was exercised successfully. Repeated initialization at `/workspace/ism-runtime` retained exactly nine sources, and the initialized UI returned expected inbox/source HTTP responses. At 08:57:26 UTC both official-host robots probes still returned proxy CONNECT 403. No new live content was obtained, no dynamic endpoint was guessed, and P06 remains blocked. This checkpoint updates setup/validation evidence only; it does not complete P06/P07. Full details are in VALIDATION.

Current cloud paths supersede the earlier environment notes below: Python is `/workspace/Immigration-Source-Monitor/.venv/bin/python`; runtime data is `/workspace/ism-runtime`. The current draft saves complete tested installation and startup instructions plus the two official-host network additions. The save confirmed publication is required; it has not applied the network policy or verified restoration in a new task.

- `python -m pytest -q`: **55 passed**, no failures/skips (Linux Python 3.12.14).
- Hash-locked pip install and `pip check`: passed. Saved environment install script was exercised successfully (then-current 53 tests); the final expanded suite is 55 passing tests.
- `python scripts/smoke-local.py`: passed fresh fictional demo, six actual HTTP screens, security headers, attachment download, own-server cleanup.
- Fictional CLI demo covers baseline → wording edit → failed check → recovery → browser review → digest. `init` is idempotent (nine unverified sources, no duplicate baselines).
- Backup round-trip and unsafe schema/path/integrity tests passed; compileall and whitespace checks passed.
- **Live:** all nine blocked. `docs/source-verification.json` / `.md` preserve each attempt and two diagnostic probes at **2026-10-29 07:48:32 UTC**, both returning managed-proxy CONNECT **403 Forbidden**. No official page/robots body, redirects, current guides, or dynamic data was verified.
- **Not run:** Windows execution; actual SMTP delivery. Fake-sender tests are not real-email evidence. No graphical browser test was performed.

See `docs/VALIDATION.md` for evidence and `docs/LIMITATIONS.md` for precise gaps.

## Exact next steps, priority order

1. Resume safely: inspect status/remotes, fetch, verify this is the latest remote `codex/immigration-monitor` tip, read AGENTS/PLAN/spec, install locked dependencies, run pytest. Preserve unexpected changes; never force-push.
2. Enable the requested official domains through the supported cloud environment settings. A draft adds only `www.canada.ca` and `www.welcomebc.ca` to custom destinations; it is **saved, not applied/published**. Review/save/publish, inspect current `environment_status`, then retry:
   `ISM_TRUSTED_PROXY=1 python -m immigration_monitor verify-sources --output docs/source-verification.json`
   Only use that flag for the reviewed managed proxy. The command now exits 1 for any blocked/failed source. Do not bypass access controls or infer withdrawal/no change.
3. Inspect live official page structure and public network/data requests. Implement dynamic handling only for observed verified official endpoints (or safely bounded rendering); no dynamic JSON adapter/browser renderer exists yet. Express Entry's unpopulated table and other empty placeholders intentionally yield uncertainty. Confirm main-content/list selectors and expected markers for all nine pages.
4. From the actual BC documents page discover Skills Immigration Program Guide and Application Guide. Present candidates in the app and require user approval before monitoring them. Verify same-URL replacements and changed download links against actual sources; fixture coverage already passes.
5. On Windows run Setup.cmd, Launch.cmd, explicit scheduler install/remove and DPAPI credential setup. Verify browser-closed checking, sleep/offline catch-up, restore, and task results. With optional user-configured SMTP, verify a real readable mobile digest and failure handling. Do not claim unrun checks passed.
6. Update PLAN/HANDOFF/VALIDATION/limitations and publish another tested checkpoint after each meaningful unit. Final live acceptance remains pending until supported by evidence.

## Decisions, setup, publication

- Stack: Python 3.11+, Flask, Waitress, SQLite, BeautifulSoup, pypdf, filelock. No cloud runtime, AI, Docker, paid services, or external DB requirement.
- `python -m pip install --require-hashes -r requirements.txt`; `python -m pytest -q`; `python -m immigration_monitor init/serve/check`. Read README for Windows paths and commands.
- Runtime data is outside checkout. Default Windows path: `%LOCALAPPDATA%\ImmigrationSourceMonitor`. `ISM_DATA_DIR` may override. Current-task `/workspace/ism-venv`, `/workspace/ism-runtime`, and `/tmp` demos are **not cross-account project memory**. Recreate them from committed instructions. The cloud draft saves complete `install_script` and `start_skill`; neither save executes/applies/publishes automatically. A new-task restore has not been tested.
- Every valid full observation is retained; 304 needs a corresponding baseline and daily full validation. Failures retain the old valid baseline. Parser/config changes explicitly rebaseline; A→B→A remains evidence. PDFs require visual table/layout review; no OCR. Failed captures are never rendered as a substantive deletion comparison.
- Default direct fetches pin validated public DNS addresses and verify TLS hostname. Explicit trusted proxy mode delegates resolution/public-address enforcement to that reviewed proxy because local DNS is unavailable here. The proxy denial must be fixed in settings, not bypassed.
- SQLite stores raw evidence blobs for coherent backups; reviews are separate. SMTP cannot ensure exactly-once delivery: interrupted sends become uncertain and require mailbox reconciliation, with no automatic resend. Restores disable email/hold unsent messages; credentials and OS task registration are separate. Restore size limit is 512 MiB extracted DB, exact schema compatibility required.
- No source code changes are left intentionally unpublished at this checkpoint. Verify `git rev-parse HEAD` equals `git ls-remote origin refs/heads/codex/immigration-monitor`. Previous published milestone: `670a9f18bf28948cad5a90aee0451d719f3096da`. If publication fails, mark NEEDS_PUBLISHING and provide a Git bundle; another account cannot recover local-only files.
