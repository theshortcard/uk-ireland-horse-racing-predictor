import pytest

from src.backtest import evaluate


def test_backtest_metrics_and_flat_stake_roi():
    rows = [
        {"race_id": "R1", "horse": "Winner", "horse_age": "5", "official_rating": "110", "days_since_run": "20", "odds_decimal": "3.0", "finish_position": "1"},
        {"race_id": "R1", "horse": "Second", "horse_age": "6", "official_rating": "90", "days_since_run": "30", "odds_decimal": "6.0", "finish_position": "2"},
        {"race_id": "R2", "horse": "Loser", "horse_age": "5", "official_rating": "110", "days_since_run": "20", "odds_decimal": "3.0", "finish_position": "2"},
        {"race_id": "R2", "horse": "Winner 2", "horse_age": "6", "official_rating": "90", "days_since_run": "30", "odds_decimal": "6.0", "finish_position": "1"},
    ]
    result = evaluate(rows)
    assert result["races_evaluated"] == 2
    assert result["top_pick_wins"] == 1
    assert result["flat_stake_bets_with_odds"] == 2
    assert result["flat_stake_profit_units"] == pytest.approx(1.0)
    assert result["flat_stake_roi"] == pytest.approx(0.5)


def test_backtest_rejects_races_without_exactly_one_winner():
    with pytest.raises(ValueError, match="No evaluable races"):
        evaluate([{"race_id": "R1", "horse": "No result", "finish_position": "2"}])
