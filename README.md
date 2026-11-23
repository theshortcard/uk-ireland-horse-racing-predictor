# UK & Ireland Horse Racing Predictor

A zero-monthly-data-budget project for UK and Irish horse racing, designed to produce race-level win probabilities, ranked runners, and transparent value/expected-value (EV) assessments.

## Current status

The first working baseline is now in the repository:
- CSV racecard import and data-quality validation
- Explainable rating-led win probability estimates
- Optional raw EV calculation when decimal odds are supplied
- Markdown race report
- Automated pytest checks and GitHub Actions workflow

**Important:** this is an experimental baseline, not a trained or proven profitable model. The sample racecard contains fictional runners solely to test the software. It is not a live racecard.

## Run it

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.run --input data/sample_racecard.csv --output reports/daily_report.md
```

The report is created at `reports/daily_report.md`. To use your own racecard, make a CSV with the same columns as `data/sample_racecard.csv`, then replace the input path:

```bash
python -m src.run --input path/to/your_racecard.csv --output reports/daily_report.md
```

Required CSV columns: `race_id,date,course,country,off_time,horse,horse_age,official_rating,odds_decimal`. Country must be `GB` or `IRE`. Leave `odds_decimal` blank if no verified price is available.

## Integrity rules

- Never invent racecards, runners, non-runners, results, odds, or prices.
- Clearly label missing, stale, estimated, or unverified information.
- EV is calculated only when a valid decimal price is supplied; it is a raw estimate and does not remove bookmaker margin.
- Do not treat a positive EV estimate as a betting recommendation until the model is calibrated and tested out of sample.
- Keep historical evaluation separate from live predictions to prevent data leakage.
- Track calibration, log loss, Brier score, and ROI only where valid historical odds/results exist.

## Zero-cost data policy

No paid API or monthly subscription is assumed. User-supplied CSV files are supported now. Automated UK and Irish data feeds will only be added after checking their availability, licensing, terms, reliability, and permitted access. See [Data sources](docs/DATA_SOURCES.md).

## Roadmap

See [development roadmap](docs/ROADMAP.md) for the remaining work: permitted free data sources, historical results, non-runner handling, leakage-safe backtesting, improved features, and daily automation.
