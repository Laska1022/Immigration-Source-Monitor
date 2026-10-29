# Immigration Source Monitor — original requirements

This document preserves the user's application and sequential-development requirements. Implementation status belongs in PLAN and HANDOFF, not in weakened requirements here.

## 1. Purpose

Build and test a usable application, not a mock-up or architectural proposal. Read repository instructions, preserve unrelated work, plan briefly, implement, make reasonable reversible decisions, and record assumptions, limitations, and genuine blockers.

The user works with Canadian immigration matters and regularly researches IRCC instructions, provincial programs, employer requirements, work permits, IEC, and application procedures. The application must show:
- Which monitored official sources changed.
- Exactly what wording, numbers, links, or documents changed.
- When the application detected the change.
- Whether an official publication or effective date is stated.
- Which sources could not be checked reliably.

This is an evidence-preserving monitoring tool, not a legal-advice or eligibility engine. **“Could not check” must NEVER become “No change.”**

## 2. Platform and cost

Assume Windows and one nontechnical user initially. Build a local application with a browser interface, local database, and separate command-line checking process that can run without the browser being open. Use a small, maintainable free/open-source stack. Avoid unnecessary infrastructure, Docker requirements, and paid services. The core must not require an AI API/LLM, paid monitoring service, cloud database, public deployment, or subscription. Internet is needed for fetching and optional email; saved evidence remains accessible offline. Provide a simple Windows launcher and setup instructions. Codex Cloud is not the permanent host; implement actual runtime and scheduling separately.

## 3. Source registry and starter watchlist

Allow adding, editing, pausing, grouping, and removing sources through the UI. Store title, URL, agency/jurisdiction, topic tags, source type (announcement, public guidance, operational instructions, legislation, document index, downloadable guide), frequency, monitoring scope (main content, selected section, listing entries, selected linked document), last attempted/successful/next due checks, health, optional monitoring notes.

Use an explicitly approved official-source registry. A link from a government page does not establish official status. Seed these exact URLs, recheck during implementation, and record redirects and verification results; never invent replacement URLs:

1. IRCC Program Delivery Updates: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/updates.html
2. IRCC notices: https://www.canada.ca/en/immigration-refugees-citizenship/news/notices.html
3. Express Entry rounds: https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html
4. IEC recognized organizations — public guidance: https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada/iec/recognized-organizations.html
5. IEC recognized organizations — operational instructions: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/temporary-residents/foreign-workers/exemption-codes/international-experience/canadian-interests-reciprocal-employment-international-experience-canada-recognized-organizations-foreign-youth.html
6. BC PNP news: https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/news
7. BC PNP invitations: https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/invitations-to-apply
8. BC PNP documents: https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/documents
9. BC PNP employer information: https://www.welcomebc.ca/immigrate-to-b-c/for-employers

Discover the Skills Immigration Program Guide and Application Guide from the BC documents page. Ask for approval within onboarding before adding discovered documents. Other provinces and selected IRCC pages must be addable without code changes. Do not crawl entire websites.

## 4. New publications and quiet edits

Support distinct events: A new entry appears on an announcement/index page; B existing page/document content changes. Track listing entries using URLs and identifying information, not row positions. New rows shifting a table must not mark all rows new.

For new announcements capture title, source link, explicit publication date; save the article from an approved official host; identify linked official instructions as monitoring candidates, without unlimited recursive crawling. Approved guides are checked independently even when the index is unchanged. Detect same-URL replacement and changed download links. First success is a baseline, not evidence of recent change. Label newly discovered documents lacking earlier versions.

## 5. Reliable fetching and extraction

Respect request rates, timeouts, bounded retries, domain limits, robots, restrictions, and Retry-After. Use a descriptive user agent. Never bypass login, CAPTCHA, or anti-bot controls. Support ordinary HTML, public feeds, and text PDFs. For dynamic pages inspect how the official page obtains public data; use a verified public data source or bounded browser rendering as needed. An empty shell must never be success. Validate expected content, not merely HTTP status.

