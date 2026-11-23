# Free racecard feed audit

**Status:** multi-day validation in progress  
**Feed:** The Racing API free `/v1/racecards/free` endpoint  
**Policy:** manual, one-day-at-a-time testing; no paid endpoints, no subscription, no odds, and no model import until the feed is validated.

## Snapshot under review

The inspected workflow artifact for Tuesday 24 November 2026 reported:

- **39 race records** and **475 runner records**
- **32 UK** and **7 Irish** race records
- Five venues: Lingfield, Southwell, Tramore, Wincanton, and Wolverhampton
- 33 race records marked declared and 6 marked abandoned
- 39 unique race IDs; no empty runner arrays

The artifact was retrieved at `2026-11-23T06:05:19.904912Z`, with HTTP 200. The JSON is a raw snapshot; it does not include odds or establish betting value.

## Second snapshot — Monday 23 November 2026

Workflow run `45124155080`, artifact `theracingapi-free-racecard-today`, retrieved at `2026-11-23T06:27:01.705261Z`, HTTP 200.

- **38 race records** and **366 runner objects**
- All 38 records dated 23 November 2026
- **38 GB** race records; **0 IRE** race records
- Five venues: Bangor-on-Dee (7), Huntingdon (6), Kempton (7), Newcastle (9), and Wolverhampton (9)
- All 38 races marked declared
- 38 unique race IDs; no missing IDs
- Sum of advertised `field_size`: 365

The race count and meeting breakdown matched independent same-date published listings (38 races across the same five courses). The API's Newcastle 16:40 record contains 8 runner objects while `field_size` is 7. Racing Post's same-date non-runner listing identifies Sultan Darius as a non-runner in that race. This is a runner-status distinction, not an extra race or a race-count discrepancy.

The snapshot was requested with both GB and IRE region codes, but returned only GB races. This is not evidence of a coverage failure: the independent fixture listings for 23 November show no Irish meeting. The Tuesday 24 November snapshot includes Tramore (7 Irish races), so Irish coverage is being tested on a date with an Irish fixture.

## Discrepancies reviewed

### Wincanton status — resolved

All six Wincanton races were marked abandoned by the API. The official Wincanton Racecourse notice confirmed that the Tuesday 24 November fixture was abandoned following a morning inspection. The API's abandoned status is therefore consistent with the official course notice. Some third-party racecard pages continued to display the original scheduled programme, which caused the apparent conflict.

### Runner counts — explained

The difference between the sum of advertised `field_size` values (461) and the number of runner objects (475) in the Tuesday snapshot was traced to non-runners and reserves in the feed. Six races had a difference between `field_size` and the number of runner objects. Do not treat every runner object as a confirmed active runner; retain the provider's runner-level status and distinguish reserves, non-runners, and declared runners in downstream processing.

The Monday snapshot shows the same principle on a specific race: Newcastle 16:40 has `field_size=7` and 8 runner objects, with Sultan Darius independently listed as a non-runner.

### Race counts — comparison completed for this date, repeat test still required

| Course | API | Racecards.uk comparison | Racing Post comparison |
|---|---:|---:|---:|
| Lingfield | 9 | 9 | 8 |
| Southwell | 8 | 8 | 7 |
| Tramore | 7 | 7 | 7 |
| Wolverhampton | 9 | 9 | 8 |
| Wincanton | 6 | Fixture abandoned | 6 listed |

For the four active meetings, the API counts matched the Racecards.uk listing checked during this investigation. Racing Post showed one fewer race at Lingfield, Southwell, and Wolverhampton. This means the API's extra records are not established as errors; published listings can differ. Wincanton's six records represent an abandoned fixture, not six races to include in a live card.

The Monday 23 November snapshot independently matched published listings at all five active meetings: Bangor-on-Dee 7, Huntingdon 6, Kempton 7, Newcastle 9, and Wolverhampton 9 — 38 races total.

These are date-specific comparisons. They do not prove the feed will remain complete or consistent on other dates. Keep source capture times with future comparisons because racecards can change during the day.

## Audit procedure

For each new test snapshot:

1. Preserve the original JSON artifact unchanged and record its workflow run, retrieval timestamp, selected date, and SHA-256 checksum.
2. Normalize race identity using the source race ID where present; retain the original ID and raw record.
3. Group records by country, course, local race date, and scheduled off time.
4. Count unique races separately from raw race records. Flag duplicate IDs, duplicate course/off-time pairs, missing IDs, and unexpected dates.
5. Compare each course against a time-stamped published racecard for the same local date. Record the reference source and capture time.
6. Compare race status values without silently converting them. Exclude abandoned meetings/races from active-card predictions while retaining them in the audit.
7. Classify runner records using runner-level status; keep reserves and non-runners separate from active declared runners.
8. Produce a discrepancy report. Never silently delete, merge, or relabel records.

## Acceptance criteria before predictor integration

- Race counts reconcile to a dated published-card reference, or every difference is explicitly explained.
- No unexplained duplicate race identities remain.
- Abandoned/cancelled statuses are checked against an independent reference.
- UK and Irish coverage is checked independently.
- Runner statuses distinguish active declarations, non-runners, and reserves.
- The same checks pass on multiple dates.
- Raw snapshots remain unchanged and traceable.
- No odds, EV, or predictor inputs are inferred from this free endpoint.

## Current conclusion

The free feed is promising. The Wincanton abandonment, runner-count differences, and race-count comparisons have been investigated across two dates. **It is not yet validated for automatic predictor ingestion.** The next validation step is to continue checking a date with Irish fixtures and repeat the comparisons. Continue using the free tier; do not purchase a subscription for this investigation.

The free racecard endpoint is a racecard source only. Do not infer odds, expected value, or a profitable betting edge from it.
