import pytest

from src.backtest import chronological_split, evaluate, expected_calibration_error


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


def test_reused_source_race_id_does_not_merge_different_dates():
    rows = [
        {"race_id": "123", "date": "2026-01-01", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Winner A", "horse_age": "5", "official_rating": "100", "odds_decimal": "2.0", "finish_position": "1"},
        {"race_id": "123", "date": "2026-01-02", "course": "Ascot", "off_time": "13:00", "country": "GB",
         "horse": "Winner B", "horse_age": "5", "official_rating": "100", "odds_decimal": "2.0", "finish_position": "1"},
    ]
    result = evaluate(rows)
    assert result["races_evaluated"] == 2
    assert result["top_pick_wins"] == 2


def test_dead_heat_uses_fractional_probability_targets_and_split_returns():
    rows = [
        {"race_id": "DH1", "horse": "Tied A", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "4.0", "finish_position": "1"},
        {"race_id": "DH1", "horse": "Tied B", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "4.0", "finish_position": "1"},
        {"race_id": "DH1", "horse": "Third", "horse_age": "5", "official_rating": "80",
         "odds_decimal": "8.0", "finish_position": "3"},
    ]
    result = evaluate(rows)
    assert result["races_evaluated"] == 1
    assert result["dead_heat_races"] == 1
    assert result["top_pick_wins"] == 1
    assert result["flat_stake_profit_units"] == pytest.approx(1.0)
    assert result["flat_stake_roi"] == pytest.approx(1.0)


def test_non_runner_is_excluded_from_predictions_and_roi():
    rows = [
        {"race_id": "NR1", "horse": "Withdrawn Favourite", "horse_age": "5", "official_rating": "130",
         "odds_decimal": "1.5", "finish_position": "", "runner_status": "NON_RUNNER"},
        {"race_id": "NR1", "horse": "Actual Winner", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "3.0", "finish_position": "1"},
        {"race_id": "NR1", "horse": "Second", "horse_age": "5", "official_rating": "90",
         "odds_decimal": "5.0", "finish_position": "2"},
    ]
    result = evaluate(rows)
    assert result["non_runners_excluded"] == 1
    assert result["top_pick_wins"] == 1
    assert result["flat_stake_profit_units"] == pytest.approx(2.0)


def test_void_and_incomplete_races_are_skipped():
    rows = [
        {"race_id": "OK", "horse": "Winner", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "1"},
        {"race_id": "VOID", "horse": "Runner", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "", "result_status": "VOID"},
        {"race_id": "INC", "horse": "Runner", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "", "result_status": "INCOMPLETE"},
    ]
    result = evaluate(rows)
    assert result["races_evaluated"] == 1
    assert result["void_races_skipped"] == 1
    assert result["incomplete_races_skipped"] == 1


def test_market_benchmark_is_reported_when_all_runner_prices_exist():
    rows = [
        {"race_id": "M1", "horse": "Favourite", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "1"},
        {"race_id": "M1", "horse": "Outsider", "horse_age": "5", "official_rating": "90",
         "odds_decimal": "4.0", "finish_position": "2"},
    ]
    result = evaluate(rows)
    assert result["market_benchmark_races"] == 1
    assert result["market_top_pick_wins"] == 1
    assert result["market_mean_multiclass_brier"] is not None
    assert result["market_mean_log_loss"] is not None
    assert result["market_flat_stake_roi"] == pytest.approx(1.0)


def test_market_benchmark_skips_races_with_missing_runner_prices():
    rows = [
        {"race_id": "M2", "horse": "Favourite", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "1"},
        {"race_id": "M2", "horse": "No Price", "horse_age": "5", "official_rating": "90",
         "odds_decimal": "", "finish_position": "2"},
    ]
    result = evaluate(rows)
    assert result["races_evaluated"] == 1
    assert result["market_benchmark_races"] == 0
    assert result["market_mean_multiclass_brier"] is None
    assert result["market_flat_stake_roi"] is None


def test_chronological_split_keeps_whole_dates_in_holdout():
    rows = [
        {"date": "2026-01-01", "race_id": "A", "horse": "A1"},
        {"date": "2026-01-01", "race_id": "A", "horse": "A2"},
        {"date": "2026-01-02", "race_id": "B", "horse": "B1"},
        {"date": "2026-01-03", "race_id": "C", "horse": "C1"},
    ]
    training, holdout = chronological_split(rows, test_fraction=0.34)
    assert {row["date"] for row in training} == {"2026-01-01", "2026-01-02"}
    assert {row["date"] for row in holdout} == {"2026-01-03"}
    assert len(training) + len(holdout) == len(rows)


def test_chronological_split_rejects_single_date():
    with pytest.raises(ValueError, match="at least two distinct race dates"):
        chronological_split([{"date": "2026-01-01"}])


def test_chronological_split_rejects_invalid_fraction():
    with pytest.raises(ValueError, match="test_fraction"):
        chronological_split([{"date": "2026-01-01"}, {"date": "2026-01-02"}], 1.0)


def test_expected_calibration_error_is_zero_for_perfect_predictions():
    assert expected_calibration_error([0.05, 0.95], [0.0, 1.0]) == pytest.approx(0.05)


def test_expected_calibration_error_handles_probability_one():
    assert expected_calibration_error([1.0], [1.0]) == pytest.approx(0.0)


def test_expected_calibration_error_rejects_invalid_probabilities():
    with pytest.raises(ValueError, match="between 0 and 1"):
        expected_calibration_error([1.1], [1.0])


def test_backtest_returns_model_and_market_calibration_metrics():
    rows = [
        {"race_id": "CAL1", "horse": "Favourite", "horse_age": "5", "official_rating": "100",
         "odds_decimal": "2.0", "finish_position": "1"},
        {"race_id": "CAL1", "horse": "Outsider", "horse_age": "5", "official_rating": "90",
         "odds_decimal": "4.0", "finish_position": "2"},
    ]
    result = evaluate(rows)
    assert result["model_calibration_ece"] is not None
    assert result["market_calibration_ece"] is not None
