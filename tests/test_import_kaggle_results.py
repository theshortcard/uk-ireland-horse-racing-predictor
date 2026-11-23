from src.import_kaggle_results import classify_course, convert_row, normalise_course, stage_files


def test_course_classification_is_conservative():
    assert classify_course("Dundalk (AW) (IRE)") == "IRE"
    assert classify_course("Dundalk (AW)") == "IRE"
    assert classify_course("Fairyhouse (IRE)") == "IRE"
    assert classify_course("Curragh (IRE)") == "IRE"
    assert classify_course("Wolverhampton (AW)") == "GB"
    assert classify_course("Carlisle") == "GB"
    assert classify_course("Yarmouth") == "GB"
    assert classify_course("Ffos Las") == "GB"
    assert classify_course("Aintree") == "GB"
    assert classify_course("Down Royal") == "IRE"
    assert classify_course("Down Royal (IRE)") == "IRE"
    assert classify_course("Ballinrobe") == "IRE"
    assert classify_course("Tralee") == "IRE"
    assert classify_course("Deauville (FR)") is None
    assert classify_course("Unknown Park") is None


def test_course_normalisation_removes_parenthetical_notes():
    assert normalise_course("Dundalk (AW) (IRE)") == "dundalk"
    assert normalise_course("Carlisle\u00a0") == "carlisle"
    assert normalise_course("Carlisle\u200b") == "carlisle"


def test_archive_starting_price_never_becomes_decimal_odds():
    row = {
        "date": "2026-11-20", "course": "Ascot", "race_id": "R1",
        "off": "1:05", "horse": "Example Runner", "age": "5",
        "or": "110", "pos": "1", "sp": "5/1",
    }
    converted = convert_row(row, "raceform.csv")
    assert converted is not None
    assert converted["odds_decimal"] == ""
    assert converted["source_sp"] == "5/1"
    assert converted["result_status"] == "UNVERIFIED"
    assert converted["result_source"] == ""
    assert converted["result_verified_at"] == ""
    assert converted["source_archive_file"] == "raceform.csv"


def test_non_numeric_finish_code_is_preserved_without_fake_position():
    row = {
        "date": "2026-11-20", "course": "Leopardstown (IRE)", "race_id": "R2",
        "off": "14:00", "horse": "Runner Two", "age": "6",
        "or": "–", "pos": "PU", "sp": "12/1",
    }
    converted = convert_row(row, "raceform.csv")
    assert converted is not None
    assert converted["finish_position"] == ""
    assert converted["source_finish_code"] == "PU"
    assert converted["official_rating"] == ""


def test_stage_files_excludes_unknown_courses_and_keeps_only_known_venues(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        """date,course,race_id,off,horse,age,or,pos,sp
2026-11-20,Ascot,R1,13:00,Runner A,5,100,1,2/1
2026-11-20,Deauville (FR),R2,13:30,Runner B,4,90,2,3/1
2026-11-20,Dundalk (AW) (IRE),R3,14:00,Runner C,6,80,PU,5/1
""",
        encoding="utf-8",
    )
    output = tmp_path / "staging.csv"
    counts = stage_files([source], output)
    assert counts["staged_rows"] == 2
    assert counts["included_GB_rows"] == 1
    assert counts["included_IRE_rows"] == 1
    assert counts["excluded_unknown_or_overseas_course"] == 1
    assert counts["included_course|GB|Ascot"] == 1
    assert counts["included_course|IRE|Dundalk (AW) (IRE)"] == 1
    assert counts["excluded_course|Deauville (FR)"] == 1
    content = output.read_text(encoding="utf-8")
    assert ",UNVERIFIED," in content
    assert "5/1" in content



def test_non_runner_code_is_not_marked_as_a_runner():
    row = {
        "date": "2026-11-20", "course": "Ascot", "race_id": "R3",
        "off": "15:00", "horse": "Non Runner", "age": "5",
        "or": "90", "pos": "NR", "sp": "",
    }
    converted = convert_row(row, "raceform.csv")
    assert converted is not None
    assert converted["runner_status"] == "NON_RUNNER"
    assert converted["source_finish_code"] == "NR"
    assert converted["finish_position"] == ""
