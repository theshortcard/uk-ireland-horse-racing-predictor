import hashlib
from datetime import datetime, timezone

from src.manifest import validate_manifest


def valid_manifest(tmp_path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text("race_id,horse\nR1,Runner\n", encoding="utf-8")
    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    return {
        "dataset_name": "Test archive",
        "provider": "Test provider",
        "source_url": "https://example.com/data",
        "license_name": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "file_path": "dataset.csv",
        "sha256": digest,
        "coverage_start": "2020-01-01",
        "coverage_end": "2026-11-20",
        "countries": ["GB", "IRE"],
        "notes": "Fictional test data only.",
    }


def test_valid_manifest_and_checksum_pass(tmp_path):
    data = valid_manifest(tmp_path)
    assert validate_manifest(data, tmp_path) == []


def test_checksum_mismatch_is_rejected(tmp_path):
    data = valid_manifest(tmp_path)
    data["sha256"] = "0" * 64
    assert any("does not match" in issue for issue in validate_manifest(data, tmp_path))


def test_naive_download_timestamp_is_rejected(tmp_path):
    data = valid_manifest(tmp_path)
    data["downloaded_at"] = "2026-11-20T12:00:00"
    assert any("timezone offset" in issue for issue in validate_manifest(data, tmp_path))


def test_invalid_coverage_and_country_are_rejected(tmp_path):
    data = valid_manifest(tmp_path)
    data["coverage_start"] = "2027-01-01"
    data["countries"] = ["GB", "USA"]
    issues = validate_manifest(data, tmp_path)
    assert any("coverage_start must not be later" in issue for issue in issues)
    assert any("only GB and/or IRE" in issue for issue in issues)


def test_unsafe_relative_path_is_rejected(tmp_path):
    data = valid_manifest(tmp_path)
    data["file_path"] = "../outside.csv"
    assert any("safe relative path" in issue for issue in validate_manifest(data, tmp_path))
