# Starter-source verification

Checked UTC: 2026-10-29T07:25:02+00:00

Live checks are separate from deterministic fixture tests. A blocked result is not a passed test. No replacement URLs were invented. Discovered BC guides require approval in Sources & health before monitoring.

## IRCC Program Delivery Updates
https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/updates.html

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:48+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## IRCC notices
https://www.canada.ca/en/immigration-refugees-citizenship/news/notices.html

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:48+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## Express Entry rounds
https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:50+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## IEC recognized organizations — public guidance
https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada/iec/recognized-organizations.html

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:52+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## IEC recognized organizations — operational instructions
https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/temporary-residents/foreign-workers/exemption-codes/international-experience/canadian-interests-reciprocal-employment-international-experience-canada-recognized-organizations-foreign-youth.html

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:54+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## BC PNP news
https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/news

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:56+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## BC PNP invitations
https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/invitations-to-apply

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:56+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## BC PNP documents
https://www.welcomebc.ca/immigrate-to-b-c/about-the-bc-provincial-nominee-program/documents

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:24:58+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## BC PNP employer information
https://www.welcomebc.ca/immigrate-to-b-c/for-employers

- Result: failed or blocked
- Checked UTC: 2026-10-29T07:25:00+00:00
- Extraction method: Public HTTP GET; robots verification; bounded main-content HTML extraction (no rendering)
- Detail: Network request failed (ProxyError)
- Redirect evidence: []
- Limitations: No verified current content or replacement URL. A failed prerequisite does not establish no change.

## Network prerequisite diagnosis

Latest resumption check at **2026-10-29 08:57:26 UTC**: both official-host robots HEAD probes again received managed-proxy CONNECT 403 Forbidden. This does not refresh the nine per-source attempts above or establish robots rules. The enforced runtime policy excludes both hosts. A new draft save confirmed complete installation/startup instructions and custom domain additions for `www.canada.ca` and `www.welcomebc.ca`, with publication required. Apply those settings before retrying live verification; keep TLS/access controls intact.

The initial failures were investigated separately using read-only robots requests through the configured managed proxy. No site robots policy or page content could be read. The runtime allowlist still excludes these hosts; saving a draft does not apply it.

- https://www.canada.ca/robots.txt — Managed proxy CONNECT denied: 403 Forbidden; checked 2026-10-29T07:48:32+00:00
- https://www.welcomebc.ca/robots.txt — Managed proxy CONNECT denied: 403 Forbidden; checked 2026-10-29T07:48:32+00:00

Required next action: review/save the two-host network draft in environment settings, publish the environment, then repeat live verification. No redirect destination or BC guide URL has been invented. Dynamic data inspection remains blocked.
