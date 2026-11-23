from __future__ import annotations

import pytest

from src.inspect_dataset import inspect_csv, render_markdown


def test_inspects_columns_completeness_and_likely_fields(tmp_path):
    source = tmp_path / "races.csv"
    source.write_text(
        "race_date,country,course,horse,sp,pos,extra\n"
        "2025-01-01,GB,Ascot,Runner A,3/1,1,x\n"
        "2025-01-02,IRE,Curragh,Runner B,,2,\n",
        encoding="utf-8",
    )

    summary = inspect_csv(source)
    assert summary["rows"] == 2
    assert summary["roles"]["date"] == "race_date"
    assert summary["roles"]["horse"] == "horse"
    assert summary["roles"]["odds"] == "sp"
    assert summary["country_counts"] == {"GB": 1, "IRE": 1}
    assert summary["date_min"] == "2025-01-01"
    extra = next(column for column in summary["columns"] if column["name"] == "extra")
    assert extra["missing"] == 1
    report = render_markdown(summary)
    assert "does not verify provenance" in report
    assert "Do not use post-race fields" in report


def test_rejects_duplicate_headers(tmp_path):
    source = tmp_path / "duplicate.csv"
    source.write_text("horse,horse\nA,B\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        inspect_csv(source)


def test_rejects_extra_values_in_row(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("horse,course\nA,Ascot,unexpected\n", encoding="utf-8")
    with pytest.raises(ValueError, match="more values"):
        inspect_csv(source)


def test_rejects_header_only_file(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("horse,course\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no data rows"):
        inspect_csv(source)
