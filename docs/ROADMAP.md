# Development roadmap

## Phase 1 — foundation
- [x] Repository and project structure
- [x] CSV racecard import and validation
- [x] Explainable baseline probabilities
- [x] Optional raw EV calculation
- [x] Markdown race report
- [x] Automated tests and CI workflow across Python 3.10 and 3.12
- [x] Race identity protection in reports and historical backtests
- [x] Blank racecard and historical CSV templates
- [x] Data dictionary and source/timestamp recording guide

## Phase 2 — evaluation
- [x] Historical backtest framework
- [x] Top-pick hit rate, multiclass Brier score and log loss
- [x] Flat-stake ROI where valid pre-race prices are supplied
- [x] Add dead-heat, void-race and non-runner settlement rules
- [ ] Add time-based train/test split and benchmark comparisons

## Phase 3 — data
- [x] Review candidate free sources and document licence/coverage constraints
- [ ] Secure a permitted UK racecard and results feed
- [ ] Secure a permitted Irish racecard and results feed
- [ ] Automate source metadata and collection timestamps
- [ ] Add non-runner and late-change handling
- [ ] Build a prospective historical archive

## Phase 4 — modelling
- [ ] Build leakage-safe historical dataset
- [ ] Establish market and rating baselines
- [ ] Add course, distance, going, class, trainer, and jockey features when data supports them
- [ ] Evaluate log loss, Brier score, calibration, and ROI out of sample
- [ ] Only promote models that outperform baselines

## Phase 5 — daily operation
- [ ] Automated daily racecard refresh
- [ ] Daily UK and Ireland report
- [ ] Odds timestamp and price movement tracking
- [ ] Alerts for missing or stale data

The model must not be described as profitable or reliable until sufficient out-of-sample evidence supports that claim.
