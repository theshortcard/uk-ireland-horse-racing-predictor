from __future__ import annotations

import hashlib
import json

import pytest

import src.fetch_results_api as fetcher


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


def test_saves_raw_response_and_key_free_metadata(tmp_path, monkeypatch):
    body = b'{"meta":{"plan":"free"},"data":[{"race_id":"abc"}]}'
    seen = {}

    def fake_urlopen(request, timeout):
        seen["key"] = request.get_header("X-api-key")
        seen["timeout"] = timeout
        return FakeResponse(body)

    monkeypatch.setattr(fetcher, "urlopen", fake_urlopen)
    raw_path, meta_path = fetcher.fetch_snapshot("secret-token", tmp_path)

    assert raw_path.read_bytes() == body
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["sha256"] == hashlib.sha256(body).hexdigest()
    assert "secret-token" not in meta_path.read_text(encoding="utf-8")
    assert seen == {"key": "secret-token", "timeout": 30}


def test_rejects_api_error_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "urlopen", lambda *a, **k: FakeResponse(b'{"error":{"code":"bad_key"}}'))
    with pytest.raises(RuntimeError, match="API returned an error"):
        fetcher.fetch_snapshot("key", tmp_path)


def test_rejects_missing_data_field(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "urlopen", lambda *a, **k: FakeResponse(b'{"meta":{}}'))
    with pytest.raises(RuntimeError, match="documented 'data' field"):
        fetcher.fetch_snapshot("key", tmp_path)


def test_rejects_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "urlopen", lambda *a, **k: FakeResponse(b"not json"))
    with pytest.raises(RuntimeError, match="valid JSON"):
        fetcher.fetch_snapshot("key", tmp_path)


def test_rejects_empty_key(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        fetcher.fetch_snapshot("", tmp_path)
