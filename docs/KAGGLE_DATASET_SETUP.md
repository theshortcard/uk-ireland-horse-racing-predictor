# Getting the Kaggle UK & Ireland historical archive

## Dataset

- Kaggle dataset: [Horse Racing results - UK/Ireland 1988-2026](https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025)
- Dataset owner: `deltaromeo`
- The public listing currently reports approximately 1.34 GB and CDLA-Sharing-1.0. The listing says it was updated to 20 November 2026.
- The archive is a community dataset, not an official BHA/IHRB feed. Its original record-level provenance and field definitions must be reviewed before we rely on it.

## Provenance and upstream-rights blocker

The archive's own bundled README identifies its upstream source as the
[Sporting-Life-Results-Scraper project](https://github.com/tastethewhip/Sporting-Life-Results-Scraper)
and links to its GitLab project. This is important: the Kaggle listing's
CDLA-Sharing-1.0 label is not, by itself, proof that the uploader had permission
to republish all upstream material under that agreement.

Sporting Life's published terms currently state that data capture (including
screen scraping) is prohibited and that its content/data may not be copied,
reproduced, stored or transmitted without explicit permission
([Sporting Life terms](https://www.sportinglife.com/terms-and-conditions)).
The CDLA-Sharing-1.0 agreement also relies on the Data Provider's representation
that it created the data or obtained it from others with the right to publish
it (section 4.1). We have not found documentation establishing that permission
for this archive.

**Decision: treat the Kaggle archive as rights-unverified and do not use it to
train, backtest, publish derived datasets, or support betting/ROI claims unless
the uploader can document the upstream permissions or a suitable rights holder
confirms permission.** This is a provenance/permission gap, not a legal finding
that infringement occurred. Keep the existing importer and audit as diagnostic
code only; do not retain or redistribute downloaded source files.

The CDLA-Sharing-1.0 terms distinguish computational results from the data
itself (section 3.5), and require received/enhanced data to remain under the
same agreement if published (section 3). Those provisions do not resolve
whether the Kaggle uploader had authority to grant the licence in the first
place. See the [CDLA-Sharing-1.0 text](https://cdla.dev/sharing-1-0/).

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


## Conservative staging importer

The repository includes a separate importer, but it does **not** certify the community archive or make it approved model-training data. After downloading and extracting the archive locally, run it against the CSV files (the archive paths may differ if Kaggle changes its packaging):

```bash
python -m src.import_kaggle_results \
  --input path/to/1988-2004.csv \
  --input path/to/2005-2014.csv \
  --input path/to/raceform.csv \
  --output data/external/kaggle_results_staging.csv
```

The importer:
- includes only course names in explicit GB/IRE allowlists; overseas and unknown venues are excluded rather than guessed;
- removes repeated CSV header rows and rows missing core race identity fields;
- maps the source's `age`, `or`, `pos`, and `sp` fields to separate staging fields;
- leaves `odds_decimal`, odds-source and odds-capture timestamps blank; source SP is preserved only in `source_sp`;
- sets `result_status=UNVERIFIED` and leaves result source/verification fields blank;
- writes only to the requested staging path (the default location is ignored by Git).

Course allowlists are deliberately conservative and incomplete. A course excluded by the importer may still be a valid GB or Irish venue; review the excluded-course counts and extend the allowlists only after checking each venue. The importer does not resolve duplicate runners, verify finishing positions, prove source rights, or make results official. Withdrawn/non-runner (`NR`, `WD`) and void-coded rows are not labelled as losers by the preparation step; they are quarantined for review. It also does not calculate ROI. Do not change UNVERIFIED to COMPLETED or supply odds fields unless the relevant source and permissions have been independently established.

The raw archive is not uploaded to this repository by this tool. Keep downloaded data outside GitHub and comply with the dataset licence and upstream source terms.
