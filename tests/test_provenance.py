from src.provenance import audit_provenance


BASE_ROW = {
    "race_id": "P1",
    "date": "2026-11-23",
    "course": "Ascot",
    "country": "GB",
    "off_time": "13:00",
    "horse": "Runner",
    "horse_age": "5",
    "official_rating": "100",
    "odds_decimal": "3.0",
    "odds_source": "Licensed feed",
    "odds_captured_at": "2026-11-23T12:30:00Z",
    "source_name": "Licensed feed",
    "retrieved_at": "2026-11-23T12:35:00Z",
    "finish_position": "",
    "result_source": "",
    "result_verified_at": "",
}


def test_valid_pre_off_provenance_passes():
    assert audit_provenance([dict(BASE_ROW)]) == []


def test_odds_captured_at_or_after_off_is_flagged():
    row = dict(BASE_ROW, odds_captured_at="2026-11-23T13:00:00Z", retrieved_at="2026-11-23T13:05:00Z")
    issues = audit_provenance([row])
    assert any("at or after the scheduled off time" in issue for issue in issues)


def test_naive_timestamp_is_rejected():
    row = dict(BASE_ROW, retrieved_at="2026-11-23T12:35:00")
    issues = audit_provenance([row])
    assert any("must include a timezone offset" in issue for issue in issues)


def test_historical_result_requires_source_and_verification_time():
    row = dict(BASE_ROW, finish_position="1")
    issues = audit_provenance([row])
    assert any("result_source is missing" in issue for issue in issues)
    assert any("result_verified_at is missing" in issue for issue in issues)


def test_price_capture_cannot_follow_retrieval_time():
    row = dict(BASE_ROW, odds_captured_at="2026-11-23T12:40:00Z")
    issues = audit_provenance([row])
    assert any("later than retrieved_at" in issue for issue in issues)
