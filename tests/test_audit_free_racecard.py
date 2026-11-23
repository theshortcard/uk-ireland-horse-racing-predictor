from src.audit_free_racecard import audit_payload


def test_audit_counts_races_regions_and_runner_mismatches():
    payload = {
        "total": 2,
        "limit": 500,
        "skip": 0,
        "racecards": [
            {
                "race_id": "r1", "date": "2026-11-23", "course": "Newcastle",
                "off_time": "4:40", "region": "gb", "race_status": "declared",
                "field_size": 7, "runners": [{"horse": "Alpha"}, {"horse": "Sultan Darius"}],
            },
            {
                "race_id": "r2", "date": "2026-11-23", "course": "Tramore",
                "off_time": "2:00", "region": "ire", "race_status": "abandoned",
                "field_size": 0, "runners": [],
            },
        ],
    }

    report = audit_payload(payload)

    assert report["race_count"] == 2
    assert report["unique_race_ids"] == 2
    assert report["missing_race_ids"] == 0
    assert report["regions"] == {"gb": 1, "ire": 1}
    assert report["race_statuses"] == {"abandoned": 1, "declared": 1}
    assert report["runner_objects"] == 2
    assert report["empty_runner_races"] == 1
    assert report["field_size_sum"] == 7
    assert report["field_size_runner_object_mismatches"][0]["field_size"] == 7
    assert report["field_size_runner_object_mismatches"][0]["runner_objects"] == 2


def test_audit_flags_duplicate_race_identity_and_course_time():
    race = {
        "race_id": "same", "date": "2026-11-23", "course": "Kempton",
        "off_time": "1:00", "region": "gb", "race_status": "declared",
        "field_size": 1, "runners": [{"horse": "Alpha"}],
    }
    report = audit_payload({"racecards": [race, dict(race)]})

    assert report["duplicate_race_ids"] == ["same"]
    assert report["duplicate_course_off_time_keys"] == [
        {"date": "2026-11-23", "course": "kempton", "off_time": "1:00", "count": 2}
    ]


def test_audit_rejects_missing_racecards_list():
    try:
        audit_payload({"total": 0})
    except ValueError as exc:
        assert "racecards" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
