# Free racecard feed audit

**Status:** investigation in progress  
**Feed:** The Racing API free `/v1/racecards/free` endpoint  
**Policy:** manual, one-day-at-a-time testing; no paid endpoints, no subscription, no odds, and no model import until the feed is validated.

## Latest observed snapshot

The latest inspected workflow artifact contained:

- **39 race records** and **475 runner records**
- **32 UK** and **7 Irish** race records
- All five expected venues were present
- **33 runners** were reported as declared (26 UK, 7 Irish)

These are observations from the workflow artifact, not proof that the feed is complete or that every status is correct.

## Discrepancies to investigate

| Course | API records | Published card | Observed issue |
|---|---:|---:|---|
| Lingfield | 9 | 8 | One additional API race record |
| Southwell | 8 | 7 | One additional API race record |
| Wolverhampton | 9 | 8 | One additional API race record |
| Wincanton | 6 | 6 | All six API records were marked abandoned although the published card still showed six races |

The three extra-record differences and the Wincanton status conflict are **unexplained**. Do not assume they are API defects: first check date/time-zone handling, duplicate race identifiers, meetings or divisions, stale/cancelled records, and the published-card snapshot time.

## Audit procedure

For each new test snapshot:

1. Preserve the original JSON artifact unchanged and record its workflow run, retrieval timestamp, selected date, and SHA-256 checksum.
2. Normalize race identity using the source race ID where present; retain the original ID and raw record.
3. Group records by country, course, local race date, and scheduled off time.
4. Count unique races separately from raw race records. Flag duplicate IDs, duplicate course/off-time pairs, missing IDs, and unexpected dates.
5. Compare each course against a time-stamped published racecard for the same local date. Record the reference source and capture time.
6. Compare race status values without silently converting them. Flag abandoned/cancelled/void statuses where the contemporaneous published card shows a race scheduled to run.
7. Compare runner counts and declared/non-runner statuses separately; do not equate a runner record with a confirmed declaration.
8. Produce a discrepancy report. Never silently delete, merge, or relabel records.

## Acceptance criteria before predictor integration

- Race counts reconcile to a dated published-card reference, or every difference is explicitly explained.
- No unexplained duplicate race identities remain.
- Wincanton status conflicts are resolved against an independent, time-stamped reference.
- UK and Irish coverage is checked independently.
- Raw snapshots remain unchanged and traceable.
- No odds, EV, or predictor inputs are inferred from this free endpoint.

## Current conclusion

The free feed is promising enough to continue testing, but **it is not yet validated for automatic predictor ingestion**. The current evidence identifies specific discrepancies; it does not establish their cause.

The next step is to inspect the raw JSON from the latest `theracingapi-free-racecard-tomorrow` artifact and build a reproducible parser/audit against its actual schema. Keep the artifact private and do not commit credentials or raw provider data to the repository.