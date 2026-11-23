# UK & Ireland Horse Racing Predictor

A zero-monthly-data-budget project for UK and Irish horse racing, designed to produce race-level win probabilities, ranked runners, and transparent value/expected-value (EV) assessments.

## Current status

The first working baseline is in the repository:
- CSV racecard import and data-quality validation
- Explainable rating-led win probability estimates
- Optional raw EV calculation when decimal odds are supplied
- Normalized market fair probabilities, model-vs-market probability edge and model fair odds when the full field is priced
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
python -m src.provenance --input path/to/your_racecard.csv
python -m src.manifest --input data/source_manifest.json
```

The daily report is created at `reports/daily_report.md`, and the fictional historical example produces `reports/backtest.md`. Run `src.provenance` on your own CSV to check source fields, timestamp offsets, result verification and whether odds were captured before the scheduled off. Copy `data/source_manifest.template.json` to `data/source_manifest.json`, fill in the exact source and licence details, and run `src.manifest` to validate the metadata and verify the dataset SHA-256 checksum.

## Use your own data

Start with:
- `data/racecard_template.csv` for pre-race predictions.
- `data/historical_template.csv` for historical results and evaluation.

For an unfamiliar historical CSV, inspect its structure before mapping or importing it:

```bash
python -m src.inspect_dataset --input path/to/source.csv --output reports/dataset_inspection.md
```

This read-only utility streams the file and reports row/column counts, missing values, sample values, and likely date/country/horse/odds/result columns. It does not certify the source, licence, field meanings, or pre-race availability. Review those manually before building an import mapping.

An optional results snapshot utility can save yesterday's settled results from APIHorseRacing.com. It stores the raw JSON and a SHA-256/retrieval-time sidecar under `data/external/`, which is excluded from Git. It does not map records into the predictor or provide pre-race prices.

Set `AHR_API_KEY` in your local environment (never paste the key into ChatGPT or commit it), then run:

```bash
python -m src.fetch_results_api --output-dir data/external/apihorseracing
```

This optional service requires a free account. Its free key only reaches yesterday's results, with no historical archive or starting prices; see [data-source limitations](docs/DATA_SOURCES.md). A raw response must be reviewed before we can map or import it.

Required racecard columns: `race_id,date,course,country,off_time,horse,horse_age,official_rating,odds_decimal`. Country must be `GB` or `IRE`. Leave `odds_decimal` blank if no verified price is available.

For a racecard, run:

```bash
python -m src.run --input path/to/your_racecard.csv --output reports/daily_report.md
```

For historical evaluation, include `finish_position` and use only features and prices captured before the off:

```bash
python -m src.backtest --input path/to/historical.csv --output reports/backtest.md --test-fraction 0.2
```

See [the CSV data guide](docs/CSV_DATA_GUIDE.md) for field definitions, source/timestamp recording, and rules for historical data. The backtest supports dead heats (split-stake settlement), excludes withdrawn runners, and skips void, abandoned and incomplete races. It compares the model with a simple official-rating-only ranking (only where every runner has a supplied rating) and normalized market-implied probabilities (only where every active runner has a valid price). For each available approach it reports appropriate win-rate, Brier/log-loss and calibration comparisons, plus ROI where valid prices exist. It also reports a chronological holdout on the newest dates when enough historical dates are available. The holdout evaluates the fixed baseline; it does not train a model. See the [CSV data guide](docs/CSV_DATA_GUIDE.md) for result-status fields and limitations.

## Integrity rules

- Never invent racecards, runners, non-runners, results, odds, or prices.
- Clearly label missing, stale, estimated, or unverified information.
- EV is a raw estimate and does not remove bookmaker margin. Market fair probabilities require valid prices for every runner.
- Do not treat positive EV as a betting recommendation until the model is calibrated and tested out of sample.
- Keep historical evaluation separate from live predictions to prevent data leakage.
- Use only data whose terms permit the intended collection, storage, and model-development use.

## Zero-cost data policy

No paid API or monthly subscription is assumed. User-supplied CSV files are supported now. Automated UK and Irish data feeds will only be added after checking availability, licensing, terms, reliability, and permitted access. See [Data sources](docs/DATA_SOURCES.md) and the [Kaggle archive setup guide](docs/KAGGLE_DATASET_SETUP.md) for the optional historical dataset inspection workflow.

## Roadmap

See [development roadmap](docs/ROADMAP.md) for the remaining work: permitted free data sources, historical results, settlement handling, leakage-safe backtesting, improved features, and daily automation.
