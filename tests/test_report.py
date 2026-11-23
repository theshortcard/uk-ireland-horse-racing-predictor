from src.report import build_report


def _verified_row(horse, rating):
    return {
        "race_id": "EDGE1", "date": "2026-11-20", "course": "Ascot",
        "off_time": "13:00", "country": "GB", "horse": horse,
        "horse_age": "5", "official_rating": str(rating), "odds_decimal": "2.0",
        "source_name": "Permitted test feed", "retrieved_at": "2026-11-20T12:35:00Z",
        "odds_source": "Permitted test feed", "odds_captured_at": "2026-11-20T12:30:00Z",
    }


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


def test_unverified_prices_suppress_market_edge_and_ev():
    rows = [
        {"race_id": "EDGE1", "date": "2026-11-20", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Runner A", "horse_age": "5", "official_rating": "110", "odds_decimal": "2.0"},
        {"race_id": "EDGE1", "date": "2026-11-20", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Runner B", "horse_age": "5", "official_rating": "90", "odds_decimal": "4.0"},
    ]
    report = build_report(rows, [])
    assert "PRICE PROVENANCE GATE: BLOCKED" in report
    assert "Not verified" in report
    assert "Suppressed" in report
    assert "| + " not in report


def test_verified_complete_market_can_show_edge_and_ev():
    report = build_report([_verified_row("Runner A", 110), _verified_row("Runner B", 90)], [])
    assert "Price provenance gate: PASSED" in report
    assert "Market fair %" in report
    assert "Edge (pp)" in report
    assert "Model fair odds" in report
    assert "Incomplete book" not in report
    assert "Suppressed" not in report
