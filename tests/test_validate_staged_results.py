from src.validate_staged_results import audit_file, valid_time


def test_time_validation():
    assert valid_time("13:05")
    assert valid_time("9:05")
    assert valid_time("13:05:42")
    assert not valid_time("25:05")
    assert not valid_time("13:99")
    assert not valid_time("")


def test_audit_counts_duplicates_and_invalid_rows(tmp_path):
    source = tmp_path / "staging.csv"
    source.write_text(
        """race_id,date,course,country,off_time,horse,horse_age,official_rating,finish_position,result_status,source_finish_code
R1,2026-11-20,Ascot,GB,13:00,Runner A,5,100,1,UNVERIFIED,
R1,2026-11-20,Ascot,GB,13:00,Runner A,5,100,1,UNVERIFIED,
R1,2026-11-20,Ascot,GB,13:00,Runner B,4,,2,UNVERIFIED,
R2,2026-11-20,Dundalk,IRE,25:00,Runner C,0,-1,,UNVERIFIED,XYZ
R3,2026-11-20,Ascot,GB,14:00,Runner D,5,90,0,UNVERIFIED,
R4,2026-11-20,Ascot,GB,15:00,Runner E,5,90,,UNVERIFIED,LFT
R5,2026-11-20,Ascot,GB,16:00,Runner F,5,90,,UNVERIFIED,-
""",
        encoding="utf-8",
    )
    report = audit_file(source)
    counts = report["counts"]
    assert counts["rows"] == 7
    assert counts["duplicate_runner_rows"] == 1
    assert counts["missing_official_rating"] == 1
    assert counts["invalid_off_time"] == 1
    assert counts["invalid_horse_age"] == 1
    assert counts["invalid_official_rating"] == 1
    assert counts["invalid_finish_position"] == 1
    assert counts["unrecognised_finish_code"] == 1
    assert counts["missing_finish_outcome"] == 1
    assert counts["race_groups"] == 5
    assert report["date_range"] == ["2026-11-20", "2026-11-20"]


def test_audit_rejects_missing_columns(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("date,horse\n2026-11-20,A\n", encoding="utf-8")
    try:
        audit_file(source)
    except ValueError as exc:
        assert "Missing required columns" in str(exc)
    else:
        raise AssertionError("Expected missing-column validation error")
