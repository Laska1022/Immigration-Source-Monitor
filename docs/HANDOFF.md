# Handoff

**Status: READY** — publishing agent verifies remote SHA after push; release acceptance remains incomplete.
Continuation: **codex/immigration-monitor**. This checkpoint resumes verified remote `29a48711d538d0e7898fd48c5514c66bdab73b27`; local checkout was behind and fast-forwarded before edits. No PR/merge or environment configuration changes.

## Current milestone and actual implementation

P06 Express Entry adapter is implemented and fixture-tested; live validation is pending. `express_entry.py` captures only the official page and previously observed `/content/dam/ircc/documents/json/ee_rounds_123_en.json` reference. Both are fetched unconditionally, archived as exact bytes with a manifest (URLs/times/headers/hashes), and validated by the bounded worker before comparing static text and stable round records. Partial captures never replace the baseline. Missing history, malformed/partial data, changed endpoints, 304-only responses, and unknown dynamic placeholders remain uncertain. Distribution keys and extra fields are retained verbatim. Raw ZIP download and backup round-trip work without database schema changes.

Core app/Windows scripts remain as implemented in prior checkpoints. HTML parser stays `html-3/pdf-1/feed-1`; Express Entry has its own `express-entry-1` configuration component, so unrelated sources are not needlessly rebaselined. See README, PROJECT_SPEC, LIVE_SOURCE_NOTES and LIMITATIONS.

## Checks and runtime discrepancy

- Baseline after fast-forward: **59 passed**.
- Adapter tests: **25 passed**; full suite **84 passed**, no skipped/failed tests. Includes data-only changes, dates/counts/scores/distribution/history/reversions, reordered/new rounds, partial/invalid/changed-reference failures, archive hashes, ZIP download, bounded worker and restore.
- Previous published live evidence remains **8/9 successes**, Express Entry uncertain, on the earlier unrestricted instance (09:50 UTC). Both requested BC guide links were discovered but not approved/checked. Do not repeat that completed research.
- **This task's runtime differs**: current observations report restricted enforced access with no custom official hosts. A robots-respecting probe at **2026-10-29T12:27:02+00:00** returned managed-proxy CONNECT 403. No new live adapter success was obtained. The earlier source-verification report is preserved unchanged.
- Windows, real SMTP, graphical browser tests remain unrun. No settings were changed/published, respecting the user's previously recorded preference.

## Next steps

1. Finish P08 bug regression audit: inspect source editing during a fetch and guide replacement discovery/event ordering. Reproduce before fixing; add targeted tests. These are independent of blocked live access.
2. Run full tests and real local smoke after changes; update docs and publish another checkpoint.
3. When a runtime with the user's intended public access is attached, inspect environment_status and run `ISM_TRUSTED_PROXY=1 python -m immigration_monitor verify-sources --output docs/source-verification.json`. Do not change/publish environment settings without the user's instruction. Validate the new adapter against actual page declarations and data types/field completeness; its strict assumptions are currently fixture-tested only. Do not weaken validation solely to make a test pass.
4. Ask for approval inside the app before monitoring the two actual BC Skills Immigration guides listed in LIVE_SOURCE_NOTES; PDF redirects/content/extraction remain unverified. Apply its three existing-source adjustments if needed; init preserves user edits.
5. Complete Windows setup/launcher/scheduler/DPAPI/restore and optional configured SMTP acceptance. P06/P07 remain incomplete until their actual checks pass.

## Reproduction and handoff rules

Use existing checkout; no worktree. Python 3.11+; install `python -m pip install --require-hashes -r requirements.txt`. Tests: `python -m pytest -q`; actual HTTP smoke: `python scripts/smoke-local.py`. Current task uses `/workspace/ism-venv/bin/python`, which is not cross-account memory; recreate dependencies as needed. Data stays outside checkout. No secrets needed for fixture tests.

Inspect/fetch remote at every resume and before push, preserve unrelated changes, never force-push/merge stable without approval. Confirm `git rev-parse HEAD` equals the continuation ref from `git ls-remote origin refs/heads/codex/immigration-monitor`. No unpublished work is intended after this checkpoint; if publication fails, mark NEEDS_PUBLISHING and export a Git bundle. READY means GitHub availability, not completed live/Windows acceptance.
