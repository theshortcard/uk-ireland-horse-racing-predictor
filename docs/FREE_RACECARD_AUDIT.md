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

The snapshot was requested with both GB and IRE region codes, but returned only GB races. This is not evidence of a coverage failure: independent fixture listings show no Irish meeting on 23 November.

## Irish coverage check — Tuesday 24 November 2026

The Tuesday snapshot includes Tramore (IRE), with **7 race records** at 12:45, 13:15, 13:45, 14:15, 14:45, 15:15, and 15:50. Racing Post independently lists Tramore with the same seven races and the same scheduled off-times. Irish Horse Racing and RaceWatch also show one Irish meeting and seven races for this date.

This confirms that the free endpoint returned the Irish meeting when one was scheduled. It is a useful positive coverage check, but only one Irish meeting/date has been tested so far.

The Tramore runner totals need careful interpretation: the API snapshot contains 106 runner objects across the seven races, while its advertised `field_size` values sum to 94. Independent listings updated later in the day report different runner totals as declarations and non-runner information change. Preserve the raw snapshot and treat runner-level reconciliation as a separate validation item; do not use raw runner-object counts as confirmed active field sizes.

## Discrepancies reviewed

### Wincanton status — resolved

All six Wincanton races were marked abandoned by the API. The official Wincanton Racecourse notice confirmed that the Tuesday 24 November fixture was abandoned following a morning inspection. The API's abandoned status is therefore consistent with the official course notice. Some third-party racecard pages continued to display the original scheduled programme, which caused the apparent conflict.

### Runner counts — explained, with live-card reconciliation still required

The difference between the sum of advertised `field_size` values (461) and the number of runner objects (475) in the Tuesday snapshot was traced to non-runners and reserves in the feed. Six races had a difference between `field_size` and the number of runner objects. Do not treat every runner object as a confirmed active runner; retain the provider's runner-level status and distinguish reserves, non-runners, and declared runners in downstream processing.

The Monday snapshot shows the same principle on a specific race: Newcastle 16:40 has `field_size=7` and 8 runner objects, with Sultan Darius independently listed as a non-runner.

### Race counts — comparison completed for two dates

| Course | Tuesday API | Tuesday published comparison |
|---|---:|---:|
| Lingfield | 9 | 9 |
| Southwell | 8 | 8 |
| Tramore (IRE) | 7 | 7 |
| Wolverhampton | 9 | 9 |
| Wincanton | 6 | Fixture abandoned |

For Tuesday 24 November, the API's active-meeting race counts match the published listings checked for Lingfield, Southwell, Tramore, and Wolverhampton. Wincanton's six records represent an abandoned fixture, not six races to include in a live card. Earlier third-party listings differed on some counts, which is why source date and capture time must be recorded.

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

The free feed is promising. Wincanton's abandonment, race-count differences, and the presence of an Irish meeting have now been checked across two dates. **It is not yet validated for automatic predictor ingestion.** The next validation step is to repeat the test on another date with Irish fixtures and improve runner-status reconciliation. Continue using the free tier; do not purchase a subscription for this investigation.

The free racecard endpoint is a racecard source only. Do not infer odds, expected value, or a profitable betting edge from it.


## Third snapshot — Wednesday 25 November 2026

Workflow run `45302806570`, artifact `theracingapi-free-racecard-tomorrow`, retrieved at `2026-11-24T01:09:04.400474Z`, HTTP 200.

- **40 race records** and **461 runner objects**
- All 40 records dated 25 November 2026
- **32 GB** and **8 IRE** race records
- Five venues: Hereford (7), Kempton (9), Newcastle (9), Wetherby (7), and Dundalk (8)
- All 40 records marked declared; 40 unique race IDs; no duplicate course/off-time keys; no empty runner arrays
- Advertised field sizes sum to **452** across all 40 races

### Dundalk race-count discrepancy — resolved

The API returned eight Dundalk races at 14:01, 14:31, 15:01, 15:31, 16:06, 16:40, 17:10, and 17:40. Racing Post and Racing TV independently list the same eight races and times for 25 November. IrishRacing displays the same fixture beginning at 14:01 on its alternate date URL; its other indexed page appears to show 14:31 as the first race, which explains the earlier apparent seven-race count. The 14:01 race is not missing from the API feed.

