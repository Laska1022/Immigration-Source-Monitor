# Implementation plan

Continuation branch: `codex/immigration-monitor`. Statuses: not started / in progress / blocked / completed.

| ID | Task | Dependencies | Acceptance | Status |
|---|---|---|---|---|
| P01 | Durable project memory, dependency lock, runtime skeleton | none | Reproducible install; spec/plan/handoff committed | completed |
| P02 | SQLite evidence model, approved registry, safe fetch/extract/compare | P01 | Baseline, failure/recovery, quiet edits, listings, PDFs, rebaseline tests | completed |
| P03 | Local browser UI and source onboarding | P02 | CRUD, approval candidates, inbox, comparisons, notes, history, exports | completed |
| P04 | CLI scheduling, health transitions, digest and SMTP queue | P02 | Catch-up/lock/dedup/coverage tests; opt-in Windows scripts | completed |
| P05 | Backup/restore and security validation | P03,P04 | Round-trip evidence/settings; unsafe URL/import/HTML tests | completed |
| P06 | Starter-source verification and deterministic demo | P02,P03,P04 | All nine live layouts/data verified; BC guides discovered for approval; fictional demo passes | blocked |
| P07 | Release validation and operator documentation | P05,P06 | Full tests/local HTTP/docs complete; live and Windows acceptance explicitly verified | in progress |

Scope is the complete PROJECT_SPEC. Live destinations blocked by development network policy are reported separately; they never count as successful source checks. Windows execution and real SMTP delivery require their respective runtime/credentials and must remain explicitly unverified here.

## Current evidence (2026-10-29 UTC)

Resumption from published `fdddae3`: fresh locked installation, 55 tests, six-screen HTTP smoke, repeatable nine-source initialization, and initialized-server HTTP checks passed. Both official hosts still returned proxy CONNECT 403 at 2026-10-29 08:57:26 UTC. P06 remains the next task and is blocked on applying the saved two-host network draft; dynamic inspection and guide discovery cannot be inferred from fixtures. Complete reusable installation/startup instructions were saved again in the current environment draft. Review/save/publish is still required; no new-task restore was verified.

P01–P05 implementation checks pass. Final deterministic suite: **55 passed**; real local HTTP smoke and fictional demo passed. P06: nine live attempts blocked, both official-host CONNECT probes return 403; no verified dynamic adapter or BC guide discovery. P07 remains in progress because live/Windows acceptance is unverified, although operator/security/backup documentation and local validation are complete. Optional real SMTP delivery also remains unrun. See VALIDATION and HANDOFF for exact commands and continuation steps.
