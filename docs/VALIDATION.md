# Validation record — 2026-10-29 UTC

Environment: Linux, Python 3.12.14. Tests use isolated temporary SQLite databases and clearly fictional HTML/feed/PDF fixtures. No real annotations, client information, credentials, or production snapshots are in Git.

| Check | Actual result |
|---|---|
| `python -m pytest -q` | **92 passed**, 0 failed, 0 skipped; current suite completed |
| Hash-locked dependency install | Passed using `pip install --no-cache-dir --require-hashes -r requirements.txt` |
| `python -m pip check` | Passed: no broken requirements |
| Saved cloud install script | Re-executed successfully on resumption: hash-locked install, dependency check, all 55 tests, six-screen HTTP smoke, and external runtime initialization |
| `python -m compileall -q immigration_monitor tests scripts/smoke-local.py` | Passed |
| `git diff --check` | Passed before checkpoint |
| `python scripts/smoke-local.py` | Passed: fresh CLI fictional demo; six real loopback HTTP screens; expected content and CSP; attachment download; server stopped afterward |
| `python -m immigration_monitor ... demo` | Passed: baseline → wording change → failed check → recovery → reviewed alert via browser route → digest; fictional source paused |
| Startup `init` repeatability | Passed: two runs leave nine unverified starter sources, no duplicates or fabricated evidence |
| Backup/restore | Passed: sources, raw/extracted versions, hashes, attempts, annotations, settings preserved; unsafe archives/schema rejected; credentials excluded; email disabled and outbox held after restore |
| Optional live source verification | **8 fetch/extraction passes, 1 extraction uncertain** (Express Entry); all nine pages reached; live CLI exited 1 for incomplete coverage |
| Windows setup/launcher/scheduler/DPAPI execution | **Not run** — no Windows host available |
| Real SMTP delivery | **Not run** — optional provider/credentials not configured; fake-sender queue tests passed |

## Current live validation — 2026-10-29 09:50 UTC

The user published the cloud environment with unrestricted public access. Current observations report enforced policy, and the replacement instance restored the virtualenv successfully. No environment settings were changed here. Live verification reached all nine sources, with eight fetch/extraction passes and Express Entry uncertain. The verified fixes and three existing-source adjustments are documented in [LIVE_SOURCE_NOTES](LIVE_SOURCE_NOTES.md).

The 1,375-row IRCC table now extracts in about two seconds within unchanged limits; four added regression cases bring pytest to 59 passing tests. The six-screen HTTP smoke passes. An offline application replay of captured public HTML created eight baselines then eight unchanged results; Express Entry stayed uncertain, and both requested BC guides remained pending without child sources. This replay is distinct from the live report. The official Express Entry JSON endpoint returned HTTP 200 with 454 rounds, but no adapter exists yet. Guide PDFs, Windows execution and SMTP remain unverified.

## Express Entry adapter continuation

Resumed the published `29a4871` checkpoint; its 59-test baseline passed. Added 25 fictional fixture tests: exact page/JSON artifacts and hashes/times, unchanged HTML with changed data, numeric/date/score/distribution and historical edits, reversions, ordering/new rounds, missing/invalid fields, endpoint changes, failures/304s, missing historical rounds, unknown dynamic content, bounded extraction, raw ZIP download and backup round-trip. Full result: **84 passed**.

At 2026-10-29T12:27:02+00:00 this task's reviewed managed proxy returned CONNECT 403 for the Express Entry fetch prerequisite. Current runtime observations report enforced restricted access with no custom official hosts. This differs from the previous task's unrestricted runtime. The previous successful live-source report is retained unchanged; no new live adapter success is claimed. No environment settings were changed. The adapter's strict field assumptions must be checked against actual current data when access is available.

## Confirmed bug fixes

Eight targeted regression cases cover five defects/behaviors: a guide replacement alert swallowed by prior candidate insertion; an in-flight old check overwriting freshly edited source settings/health on success or failure; request-start times incorrectly used for completed observations; queued sources still fetched after being paused; and repeated failures in the first five articles starving later discoveries. The guide test also verifies reversions, deduplication, approval gating, legacy immutable metadata and visible link excerpts. See [BUG_AUDIT](BUG_AUDIT.md).

Before the fixes, four of the initial five reproductions failed; the separate starvation reproduction also failed. After fixes, all **92 tests pass**, with no skips/failures. `python scripts/smoke-local.py` passes the fictional CLI demo, six actual HTTP screens, CSP/content checks, attachment and cleanup. `compileall` and `git diff --check` passed. These tests do not establish live adapter or Windows/SMTP acceptance.

## Deterministic acceptance coverage

### Historical cloud resumption — 2026-10-29 08:57 UTC (superseded above)

Started from published commit `fdddae33273798442d8187d8d41e3239711fd7b7`; remote lookup and fetch confirmed the continuation branch matched. A fresh Python 3.12.14 environment installed all locked dependencies with hashes and passed `pip check`, 55 tests (0 failed/skipped), and the existing six-screen HTTP smoke. The reusable installation script was then exercised successfully. Two `init` calls using `/workspace/ism-runtime` left exactly nine sources. A separately started UI on loopback port 8765 returned HTTP 200 and expected inbox/source content. Runtime data and session keys remain outside Git.

At 08:57:26 UTC, independent robots HEAD probes to both official hosts received managed-proxy CONNECT 403 Forbidden. These are network prerequisite checks, not new nine-source verification or evidence of site robots restrictions. At that time, enforced policy excluded both hosts. Saved draft fields: complete `install_script`, complete `start_skill`, and custom network domains `www.canada.ca` and `www.welcomebc.ca` (package-manager presets preserved). The save confirmed `requires_publish: true`; runtime application and publication remain outstanding. At that time P06 could not proceed until access was applied. No application code, tests, dependency declarations, or lockfiles were changed during setup. No new-task restore was verified.

### Existing acceptance suite

Tests cover baseline without alert, identical/navigation-only content, changed word/date/amount/table cell, changed URL and fragment, stable listing identities/new entry once/reappearance, same-URL PDF replacement, byte-only PDF changes, image-only PDFs, empty/challenge/dynamic shells, failed baseline preservation, recovery, content reversions, parser rebaseline, metadata-only date changes, conditional/invalid 304 and full-validation rules, persisted Retry-After, overlap and one catch-up, announcement capture without recursive crawling, explicit publication/effective wording, user approval of guides, independent guide checking, unsafe URL/DNS/redirect/robots/XML handling, escaped HTML, CSRF/Host/origin protection, review workflow/exports, restored-schema integrity, notification restart deduplication, uncertain send handling, source-vs-delivery failures, timezone scheduling, digest event boundaries, and blocked live-report outcomes.

The local HTTP smoke is deliberately separate from pytest because sandboxed runners may prohibit listening sockets. It uses only a test-owned loopback server. It is not a graphical browser/screenshot test. The Linux shell cannot establish Windows execution or email inbox receipt.

## Interpretation of readiness

The local application and independent checker are implemented and tested against deterministic evidence. The original **live Windows acceptance goal is not fully verified**: live Express Entry adapter validation, approved BC guide PDF verification, and Windows execution remain pending. No mocked success is counted as live-source coverage. See [LIMITATIONS](LIMITATIONS.md) and [source verification](source-verification.md).

Reusable cloud `install_script` and `start_skill` were previously saved. The user has now published the environment; the replacement instance restored the virtualenv and passed dependency checks/tests. This later Git checkpoint is not assumed to be in that earlier filesystem snapshot. No further environment settings were edited or published by the agent. The app's actual long-term host is the user's local computer, with explicit scheduling, not this development task.
