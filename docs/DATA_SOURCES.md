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
