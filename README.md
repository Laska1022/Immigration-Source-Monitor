# Immigration Source Monitor

A local evidence desk for official Canadian immigration sources. It records **what was observed**, keeps previous versions, and makes failed checks visible. It does not give legal advice, decide eligibility, or store client records.

**Current delivery:** working local application with 92 deterministic tests and a fictional demo. Live fetching/extraction passed for eight of the nine starter sources on 2026-10-29; The Express Entry page-plus-JSON adapter is now implemented and fixture-tested; its live acceptance remains pending because this task runtime returns proxy CONNECT 403. The earlier eight-page live evidence is retained. Windows scripts and real SMTP delivery have not been executed on Windows or against an email provider. See [validation](docs/VALIDATION.md), [live verification](docs/source-verification.md), and [limitations](docs/LIMITATIONS.md). Existing installations need the three source-setting adjustments in [live source notes](docs/LIVE_SOURCE_NOTES.md); setup preserves saved source edits.

## Windows quick start

1. Download or clone the **`codex/immigration-monitor`** branch of this repository. Keep it in a normal local folder, outside OneDrive/synchronizing folders where practical.
2. Install **Python 3.11 or newer** from python.org, including its Python launcher (`py`). No Docker, Node.js, paid service, AI key, or database server is needed.
3. Double-click **`Setup.cmd`**. It creates `.venv`, installs exact hash-locked dependencies, and initializes the nine starter sources. Read any failure; setup does not silently treat it as success.
4. Double-click **`Launch.cmd`**. It starts the local browser interface on loopback, port 8765. Keep its console open while using the interface. Saved evidence is available offline.
5. In **Sources & health**, review the watchlist and click **Check due sources now**. Refresh to see completed checks. A first successful capture creates a baseline; it is not a newly changed policy.
6. Optionally install the scheduler below. **Launching the browser alone does not install background monitoring.**

Runtime data defaults to `%LOCALAPPDATA%\ImmigrationSourceMonitor`, outside the repository. The database contains evidence and annotations; the separate DPAPI password file contains an encrypted email credential when configured. Do not put the data folder in Git. To move the data location, set the user environment variable `ISM_DATA_DIR` to an external folder and use it consistently for UI and scheduler. The app rejects data paths inside its checkout.

For updates: back up, close the UI and checker, pull the continuation branch, run `Setup.cmd`, and read HANDOFF for schema compatibility. Do not delete the data folder to resolve an error.

## What the screens do

- **Review inbox:** new changes, first unhealthy transitions, and recoveries. Review states are New, Reviewed, Action needed, Archived. Priority labels are review aids only. All detected content changes remain recorded.
- **Sources & health:** add/edit/group/pause/remove sources; see attempts, successful checks, due times, and failures. Removal retains evidence; restore monitoring from History. Failed, uncertain, redirected, overdue, and paused are distinct.
- **Comparison:** inline and side-by-side changes with original downloads, SHA-256 hashes, detection/observation/publication/modified dates, and effective-date wording only when explicitly found. User interpretation and follow-up notes are separate from evidence. Do not enter client identities.
- **History:** search captured text, source titles, changed evidence, and private notes. Includes baselines, all attempts, metadata-only edits, and internal rebaselines. Each section is paginated in batches of 100.
- **Schedule & notifications:** timezone (initially Europe/Istanbul), daily digest time (09:00), review keywords, optional SMTP, persistent delivery status.
- **Backup & restore:** storage usage, consistent downloadable archive, validated staging of a restore. No history is automatically purged.

Select inbox events to export Markdown or self-contained HTML. Exports contain official links, timestamps, old/new excerpts, hashes, uncertainty, and separately labelled private notes. Keep exported notes private. Large changes have bounded excerpts; download full saved versions for exhaustive comparison. PDF downloads retain the original file, with page markers in extracted text when available. Inspect the original for tables/layout.

## Add an official source once

1. Verify the exact hostname is operated by the official agency. In **Sources & health → Approved official-host registry**, approve it if needed. Subdomains are separate. A government page linking a private organization does not make that organization an approved official source.
2. Click **Add source**. Enter its exact URL, title, agency, tags, optional group, type, and reason for monitoring.
3. Choose main content, selected section, listing entries, or selected linked document. The six-hour frequency can be changed (minimum 15 minutes).
4. Add an **expected phrase** that should occur in the monitored content. This helps detect a changed layout, unrelated redirect destination, or empty shell.
5. Leave the selector blank for a normal `<main>` or `<article>`. For a specific section/list, enter its CSS container selector, such as `#requirements` or `#news-list`. A missing selector or empty table produces uncertainty, never an unchanged result. A helper may be useful for site-specific selectors.
6. Check now, inspect the saved baseline and source health, and then leave the scheduled checker running.

