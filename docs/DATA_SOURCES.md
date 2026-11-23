# Data sources and zero-budget policy

The project is designed to keep recurring data costs at £0 / C$0. Free access does not automatically mean that automated extraction, storage, model training, or redistribution is permitted; each source must be checked before integration.

## Current source review

### HorseRacingAPI.org — possible results-history starter

- Its public documentation describes a free key for yesterday's results across Great Britain, Ireland, Northern Ireland, France and the USA.
- The free key is limited to 50 calls per day and does not include racecards or prices.
- Its terms restrict raw-data resale/republishing and systematic reconstruction of its database.
- This could help collect daily outcomes prospectively, but it does not provide the pre-race runner features or historical racecards required to train and validate a predictor.
- A free key requires account registration. No key is stored in this repository.

Documentation: https://horseracingapi.org/

### APIHorseRacing.com — separate free-key candidate

- This is a different service and domain from HorseRacingAPI.org. Its documentation says the free key can read yesterday's settled results, including GB and IRE, with a 50-request daily quota and 60 requests per minute.
- The free tier does not provide historical data before yesterday or starting prices/market prices. Paid archive access is listed from US$99/month, so it is outside the project's zero-budget requirement.
- Its terms permit use in the user's own models and products, but prohibit redistribution of raw data as a competing feed. The provider also disclaims completeness and accuracy.
- The endpoint documentation currently has no captured response example. We should not write an importer until a real response is inspected and the field mapping is tested.
- Potential use: optional prospective result verification for races run yesterday, not historical model training or EV calculation. A free key requires account registration; no key is stored in this repository.

Free-key limits: https://apihorseracing.com/documentation/free-key
Endpoint documentation: https://apihorseracing.com/documentation/results-yesterday
Terms: https://apihorseracing.com/terms

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
- A separate public GitHub importer project identifies this Kaggle archive as its source and documents an expected CSV staging layout. Its fields include date, course, race ID, off time, race name/type/class, pattern, rating/age/sex restrictions, distance, going, declared/actual runner counts, runner number, position, draw, beaten distances, horse, age, sex, weight, headgear, time, starting price (SP), jockey, trainer, prize, official rating (OR), Racing Post Rating (RPR), Topspeed (TS), pedigree, owner and comment. This corroborates the likely shape of the file, but does not independently establish field accuracy, upstream provenance, or completeness.
- Important: the documented `sp` field is a starting price, not a timestamped price captured before the off. It cannot be treated as verified pre-race odds for ROI evaluation. The importer project is useful as a schema reference only; its Apache-2.0 code licence does not change the separate dataset licence.
- Status: promising research candidate; not downloaded, verified, or integrated. No training or betting claims are based on it.

A generic CSV inspection utility is available at `src/inspect_dataset.py`. It can profile a downloaded file without importing it or loading all rows into memory. It is a structural first check only: it does not approve the Kaggle candidate, establish upstream provenance, validate the CDLA obligations, or make its fields safe for training. The archive remains unapproved until those checks are completed.

Schema reference (code project, not the dataset itself): https://github.com/openclosed-dev/raceform-database


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