### Dundalk runner objects — reconciliation pending independent recheck

The API supplies `field_size` as a numeric string (for example, `"14"`), not an integer. The audit code has been corrected to parse numeric strings and to flag reserve runners by runner number beginning with `R`.

The current documentation previously recorded a reserve-based reconciliation for this snapshot. That detailed runner-level result still needs to be independently rerun against the raw Wednesday artifact before it is treated as confirmed. Until then, retain the raw count of 461 runner objects and the advertised field-size sum of 452 as separate figures; do not assume the nine-record difference is fully explained by reserves.

Automated tests covering numeric-string field sizes and reserve exclusion have since completed successfully. A green test run confirms the audit logic passes its test cases; it does not, by itself, verify the contents of this particular downloaded snapshot.

## Current conclusion update

The third snapshot provides a second positive Irish coverage check (Dundalk, eight races) and resolves the earlier Dundalk seven-versus-eight race-count discrepancy. The revised automated tests are green, but the Wednesday runner-level reconciliation still requires a fresh audit of the raw artifact. Continue collecting dated snapshots; do not integrate the feed into the predictor until runner statuses are verified against real snapshots and several more dates reconcile.

## Fourth snapshot — Thursday 26 November 2026

Workflow run `45525315753`, artifact `theracingapi-free-racecard-tomorrow`, retrieved at `2026-11-25T01:23:03.336237Z`, HTTP 200. Snapshot SHA-256: `841c78f6af698ed07b8a30c4a336cc5b9b6df29dfe8099c1e0cd2826d161ae61`.

The workflow's saved audit report records:

- **35 race records**: **28 GB** and **7 IRE**
- Five courses: Chelmsford (AW) (9), Lingfield (6), Market Rasen (7), Taunton (6), and Thurles (7)
- All 35 records dated 26 November and marked declared
- 35 unique race IDs; no missing IDs, duplicate IDs, or duplicate course/off-time keys
- **360 runner objects**, including **5 records classified as reserves** by the audit rule (runner number beginning with `R`)
- **355 declared runner objects** after excluding those reserves; advertised field sizes sum to **355**
- No empty runner arrays, duplicate runner names, or field-size/declared-runner mismatches

The reserve classification is an audit-rule result. The five underlying runner records still require direct per-race inspection before their status can be treated as independently confirmed.

### Chelmsford race-count discrepancy — likely explained, raw API match still to verify

The API audit reports **9 Chelmsford races**. The apparent discrepancy is caused by inconsistent published summaries. Racing Post's individual 16:30 racecard explicitly lists the Midnite A Next Generation Betting App Handicap with 14 runners, and RaceTrends lists nine races from 16:30 to 20:30. However, Racing Post's meeting overview and Chelmsford Racecourse's fixture page currently summarize the meeting as eight races beginning at 17:00; Betfred and HorseRacing.net also show eight-race summaries beginning at 17:00.

The 16:30 race therefore appears to be a genuine scheduled race, not simply an API overcount. The raw API records still need direct inspection to confirm that the ninth Chelmsford record is this exact 16:30 race and that the other eight off-times and identities match the detailed card. Do not remove the 16:30 record based only on the conflicting eight-race summaries.

The other four course counts agree across the API audit and the independent listings checked: Lingfield 6, Market Rasen 7, Taunton 6, and Thurles 7.

The Thursday snapshot is a strong positive UK-and-Ireland coverage check. Chelmsford's count is provisionally explained by the detailed racecard evidence, but raw-record matching and direct inspection of the five reserve records remain outstanding. Keep the free tier and continue manual validation. The snapshot contains no odds and does not establish expected value or betting profitability.

### Chelmsford follow-up — detailed racecards support nine races

A further source check strengthens the explanation above. Racing Post's individual 26 November Chelmsford card explicitly shows the 16:30 Midnite A Next Generation Betting App Handicap (14 runners), followed by the 17:00 and later races. Betfred's individual 16:30 racecard also lists the same race and 14 runners. RaceTrends lists all nine Chelmsford races from 16:30 through 20:30, and Racecards.uk independently lists the 16:30 race with the same 14 named runners.

