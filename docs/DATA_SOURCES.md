# Data sources and zero-budget policy

The project is intentionally designed to avoid paid APIs and recurring subscriptions.

## First-stage inputs

- User-supplied racecard CSV files are supported immediately.
- The repository includes a clearly fictional sample CSV for testing the pipeline.
- No live racecard or bookmaker odds are bundled or fabricated.

## Before adding an automated source

For each source, document:
1. Official URL and publisher.
2. Whether access is free and stable.
3. Terms of use, licensing, and permitted automated access.
4. Coverage of Great Britain and/or Ireland.
5. Update frequency and timestamp handling.
6. Fields available (race, runner, going, distance, trainer, jockey, results, prices).
7. Failure behaviour and how stale data is labelled.

Do not scrape a site or redistribute its data unless its terms permit it. Prefer official downloads, open datasets, and sources with explicit reuse permissions.

## Odds policy

Odds must be supplied by the user or obtained from a source whose access and use are permitted. Every price should carry a source and timestamp in future versions. Missing odds mean no EV calculation and no value flag.