Separate statuses: baseline created; successfully unchanged; change detected; failed/blocked; extraction uncertain; unavailable/redirected; overdue/stale; paused. HTTP failures, timeouts, challenges, empty output, unexpected redirects, and suspiciously incomplete extraction cannot replace the last valid baseline. A 404 is unavailability, not proof of policy withdrawal. Conditional requests are permitted with periodic full validation; 304 requires a valid corresponding baseline.

## 6. Comparison and evidence

Immutable versions contain original/final URLs, UTC retrieval time, raw body/document, extracted content, hashes, response metadata, extraction/configuration version. Never overwrite older versions. Exclude navigation, cookie banners, irrelevant furniture while preserving headings, paragraph/list order, table headers/row context, numbers/currency/dates/units/NOC codes, negations/conditions, meaningful link destinations. One changed word such as “not” matters; percentage change cannot suppress it.

Offer side-by-side and inline additions/deletions with context. Keep page-level last-modified changes separate from substantive content; preserve metadata history even without prominent alerts. Parser/rule upgrades must not masquerade as policy changes: reprocess comparable stored versions or label internal rebaseline.

PDFs: distinguish byte/text changes; retain originals; page references where reliable; equal text does not prove equal documents; changed bytes with unchanged/unreliable text need manual review; flag image-only pages/problematic tables; OCR is not required. Reversions A → B → A create a new observed event even when A existed before.

## 7. Alerts and review

Every change record includes source title/agency/direct official link/tags; previous successful observation; detection time; explicit publication/modified date; reliably identified effective-date wording; changed section with old/new excerpts; saved comparison; extraction uncertainty. Dates are distinct. When unclear say **“Effective date not established from the monitored content.”** Use neutral descriptions such as “Text changed in the Employer Requirements section.” Never automatically claim “Employer eligibility rules have changed.” Do not determine eligibility, resolve contradictions, or choose a client's applicable rule.

Editable priority rules for changed numbers, deadlines, eligibility wording, openings/closures, selected keywords are review aids, not legal conclusions. Keyword filters cannot silently discard other changes. Review states: New → Reviewed → Action needed → Archived. User interpretations/follow-up notes are editable and separate from evidence. Do not request client identities.

## 8. Automation and notifications

Six-hour default checks with per-source overrides and Check now. Configurable timezone initially Europe/Istanbul; UTC storage. Opt-in Windows Task Scheduler installation/removal. Monitoring needs a running connected host; sleep/off prevents ordinary checks; catch-up cannot reconstruct every intermediate version; detection of every update is not guaranteed. One catch-up check per missed interval, no burst; prevent overlap and duplicate alerts.

In-app inbox and daily digest at 09:00 selected timezone. Email disabled until configured/enabled, to the configured address only; supported SMTP without paid platform; readable old/new excerpts and official links; mobile-friendly and independent of phone access to localhost; credentials excluded from source control/logs. Separate delivery/source failures. Persistent queue and restart deduplication. Digest coverage e.g. “12 checked successfully; 2 failed; 1 overdue” uses real counts, never example constants. Never send unqualified “No changes” while checks failed. Notify first unhealthy transition and recovery, without identical repeated failure notifications.

## 9. Interface, security, backup

Clear review inbox; sources/health; comparison; searchable history; scheduling/notifications; backup/restore. Health prominent, no misleading overall green. Export selected evidence to Markdown or self-contained HTML with source links, times, excerpts, notes. Separate public evidence and private annotations. No client records. Loopback binding by default, no automatic public/LAN exposure.

Downloaded content is untrusted: escape/sanitize HTML, never execute snapshot scripts; only approved public HTTP(S); block private, loopback, link-local, metadata addresses including DNS/redirects; bound response size/processing time/downloads; validate import/export paths. No analytics, telemetry, third-party uploads. Keep runtime data, snapshots, credentials, backups outside repo with exclusions. Backup and tested restore must preserve sources/snapshots/annotations/history/scheduler settings. Credentials handled separately with limitations explained. Show storage use; no silent retention deletion, explicit choice required.

