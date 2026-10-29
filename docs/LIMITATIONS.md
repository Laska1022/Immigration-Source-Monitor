# Known limitations and unfinished acceptance work

## External blockers / unverified operations

- All nine starter live checks were attempted on 2026-10-29 UTC. Local DNS is unavailable in this managed environment; using its explicitly trusted proxy reaches a CONNECT **403 Forbidden** for both official hosts. A draft adding `www.canada.ca` and `www.welcomebc.ca` was saved, but that does not apply or publish the policy. Review/save/publish it in environment settings, then retry. No current page, redirect chain, guide URL, or live parser success has been verified. See the machine-readable and readable source-verification reports.
- BC Skills Immigration Program Guide and Application Guide cannot be discovered until the supplied documents page can be read. No guessed links were substituted. The implemented candidate approval UI must ask the user before adding actual discovered documents.
- Express Entry public data and any dynamic BC pages require inspection of their current official network/data sources once accessible. The app rejects known empty data placeholders and an unpopulated Express Entry rounds table. It has **no verified dynamic JSON adapter or browser rendering yet**; it will report uncertainty rather than claim live coverage. This is an unfinished requirement, not a passing live test.
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
