from src.io_utils import validate_racecard
from src.model import predict_race

RUNNERS = [
    {"race_id": "A", "horse": "Top", "horse_age": "5", "official_rating": "110", "days_since_run": "20", "odds_decimal": "3.0", "country": "GB"},
    {"race_id": "A", "horse": "Other", "horse_age": "6", "official_rating": "90", "days_since_run": "30", "odds_decimal": "6.0", "country": "IRE"},
]


def test_probabilities_sum_to_one():
    result = predict_race(RUNNERS)
    assert abs(sum(row["win_probability"] for row in result) - 1.0) < 1e-9


def test_higher_rating_ranks_first():
    result = predict_race(RUNNERS)
    assert result[0]["horse"] == "Top"


def test_ev_requires_valid_odds():
    rows = [{"horse": "No price", "official_rating": "100", "odds_decimal": ""}]
    result = predict_race(rows)
    assert result[0]["expected_value"] is None


def test_duplicate_runner_is_flagged():
    rows = RUNNERS + [dict(RUNNERS[0])]
    issues = validate_racecard(rows)
    assert any("duplicate" in issue.lower() for issue in issues)


def test_country_validation():
    rows = [dict(RUNNERS[0], country="FR")]
    issues = validate_racecard(rows)
    assert any("country must be GB or IRE" in issue for issue in issues)
