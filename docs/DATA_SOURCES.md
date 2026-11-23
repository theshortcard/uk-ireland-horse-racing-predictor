# Data sources and zero-budget policy

The project is designed to keep recurring data costs at £0 / C$0. Free access does not automatically mean that automated extraction, storage, model training, or redistribution is permitted; each source must be checked before integration.

## Current source review

### HorseRacingAPI.org — possible results-history starter

- Its public documentation says the free key provides yesterday's results for Great Britain, Ireland (including Northern Ireland), France, the USA and South Africa.
- The free key is limited to 50 calls per day and does not include racecards.
- The API says results can be used in your own app, but raw data cannot be resold or republished, and rebuilding its database is not allowed.
- This could help us collect daily outcomes prospectively, but by itself it does not provide the pre-race runner features or historical racecards required to train and validate a predictor.
- A free key requires account registration. No key is stored in this repository.

Documentation: https://horseracingapi.org/

### Horse Racing API UK — UK-only free-tier candidate

- Its documentation describes a free key with yesterday's UK results and paid plans for additional historical and racecard endpoints.
- Its documentation labels the racecard/results endpoints as UK coverage; we must not assume this includes the Republic of Ireland.
- It is not sufficient as a single free source for the project's full UK-and-Ireland racecard requirement.

Documentation: https://horseracingapi.co.uk/documentation/racecards-and-results

### British Horseracing Authority (BHA)

- The BHA website is useful for checking official UK racing information.
- Its published website terms prohibit commercial use without a licence and prohibit automated extraction/scraping for commercial purposes.
- We will not build an automated BHA scraper. Any reuse must be checked against current terms and any applicable licence.

Terms: https://www.britishhorseracing.com/terms-conditions/

### Irish public racing pages

- Irish Horse Racing public pages state that racecards and results are supplied by a third-party data provider.
- The public terms reviewed do not grant a clear machine-readable reuse or bulk model-training licence.
- We will not scrape these pages unless the provider confirms permission.

Terms: https://irishhorseracing.com/terms

## Current implementation decision

1. Use user-supplied CSV data immediately.
2. Add an API adapter only after its authentication, exact response schema, limits, retention rights and use for model development are verified.
3. Keep UK and Irish coverage labels separate; never infer missing coverage.
4. Store source name, retrieval timestamp, race date and price timestamp with every future imported record.
5. Do not publish live EV selections without verified pre-race prices and a calibrated probability model.

## Required future data fields

At minimum, a useful training record needs a stable race ID, runner ID/name, country, race date/time, course, race conditions, pre-race features, non-runner status, official finishing position, and (for ROI evaluation) a decimal price with source and timestamp captured before the off.


### Community UK/Ireland historical archive — Kaggle candidate, not yet approved

- A community dataset titled "Horse Racing results - UK/Ireland 1988-2026" is listed as covering results from 1988 onward and was updated to 20 November 2026.
- The listing reports a download size of approximately 1.34 GB and the licence as Community Data License Agreement — Sharing — Version 1.0 (CDLA-Sharing-1.0).
- The licence permits computational use. If we publish the received data or enhanced data, we must publish it under the unmodified same agreement, preserve available provider attribution, mark changes, and not add restrictions. The licence does not restrict publication of computational results.
- The listing alone does not establish the original source and provenance of every historical record, nor prove that every field is accurate or consistently defined. We must inspect the dataset's own documentation, field definitions, source acknowledgements and sample records before accepting it.
- The archive is too large to commit to this Git repository. If approved, it should remain a local/external data asset; only import scripts, schema documentation and non-sensitive aggregate evaluation outputs belong in Git.
- Status: promising research candidate; not downloaded, verified, or integrated. No training or betting claims are based on it.

Dataset listing: https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025

Licence text: https://cdla.dev/sharing-1-0/

### Kickthebookies open racing angles — aggregate benchmark only

- The publisher offers downloadable CSV and JSON aggregate statistics under CC BY 4.0, with attribution and a link to the source required.
- Its published archive covers completed GB and Irish races since 2 January 2005, but its open-data tables contain angle/segment aggregates (runs, wins, places and fair A/E), not individual race or runner rows.
- This is suitable for contextual market/racing-angle benchmarking and checking broad historical patterns. It is not a substitute for runner-level features, individual results, racecards or pre-off odds, and cannot train the horse-level model.
- Do not infer individual outcomes from the aggregate rows.

Open data and attribution: https://kickthebookies.com/open-data/

### Licensing interpretation and integration gate

A dataset being downloadable without payment is not the same as being unrestricted. Before integration, confirm the exact dataset version, licence attached to that version, source acknowledgements, field definitions, and whether any upstream restrictions are disclosed. Do not redistribute raw or enhanced CDLA-Sharing data unless the project can comply with the same licence and attribution conditions. Model-derived computational results are treated separately under the CDLA terms.
