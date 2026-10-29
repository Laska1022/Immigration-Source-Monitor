# Implementation plan

Continuation branch: `codex/immigration-monitor`. Statuses: not started / in progress / blocked / completed.

| ID | Task | Dependencies | Acceptance | Status |
|---|---|---|---|---|
| P01 | Durable project memory, dependency lock, runtime skeleton | none | Reproducible install; spec/plan/handoff committed | completed |
| P02 | SQLite evidence model, approved registry, safe fetch/extract/compare | P01 | Baseline, failure/recovery, quiet edits, listings, PDFs, rebaseline tests | completed |
| P03 | Local browser UI and source onboarding | P02 | CRUD, approval candidates, inbox, comparisons, notes, history, exports | completed |
| P04 | CLI scheduling, health transitions, digest and SMTP queue | P02 | Catch-up/lock/dedup/coverage tests; opt-in Windows scripts | completed |
| P05 | Backup/restore and security validation | P03,P04 | Round-trip evidence/settings; unsafe archives rejected | completed |
| P06 | Starter-source verification and deterministic demo | P02,P03,P04 | All nine live layouts/data verified; BC guides discovered for approval; fictional demo passes | in progress |
| P08 | Bug regression audit | P02,P03 | Reproduce and fix stale-source and guide-replacement issues with regression checks | in progress |
| P07 | Release validation and operator documentation | P05,P06 | Full tests/local HTTP/docs complete; live and Windows acceptance explicitly verified | in progress |

Scope remains the complete PROJECT_SPEC. “Could not check” never becomes “No change.” Windows execution and real SMTP delivery remain unverified without their respective runtime/credentials.

## Current evidence (2026-10-29 UTC)

Resumed remote `29a4871` by fast-forward; its 59-test baseline passed. The previous live report (09:50 UTC) remains eight successful captures and Express Entry uncertain; actual HTML/data inspection is recorded in LIVE_SOURCE_NOTES. This task's runtime reports restricted access and a 12:27:02 UTC probe failed with proxy CONNECT 403. No environment settings were changed and historical live evidence was not overwritten.

P06: Express Entry compound capture is implemented, with complete HTML/JSON evidence, unconditional data checks, schema/reference validation, bounded extraction and history-preserving failures. **84 tests pass**, including 25 adapter tests. Live adapter acceptance and user-approved BC guide PDF checks remain pending. P07 still needs Windows and final live acceptance; real SMTP remains unrun. P08 is the next independent task while live access is blocked.
