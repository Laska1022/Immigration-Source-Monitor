# Validation record — 2026-10-29 UTC

Environment: Linux, Python 3.12.14. Tests use isolated temporary SQLite databases and clearly fictional HTML/feed/PDF fixtures. No real annotations, client information, credentials, or production snapshots are in Git.

| Check | Actual result |
|---|---|
| `python -m pytest -q` | **55 passed**, 0 failed, 0 skipped; final suite completed |
| Hash-locked dependency install | Passed using `pip install --no-cache-dir --require-hashes -r requirements.txt` |
| `python -m pip check` | Passed: no broken requirements |
| Saved cloud install script | Re-executed successfully on resumption: hash-locked install, dependency check, all 55 tests, six-screen HTTP smoke, and external runtime initialization |
| `python -m compileall -q immigration_monitor tests scripts/smoke-local.py` | Passed |
| `git diff --check` | Passed before checkpoint |
| `python scripts/smoke-local.py` | Passed: fresh CLI fictional demo; six real loopback HTTP screens; expected content and CSP; attachment download; server stopped afterward |
| `python -m immigration_monitor ... demo` | Passed: baseline → wording change → failed check → recovery → reviewed alert via browser route → digest; fictional source paused |
| Startup `init` repeatability | Passed: two runs leave nine unverified starter sources, no duplicates or fabricated evidence |
| Backup/restore | Passed: sources, raw/extracted versions, hashes, attempts, annotations, settings preserved; unsafe archives/schema rejected; credentials excluded; email disabled and outbox held after restore |
| Optional live source verification | **9 blocked, 0 verified live successes**. CONNECT 403 Forbidden confirmed for the two official hosts; no government page/robots content obtained |
| Windows setup/launcher/scheduler/DPAPI execution | **Not run** — no Windows host available |
| Real SMTP delivery | **Not run** — optional provider/credentials not configured; fake-sender queue tests passed |

## Deterministic acceptance coverage

### Cloud resumption — 2026-10-29 08:57 UTC

Started from published commit `fdddae33273798442d8187d8d41e3239711fd7b7`; remote lookup and fetch confirmed the continuation branch matched. A fresh Python 3.12.14 environment installed all locked dependencies with hashes and passed `pip check`, 55 tests (0 failed/skipped), and the existing six-screen HTTP smoke. The reusable installation script was then exercised successfully. Two `init` calls using `/workspace/ism-runtime` left exactly nine sources. A separately started UI on loopback port 8765 returned HTTP 200 and expected inbox/source content. Runtime data and session keys remain outside Git.

At 08:57:26 UTC, independent robots HEAD probes to both official hosts received managed-proxy CONNECT 403 Forbidden. These are network prerequisite checks, not new nine-source verification or evidence of site robots restrictions. Current enforced policy excludes both hosts. Saved draft fields: complete `install_script`, complete `start_skill`, and custom network domains `www.canada.ca` and `www.welcomebc.ca` (package-manager presets preserved). The save confirmed `requires_publish: true`; runtime application and publication remain outstanding. P06 cannot proceed until access is applied. No application code, tests, dependency declarations, or lockfiles were changed during setup. No new-task restore was verified.

### Existing acceptance suite

Tests cover baseline without alert, identical/navigation-only content, changed word/date/amount/table cell, changed URL and fragment, stable listing identities/new entry once/reappearance, same-URL PDF replacement, byte-only PDF changes, image-only PDFs, empty/challenge/dynamic shells, failed baseline preservation, recovery, content reversions, parser rebaseline, metadata-only date changes, conditional/invalid 304 and full-validation rules, persisted Retry-After, overlap and one catch-up, announcement capture without recursive crawling, explicit publication/effective wording, user approval of guides, independent guide checking, unsafe URL/DNS/redirect/robots/XML handling, escaped HTML, CSRF/Host/origin protection, review workflow/exports, restored-schema integrity, notification restart deduplication, uncertain send handling, source-vs-delivery failures, timezone scheduling, digest event boundaries, and blocked live-report outcomes.

The local HTTP smoke is deliberately separate from pytest because sandboxed runners may prohibit listening sockets. It uses only a test-owned loopback server. It is not a graphical browser/screenshot test. The Linux shell cannot establish Windows execution or email inbox receipt.

## Interpretation of readiness

The local application and independent checker are implemented and tested against deterministic evidence. The original **live Windows acceptance goal is not fully verified**: current official-source extraction, dynamic adapters, BC guide discovery/approval, and Windows execution remain pending. No mocked success is counted as live-source coverage. See [LIMITATIONS](LIMITATIONS.md) and [source verification](source-verification.md).

Reusable cloud `install_script` and `start_skill`, plus the two-host network draft, were saved. Saving is not runtime application or environment publication; no fresh cloud task restoration has been tested. The app's actual long-term host is the user's local computer, with explicit scheduling, not this development task.
