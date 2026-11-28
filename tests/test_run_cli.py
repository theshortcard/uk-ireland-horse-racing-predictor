from src import run


def test_run_blocks_validation_warnings_by_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["run", "--input", "input.csv", "--output", "out.md"])
    monkeypatch.setattr(run, "read_racecard", lambda path: [{"horse": "Example"}])
    monkeypatch.setattr(run, "validate_racecard", lambda rows: ["Line 2: days_since_run is blank."])
    monkeypatch.setattr(run, "audit_provenance", lambda rows: [])
    monkeypatch.setattr(run, "build_report", lambda rows, issues: "# report")
    monkeypatch.setattr(run, "write_report", lambda content, path: None)

    assert run.main() == 1


def test_run_can_explicitly_allow_visible_validation_warnings(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["run", "--input", "input.csv", "--output", "out.md", "--allow-validation-warnings"],
    )
    monkeypatch.setattr(run, "read_racecard", lambda path: [{"horse": "Example"}])
    monkeypatch.setattr(run, "validate_racecard", lambda rows: ["Line 2: days_since_run is blank."])
    monkeypatch.setattr(run, "audit_provenance", lambda rows: [])
    monkeypatch.setattr(run, "build_report", lambda rows, issues: "# report")
    monkeypatch.setattr(run, "write_report", lambda content, path: None)

    assert run.main() == 0
