# Development roadmap

## Phase 1 — foundation
- [x] Repository and project structure
- [x] CSV racecard import and validation
- [x] Explainable baseline probabilities
- [x] Optional decimal-odds EV calculation
- [x] Markdown report
- [x] Automated tests and CI workflow

## Phase 2 — data
- [ ] Verify free, permitted UK racecard source(s)
- [ ] Verify free, permitted Irish racecard source(s)
- [ ] Add source metadata and collection timestamps
- [ ] Add non-runner and late-change handling
- [ ] Add result ingestion and historical archive

## Phase 3 — modelling
- [ ] Build leakage-safe historical dataset
- [ ] Establish market and rating baselines
- [ ] Add course, distance, going, class, trainer, and jockey features when data supports them
- [ ] Evaluate log loss, Brier score, calibration, and ROI
- [ ] Only promote models that outperform baselines out of sample

## Phase 4 — daily operation
- [ ] Automated daily racecard refresh
- [ ] Daily UK and Ireland report
- [ ] Odds timestamp and price movement tracking
- [ ] Alerts for missing or stale data

The model must not be described as profitable or reliable until sufficient out-of-sample evidence supports that claim.
