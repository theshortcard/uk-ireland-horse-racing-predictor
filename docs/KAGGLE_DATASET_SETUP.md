# Getting the Kaggle UK & Ireland historical archive

## Dataset

- Kaggle dataset: [Horse Racing results - UK/Ireland 1988-2026](https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025)
- Dataset owner: `deltaromeo`
- The public listing currently reports approximately 1.34 GB and CDLA-Sharing-1.0. The listing says it was updated to 20 November 2026.
- The archive is a community dataset, not an official BHA/IHRB feed. Its original record-level provenance and field definitions must be reviewed before we rely on it.

## Why we are not committing the archive to GitHub

The archive is too large for normal GitHub source control. The repository must contain code and documentation only; raw data stays outside Git. The dataset licence also has sharing and attribution obligations. Do not upload the raw archive or an enhanced copy to this public repository.

## One-time setup

1. Sign in to [Kaggle](https://www.kaggle.com/) or create a free account.
2. Open the dataset link above and accept its displayed terms/licence if Kaggle asks.
3. In Kaggle account settings, open the API section and create an API token. Kaggle downloads a `kaggle.json` credential file. Do not upload that file to GitHub or ChatGPT.
4. Open this GitHub repository, then **Settings → Secrets and variables → Actions**.
5. Create two repository secrets:
   - `KAGGLE_USERNAME`: the `username` value from your Kaggle token file.
   - `KAGGLE_KEY`: the `key` value from your Kaggle token file.
6. In the repository, open **Actions → Inspect Kaggle historical archive → Run workflow**.
7. Wait for the run to finish. Its log will show the downloaded file inventory, dataset metadata where available, CSV headers and a small first-row sample, or SQLite table/column names.

The workflow downloads the archive into a temporary GitHub runner, inspects its structure, and deletes the Kaggle credential file. It does **not** commit, publish, or retain the raw archive. It does not yet import or train on the data.

## What happens after inspection

We will use the actual file layout and headers to write a deliberate importer into the project's historical schema. Before that importer is accepted, we must check:

- the dataset's included documentation, upstream sources and attribution;
- field meanings, country coverage, date coverage and missingness;
- duplicate race/runner records and result status;
- whether any odds are starting prices (SP) rather than genuinely captured pre-race prices;
- the exact licence attached to the downloaded version and any upstream restrictions.

In particular, SP is not a timestamped pre-race bookmaker quote. It must not be used as verified pre-off odds for historical EV/ROI calculations. The imported results may still be useful for learning runner/race patterns, subject to provenance and licence checks.

## Licence and research safeguards

The listing currently identifies CDLA-Sharing-1.0. Read the [licence text](https://cdla.dev/sharing-1-0/) and retain its attribution and change-notice requirements. Do not redistribute raw or enhanced data unless we can comply with the same licence. Computational results are treated separately by that licence.

No performance, profitability or betting-edge claim will be made from fictional sample files or from this archive until provenance, mapping, leakage controls and out-of-sample testing have been completed.
