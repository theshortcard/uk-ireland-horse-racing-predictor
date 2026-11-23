from __future__ import annotations

import base64
import hashlib
import json
from urllib.parse import parse_qs, urlparse

import pytest

import src.fetch_racecards_api as fetcher


class FakeResponse:
    status = 200

    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return self.body[:limit]


def test_saves_raw_response_and_uses_basic_auth_and_free_regions(tmp_path, monkeypatch):
    body = b'{"races":[{"race_id":"abc","runners":[{"horse":"Example"}]}]}'
    seen = {}

    def fake_urlopen(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        return FakeResponse(body)

    monkeypatch.setattr(fetcher, "urlopen", fake_urlopen)
    raw_path, meta_path = fetcher.fetch_snapshot("demo-user", "demo-pass", tmp_path, day="tomorrow")

    assert raw_path.read_bytes() == body
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["sha256"] == hashlib.sha256(body).hexdigest()
    assert metadata["regions_requested"] == ["gb", "ire"]
    assert "demo-user" not in meta_path.read_text(encoding="utf-8")
    assert "demo-pass" not in meta_path.read_text(encoding="utf-8")
    assert seen["auth"] == "Basic " + base64.b64encode(b"demo-user:demo-pass").decode("ascii")
    query = parse_qs(urlparse(seen["url"]).query)
    assert query["day"] == ["tomorrow"]
    assert query["region_codes"] == ["gb", "ire"]
    assert seen["timeout"] == 30


@pytest.mark.parametrize("username,password", [("", "pass"), ("user", ""), (" ", "pass")])
def test_rejects_missing_credentials(tmp_path, username, password):
    with pytest.raises(ValueError, match="empty"):
        fetcher.fetch_snapshot(username, password, tmp_path)


def test_rejects_invalid_day(tmp_path):
    with pytest.raises(ValueError, match="day"):
        fetcher.fetch_snapshot("user", "pass", tmp_path, day="yesterday")


def test_rejects_api_error_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "urlopen", lambda *a, **k: FakeResponse(b'{"error":{"code":"bad_key"}}'))
    with pytest.raises(RuntimeError, match="error payload"):
        fetcher.fetch_snapshot("user", "pass", tmp_path)


def test_rejects_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "urlopen", lambda *a, **k: FakeResponse(b"not json"))
    with pytest.raises(RuntimeError, match="valid JSON"):
        fetcher.fetch_snapshot("user", "pass", tmp_path)