This detailed race-level evidence supports **nine scheduled Chelmsford races**. The racecourse's own event summary still says first race 17:00 and eight races, so its summary conflicts with the detailed racecard listings. The most likely explanation is that the event summary is stale or inconsistent. The API's Chelmsford count of nine is therefore provisionally supported by multiple detailed racecard sources, although direct matching of the raw API race IDs, off-times, and titles remains outstanding.

Sources checked: Racing Post individual Chelmsford card; Betfred individual 16:30 card; RaceTrends dated card; Racecards.uk individual 16:30 card; Chelmsford City Racecourse event summary. This source check validates the published schedule evidence, not the exact contents of the API's raw Chelmsford records.

### Repeat capture — 26 November card, 25 November at 06:43 UTC

A second free-tier request for the same target date completed successfully in workflow run `45562683304` (artifact ID `14998477515`). The fetch log records the raw snapshot as `racecards_tomorrow_20261125T064319Z.json`; the audit ran successfully and printed the following results:

- **35 races**, all dated 26 November 2026: 28 GB and 7 IRE
- Course counts unchanged: Chelmsford (AW) 9, Lingfield 6, Market Rasen 7, Taunton 6, Thurles 7
- All 35 races marked declared; 35 unique race IDs; no missing IDs or duplicate race/course-off-time keys
- **360 runner objects**, of which the audit classified 5 as reserves and 355 as declared
- Advertised field-size sum **355**, with no field-size/declared-runner mismatches
- No empty runner arrays or duplicate runner names

This repeat capture was made about 5 hours 20 minutes after the earlier 01:23 UTC capture and produced the same headline counts. It provides a useful consistency check for the card during that interval. It is not an independent date or an independent provider, and it does not replace inspection of the five individual reserve records or matching each raw Chelmsford record to the detailed published card. The workflow log exposes the audit summary, not the full raw race-by-race JSON.

Artifact digest: `sha256:094a9d4827136516de613a98b3aaf4d401ecbd98a749713da950b27de7d456ad`.

### Friday 27 November 2026 — repeatable cross-region coverage test

Workflow run `45765357856` completed successfully. Artifact ID `15091417840`; raw snapshot `racecards_tomorrow_20261126T060134Z.json`; captured 26 November 2026 at 06:01:34 UTC. The workflow audit summary reports:

- **38 races** dated 27 November 2026: 31 GB and 7 IRE
- Course counts: Doncaster 7, Dundalk (AW) 7, Musselburgh 7, Newbury 8, Southwell (AW) 9
- All 38 races marked declared; 38 unique race IDs; no missing IDs, duplicate IDs, or duplicate course/off-time keys
- **344 runner objects**: 338 classified as declared and 6 classified as reserves
- Advertised field-size sum 338 across all 38 races; no field-size/declared-runner mismatches
- No empty runner arrays or duplicate runner names

The 38-race total and course counts match the detailed Racing Post listing and another detailed racecard listing (Newbury 8, Southwell 9, Doncaster 7, Musselburgh 7, Dundalk 7). A live declaration tracker at an earlier update showed only 36 races, explicitly noting that four races were still awaiting declarations; its provisional counts were Newbury 7 and Southwell 8. This is consistent with a timing/declaration-state difference rather than evidence of missing API meetings. The tracker is dynamic, so the time of comparison matters.

This validates a further date with both GB and Irish coverage at the meeting-count level. It does not independently verify the six reserve classifications or every raw runner record; those remain subject to per-race raw snapshot inspection.

Artifact ZIP digest: `sha256:5ff813cbcbb39b478f982c7609c22533acf9fb397ab0fa48932916515877371e`.


## Saturday 28 November 2026 — successful audit after transient response-format failures

Workflow run `45937163995` completed successfully on commit `a0e652f4e14c38a09816c20ca10532269cefc62f`. Artifact ID `15170798540`; snapshot retrieved at `2026-11-27T03:58:09Z`. The fetch, audit, and artifact-upload steps all completed successfully.

The audit report records:

