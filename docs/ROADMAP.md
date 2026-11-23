# Development roadmap

## Phase 1 — foundation
- [x] Repository and project structure
- [x] CSV racecard import and validation
- [x] Explainable baseline probabilities
- [x] Optional raw EV calculation
- [x] Daily report market fair probabilities, model edge and fair odds (complete books only)
- [x] Markdown race report
- [x] Automated tests and CI workflow across Python 3.10 and 3.12
- [x] Race identity protection in reports and historical backtests
- [x] Blank racecard and historical CSV templates
- [x] Data dictionary and source/timestamp recording guide
- [x] Provenance audit for timezone-aware timestamps and pre-off odds

## Phase 2 — evaluation
- [x] Historical backtest framework
- [x] Top-pick hit rate, multiclass Brier score, log loss and expected calibration error
- [x] Flat-stake ROI where valid pre-race prices are supplied
- [x] Add dead-heat, void-race and non-runner settlement rules
- [x] Add market benchmark comparisons (normalized implied probabilities; complete-price races only)
- [x] Add chronological holdout evaluation by race date
- [x] Add official-rating-only benchmark comparison alongside the model and market favourite

## Phase 3 — data
- [x] Review candidate free sources and document licence/coverage constraints
- [x] Add dataset source manifest and SHA-256 integrity validator
- [x] Identify a CC BY aggregate benchmark source (not runner-level training data)
- [x] Add low-memory, read-only inspection for unfamiliar source CSV files
- [x] Review the Kaggle archive's importer schema without treating it as verified source data
- [x] Assess the separate APIHorseRacing free-key limits for daily results collection
- [x] Review HorseRacingAPI.org free result-only access and its no-database-rebuild restriction
- [x] Review RacingAPI.net UK/IRE coverage and confirm its listed subscription is outside the £0 budget
- [x] Review BHA public racing data packs; aggregate PDFs do not provide runner-level training rows
- [x] Distinguish RacingAPI.net card-required trial from Horse Racing API UK's limited free yesterday-results key
- [x] Review RPScrape and community fork; defer use pending explicit Racing Post permission and source-data rights
- [x] Add optional key-based raw results snapshot capture with local-only storage and checksum metadata


- [ ] Secure a permitted UK racecard and results feed
- [ ] Secure a permitted Irish racecard and results feed
- [ ] Automate source metadata and collection timestamps
- [ ] Add non-runner and late-change handling
- [ ] Build a prospective historical archive

## Phase 4 — modelling
- [ ] Build leakage-safe historical dataset
- [ ] Establish market and rating baselines
- [ ] Add course, distance, going, class, trainer, and jockey features when data supports them
- [ ] Evaluate log loss, Brier score, calibration, and ROI out of sample on a sufficiently large real dataset
- [ ] Only promote models that outperform baselines

## Phase 5 — daily operation
- [ ] Automated daily racecard refresh
- [ ] Daily UK and Ireland report
- [ ] Odds timestamp and price movement tracking
- [ ] Alerts for missing or stale data

The model must not be described as profitable or reliable until sufficient out-of-sample evidence supports that claim.
