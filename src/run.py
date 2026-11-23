"""Command-line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from .io_utils import read_racecard, validate_racecard
from .provenance import audit_provenance
from .report import build_report, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a UK/Irish horse racing baseline report.")
    parser.add_argument("--input", default="data/sample_racecard.csv", help="Path to racecard CSV")
    parser.add_argument("--output", default="reports/daily_report.md", help="Path for Markdown report")
    parser.add_argument("--allow-blocked-provenance", action="store_true", help="Allow report generation to finish when provenance is blocked; market edge and EV remain suppressed")
    args = parser.parse_args()

    rows = read_racecard(args.input)
    validation_issues = validate_racecard(rows)
    provenance_issues = audit_provenance(rows)
    report = build_report(rows, validation_issues)
    write_report(report, args.output)
    print(f"Report written to {Path(args.output)}")

    if validation_issues:
        print(f"Completed with {len(validation_issues)} structural validation warning(s).")
    else:
        print("Structural validation passed.")

    if provenance_issues:
        print(f"PRICE PROVENANCE GATE BLOCKED: {len(provenance_issues)} issue(s). Market edge and EV are suppressed.")
        if not args.allow_blocked_provenance:
            return 1
        print("Continuing because --allow-blocked-provenance was explicitly supplied; no market edge or EV is published.")
    else:
        print("Price provenance checks passed. Market comparisons may be shown only for complete priced fields.")

    if validation_issues:
        return 1
    if provenance_issues:
        print("Demo report generated; provenance remains blocked and market edge/EV remain suppressed.")
        return 0
    print("Completed with no structural or provenance issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
