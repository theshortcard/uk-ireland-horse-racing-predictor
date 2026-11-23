"""Leakage-aware evaluation for historical racecard CSV files.

Pre-race fields are used for predictions. Result and runner status fields are
used only to determine which runners/races qualify and how bets settle.
"""
from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

from .io_utils import read_racecard, validate_racecard
from .model import predict_race


def _race_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    """Build a race identity that remains safe when source race IDs are reused."""
    return tuple(
        (row.get(field) or "").strip().casefold()
        for field in ("date", "course", "off_time", "country", "race_id")
    )


def _is_non_runner(row: dict[str, str]) -> bool:
    status = (row.get("runner_status") or "RUNNER").strip().upper().replace("-", "_").replace(" ", "_")
    return status in {"NR", "NON_RUNNER", "WITHDRAWN", "SCRATCHED"}


def chronological_split(
    rows: list[dict[str, str]], test_fraction: float = 0.2
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split by whole race dates, keeping the newest dates for holdout evaluation."""
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be greater than 0 and less than 1.")
    dates = sorted({(row.get("date") or "").strip() for row in rows if (row.get("date") or "").strip()})
    if len(dates) < 2:
        raise ValueError("A chronological holdout requires at least two distinct race dates.")
    split_at = max(1, min(len(dates) - 1, math.ceil(len(dates) * (1.0 - test_fraction))))
    training_dates = set(dates[:split_at])
    holdout_dates = set(dates[split_at:])
    training_rows = [row for row in rows if (row.get("date") or "").strip() in training_dates]
    holdout_rows = [row for row in rows if (row.get("date") or "").strip() in holdout_dates]
    return training_rows, holdout_rows


def evaluate(rows: list[dict[str, str]]) -> dict[str, float | int | None]:
    """Evaluate completed races, including dead-heat win settlement."""
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_race_key(row)].append(row)

    race_count = 0
    brier_total = 0.0
    logloss_total = 0.0
    top_hits = 0
    roi_profit = 0.0
    roi_bets = 0
    dead_heat_races = 0
    non_runners_excluded = 0
    void_races_skipped = 0
    incomplete_races_skipped = 0
    market_races = 0
    market_brier_total = 0.0
    market_logloss_total = 0.0
    market_top_hits = 0
    market_roi_profit = 0.0
    market_roi_bets = 0

    for race_rows in groups.values():
        result_statuses = {
            (row.get("result_status") or "COMPLETED").strip().upper()
            for row in race_rows
        }
        if result_statuses & {"VOID", "ABANDONED"}:
            void_races_skipped += 1
            continue
        if result_statuses - {"COMPLETED", "FINISHED", "OFFICIAL", ""}:
            incomplete_races_skipped += 1
            continue

        non_runners = [row for row in race_rows if _is_non_runner(row)]
        non_runners_excluded += len(non_runners)
        runners = [row for row in race_rows if not _is_non_runner(row)]
        if not runners or not any((row.get("finish_position") or "").strip() for row in runners):
            incomplete_races_skipped += 1
            continue

        winners = [
            row for row in runners
            if (row.get("finish_position") or "").strip() in {"1", "1.0"}
        ]
        if not winners:
            incomplete_races_skipped += 1
            continue
        dead_heat_places = len(winners)
        if dead_heat_places > 1:
            dead_heat_races += 1

        predictions = predict_race(runners)
        winner_keys = {str(row.get("horse", "")).casefold() for row in winners}
        target_by_horse = {
            str(item.get("horse", "")).casefold(): (
                1.0 / dead_heat_places
                if str(item.get("horse", "")).casefold() in winner_keys else 0.0
            )
            for item in predictions
        }

        race_count += 1
        for item in predictions:
            horse_key = str(item.get("horse", "")).casefold()
            probability = float(item["win_probability"])
            target = target_by_horse[horse_key]
            brier_total += (probability - target) ** 2
            if target:
                logloss_total += -target * math.log(max(probability, 1e-15))

        # Compare against a normalized implied-probability market baseline only
        # when every active runner has a valid decimal price.
        market_prices: list[tuple[dict[str, object], float]] = []
        for item in predictions:
            try:
                price = float(item.get("odds_decimal") or "")
            except (TypeError, ValueError):
                price = 0.0
            if not math.isfinite(price) or price <= 1.0:
                market_prices = []
                break
            market_prices.append((item, 1.0 / price))
        if len(market_prices) == len(predictions) and market_prices:
            market_total = sum(probability for _, probability in market_prices)
            market_probabilities = [
                (item, raw_probability / market_total)
                for item, raw_probability in market_prices
            ]
            market_races += 1
            for item, probability in market_probabilities:
                target = target_by_horse[str(item.get("horse", "")).casefold()]
                market_brier_total += (probability - target) ** 2
                if target:
                    market_logloss_total += -target * math.log(max(probability, 1e-15))
            market_pick, _ = max(market_probabilities, key=lambda pair: pair[1])
            market_pick_key = str(market_pick.get("horse", "")).casefold()
            market_pick_won = market_pick_key in winner_keys
            if market_pick_won:
                market_top_hits += 1
            market_odds = float(market_pick["odds_decimal"])
            market_roi_bets += 1
            market_roi_profit += (
                market_odds / dead_heat_places - 1.0 if market_pick_won else -1.0
            )

        top_pick = predictions[0]
        top_pick_key = str(top_pick.get("horse", "")).casefold()
        top_pick_won = top_pick_key in winner_keys
        if top_pick_won:
            top_hits += 1

        # Standard dead-heat settlement: winning stake is divided by tied places.
        try:
            odds = float(top_pick.get("odds_decimal") or "")
        except (TypeError, ValueError):
            odds = 0.0
        if math.isfinite(odds) and odds > 1.0:
            roi_bets += 1
            if top_pick_won:
                roi_profit += odds / dead_heat_places - 1.0
            else:
                roi_profit -= 1.0

    if not race_count:
        raise ValueError("No evaluable races: provide completed races with at least one classified winner.")
    return {
        "races_evaluated": race_count,
        "top_pick_wins": top_hits,
        "top_pick_win_rate": top_hits / race_count,
        "mean_multiclass_brier": brier_total / race_count,
        "mean_log_loss": logloss_total / race_count,
        "flat_stake_bets_with_odds": roi_bets,
        "flat_stake_profit_units": roi_profit if roi_bets else None,
        "flat_stake_roi": roi_profit / roi_bets if roi_bets else None,
        "dead_heat_races": dead_heat_races,
        "non_runners_excluded": non_runners_excluded,
        "void_races_skipped": void_races_skipped,
        "incomplete_races_skipped": incomplete_races_skipped,
        "market_benchmark_races": market_races,
        "market_mean_multiclass_brier": market_brier_total / market_races if market_races else None,
        "market_mean_log_loss": market_logloss_total / market_races if market_races else None,
        "market_top_pick_wins": market_top_hits if market_races else None,
        "market_top_pick_win_rate": market_top_hits / market_races if market_races else None,
        "market_flat_stake_roi": market_roi_profit / market_roi_bets if market_roi_bets else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the baseline on historical racecard data.")
    parser.add_argument("--input", required=True, help="Historical CSV with pre-race features and finish_position")
    parser.add_argument("--output", default="reports/backtest.md", help="Markdown report output")
    parser.add_argument("--test-fraction", type=float, default=0.2, help="Share of newest distinct race dates reserved for holdout (default: 0.2)")
    args = parser.parse_args()
    if not 0.0 < args.test_fraction < 1.0:
        parser.error("--test-fraction must be greater than 0 and less than 1")

    rows = read_racecard(args.input)
    issues = validate_racecard(rows)
    if issues:
        raise SystemExit("Input validation failed:\\n- " + "\\n- ".join(issues))
    metrics = evaluate(rows)
    temporal_metrics = None
    training_rows: list[dict[str, str]] = []
    holdout_rows: list[dict[str, str]] = []
    try:
        training_rows, holdout_rows = chronological_split(rows, args.test_fraction)
        temporal_metrics = evaluate(holdout_rows)
    except ValueError:
        # Small or incomplete datasets may not yet support a valid chronological holdout.
        temporal_metrics = None

    lines = [
        "# Historical Backtest",
        "",
        "> Experimental evaluation only. This is not evidence of future profitability.",
        "",
        f"- Races evaluated: {metrics['races_evaluated']}",
        f"- Model top-pick wins (including dead heats): {metrics['top_pick_wins']}",
        f"- Top-pick win rate: {float(metrics['top_pick_win_rate']) * 100:.1f}%",
        f"- Mean multiclass Brier score: {float(metrics['mean_multiclass_brier']):.5f} (lower is better)",
        f"- Mean log loss: {float(metrics['mean_log_loss']):.5f} (lower is better)",
        f"- Flat-stake bets with valid pre-race odds: {metrics['flat_stake_bets_with_odds']}",
        f"- Flat-stake profit (units): {metrics['flat_stake_profit_units'] if metrics['flat_stake_profit_units'] is not None else 'Not available'}",
        f"- Flat-stake ROI: {float(metrics['flat_stake_roi']) * 100:.1f}%" if metrics['flat_stake_roi'] is not None else "- Flat-stake ROI: Not available (no valid odds)",
        f"- Dead-heat races: {metrics['dead_heat_races']}",
        f"- Non-runners excluded: {metrics['non_runners_excluded']}",
        f"- Void/abandoned races skipped: {metrics['void_races_skipped']}",
        f"- Incomplete races skipped: {metrics['incomplete_races_skipped']}",
        f"- Races with complete valid odds for market benchmark: {metrics['market_benchmark_races']}",
        f"- Market benchmark Brier score: {float(metrics['market_mean_multiclass_brier']):.5f}" if metrics["market_mean_multiclass_brier"] is not None else "- Market benchmark Brier score: Not available",
        f"- Market benchmark log loss: {float(metrics['market_mean_log_loss']):.5f}" if metrics["market_mean_log_loss"] is not None else "- Market benchmark log loss: Not available",
        f"- Market favourite win rate: {float(metrics['market_top_pick_win_rate']) * 100:.1f}%" if metrics["market_top_pick_win_rate"] is not None else "- Market favourite win rate: Not available",
        f"- Market favourite flat-stake ROI: {float(metrics['market_flat_stake_roi']) * 100:.1f}%" if metrics["market_flat_stake_roi"] is not None else "- Market favourite flat-stake ROI: Not available",
        "",
        "## Data requirements",
        "",
        "- Every feature and price must have been recorded before the race started.",
        "- Results must be official; use result_status=VOID or ABANDONED for races with no settlement.",
        "- Use runner_status=NON_RUNNER for withdrawn runners and retain their rows for audit.",
        "- Multiple finish_position=1 rows are treated as a dead heat; winning returns are divided by the number of tied winners.",
        "- Race identity uses date, course, off time, country, and race ID so reused source IDs do not merge separate races.",
        "- Market benchmark uses normalized implied probabilities and is calculated only when every active runner has a valid decimal price.",
        "- Record price timestamps and confirm prices were captured before the off; the backtest cannot independently verify timestamps.",
        "- Do not use closing odds or post-race fields as model inputs.",
        "",
    ]
    if temporal_metrics is not None:
        holdout_dates = sorted({row.get("date", "") for row in holdout_rows})
        lines.extend([
            "## Chronological holdout (newest dates)",
            "",
            "> This evaluates the fixed baseline on later dates; it does not train or fit a model.",
            "",
            f"- Earlier-period rows: {len(training_rows)}",
            f"- Holdout rows: {len(holdout_rows)}",
            f"- Holdout date range: {holdout_dates[0]} to {holdout_dates[-1]}",
            f"- Holdout races evaluated: {temporal_metrics['races_evaluated']}",
            f"- Holdout top-pick win rate: {float(temporal_metrics['top_pick_win_rate']) * 100:.1f}%",
            f"- Holdout Brier score: {float(temporal_metrics['mean_multiclass_brier']):.5f}",
            f"- Holdout log loss: {float(temporal_metrics['mean_log_loss']):.5f}",
            "",
        ])
    else:
        lines.extend([
            "## Chronological holdout",
            "",
            "- Not available: at least two distinct race dates and evaluable later-period races are required.",
            "",
        ])
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\\n".join(lines), encoding="utf-8")
    print(f"Backtest report written to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
