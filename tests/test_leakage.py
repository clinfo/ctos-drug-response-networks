from pathlib import Path

from ctos_drug_response_networks.leakage import scan_repo
from ctos_drug_response_networks.config import load_config


def test_public_surface_has_no_forbidden_hits():
    config = load_config("config/default.yaml")
    report = scan_repo(".", config["policy"]["forbidden_strings"])
    assert report["hit_count"] == 0, report


def test_virtualenv_and_build_dirs_are_ignored(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".venv").mkdir()
    (repo / ".venv" / "note.txt").write_text("placeholder absolute-like text\n", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "trace.txt").write_text("windows_absolute_like_text\n", encoding="utf-8")
    (repo / "README.md").write_text("clean\n", encoding="utf-8")
    report = scan_repo(repo, [])
    assert report["hit_count"] == 0, report
