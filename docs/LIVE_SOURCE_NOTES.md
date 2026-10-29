# Live source inspection — 2026-10-29

The user published the cloud environment with public Internet access enabled. The replacement instance reports current, enforced unrestricted HTTP policy; the restored virtualenv passes dependency checks and tests. No environment settings were changed in this continuation. Live verification completed at **2026-10-29T09:50:44+00:00**: eight pages fetched and extracted; Express Entry remained uncertain. The CLI correctly exited 1 for the incomplete set. See `source-verification.json` for each URL, timestamp, raw hash, result, and extracted size.

## Corrections supported by the observed HTML

- IRCC Program Delivery Updates contains a 1,375-row data table. Repeatedly scanning its headers for every link exceeded the existing extraction budget. Headers are now read once per table; the captured page extracts in about two seconds under the same 20-second CPU / 25-second wall limits. It yields 1,374 distinct URL entries; listing identity remains canonical URL, not table position. Multiple rows sharing one URL do not become distinct publications.
- Canada.ca includes an empty AJAX page-feedback fragment alongside substantive guidance. This specific observed widget is removed as furniture before checking for missing data. Unknown AJAX placeholders and empty `data-json-replace` / `data-json-append` fields remain uncertain. Navigation is also excluded before placeholder validation.
- The IEC public page's current heading uses singular “Recognized Organization”; the prior plural marker was absent. The new marker matches the actual complete heading.
- BC news consists of inline dated announcements, and the documents page has guide links inside paragraphs. The prior listing scope selected breadcrumb links while omitting the intended content. Both now monitor main content within the observed `main .col-lg-9` container; missing containers fail explicitly. News text grew from 388 to 12,833 characters, and documents from 403 to 2,315. The published document guide links are included in the monitored text and candidate discovery.
- Parser version is now `html-3/pdf-1/feed-1`. Existing valid captures are immutable. A subsequent successful capture with the new parser/configuration creates an internal rebaseline, not a claim of an official change.

## Existing installations: review saved source settings

`init` inserts missing starter sources but intentionally preserves existing source edits. In **Sources & health**, edit these three sources as follows, keeping each original official URL:

| Source | Scope | CSS selector | Expected phrase |
|---|---|---|---|
| BC PNP news | Main content | `main .col-lg-9` | `news` |
| BC PNP documents | Main content | `main .col-lg-9` | `documents` |
| IEC recognized organizations — public guidance | Main content | blank | `Work and Travel in Canada using a Recognized Organization` |

Review any deliberate custom extraction settings before changing them. Check each source and inspect the internal rebaseline. Fresh installations seed these settings automatically, including the selectors.

## Guide candidates requiring user approval

The official BC documents page directly links:

- [Skills Immigration Program Guide](https://www.welcomebc.ca/immigrate-to-b-c/bc-pnp-si-program-guide-pdf)
- [Skills Immigration Application Guide](https://www.welcomebc.ca/immigrate-to-b-c/bc-pnp-si-technical-guide-pdf)

The source labels both as PDF documents. PDF contents, redirects, extraction quality, and current guide versions have not yet been live-verified. Checking the corrected documents source discovers them as pending candidates. Approve each desired candidate in Sources & health before enabling independent monitoring. Other guide links on that page must not be mistaken for the two requested Skills Immigration guides.

## Observed Express Entry data (previous live task)

The fetched official page contains `data-wb-json` and `data-wb-jsonmanager` pointing to:

`https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json`

A robots-checked fetch of that observed endpoint returned HTTP 200. Top-level keys are `classes` and `rounds`; 454 round records were present. The first record includes `drawNumber`, `drawNumberURL`, `drawDate`, `drawDateFull`, `drawName`, `drawSize`, `drawCRS`, `mitext`, `DrawText1`, `drawText2`, `drawDateTime`, `drawCutOff`, `drawDistributionAsOn`, and `dd1` through `dd18`. These are observations of the current payload, not a guaranteed schema or policy interpretation.

Implement bounded support that validates the page's endpoint reference and the data schema, preserves the exact HTML and JSON observations with their URLs/times/hashes, and compares only complete captures. Test changed scores/dates/counts, revisions to existing rounds, malformed/missing fields, endpoint changes, fetch failures and baseline retention. Do not merely suppress empty-placeholder checks or fabricate an HTML table from unrecorded data. No adapter has been added in this checkpoint.

## Evidence and remaining acceptance

59 deterministic tests and the six-screen loopback HTTP smoke pass. A separate offline integration replay of the fetched HTML creates eight baselines, keeps Express Entry uncertain, then records eight unchanged results for repeated identical captures. The two Skills Immigration guides remain pending with no child source added. This replay tests application integration; it is separate from live requests and proves no historical policy change.

P06 remains in progress for the Express Entry adapter, approved guide verification, and further live acceptance. Windows setup, scheduler/DPAPI execution, and real SMTP delivery remain unrun. No public web preview or cloud background scheduler is installed.

## Adapter implementation checkpoint

`express_entry.py` now captures the referenced page and JSON on every check. A downloadable immutable ZIP stores exact bytes plus per-artifact URLs, observation times, headers and SHA-256 hashes; partial/invalid observations are retained without advancing the baseline. The bounded extractor validates round identities/dates/counts/scores, distribution completeness, and the exact previously observed endpoint, then compares static wording and stable round records together. It retains extra JSON fields. Reordering rounds does not create false content changes. Page-only ETags cannot hide JSON edits.

Current task validation: 25 adapter fixture tests, 84 total tests. This runtime is restricted and the 12:27:02 UTC probe received proxy CONNECT 403. Thus the adapter has **no live acceptance yet**; the documented numeric/schema assumptions may conservatively reject actual records until verified. No prior successful live report or guide-approval requirement was replaced.
