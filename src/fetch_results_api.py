"""Fetch yesterday's settled results as an untouched JSON snapshot.

This captures raw provider output only. It does not map runners into the
historical training schema or establish that a price was available pre-race.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINT = "https://api.apihorseracing.com/v1/results/yesterday"
KEY_ENV = "AHR_API_KEY"
MAX_RESPONSE_BYTES = 50 * 1024 * 1024


def fetch_snapshot(api_key: str, output_dir: str | Path, *, timeout: int = 30) -> tuple[Path, Path]:
    """Fetch and save one raw response plus a key-free provenance sidecar."""
    if not api_key or not api_key.strip():
        raise ValueError("API key is empty.")
    request = Request(
        ENDPOINT,
        headers={"X-API-Key": api_key.strip(), "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach the racing results API: {exc.reason}") from exc

    if status != 200:
        raise RuntimeError(f"API request returned unexpected HTTP status {status}.")
    if len(body) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"API response exceeded the {MAX_RESPONSE_BYTES}-byte safety limit.")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("API response was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("API response was not a JSON object.")
    if payload.get("error"):
        raise RuntimeError(f"API returned an error: {payload['error']}")
    if "data" not in payload:
        raise RuntimeError("API response did not contain the documented 'data' field.")

    retrieved_at = datetime.now(timezone.utc)
    stamp = retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"results_yesterday_{stamp}.json"
    meta_path = directory / f"results_yesterday_{stamp}.meta.json"
    digest = hashlib.sha256(body).hexdigest()

    # Preserve the provider response byte-for-byte; keep collection metadata separately.
    raw_path.write_bytes(body)
    metadata = {
        "provider": "APIHorseRacing.com",
        "endpoint": ENDPOINT,
        "retrieved_at": retrieved_at.isoformat(),
        "http_status": status,
        "sha256": digest,
        "response_bytes": len(body),
        "note": "Raw response only; field mapping, provenance review and result verification remain required.",
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return raw_path, meta_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Save yesterday's settled racing results as a raw JSON snapshot.")
    parser.add_argument("--output-dir", default="data/external/apihorseracing")
    args = parser.parse_args()
    api_key = os.environ.get(KEY_ENV, "")
    if not api_key:
        parser.error(f"Set {KEY_ENV} in your environment; never put the key in a command or source file.")
    raw_path, meta_path = fetch_snapshot(api_key, args.output_dir)
    print(f"Saved raw results: {raw_path}")
    print(f"Saved provenance: {meta_path}")
    print("No runner mapping or model import was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
