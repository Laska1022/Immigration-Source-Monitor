# Implementation plan

Continuation branch: `codex/immigration-monitor`. Statuses: not started / in progress / blocked / completed.

| ID | Task | Dependencies | Acceptance | Status |
|---|---|---|---|---|
| P01 | Durable project memory, dependency lock, runtime skeleton | none | Reproducible install; spec/plan/handoff committed | completed |
| P02 | SQLite evidence model, approved registry, safe fetch/extract/compare | P01 | Baseline, failure/recovery, quiet edits, listings, PDFs, rebaseline tests | not started |
| P03 | Local browser UI and source onboarding | P02 | CRUD, approval candidates, inbox, comparisons, notes, history, exports | not started |
| P04 | CLI scheduling, health transitions, digest and SMTP queue | P02 | Catch-up/lock/dedup/coverage tests; opt-in Windows scripts | not started |
| P05 | Backup/restore and security validation | P03,P04 | Round-trip evidence/settings; unsafe URL/import/HTML tests | not started |
| P06 | Starter-source verification and deterministic demo | P02,P03,P04 | All nine URLs attempted; results/limits recorded; demo passes | not started |
| P07 | Release validation and operator documentation | P05,P06 | Full tests, local HTTP smoke, Windows instructions, honest limitations | not started |

Scope is the complete PROJECT_SPEC. Live destinations blocked by development network policy are reported separately; they never count as successful source checks. Windows execution and real SMTP delivery require their respective runtime/credentials and must remain explicitly unverified here.
