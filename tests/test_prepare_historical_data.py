import csv

from src.prepare_historical_data import finish_outcome, prepare_file


def test_finish_outcomes_keep_starting_prices_out_of_win_labels():
    assert finish_outcome({"finish_position": "1", "source_finish_code": "", "source_sp": "5/1"}) == ("known", "1")
    assert finish_outcome({"finish_position": "3", "source_finish_code": "", "source_sp": "5/1"}) == ("known", "0")
    assert finish_outcome({"finish_position": "", "source_finish_code": "PU"}) == ("known", "0")
    assert finish_outcome({"finish_position": "", "source_finish_code": "NR"}) == ("excluded", "")
    assert finish_outcome({"finish_position": "", "source_finish_code": "WD"}) == ("excluded", "")
    assert finish_outcome({"finish_position": "", "source_finish_code": "VOID"}) == ("excluded", "")
    assert finish_outcome({"finish_position": "", "source_finish_code": "-"}) == ("missing", "")
    assert finish_outcome({"finish_position": "", "source_finish_code": "MYSTERY"}) == ("unknown", "")
    assert finish_outcome({"finish_position": "0", "source_finish_code": ""}) == ("invalid", "")


def test_prepare_splits_clean_candidates_and_quarantine(tmp_path):
    source = tmp_path / "staging.csv"
    fields = [
        "race_id", "date", "course", "country", "off_time", "horse",
        "finish_position", "result_status", "source_finish_code", "source_sp",
        "odds_decimal", "official_rating",
    ]
    rows = [
        ["R1", "2026-11-20", "Ascot", "GB", "13:00", "Winner", "1", "UNVERIFIED", "", "3/1", "", "100"],
        ["R1", "2026-11-20", "Ascot", "GB", "13:00", "Placed", "2", "UNVERIFIED", "", "4/1", "", ""],
        ["R1", "2026-11-20", "Ascot", "GB", "13:00", "Winner", "1", "UNVERIFIED", "", "3/1", "", "100"],
        ["R2", "2026-11-20", "Dundalk", "IRE", "14:00", "Pulled Up", "", "UNVERIFIED", "PU", "8/1", "", "70"],
        ["R3", "2026-11-20", "Ascot", "GB", "25:00", "Bad Time", "1", "UNVERIFIED", "", "2/1", "", "80"],
        ["R4", "2026-11-20", "Ascot", "GB", "15:00", "No Result", "", "UNVERIFIED", "-", "5/1", "", "80"],
        ["R5", "2026-11-20", "Ascot", "GB", "16:00", "Withdrawn", "", "UNVERIFIED", "NR", "", "", "80"],
    ]
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)

    prepared = tmp_path / "prepared.csv"
    quarantine = tmp_path / "quarantine.csv"
    counts = prepare_file(source, prepared, quarantine)

    with prepared.open(newline="", encoding="utf-8") as handle:
        good_rows = list(csv.DictReader(handle))
    with quarantine.open(newline="", encoding="utf-8") as handle:
        bad_rows = list(csv.DictReader(handle))

    assert counts["rows_seen"] == 7
    assert counts["research_only_rows"] == 3
    assert counts["quarantined_rows"] == 4
    assert [row["research_win_outcome"] for row in good_rows] == ["1", "0", "0"]
    assert good_rows[0]["source_sp"] == "3/1"
    assert good_rows[0]["odds_decimal"] == ""
    assert good_rows[0]["result_status"] == "UNVERIFIED"
    assert bad_rows[0]["preparation_reasons"] == "duplicate_runner_in_race"
    assert bad_rows[1]["preparation_reasons"] == "invalid_off_time"
    assert bad_rows[2]["preparation_reasons"] == "missing_finish_outcome"
    assert bad_rows[3]["preparation_reasons"] == "non_runner_or_void_result"
