"""Human-readable daily prediction report."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from .model import predict_race
from .provenance import audit_provenance


def _race_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    """Avoid combining separate races when a source reuses its race ID."""
    return tuple(
        (row.get(field) or "").strip().casefold()
        for field in ("date", "course", "off_time", "country", "race_id")
    )


def build_report(rows: list[dict[str, str]], issues: list[str]) -> str:
    """Build a report; suppress market edges and EV unless provenance is clean."""
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_race_key(row)].append(row)

    provenance_issues = audit_provenance(rows)
    provenance_ok = not provenance_issues
    all_issues = list(issues) + provenance_issues

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
    if all_issues:
        lines.extend([f"- WARNING: {issue}" for issue in all_issues])
    else:
        lines.append("- Structural validation and supplied provenance checks passed.")
    if provenance_ok:
        lines.append("- Price provenance gate: PASSED. Market comparisons are shown only where the entire field has valid prices.")
    else:
        lines.append("- PRICE PROVENANCE GATE: BLOCKED. Market fair probabilities, probability edges and raw EV are suppressed.")
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
            market_probability = item.get("market_probability") if provenance_ok else None
            edge = item.get("probability_edge") if provenance_ok else None
            # EV is meaningful for this report only with a complete, provenance-checked field.
            ev = item.get("expected_value") if provenance_ok and market_probability is not None else None
            fair_odds = item.get("fair_odds")
            odds_text = f"{float(odds):.2f}" if odds not in (None, "") else "Not supplied"
            if odds not in (None, "") and not provenance_ok:
                odds_text += " (unverified)"
            ev_text = f"{float(ev) * 100:.1f}%" if ev is not None else "Suppressed"
            market_text = f"{float(market_probability) * 100:.1f}%" if market_probability is not None else ("Not verified" if not provenance_ok else "Incomplete book")
            edge_text = f"{float(edge) * 100:+.1f}" if edge is not None else "N/A"
            fair_odds_text = f"{float(fair_odds):.2f}" if fair_odds is not None else "N/A"
            lines.append(f"| {rank} | {item.get('horse', '')} | {float(item['win_probability']) * 100:.1f}% | {market_text} | {edge_text} | {fair_odds_text} | {odds_text} | {ev_text} |")
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
        "- The model currently uses a simple rating-led heuristic with small age/recency adjustments; it is not trained or calibrated.",
        "- Market fair probabilities and model-versus-market edges require a complete field of valid decimal prices and a clean provenance audit for source name, retrieval timestamp, odds source, timezone-aware capture timestamp and pre-off timing.",
        "- Raw EV is suppressed unless the complete field has valid prices and the provenance gate passes. A passing timestamp audit does not independently prove that a provider's licence permits this use.",
        "- Model fair odds are the inverse of the experimental model probability; they are not evidence of an advantage.",
        "- Do not treat any output as a bet recommendation until suitable data rights, historical validation and out-of-sample calibration are established.",
        "- Example rows are fictional and must never be mistaken for real race information.",
        "",
    ])
    return "\n".join(lines)


def write_report(content: str, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
