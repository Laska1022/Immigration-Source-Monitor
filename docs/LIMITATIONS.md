# Known limitations and unfinished acceptance work

## External blockers / unverified operations

- The earlier live run used unrestricted access; this task runtime currently reports enforced restricted access and CONNECT 403 for www.canada.ca. No environment settings were changed. Live fetching/extraction passed for eight of nine starter pages on 2026-10-29; Express Entry remains uncertain. This establishes one observed capture per passing page, not continuous coverage or Windows acceptance. See the source-verification reports and [live source notes](LIVE_SOURCE_NOTES.md).
- BC Skills Immigration Program Guide and Application Guide URLs were discovered from the official documents page. They remain pending user approval, and their PDF contents have not been live-verified. No guide monitoring was enabled automatically.
- The Express Entry page explicitly references `/content/dam/ircc/documents/json/ee_rounds_123_en.json` on www.canada.ca; a robots-checked fetch returned JSON with 454 rounds. The adapter now preserves both exact observations and validates the documented schema, including latest distribution data. It is tested with fictional fixtures but **has not been validated against the live payload in this task**. Unrecognized values/fields, missing historical rounds, or changed endpoints fail safely. The two HTTP observations are not an atomic website snapshot. No browser rendering is implemented.
- New installations receive corrected BC news/documents scopes and the observed IEC heading marker. Existing saved sources are preserved by `init`; apply the three adjustments in LIVE_SOURCE_NOTES before expecting these live results. BC news currently monitors inline announcements as page-text changes; it does not invent individual article URLs or publication dates for sections without them.
- Windows setup/launcher/Task Scheduler/DPAPI scripts have not been executed on Windows. They need an actual Windows acceptance run. The selected local stack and scheduling tests run on Linux.
- SMTP dispatch has been tested using deterministic fake senders, including failure and restart states. No real credentials/provider/email delivery were used. Test it only after the user configures and enables their chosen SMTP account.

## Deliberate first-release limits

- Monitoring only observes successful checks. Offline/sleeping/powered-off computers and gaps can miss intermediate changes. No legal/eligibility conclusions or official-date inference from detection time.
- HTML extraction needs a main/article or user-selected container. Site-specific selectors/expected phrases may require a helper. Listing identities use canonical URLs; use main-content/table comparison when multiple entries share one URL. Section selection is CSS-based, not a visual page picker.
- Redirects require explicit review, even for legitimate redirects. No broad crawling: new article captures are one hop, at most five per run, and instruction/guide monitoring requires approval.
- Every full valid check retains an immutable capture, even when text is unchanged. This favours evidence completeness over storage efficiency. UI shows usage; there is no automatic retention/deletion or storage deduplication policy. A first baseline is not an alert.
- PDF text order/table relationships may be imperfect. Every PDF includes a visual-review warning; image-only/partially unreadable PDFs fail validation. Byte-only changes require manual review. No OCR.
- Changed content shrinking by more than 55% is held for inspection. Confirm a legitimate structural change and deliberately adjust extraction configuration to rebaseline; do not silently accept a truncated response.
- Large changes preserve the whole evidence but use bounded excerpts/diffs and may omit automatic keyword analysis. Important content is not discarded; manually compare full saved originals.
- SMTP cannot guarantee exactly-once inbox delivery. Interrupted send outcomes are held, not auto-retried. Rejected deliveries also require user review before retry. Auth supports standard TLS SMTP username/password/app-password, not OAuth-only providers.
- Daily digests are immutable and unique per local date. Preparing one early does not generate another that day; subsequent events wait for the next digest. Coverage reflects latest active-source observations and overdue overlaps, not continuous monitoring. Paused/removed sources are excluded.
- The default Windows scheduled task needs the user logged in and a running connected machine; it does not wake the computer. It checks due work every 15 minutes. Custom data-directory variables must be visible to that user's scheduled process.
- Restore supports this exact schema, with a 512 MiB extracted-database limit (128 MiB browser upload). Streaming large restore, automatic schema migrations from arbitrary intermediate checkpoints, and automated retention are unfinished future work. Runtime credentials and OS task registration are separate. A restore disables email and holds unsent deliveries for reconciliation.
- Local single-user security relies on the OS account. Trusted outbound proxy mode delegates DNS/address enforcement to that reviewed proxy; direct mode pins public DNS IPs. Windows extraction workers have time limits but no POSIX memory cap.

## Next implementation milestone

Complete live source validation and any necessary observed official-data adapters, discover the two BC guides for user approval, then run Windows and opt-in SMTP acceptance. Do not mark the original live-monitoring acceptance goal fully met until these checks are complete. Preserve the working engine, tests, and published handoff while addressing these gaps.
