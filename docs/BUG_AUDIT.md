# Bug audit — continuation from 29a4871

This is a focused review of observation correctness and pending P06 work, not a claim that all possible defects have been eliminated.

| Confirmed defect | Trigger and old behavior | Fix and regression evidence |
|---|---|---|
| Guide replacement alert suppressed | Discovery inserted a pending guide before checking whether a new link existed, so the dedicated `download_link_changed` event was never emitted. | Compare consecutive valid link observations, retain old/new excerpts and version references, preserve A→B→A, and deduplicate repeated captures. User approval remains required. Old captures without structured link metadata are supported without altering evidence. |
| Stale check overwrites an edit | Edit URL/scope while a network request runs; its old result could replace the current baseline, health, validators and next-due time, including marking the newly edited URL successful. | Recheck configuration/baseline under an immediate SQLite transaction before publication. Retain superseded attempts/raw captures without changing the edited source or creating false alerts. Both success and failure paths tested. Latest frequency is used when a non-extraction edit occurs. |
| Observation timestamp precedes completion | A slow request recorded its start as the retrieved/detected/success time. | Completed observations use completion time; attempts keep request-start time. Compound artifacts also retain their separate network observation times. |
| Paused queued source still fetched | Pause a source while another source is being checked; the checker used its stale initial queue snapshot. | Refresh each source immediately before checking and skip newly paused/removed rows. An already in-flight request may finish; its evidence is retained. |
| Article queue starvation | First five discovered articles repeatedly fail; fixed ascending LIMIT 5 meant later articles were never captured. | Persist a rotating cursor, retaining five-per-run and one-hop limits. Regression recreates the Store between runs and confirms later articles are captured despite earlier permanent failures. |

`tests/test_regressions.py` contains eight cases, including both branches of the edit race. Initial reproductions exposed four failures out of five cases; the independent queue-starvation case failed too. All eight now pass within the **92-test** suite. Existing unrelated work was preserved, and no environment settings were changed.

The new Express Entry adapter addresses the next unfinished requirement: unchanged HTML must not mask separately changed public JSON. It always captures both and preserves complete/partial raw evidence with metadata. Twenty-five fictional adapter cases pass; live validation is blocked in this task by proxy CONNECT 403. The prior task's eight successful live pages and discovered guide URLs remain recorded, not overwritten by fixture results.
