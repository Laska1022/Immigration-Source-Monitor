# Handoff

**Status: READY** — a published continuation checkpoint, not completed release acceptance. Verify publication with the commands below.

Continuation branch: **codex/immigration-monitor**. The latest commit containing this file identifies the checkpoint. Started from verified remote `f1db6b2453f7da722a1a3c94708ce9e2356f652a`. No stable-branch merge or cloud configuration publication is part of this checkpoint.

## Current milestone

The network blocker is resolved: the user published an environment with unrestricted public access, and current runtime observations report it enforced. **P06 is in progress: eight of nine starter pages now pass live fetching/extraction.** Express Entry remains uncertain pending integration of the JSON endpoint referenced by its official page. P07 still requires Windows and final live acceptance.

This continuation fixes issues exposed by real HTML: quadratic table-header scans on IRCC's updates index; a false dynamic-content warning from Canada.ca's page-feedback widget; the IEC public page's changed expected heading; and BC news/documents configurations that previously monitored breadcrumbs instead of inline content. New seeds retain CSS selectors. Existing saved sources are preserved by init; apply the three adjustments in **LIVE_SOURCE_NOTES**.

Parser version is `html-3/pdf-1/feed-1`. Parser/config changes create an internal rebaseline on the next valid capture; failed checks retain the last valid baseline. Unknown AJAX/JSON placeholders remain uncertain. No Express Entry adapter or automatically approved guide was added.

## Verified results

- Restored Python 3.12.14 virtualenv: pip check passed; baseline before changes was 55 passing tests.
- Current suite: **59 passed, 0 failed/skipped**. Added coverage for 1,500-row bounded extraction, feedback furniture versus missing policy data, BC inline content/guide links/missing selectors, and preserving seeded selectors and user edits.
- `python scripts/smoke-local.py`: passed fictional demo, six actual HTTP screens, content/CSP, attachment download, and cleanup.
- Live report completed **2026-10-29T09:50:44+00:00**: **8 fetch/extraction passes, 1 extraction uncertain** (Express Entry); command exited 1 as required for incomplete coverage. All nine official pages were reached. See source-verification.json and .md.
- Offline integration replay of observed public HTML: eight baselines, then eight unchanged captures; Express Entry stays uncertain; both requested BC guides remain pending with no child sources added. This proves integration, not a second live request or historical policy change.
- Observed Express Entry JSON endpoint: robots-checked HTTP 200, top-level classes/rounds, 454 records. Round coverage remains unverified until the adapter records and validates the data.
- Windows setup/launcher/scheduler/DPAPI, real SMTP delivery, and graphical browser testing remain **unrun**.

## Exact next steps, priority order

1. Inspect status/remotes, fetch the continuation branch, compare HEAD with the remote, and read AGENTS/PLAN/spec plus LIVE_SOURCE_NOTES. Preserve unrelated work; never force-push.
2. Implement Express Entry page-plus-data capture using the verified endpoint `https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json`. LIVE_SOURCE_NOTES records the actual page reference/schema. Validate the reference, required fields and every fetch; preserve exact HTML/JSON with URLs, observation times and hashes. Failed/malformed/changed endpoints must retain the baseline. Test changed round dates/counts/scores, historical revisions and distribution data. Do not just suppress empty-placeholder checks or silently replace the page with an unrecorded API response.
3. Rerun `ISM_TRUSTED_PROXY=1 .venv/bin/python -m immigration_monitor verify-sources --output docs/source-verification.json` through the reviewed managed proxy. Any uncertainty must keep its exit status nonzero.
4. Have the user review and approve the discovered Skills Immigration Program Guide and Application Guide candidates before monitoring. Exact links are in LIVE_SOURCE_NOTES and the JSON report. PDF contents, redirects and extraction quality are unverified. Candidate discovery also finds other guides/index links; identify the exact requested URLs.
5. On Windows, apply the three existing-source adjustments if needed, then run Setup.cmd, Launch.cmd and the HTTP smoke. Explicitly test scheduler install/remove, browser-closed checks, sleep/offline catch-up, DPAPI and backup/restore. Optional SMTP acceptance follows secure user configuration.
6. Update PLAN/HANDOFF/VALIDATION and publish tested code/docs checkpoints. Check remote advancement before push and verify afterward. Do not mark P06/P07 complete from fixture tests or one successful page capture alone.

## Environment and publication

Use the existing checkout at /workspace/Immigration-Source-Monitor, with .venv/bin/python and hash-locked requirements.txt. No worktree is needed. Runtime data stays outside the checkout, e.g. /workspace/ism-runtime; acceptance runs use separate external directories. Never commit credentials, session keys, databases or private notes.

The user published the cloud environment and asked that its settings not be changed or republished. No configuration writes were made here. Saved startup text may mention the earlier network blocker and 55-test baseline; current runtime evidence and this handoff supersede those historical statements. Fetch and inspect remote changes when restoring the published filesystem snapshot; it need not include this later Git checkpoint.

Verify publication with `git rev-parse HEAD` and `git ls-remote origin refs/heads/codex/immigration-monitor`. If publication fails, mark NEEDS_PUBLISHING and provide a Git bundle/manual recovery path. Git publication and cloud publication are separate. The actual long-term host remains the user's Windows computer with opt-in scheduling.
