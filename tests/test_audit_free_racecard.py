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
    assert report["field_size_runner_object_mismatches"][0][
        "active_runner_objects_excluding_reserves_and_non_runners"
    ] == 2


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


def test_audit_parses_provider_field_size_strings():
    payload = {
        "racecards": [{
            "race_id": "r1", "date": "2026-11-25", "course": "Dundalk",
            "off_time": "2:31", "region": "ire", "race_status": "declared",
            "field_size": "14",
            "runners": [{"horse": f"Horse {i}"} for i in range(15)],
        }]
    }
    report = audit_payload(payload)

    assert report["field_size_sum"] == 14
    assert report["field_size_known_races"] == 1
    assert report["field_size_runner_object_mismatches"] == [{
        "course": "Dundalk", "date": "2026-11-25", "off_time": "2:31",
        "field_size": 14,
        "active_runner_objects_excluding_reserves_and_non_runners": 15,
        "all_runner_objects": 15,
        "reserve_runner_objects": 0,
        "non_runner_objects": 0,
    }]


def test_audit_excludes_reserve_entries_from_declared_field_comparison():
    payload = {
        "racecards": [{
            "race_id": "r1", "date": "2026-11-25", "course": "Dundalk",
            "off_time": "2:31", "region": "ire", "race_status": "declared",
            "field_size": "14",
            "runners": (
                [{"number": str(i), "horse": f"Horse {i}"} for i in range(1, 15)]
                + [{"number": "R15", "horse": "Reserve Horse"}]
            ),
        }]
    }
    report = audit_payload(payload)

    assert report["runner_objects"] == 15
    assert report["declared_runner_objects_excluding_reserves"] == 14
    assert report["reserve_runner_objects"] == 1
    assert report["non_runner_objects"] == 0
    assert report["active_runner_objects_excluding_reserves_and_non_runners"] == 14
    assert report["field_size_runner_object_mismatches"] == []


def test_audit_excludes_nr_entries_from_active_field_size():
    payload = {
        "racecards": [{
            "race_id": "carlisle-1443", "date": "2026-11-29", "course": "Carlisle",
            "off_time": "2:43", "region": "gb", "race_status": "declared",
            "field_size": "10",
            "runners": (
                [{"number": str(i), "horse": f"Horse {i}"} for i in range(1, 11)]
                + [{"number": "NR", "horse": "Uncle Al", "jockey": ""}]
            ),
        }]
    }
    report = audit_payload(payload)

    assert report["runner_objects"] == 11
    assert report["declared_runner_objects_excluding_reserves"] == 11
    assert report["reserve_runner_objects"] == 0
    assert report["non_runner_objects"] == 1
    assert report["active_runner_objects_excluding_reserves_and_non_runners"] == 10
    assert report["field_size_runner_object_mismatches"] == []
