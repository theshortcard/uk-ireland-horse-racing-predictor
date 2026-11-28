from src.import_theracingapi_racecards import convert_payload, OUTPUT_COLUMNS


def test_importer_maps_declared_gb_and_ire_runners_without_inventing_odds():
    payload = {
        "racecards": [
            {
                "race_id": "gb-1", "date": "2026-11-29", "course": "Carlisle",
                "off_time": "2:43", "off_dt": "2026-11-29T14:43:00+00:00",
                "region": "GB", "race_status": "declared",
                "runners": [
                    {"number": "1", "horse": "Runner A", "age": "6", "ofr": "105", "last_run": "23"},
                    {"number": "NR", "horse": "Non Runner", "age": "7", "ofr": "94", "last_run": "13"},
                    {"number": "R12", "horse": "Reserve", "age": "5", "ofr": "80", "last_run": "30"},
                ],
            },
            {
                "race_id": "ire-1", "date": "2026-11-29", "course": "Fairyhouse",
                "off_time": "1:00", "off_dt": "2026-11-29T13:00:00+00:00",
                "region": "IRE", "race_status": "declared",
                "runners": [
                    {"number": "1", "horse": "Runner B", "age": "8", "ofr": "120", "last_run": "40"},
                ],
            },
            {
                "race_id": "abandoned", "date": "2026-11-29", "course": "Leicester",
                "off_time": "12:00", "off_dt": "2026-11-29T12:00:00+00:00",
                "region": "GB", "race_status": "abandoned", "runners": [
                    {"number": "1", "horse": "Do Not Include", "age": "5", "ofr": "90", "last_run": "10"}
                ],
            },
        ]
    }
    metadata = {"retrieved_at": "2026-11-28T03:56:38Z"}

    rows, counts = convert_payload(payload, metadata)

    assert [row["horse"] for row in rows] == ["Runner A", "Runner B"]
    assert rows[0]["country"] == "GB"
    assert rows[1]["country"] == "IRE"
    assert rows[0]["off_time"] == "14:43"
    assert rows[0]["official_rating"] == "105"
    assert rows[0]["days_since_run"] == "23"
    assert rows[0]["odds_decimal"] == ""
    assert rows[0]["odds_source"] == ""
    assert rows[0]["source_name"] == "The Racing API free racecards"
    assert rows[0]["retrieved_at"] == "2026-11-28T03:56:38Z"
    assert counts == {
        "races_seen": 3,
        "races_skipped_not_declared": 1,
        "races_skipped_unknown_region": 0,
        "races_included": 2,
        "runner_objects_seen": 4,
        "non_runners_excluded": 1,
        "reserves_excluded": 1,
        "runners_included": 2,
    }
    assert set(rows[0]) == set(OUTPUT_COLUMNS)


def test_importer_rejects_missing_or_naive_retrieval_timestamp():
    payload = {"racecards": []}
    try:
        convert_payload(payload, {"retrieved_at": "2026-11-28T03:56:38"})
    except ValueError as exc:
        assert "timezone offset" in str(exc)
    else:
        raise AssertionError("Expected timezone-aware retrieval timestamp")


def test_importer_rejects_ambiguous_race_off_time():
    payload = {
        "racecards": [{
            "race_id": "r1", "date": "2026-11-29", "course": "Carlisle",
            "off_time": "2:43", "region": "GB", "race_status": "declared",
            "runners": [{"number": "1", "horse": "Runner A"}],
        }]
    }
    try:
        convert_payload(payload, {"retrieved_at": "2026-11-28T03:56:38Z"})
    except ValueError as exc:
        assert "off_dt" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing off_dt")
