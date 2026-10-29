# Handoff

**Status: READY** — publication is verified against the remote SHA after push. This means the checkpoint is available to another account, not that release acceptance is complete.

Continuation branch: **codex/immigration-monitor**. Current checkpoint is the latest commit containing this file. Resumed remote `29a48711d538d0e7898fd48c5514c66bdab73b27` by fast-forward; the adapter milestone `ff55c96495dc9d5aa26a2a11fd436a044d4606e0` is already verified on GitHub. No PR/merge or environment configuration changes.

## Current milestone / implementation

P06 Express Entry adapter is implemented; live acceptance remains pending. `express_entry.py` validates the exact page reference to the previously observed `https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json`. Each check retrieves both full responses, archives exact bytes with individual URLs/times/headers/hashes, then validates and compares static text and stable round records in the bounded worker. Failures preserve partial evidence and the previous baseline. Changed/missing endpoints, malformed fields, incomplete/latest distribution data, disappearing historical rounds, and 304-only observations are uncertain. Raw ZIP download and backup work without a schema change. No browser renderer is added.

P08 bug regression audit is complete. `monitor.py` now prevents stale in-flight checks from overwriting edited sources, refreshes paused/removed queued sources, records completion timestamps separately from request starts, emits/deduplicates/reverses guide replacement events from consecutive observations, and rotates pending article capture fairly across restarts. Source modifications and saved historical versions are preserved. `tests/test_regressions.py` and `docs/BUG_AUDIT.md` record reproductions/fixes. Comparison UI shows old/new guide links. All guide monitoring remains approval-gated.

Core app/Windows scripts are retained. HTML parser is `html-3/pdf-1/feed-1`; Express Entry adds its own `express-entry-1` configuration component. Unrelated sources do not need rebaselining for the adapter. A small `article_capture_cursor` setting persists queue fairness; no database schema migration is required.

## Verified results and limitations

- Baseline after fast-forward: **59 passed**.
- Adapter checkpoint: **25 new adapter cases**, 84 total passing.
- Final suite: **92 passed**, no failures/skips, including eight targeted bug-regression cases. Four initial cases and the separate starvation reproduction failed before fixes. `python -m pytest -q` completed successfully.
- `python scripts/smoke-local.py`: passed fictional demo, six real loopback HTTP pages, expected content/CSP, attachment download and cleanup. `compileall` and `git diff --check` passed.
- Prior published live evidence is retained: **8/9 successful captures**, Express Entry uncertain, on the earlier unrestricted instance (2026-10-29 09:50 UTC). The official JSON endpoint had 454 records; both requested guide links were discovered but not approved/checked. Do not repeat that research or treat it as this adapter's live acceptance.
- This task's runtime differs: current enforced policy is restricted with no custom official hosts. A robots-respecting Express Entry probe at **2026-10-29T12:27:02+00:00** failed with managed-proxy CONNECT **403 Forbidden**. No new live adapter success was obtained. The previous source-verification files were preserved unchanged.
- Windows setup/scheduler/DPAPI, real SMTP and graphical browser testing remain unrun. No environment settings were changed or published, respecting the user's recorded preference.

## Exact next steps

1. Inspect status/remotes; fetch/verify the latest continuation tip; read AGENTS/PLAN/spec and this handoff. Install locked dependencies and run the 92-test baseline. Preserve unexpected changes and never force-push.
2. Continue P06 in a runtime with the user's intended official-site access. Inspect current environment_status; do not infer access from the previous task or change/publish environment settings without instruction. Run `ISM_TRUSTED_PROXY=1 python -m immigration_monitor verify-sources --output docs/source-verification.json` only through the reviewed managed proxy. CLI exits 1 for any failed/uncertain source.
3. Validate actual Express Entry page declarations and JSON types/field completeness against the strict adapter. Fixtures follow the documented field names but are not copies of the live payload. Legitimate historical variants may conservatively fail; diagnose observed evidence rather than weakening checks to obtain green results. Compare consecutive live captures and data-only changes where verifiable. Keep exact artifacts and no-change/failure separation.
4. Ask for approval inside the app before monitoring the two BC Skills Immigration guide candidates in LIVE_SOURCE_NOTES. PDF redirects/content/extraction remain unverified. Apply its three existing-source adjustments if needed; init intentionally preserves user edits.
5. Complete Windows setup/launcher/HTTP smoke, scheduler install/remove/browser-closed checks/catch-up, DPAPI and restore. Optional real SMTP follows secure user configuration. P06/P07 remain incomplete until those actual checks support completion.
6. Publish each meaningful unit with tests and updated plan/handoff; confirm remote SHA. No unfinished code work is intentionally left local in this checkpoint.

## Reproduction / continuation rules

Use the existing checkout, no worktree. Python 3.11+, `python -m pip install --require-hashes -r requirements.txt`; tests `python -m pytest -q`; local HTTP smoke `python scripts/smoke-local.py`. This task used `/workspace/ism-venv/bin/python`; recreate it rather than relying on another account's files. Runtime data, credentials, snapshots and backups remain outside checkout. Fixtures require no secrets or live network.

Verify publication with `git rev-parse HEAD` and `git ls-remote origin refs/heads/codex/immigration-monitor`. If push fails, mark NEEDS_PUBLISHING and provide a Git bundle/manual action. Do not merge into stable without approval. READY means shared GitHub checkpoint; actual long-term runtime remains the user's Windows computer.
