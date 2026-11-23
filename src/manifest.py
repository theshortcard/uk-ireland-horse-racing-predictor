"""Validate dataset manifests before external racing data is imported."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

REQUIRED_TEXT = (
    "dataset_name", "provider", "source_url", "license_name", "license_url",
    "file_path", "sha256", "notes",
)
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_manifest(data: dict[str, Any], base_dir: str | Path = ".") -> list[str]:
    """Return manifest issues; optionally verify the referenced file's SHA-256."""
    issues: list[str] = []
    for field in REQUIRED_TEXT:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"{field} must be a non-empty string.")

    downloaded_at = data.get("downloaded_at")
    if not isinstance(downloaded_at, str) or not downloaded_at.strip():
        issues.append("downloaded_at must be a timezone-aware ISO-8601 timestamp.")
    else:
        try:
            parsed = datetime.fromisoformat(downloaded_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                issues.append("downloaded_at must include a timezone offset.")
        except ValueError:
            issues.append("downloaded_at must be a valid ISO-8601 timestamp.")

    for field in ("coverage_start", "coverage_end"):
        value = data.get(field)
        try:
            date.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(f"{field} must use YYYY-MM-DD.")

    try:
        start = date.fromisoformat(data.get("coverage_start", ""))
        end = date.fromisoformat(data.get("coverage_end", ""))
        if start > end:
            issues.append("coverage_start must not be later than coverage_end.")
    except (TypeError, ValueError):
        pass

    countries = data.get("countries")
    if not isinstance(countries, list) or not countries:
        issues.append("countries must be a non-empty list containing GB and/or IRE.")
    elif any(country not in {"GB", "IRE"} for country in countries):
        issues.append("countries may contain only GB and/or IRE.")
    elif len(countries) != len(set(countries)):
        issues.append("countries must not contain duplicates.")

    digest = data.get("sha256")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        issues.append("sha256 must contain exactly 64 hexadecimal characters.")

    file_path = data.get("file_path")
    resolved_file: Path | None = None
    if isinstance(file_path, str) and file_path.strip():
        relative = Path(file_path)
        if relative.is_absolute() or ".." in relative.parts:
            issues.append("file_path must be a safe relative path without '..'.")
        else:
            resolved_file = Path(base_dir) / relative

    if resolved_file and isinstance(digest, str) and SHA256_PATTERN.fullmatch(digest):
        if resolved_file.is_file():
            actual = hashlib.sha256(resolved_file.read_bytes()).hexdigest()
            if actual.casefold() != digest.casefold():
                issues.append("sha256 does not match the referenced file.")
        else:
            issues.append(f"Referenced dataset file does not exist: {file_path}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a racing dataset provenance manifest.")
    parser.add_argument("--input", required=True, help="Path to manifest JSON")
    args = parser.parse_args()
    manifest_path = Path(args.input)
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read manifest: {exc}")
        return 2
    if not isinstance(data, dict):
        print("Manifest root must be a JSON object.")
        return 2
    issues = validate_manifest(data, manifest_path.parent)
    if issues:
        print("Manifest validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Manifest valid; referenced file SHA-256 verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
