from src.report import build_report


def test_report_does_not_merge_reused_race_ids():
    rows = [
        {"race_id": "123", "date": "2026-01-01", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Runner A", "horse_age": "5", "official_rating": "100", "odds_decimal": "2.0"},
        {"race_id": "123", "date": "2026-01-02", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Runner B", "horse_age": "5", "official_rating": "100", "odds_decimal": "2.0"},
    ]
    report = build_report(rows, [])
    assert "Races processed: 2" in report
    assert report.count("### 123 — Ascot") == 2