Use listing scope only for a list/index whose entries are links in list items, table rows, or articles. Entries are identified by canonical URL, not row number. For repeated invitation rounds that all link to one URL, use main-content scope to preserve row/cell changes. Public RSS/Atom feeds with official entry URLs are also supported.

New announcement entries are captured one hop from an approved host; at most five article captures are attempted per run. A persistent rotating queue prevents repeatedly failing articles from blocking later discoveries. Capture failures remain visible in onboarding and digests. Linked instructions become candidates, not an automatic crawl. BC Program/Application Guide links are discovered from the documents index when it can be fetched; **approve them in the candidate list** before monitoring. Each approved guide receives its own scheduled checks. Replacement links are visible on the index and require approval for the new document; no earlier version is claimed for it.

Unexpected redirects retain the baseline and show the observed final URL in History. Verify that destination and its official ownership, then edit the source URL explicitly. A 404 means unavailable, not that a policy was withdrawn. Express Entry observations retain the exact HTML and JSON in a downloadable ZIP with a hash/time manifest. Both are fetched on every check; malformed data, missing historical rounds, or changed endpoint references retain the baseline. Distribution keys are preserved verbatim without interpretation. Unverified dynamic data is marked uncertain; this release does not silently substitute a guessed API endpoint or pretend a static shell covers dynamic rounds.

### Adjust noise without losing changes

Navigation, script/style elements, cookie furniture, and page-level modified-date blocks are excluded from substantive HTML comparison. Meaningful link targets, headings, paragraphs, lists, table headers/cells, numbers, and negations are retained. Metadata-only date changes stay in history.

For additional irrelevant furniture, add one CSS selector per line under **Noise selectors** in the source editor. Avoid excluding policy paragraphs, table rows, dates within content, or eligibility wording. Inspect the resulting baseline. Changing scope/selectors/expected content or parser version creates a clearly labelled **internal rebaseline**, not an official change alert. No percentage-change threshold suppresses a single word. Suspicious loss of over 55% of text requires inspection and does not advance the valid baseline; after confirming a legitimate structural change, make a deliberate extraction-rule adjustment to rebaseline.

Review keywords and changed-number priorities can be edited in Settings. They prioritize rather than discard changes. Broad keywords may be noisy, but other content changes remain in the inbox.

## Background checking on Windows (opt-in)

From PowerShell in the repository, after reviewing the scripts:

```powershell
.\scripts\install-scheduler.ps1
```

If Windows marks downloaded scripts as blocked, review them first and use `Unblock-File` on those specific scripts. If your organization's execution policy prohibits scripts, follow its policy rather than disabling protections. No administrator privileges or machine-wide policy change is required by this application.

The task named **Immigration Source Monitor** runs every 15 minutes while the same Windows user is logged in. It checks only due sources (six-hour default) and prepares the daily digest at the first run at/after 09:00 in the selected timezone. Timing is therefore approximate to the next scheduler run. It uses an independent command-line process; no browser is needed. Windows Task Scheduler should show Last Run Result 0 on a successful run; 1 means source checks failed; 2 indicates an internal/configuration error. Inspect Sources/History for details.

A powered-off, sleeping, logged-out (with this default interactive task), disconnected, or restricted computer cannot perform ordinary scheduled checks. StartWhenAvailable permits one catch-up; the app checks each due source once and prevents overlap. It cannot reconstruct every intermediate edit or guarantee detection of every update. A manual source check can wait up to ten minutes for an existing check to finish; refresh health to see its outcome.

Remove the task explicitly:

```powershell
.\scripts\remove-scheduler.ps1
```

This removes scheduling only, not evidence. Reinstall after moving the repository. Custom `ISM_DATA_DIR` must be a persistent user variable visible to the scheduled process. Review/installing the task remains a Windows acceptance step; it has not been tested from the Linux development environment.

## Optional email

Email is **disabled by default**. In Settings supply your SMTP hostname, port, STARTTLS (usually 587) or TLS (usually 465), username, sender, and **one recipient address**. The provider must support SMTP authentication (username/password or app password); OAuth-only setups are not implemented. A paid notification service is not needed, but your chosen provider's policies apply.

Store the password without putting it in source files, logs, or the database:

```powershell
.\scripts\configure-email-password.ps1
```

This prompts securely and stores a Windows DPAPI-encrypted value bound to your user/machine. `run-check.ps1` loads it into `ISM_SMTP_PASSWORD` for the checker process and clears it afterward. The UI may show “password present: no” because only the checker loads it; that is expected. For a manual delivery check use `scripts\run-check.ps1`, not a plain Python invocation that lacks the variable. On other platforms inject `ISM_SMTP_PASSWORD` securely into the process environment. Never paste the password into chat or commit it.

