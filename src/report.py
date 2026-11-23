"""Human-readable daily prediction report."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from .model import predict_race


def _race_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    """Avoid combining separate races when a source reuses its race ID."""
    return tuple(
        (row.get(field) or "").strip().casefold()
        for field in ("date", "course", "off_time", "country", "race_id")
    )


def build_report(rows: list[dict[str, str]], issues: list[str]) -> str:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_race_key(row)].append(row)

    lines = [
        "# UK & Ireland Horse Racing — Daily Model Report",
        "",
        "> Experimental baseline only. Probabilities are not proven forecasts or betting advice.",
        "",
        f"Races processed: {len(groups)}",
        f"Runners processed: {len(rows)}",
        "",
        "## Data quality",
        "",
    ]
    if issues:
        lines.extend([f"- WARNING: {issue}" for issue in issues])
    else:
        lines.append("- No structural validation issues found.")
    lines.extend(["", "## Race predictions", ""])

    for race_key, runners in sorted(groups.items()):
        first = runners[0]
        race_id = first.get("race_id", "UNKNOWN")
        lines.append(f"### {race_id} — {first.get('course', 'Unknown course')} ({first.get('date', 'date unknown')} {first.get('off_time', '')})")
        lines.append("")
        lines.append("| Rank | Horse | Model win % | Market fair % | Edge (pp) | Model fair odds | Odds | Raw EV % |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")
        for rank, item in enumerate(predict_race(runners), start=1):
            odds = item.get("odds_decimal")
            ev = item.get("expected_value")
            market_probability = item.get("market_probability")
            edge = item.get("probability_edge")
            fair_odds = item.get("fair_odds")
            odds_text = f"{float(odds):.2f}" if odds not in (None, "") else "Not supplied"
            ev_text = f"{float(ev) * 100:.1f}%" if ev is not None else "Not available"
            market_text = f"{float(market_probability) * 100:.1f}%" if market_probability is not None else "Incomplete book"
            edge_text = f"{float(edge) * 100:+.1f}" if edge is not None else "N/A"
            fair_odds_text = f"{float(fair_odds):.2f}" if fair_odds is not None else "N/A"
            lines.append(f"| {rank} | {item.get('horse', '')} | {float(item['win_probability']) * 100:.1f}% | {market_text} | {edge_text} | {fair_odds_text} | {odds_text} | {ev_text} |")
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
        "- The model currently uses a simple rating-led heuristic with small age/recency adjustments.",
        "- Market fair probabilities are normalized across all runners only when every runner has a valid price; the edge is model probability minus normalized market probability (percentage points).",
        "- Model fair odds are the inverse of the model probability. Raw EV uses the supplied decimal price and does not remove bookmaker margin or account for price freshness.",
        "- Do not treat positive raw EV or a positive probability edge as a bet recommendation until the model is backtested and calibrated on suitable historical data.",
        "- Example rows are fictional and must never be mistaken for real race information.",
        "",
    ])
    return "\n".join(lines)


def write_report(content: str, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
