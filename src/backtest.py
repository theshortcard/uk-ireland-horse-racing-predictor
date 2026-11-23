"""Leakage-aware evaluation for historical racecard CSV files.

The input must contain pre-race features captured before the off and a
post-race finish_position column. The model never reads finish_position.
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


def evaluate(rows: list[dict[str, str]]) -> dict[str, float | int | None]:
    """Evaluate one-winner-per-race records using pre-race fields only."""
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if (row.get("finish_position") or "").strip():
            groups[_race_key(row)].append(row)

    race_count = 0
    brier_total = 0.0
    logloss_total = 0.0
    top_hits = 0
    roi_profit = 0.0
    roi_bets = 0

    for runners in groups.values():
        winners = [
            row for row in runners
            if (row.get("finish_position") or "").strip() in {"1", "1.0"}
        ]
        if len(winners) != 1:
            continue

        # finish_position is carried through but is never used as a model input.
        predictions = predict_race(runners)
        probability_by_horse = {
            str(item.get("horse", "")).casefold(): float(item["win_probability"])
            for item in predictions
        }
        winner_key = winners[0].get("horse", "").casefold()
        winner_probability = probability_by_horse.get(winner_key)
        if winner_probability is None:
            continue

        race_count += 1
        brier_total += sum(
            (float(item["win_probability"]) - (1.0 if str(item.get("horse", "")).casefold() == winner_key else 0.0)) ** 2
            for item in predictions
        )
        logloss_total += -math.log(max(winner_probability, 1e-15))
        top_pick = predictions[0]
        top_pick_won = str(top_pick.get("horse", "")).casefold() == winner_key
        if top_pick_won:
            top_hits += 1

        # Flat 1-unit bet on model top pick, only with valid decimal odds.
        try:
            odds = float(top_pick.get("odds_decimal") or "")
        except (TypeError, ValueError):
            odds = 0.0
        if math.isfinite(odds) and odds > 1.0:
            roi_bets += 1
            roi_profit += odds - 1.0 if top_pick_won else -1.0

    if not race_count:
        raise ValueError("No evaluable races: each race must have exactly one runner with finish_position=1.")
    return {
        "races_evaluated": race_count,
        "top_pick_wins": top_hits,
        "top_pick_win_rate": top_hits / race_count,
        "mean_multiclass_brier": brier_total / race_count,
        "mean_log_loss": logloss_total / race_count,
        "flat_stake_bets_with_odds": roi_bets,
        "flat_stake_profit_units": roi_profit if roi_bets else None,
        "flat_stake_roi": roi_profit / roi_bets if roi_bets else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the baseline on historical racecard data.")
    parser.add_argument("--input", required=True, help="Historical CSV with pre-race features and finish_position")
    parser.add_argument("--output", default="reports/backtest.md", help="Markdown report output")
    args = parser.parse_args()

    rows = read_racecard(args.input)
    issues = validate_racecard(rows)
    if issues:
        raise SystemExit("Input validation failed:\n- " + "\n- ".join(issues))
    metrics = evaluate(rows)

    lines = [
        "# Historical Backtest",
        "",
        "> Experimental evaluation only. This is not evidence of future profitability.",
        "",
        f"- Races evaluated: {metrics['races_evaluated']}",
        f"- Model top-pick wins: {metrics['top_pick_wins']}",
        f"- Top-pick win rate: {float(metrics['top_pick_win_rate']) * 100:.1f}%",
        f"- Mean multiclass Brier score: {float(metrics['mean_multiclass_brier']):.5f} (lower is better)",
        f"- Mean log loss: {float(metrics['mean_log_loss']):.5f} (lower is better)",
        f"- Flat-stake bets with valid pre-race odds: {metrics['flat_stake_bets_with_odds']}",
        f"- Flat-stake profit (units): {metrics['flat_stake_profit_units'] if metrics['flat_stake_profit_units'] is not None else 'Not available'}",
        f"- Flat-stake ROI: {float(metrics['flat_stake_roi']) * 100:.1f}%" if metrics['flat_stake_roi'] is not None else "- Flat-stake ROI: Not available (no valid odds)",
        "",
        "## Data requirements",
        "",
        "- Every feature and price must have been recorded before the race started.",
        "- Results must be official and each evaluated race must have exactly one winner row.",
        "- Exclude void races, dead heats, abandoned races, and incomplete result records until explicit settlement handling is implemented.",
        "- Race identity uses date, course, off time, country, and race ID so reused source IDs do not merge separate races.",
        "- Do not use closing odds or post-race fields as model inputs.",
        "",
    ]
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Backtest report written to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