## 10. Tests, delivery, acceptance

Use deterministic fixtures, separate optional live smoke tests. Test at least:
1. First fetch baseline without change alert.
2. Identical content no event.
3. Navigation-only edits not substantive.
4. Single changed word/date/amount/table cell detected.
5. Changed link target detected.
6. New listing entry reported once.
7. PDF same-URL replacement detected.
8. Changed PDF/equal text flagged.
9. 200 challenge/empty shell rejected.
10. Failure preserves valid baseline.
11. Recovery compares baseline.
12. Reversion creates event.
13. Parser/config changes avoid false alerts.
14. Restarts avoid duplicate alerts/deliveries.
15. Missed/overlapping schedules handled.
16. Backup/restore preserves evidence.
17. Unsafe URLs/malicious HTML handled safely.

End-to-end demo with clearly fictional versions: baseline → wording change → failed check → recovery → reviewed alert → digest.

Deliver working source, reproducible dependencies, Windows setup/launcher/scheduler instructions, editable starter configuration, automated tests with actual results, source verification report (URL/result/checked time/extraction method/limitations), plain-English adding/noise-filter instructions, backup/restore instructions, known limitations and unfinished items. Do not claim Windows/email/live tests without execution; network blocks are blocked, not passed.

Durable instructions in AGENTS.md. Exclude client management, automatic legal research, AI advice, government portal access, automatic client communications.

**Acceptance goal:** Add an official page once, leave scheduled checks on a running computer, later see an evidence-backed account of changes, successful checks, and sources that could not be verified.

## Sequential development across two Codex accounts

The repository is shared project memory; agents must continue from published checkpoints without earlier chat, local files, or environments. These rules do not make Codex the app runtime.

Maintain AGENTS.md (concise conventions/commands/handoff links, not chronological log), this complete PROJECT_SPEC (requirements unchanged unless user changes them), PLAN (prioritized stable IDs, dependencies, acceptance, not started/in progress/blocked/completed supported by checks), HANDOFF (current milestone/branch, actual implementation, WIP/files, prioritized exact next steps, actual test results, failures/blockers/assumptions, decisions/reasons, environment/permissions, unpublished work). Reproducible dependencies/instructions belong in repo. Secret names only.

At every new task inspect branch/tree/remotes, fetch when possible, read agent/handoff/relevant spec/plan, inspect recent commits/implementation, verify latest published continuation checkpoint rather than cached default branch, run baseline checks. Investigate documentation/code/test disagreement; correct handoff. Continue highest-priority unfinished task with met dependencies. Do not rebuild, redo research, replace stack, or rewrite working components merely because agent changes. Explain/record necessary changes of approach.

Use `codex/immigration-monitor`; if required to use other branch/PR record exact references. Keep unfinished work separate from stable branch; no merge without approval. One writing agent at a time; do not start another account's agent/manage credentials. Before publication check remote advancement; never force-push, discard, or overwrite others; reconcile safely/report conflict.

After each small meaningful unit: relevant checks, update plan/handoff, commit code/tests/docs, publish by authorized workflow, verify remote checkpoint. Also checkpoint before risky refactor and before ending. Prefer working/tested units. Incomplete interruptions get WIP label, exact failures, continuation instructions; no finished claim/merge. Do not predict account allowance; keep notes current.

Local commit ≠ cross-account handoff. If publication unavailable, report promptly, preserve local work, use supported PR/export, give exact manual publish action, mark NEEDS_PUBLISHING until verified. Never claim another account can see local-only changes. Never commit credentials/runtime DB/private annotations/production snapshots/personal data; small sanitized fixtures only.

At task end report: Implemented; Verified actual checks; Unfinished/blockers; Published checkpoint branch/SHA/PR if any; Next action; Handoff READY or NEEDS_PUBLISHING. READY means checkpoint/notes verified on GitHub, not whole app complete. Unexpected interruption: next agent resumes latest published state and honestly identifies gaps, never claiming recovery of another account's unpublished work. Continue until original acceptance goal, with further checkpoints and concise actionable docs.
