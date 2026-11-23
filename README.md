# UK & Ireland Horse Racing Predictor

A zero-monthly-data-budget project for UK and Irish horse racing, designed to produce race-level win probabilities, ranked runners, and transparent value/expected-value (EV) assessments.

## Current status

The first working baseline is in the repository:
- CSV racecard import and data-quality validation
- Explainable rating-led win probability estimates
- Optional raw EV calculation when decimal odds are supplied
- Markdown race report and historical backtest
- Blank CSV templates with source and timestamp fields
- Automated pytest checks and GitHub Actions workflow

**Important:** this is an experimental baseline, not a trained or proven profitable model. The sample racecard and sample historical file contain fictional runners solely to test the software. They are not live racing data.

## Run it

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.run --input data/sample_racecard.csv --output reports/daily_report.md
python -m src.backtest --input data/sample_historical.csv --output reports/backtest.md
```

The daily report is created at `reports/daily_report.md`, and the fictional historical example produces `reports/backtest.md`.

## Use your own data

Start with:
- `data/racecard_template.csv` for pre-race predictions.
- `data/historical_template.csv` for historical results and evaluation.

Required racecard columns: `race_id,date,course,country,off_time,horse,horse_age,official_rating,odds_decimal`. Country must be `GB` or `IRE`. Leave `odds_decimal` blank if no verified price is available.

For a racecard, run:

```bash
python -m src.run --input path/to/your_racecard.csv --output reports/daily_report.md
```

For historical evaluation, include `finish_position` and use only features and prices captured before the off:

```bash
python -m src.backtest --input path/to/historical.csv --output reports/backtest.md
```

See [the CSV data guide](docs/CSV_DATA_GUIDE.md) for field definitions, source/timestamp recording, and rules for historical data. The backtest supports dead heats (split-stake settlement), excludes withdrawn runners, and skips void, abandoned and incomplete races. It also compares the model with normalized market-implied probabilities when every active runner has a valid price. See the [CSV data guide](docs/CSV_DATA_GUIDE.md) for result-status fields and limitations.

## Integrity rules

- Never invent racecards, runners, non-runners, results, odds, or prices.
- Clearly label missing, stale, estimated, or unverified information.
- EV is a raw estimate and does not remove bookmaker margin.
- Do not treat positive EV as a betting recommendation until the model is calibrated and tested out of sample.
- Keep historical evaluation separate from live predictions to prevent data leakage.
- Use only data whose terms permit the intended collection, storage, and model-development use.

## Zero-cost data policy

No paid API or monthly subscription is assumed. User-supplied CSV files are supported now. Automated UK and Irish data feeds will only be added after checking availability, licensing, terms, reliability, and permitted access. See [Data sources](docs/DATA_SOURCES.md).

## Roadmap

See [development roadmap](docs/ROADMAP.md) for the remaining work: permitted free data sources, historical results, settlement handling, leakage-safe backtesting, improved features, and daily automation.
