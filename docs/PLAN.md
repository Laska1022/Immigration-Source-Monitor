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
| P07 | Release validation and operator documentation | P05,P06 | Full tests/local HTTP/docs complete; live and Windows acceptance explicitly verified | in progress |

Scope remains the complete PROJECT_SPEC. “Could not check” never becomes “No change.” Windows execution and real SMTP delivery remain unverified without their respective runtime/credentials.

## Current evidence (2026-10-29 UTC)

The user published unrestricted public access. Runtime policy is enforced and official sites now respond; the proxy blocker is resolved. The virtualenv restored successfully. This continuation starts from verified remote f1db6b2 and changes no environment settings.

P01–P05 remain implemented. Current suite: **59 passed**, with HTTP smoke and fictional demo passing. P06 live results: **8 of 9 fetch/extraction passes**, Express Entry uncertain; command exits 1. Real HTML enabled fixes for the updates-table timeout, feedback-widget false warning, IEC marker and BC scopes omitting inline content. Offline integration replay gives eight baselines then eight unchanged results, while Express Entry stays uncertain. The two requested guide URLs are discovered but pending approval; PDFs are unverified.

Remaining P06 work: integrate the observed Express Entry JSON source with complete immutable evidence and failure-safe validation; rerun live checks; obtain guide approval and verify the PDFs; complete remaining live acceptance. LIVE_SOURCE_NOTES records endpoint/schema evidence and required existing-source adjustments. P07 awaits these checks and Windows execution. Optional real SMTP acceptance remains unrun.
