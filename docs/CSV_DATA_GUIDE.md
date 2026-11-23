# CSV data guide

Use the blank templates in `data/` when entering real race information:

- `racecard_template.csv` is for pre-race predictions.
- `historical_template.csv` is for historical evaluation and includes result fields.

## Required racecard fields

`race_id,date,course,country,off_time,horse,horse_age,official_rating,odds_decimal`

Use `GB` for Great Britain and `IRE` for Ireland. Use a stable race identifier that is unique for each race on a date (for example, a source-provided race ID). Keep horse names consistent within each race. Decimal odds must be greater than 1.0; leave them blank when no verified price is available. If supplied, `days_since_run` must be a finite, nonnegative number. Blank `horse_age`, `official_rating` or `days_since_run` values trigger a visible data-quality warning because the baseline substitutes neutral defaults.

## Provenance fields

The templates include optional audit fields:

- `source_name`: where the racecard or record came from.
- `retrieved_at`: when the record was obtained, as an ISO 8601 timestamp including timezone.
- `odds_source`: bookmaker or exchange that displayed the price.
- `odds_captured_at`: when that exact price was observed, as an ISO 8601 timestamp including timezone.
- `finish_position`: official finishing position for historical records; tied winners may share position `1`.
- `runner_status`: use `RUNNER` or `NON_RUNNER` (also accepts `NR`, `WITHDRAWN`, and `SCRATCHED`). Keep withdrawn runners in the file for audit; they are excluded from model predictions and ROI.
- `result_status`: use `COMPLETED`, `VOID`, `ABANDONED`, or `INCOMPLETE`. Blank values are treated as completed for backwards compatibility.
- `result_source`: official or otherwise permitted result source.
- `result_verified_at`: when the result was checked, including timezone.

Do not enter a guessed timestamp. If a source does not provide a field, leave it blank and retain the source's original record separately where permitted. For ROI analysis, only use prices demonstrably captured before the race started. Do not use starting prices or closing prices as pre-race prices unless the model's prediction timestamp genuinely preceded them.

## Historical data rules

- Enter actual results only; never copy the fictional examples into a real training dataset.
- Keep all runners in a race, including non-runners, and mark withdrawn runners with `runner_status=NON_RUNNER`.
- Multiple runners with `finish_position=1` are treated as a dead heat. The backtest splits the winning return across tied winners (decimal odds divided by the number of tied winners).
- Mark void or abandoned races with `result_status=VOID` or `ABANDONED`; they are skipped. Incomplete races are also skipped and counted in the report.
- Result status and finish position are settlement/evaluation fields only; they must never be used as pre-race model inputs.
- The backtest also compares the model with a market baseline using normalized implied probabilities. This comparison is shown only for races where every active runner has a valid decimal price; record and check each price timestamp.
- When at least two distinct race dates are present, the report evaluates the newest dates as a chronological holdout (20% by default). Set `--test-fraction` to change the share of newest dates. This evaluates the fixed baseline; it does not train a model.
- Keep source terms and permission records. Publicly viewable does not automatically mean permitted for bulk collection, storage, or model training.

## Current model limitation

The baseline uses official rating, days since run, and age as simple ranking signals. It is not trained on the supplied sample and has no proven predictive edge. More fields should only be added to the model after sufficient lawful historical data is available and tested out of sample.


## Market comparison in the daily report

When every runner in a race has a valid decimal price, the report normalizes the implied probabilities to remove the displayed overround and shows a market-fair probability for each runner. The model edge is the model probability minus this normalized market probability, shown in percentage points. Model fair odds are the inverse of the model probability. If any runner lacks a valid price, market-fair probabilities and edges are withheld for the entire race. These are comparison diagnostics, not proof of value or betting recommendations.


The historical report includes expected calibration error (ECE) using ten equal-width probability bins for both the model and, where complete prices exist, the normalized market benchmark. Lower ECE indicates a closer match between predicted probabilities and observed win frequencies, but ECE can be unstable on small datasets and should be interpreted alongside Brier score, log loss and the chronological holdout.