- **45 race records** dated 28 November 2026: **37 GB** and **8 IRE**
- Six courses: Bangor-on-Dee (7), Doncaster (7), Fairyhouse (8), Newbury (7), Newcastle (7), and Southwell (AW) (9)
- All 45 races marked declared; 45 unique race IDs; no missing IDs, duplicate IDs, or duplicate course/off-time keys
- **456 runner objects**, including **3 classified as reserves** by the current runner-number rule; 453 declared runner objects
- Advertised field sizes sum to **453**, with no field-size/declared-runner mismatches
- No empty runner arrays or duplicate runner names
- Provider total 45, limit 500, skip 0

### Independent race-count comparison

Racing Post's dated 28 November racecard independently lists the same six UK and Irish meetings and the same course-level race counts: Newbury 7, Newcastle 7, Fairyhouse 8, Bangor-on-Dee 7, Doncaster 7, and Southwell 9 — **45 races total**. HorseRacingBot also reports six meetings and 45 races. BBC Sport's calendar independently confirms the same six meetings. This resolves the date-level race-count check for this snapshot.

The two earlier workflow attempts (runs `45936945988` and `45936989718`) failed because the response being audited did not contain the expected `racecards` list. This successful capture did contain a valid structure and passed the full audit. The available evidence shows the earlier failure was not persistent; its precise cause is not established. The workflow was also changed so that the raw snapshot is uploaded even if a future audit fails, preserving evidence for diagnosis.

The three reserve classifications still need direct per-runner inspection before being treated as independently confirmed. This snapshot is a strong positive coverage and structural-integrity check, not final approval for automatic predictor ingestion. Continue free-tier, date-by-date validation; do not add odds or EV claims to this feed.


## Sunday 29 November 2026 — final planned broad coverage sample

Workflow run `46105203652` completed successfully on commit `5ce1f7a97e4e1071539928e7a08005f5fbffd70b`. Artifact ID `15247186961`; the raw snapshot was retrieved at `2026-11-28T03:56:38Z`. Fetch, audit, and artifact-upload steps all completed successfully.

The audit summary reports:

- **28 race records** dated 29 November 2026: **20 GB** and **8 IRE**
- Four courses: Carlisle (7), Fairyhouse (8), Ffos Las (7), and Leicester (6)
- All 28 race IDs unique; no missing IDs, duplicate IDs, or duplicate course/off-time keys
- Race statuses: **22 declared** and **6 abandoned** (all six Leicester races)
- **284 runner objects**; no records classified as reserves by the current rule
- Advertised field sizes sum to **283**
- No empty runner arrays or duplicate runner names
- Provider total 28, limit 500, skip 0

### Independent race-count comparison — matched

Racing Post's dated Sunday 29 November card lists Fairyhouse 8, Carlisle 7, Ffos Las 7, and Leicester 6 (abandoned), matching the API's four course counts and **28 total race records**. Stablebet independently reports four meetings and 28 races. The Leicester records are retained in the raw feed but marked abandoned; they must not be treated as active races by a predictor.

Sources checked: Racing Post dated racecards, Stablebet dated racecards, Racecards.uk, and Betfred's dated racecard listing. The source pages agree on the meeting/race counts and Leicester abandonment.

### One runner-count mismatch remains — Carlisle 14:43

The audit flags Carlisle at 14:43: advertised `field_size=10`, but the snapshot contains 11 runner objects. The independent published cards checked show 10 runners for that race. The extra object is consistent with a non-runner or other inactive runner record retained in the provider payload, but the current summary does not expose enough per-runner detail to confirm its status. It is **not** classified as a reserve by the current rule.

The total advertised field size is 283 versus 284 raw runner objects, so this one-runner difference accounts for the overall one-record mismatch. Keep this as an explicit runner-status issue to resolve before automatic runner selection; do not silently discard the extra object.

### Conclusion after Sunday

This is a successful final planned broad coverage sample: UK and Irish course counts match independent published cards, including the six abandoned Leicester races being represented with abandoned status. The repeated snapshots now cover multiple dates and multiple Irish meetings. There is no evidence from these samples of systematic missing race meetings or a race-count problem in the free feed.

The broad racecard coverage phase can therefore be considered complete. **One targeted data-quality task remains:** inspect the Carlisle 14:43 extra runner object and verify how the provider marks non-runners/reserves in raw records. After that, we can decide whether the feed is safe for a controlled predictor input pipeline. Keep the free tier; no paid subscription is justified by these findings. The endpoint still supplies racecards only, not odds or expected value.
