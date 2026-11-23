"""A deliberately simple, explainable baseline win-probability model."""
from __future__ import annotations

import math


def _number(value: str | float | int | None, default: float = 0.0) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def score_runner(row: dict[str, str]) -> float:
    """Create a positive relative score from public racecard-style fields.

    This is a ranking baseline, not a trained or proven betting model.
    Official rating is the main signal; missing ratings receive a neutral
    fallback. Recent-run recency is only a small heuristic adjustment.
    """
    rating = _number(row.get("official_rating"), 80.0)
    days = _number(row.get("days_since_run"), 30.0)
    age = _number(row.get("horse_age"), 5.0)

    score = math.exp(max(-20.0, min(20.0, (rating - 80.0) / 35.0)))
    if days > 120:
        score *= 0.90
    elif 7 <= days <= 45:
        score *= 1.03
    if age < 3 or age > 12:
        score *= 0.97
    return max(score, 1e-9)


def predict_race(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Return runners with normalized win probabilities and optional EV."""
    if not rows:
        return []
    scores = [score_runner(row) for row in rows]
    total = sum(scores)
    output: list[dict[str, object]] = []
    for row, score in zip(rows, scores):
        probability = score / total
        odds = _number(row.get("odds_decimal"), 0.0)
        implied = 1.0 / odds if odds > 1.0 else None
        ev = probability * odds - 1.0 if odds > 1.0 else None
        output.append({
            **row,
            "model_score": round(score, 6),
            "win_probability": round(probability, 6),
            "implied_probability": round(implied, 6) if implied is not None else None,
            "expected_value": round(ev, 6) if ev is not None else None,
        })
    return sorted(output, key=lambda item: float(item["win_probability"]), reverse=True)
