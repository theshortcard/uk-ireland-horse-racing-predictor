# UK & Ireland Horse Racing Predictor

A zero-monthly-data-budget project for UK and Irish horse racing, designed to produce race-level win probabilities, ranked selections, and transparent value/expected-value (EV) assessments.

## Project goals

- Cover race meetings in Great Britain and Ireland.
- Produce probability-based race predictions, not just tip lists.
- Compare model probabilities with available bookmaker odds when supplied.
- Flag potential value only when the price, data quality, and assumptions are sufficiently reliable.
- Keep recurring data costs at £0 / C$0 by prioritising official or freely accessible sources and user-supplied odds.

## Safety and integrity rules

- Never invent racecards, runners, non-runners, results, odds, or prices.
- Clearly label missing, stale, estimated, or unverified information.
- Do not publish an EV recommendation without a usable price and an explicit probability estimate.
- Keep historical evaluation separate from live predictions to prevent data leakage.
- Track model performance with calibration, log loss, Brier score, and return-on-investment metrics where valid odds/results exist.

## Planned components

1. **Data ingestion** — racecards, runners, race conditions, results, and freely available historical data.
2. **Data validation** — duplicate checks, missing fields, timestamps, and source provenance.
3. **Feature engineering** — horse, trainer, jockey, course, distance, going, class, and recency features where reliable data is available.
4. **Prediction** — baseline probability model followed by measured improvements.
5. **Value engine** — implied probabilities, overround handling, expected value, and price thresholds.
6. **Reporting** — daily UK and Ireland race summaries with confidence and data-quality labels.
7. **Testing and audit** — reproducible tests, backtesting, and leakage checks.

## Initial development principle

Start with a transparent, testable baseline. Add data sources and model complexity only when their availability, licence/terms, and reliability have been checked. The system must remain usable without paid APIs.

## Status

Repository initialized. Data-source discovery and the first working baseline are next.