Enable email only after configuration. Digests include readable old/new excerpts, dates, official links, hashes, warnings, and coverage; they work on a phone without opening localhost. They include failures and never claim unqualified “No changes” when sources were not verified. Prepared digests are immutable, one per local date; preparing today's digest early does not regenerate it at 09:00. Later events appear in the next digest.

Delivery state is separate from source health. The persistent outbox prevents normal restart duplicates. **SMTP cannot guarantee exactly-once delivery:** interruption after sending can leave an uncertain outcome. Such messages are not automatically retried. Check your mailbox, then explicitly queue a retry in Settings if appropriate. Rejected deliveries also require review/retry, avoiding repeated login attempts. “Sent” means SMTP accepted it, not guaranteed inbox delivery. Real email delivery has not been tested here.

## Backup and restore

Use the Backup screen or:

```powershell
.venv\Scripts\python.exe -m immigration_monitor backup
```

The ZIP contains a consistent SQLite snapshot and SHA-256 manifest, including sources, raw originals, extracted versions, attempts, review notes, candidate captures, digest history, queue, timezone and scheduler settings. **It contains private notes.** Copy it to a secure location outside the original computer. Credentials, browser session keys, and Windows Task Scheduler registration are deliberately excluded.

To restore:

1. Stage/validate a ZIP in the UI if desired (128 MiB upload limit).
2. Close the UI console and stop scheduled checks. Remove or temporarily disable the Windows task.
3. Run, using the actual path to your ZIP:

```powershell
.venv\Scripts\python.exe -m immigration_monitor restore --file "C:\Backups\ism-backup.zip" --confirm
```

Restore validates the archive member names, checksum, exact supported database schema, integrity, foreign keys, and version hashes. It refuses active UI/checker locks, creates a pre-restore safety backup, and then replaces the database. The extracted database is limited to **512 MiB** in this release; larger archives require a future streaming restore implementation rather than bypassing validation. A backup must come from a schema-compatible application revision; do not assume arbitrary earlier checkpoint schemas migrate automatically.

Email is disabled after restore, and pending/failed/uncertain queue items are held for mailbox reconciliation. Reconfigure the password separately and reinstall/re-enable the scheduled task on the target Windows account. The timezone/frequency settings themselves are restored. Backups do not silently expire, and there is no automatic evidence deletion. Monitor storage usage; keep secure backups before making an explicit archival decision.

## Development and deterministic demo

On Linux/macOS (Windows uses `.venv\Scripts\python.exe`):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m immigration_monitor init
.venv/bin/python -m immigration_monitor serve
.venv/bin/python -m immigration_monitor check
```

The UI binds only to loopback. Do not put it behind a public proxy or enable LAN exposure. Each development task uses the existing isolated checkout; no worktree is needed. Runtime state stays outside the repository. Dependencies are fully pinned with hashes in `requirements.txt`, including transitive packages; `requirements.in` records direct choices. Refresh deliberately with `uv pip compile requirements.in --generate-hashes -o requirements.txt`, review, and run tests. No live tests run as part of pytest.

Run the end-to-end demo using a **separate empty folder outside the repository**:

```sh
.venv/bin/python -m immigration_monitor --data-dir /tmp/ism-fictional-demo demo
.venv/bin/python -m immigration_monitor --data-dir /tmp/ism-fictional-demo serve
```

On Windows choose an empty path under `%LOCALAPPDATA%` and use the Windows Python path. The demo is labelled FICTIONAL throughout: baseline → wording edit → failed check → recovery → browser-route review → daily digest. It performs no network requests and pauses its fictional source afterward. It refuses to populate a database that already has sources.

Optional live smoke test, separate from pytest:

```sh
.venv/bin/python -m immigration_monitor verify-sources --output docs/source-verification.json
```

It records each requested URL, UTC attempt time, results, observed redirects, method, and limitations. It respects robots and exits 1 if any source is blocked or fails validation. In the managed Codex environment, explicitly reviewed proxy trust may require `ISM_TRUSTED_PROXY=1`; the managed proxy then owns DNS and public-address enforcement. **Do not enable that option for an untrusted proxy.** Without trusted proxy mode, direct connections resolve/check public addresses and pin the validated IP while verifying the original TLS hostname. See [security](docs/SECURITY.md).

For cross-account continuation, read [AGENTS.md](AGENTS.md), [PLAN](docs/PLAN.md), and [HANDOFF](docs/HANDOFF.md). The latest published checkpoint is on `codex/immigration-monitor`; never rely on another account's temporary files. Publication status is distinct from release completeness.
