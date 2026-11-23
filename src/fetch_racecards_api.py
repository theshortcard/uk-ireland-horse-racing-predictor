"""Fetch one free-tier UK/IRE racecard response as a raw local snapshot.

The free endpoint provides basic today/tomorrow racecards, not odds. This
utility deliberately does not map data into model inputs or calculate EV.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://api.theracingapi.com/v1/racecards/free"
USERNAME_ENV = "RACING_API_USERNAME"
PASSWORD_ENV = "RACING_API_PASSWORD"
MAX_RESPONSE_BYTES = 50 * 1024 * 1024


def fetch_snapshot(
    username: str,
    password: str,
    output_dir: str | Path,
    *,
    day: str = "today",
    timeout: int = 30,
) -> tuple[Path, Path]:
    """Fetch and save one raw response plus a credential-free metadata file."""
    if not username or not username.strip():
        raise ValueError("API username is empty.")
    if not password or not password.strip():
        raise ValueError("API password is empty.")
    if day not in {"today", "tomorrow"}:
        raise ValueError("day must be 'today' or 'tomorrow'.")

    token = base64.b64encode(f"{username.strip()}:{password.strip()}".encode("utf-8")).decode("ascii")
    query = urlencode([("day", day), ("region_codes", "gb"), ("region_codes", "ire"), ("limit", "500")])
    request = Request(
        f"{ENDPOINT}?{query}",
        headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        # Do not echo response bodies: providers can include account details in errors.
        raise RuntimeError(f"The Racing API request failed with HTTP {exc.code}. Check plan access and credentials.") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach The Racing API: {exc.reason}") from exc

    if status != 200:
        raise RuntimeError(f"The Racing API returned unexpected HTTP status {status}.")
    if len(body) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"API response exceeded the {MAX_RESPONSE_BYTES}-byte safety limit.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("API response was not valid JSON.") from exc
    if not isinstance(payload, (dict, list)):
        raise RuntimeError("API response must be a JSON object or array.")
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError("The Racing API returned an error payload.")

    retrieved_at = datetime.now(timezone.utc)
    stamp = retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"racecards_{day}_{stamp}.json"
    meta_path = directory / f"racecards_{day}_{stamp}.meta.json"
    digest = hashlib.sha256(body).hexdigest()
    raw_path.write_bytes(body)
    metadata = {
        "provider": "The Racing API",
        "endpoint": ENDPOINT,
        "day": day,
        "regions_requested": ["gb", "ire"],
        "retrieved_at": retrieved_at.isoformat(),
        "http_status": status,
        "sha256": digest,
        "response_bytes": len(body),
        "note": "Raw free-tier racecard snapshot only; no field mapping, result verification, odds, or EV calculation.",
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return raw_path, meta_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Save one free-tier UK/IRE racecard response as raw JSON.")
    parser.add_argument("--day", choices=("today", "tomorrow"), default="today")
    parser.add_argument("--output-dir", default="data/external/theracingapi")
    args = parser.parse_args()
    username = os.environ.get(USERNAME_ENV, "")
    password = os.environ.get(PASSWORD_ENV, "")
    if not username or not password:
        parser.error(f"Set {USERNAME_ENV} and {PASSWORD_ENV} as environment secrets; never put credentials in source code.")
    raw_path, meta_path = fetch_snapshot(username, password, args.output_dir, day=args.day)
    print(f"Saved raw racecard snapshot: {raw_path}")
    print(f"Saved credential-free metadata: {meta_path}")
    print("No model import, odds calculation, or EV calculation was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
