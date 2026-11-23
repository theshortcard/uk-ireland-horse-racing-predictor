# CSV data guide

Use the blank templates in `data/` when entering real race information:

- `racecard_template.csv` is for pre-race predictions.
- `historical_template.csv` is for historical evaluation and includes result fields.

## Required racecard fields

`race_id,date,course,country,off_time,horse,horse_age,official_rating,odds_decimal`

Use `GB` for Great Britain and `IRE` for Ireland. Use a stable race identifier that is unique for each race on a date (for example, a source-provided race ID). Keep horse names consistent within each race. Decimal odds must be greater than 1.0; leave them blank when no verified price is available.

## Provenance fields

The templates include optional audit fields:

- `source_name`: where the racecard or record came from.
- `retrieved_at`: when the record was obtained, as an ISO 8601 timestamp including timezone.
- `odds_source`: bookmaker or exchange that displayed the price.
- `odds_captured_at`: when that exact price was observed, as an ISO 8601 timestamp including timezone.
- `finish_position`: official finishing position for historical records.
- `result_source`: official or otherwise permitted result source.
- `result_verified_at`: when the result was checked, including timezone.

Do not enter a guessed timestamp. If a source does not provide a field, leave it blank and retain the source's original record separately where permitted. For ROI analysis, only use prices demonstrably captured before the race started. Do not use starting prices or closing prices as pre-race prices unless the model's prediction timestamp genuinely preceded them.

## Historical data rules

- Enter actual results only; never copy the fictional examples into a real training dataset.
- Keep all runners in a race, including non-runners if the source records them, and document status in a separate notes/source file until explicit non-runner settlement is implemented.
- The current backtest only evaluates races with exactly one winner. Exclude dead heats, voids, abandoned races, and incomplete results.
- Keep source terms and permission records. Publicly viewable does not automatically mean permitted for bulk collection, storage, or model training.

## Current model limitation

The baseline uses official rating, days since run, and age as simple ranking signals. It is not trained on the supplied sample and has no proven predictive edge. More fields should only be added to the model after sufficient lawful historical data is available and tested out of sample.
