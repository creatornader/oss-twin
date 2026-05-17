"""End-to-end smoke tests for oss-twin commands."""

import subprocess
from pathlib import Path

import pytest

from oss_twin.commands import check_cmd, init_cmd, move_cmd, status_cmd
from oss_twin.config import Config, MirrorConfig, load_config


def _make_config(repo_root: Path, mirror_path: Path, private_paths=None, scaffold=None) -> Config:
    return Config(
        mirror=MirrorConfig(path=str(mirror_path), remote=None, visibility="private"),
        private_paths=private_paths or [],
        mirror_scaffold=scaffold or [],
        repo_root=repo_root,
    )


@pytest.fixture
def public_repo(tmp_path):
    repo = tmp_path / "public-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    return repo


def test_check_passes_when_no_private_paths_exist(public_repo, tmp_path):
    config = _make_config(public_repo, tmp_path / "mirror", private_paths=["docs/handoffs/"])
    assert check_cmd.run(config) == 0


def test_check_fails_when_private_path_exists(public_repo, tmp_path):
    (public_repo / "docs" / "handoffs").mkdir(parents=True)
    (public_repo / "docs" / "handoffs" / "secret.md").write_text("operator-only stuff")
    config = _make_config(public_repo, tmp_path / "mirror", private_paths=["docs/handoffs/"])
    assert check_cmd.run(config) == 1


def test_init_scaffolds_mirror_with_claude_md(public_repo, tmp_path):
    mirror = tmp_path / "mirror"
    config = _make_config(public_repo, mirror, scaffold=["docs/", "docs/handoffs/"])
    assert init_cmd.run(config) == 0
    assert (mirror / ".git").is_dir()
    assert (mirror / "CLAUDE.md").is_file()
    assert (mirror / "README.md").is_file()
    assert (mirror / ".gitignore").is_file()
    assert (mirror / "docs" / "handoffs").is_dir()
    assert "public-repo" in (mirror / "CLAUDE.md").read_text()


def test_move_relocates_file_to_mirror(public_repo, tmp_path):
    mirror = tmp_path / "mirror"
    config = _make_config(public_repo, mirror, private_paths=["docs/handoffs/"])
    init_cmd.run(config)

    src_dir = public_repo / "docs" / "handoffs"
    src_dir.mkdir(parents=True)
    src = src_dir / "secret.md"
    src.write_text("operator-only")

    assert move_cmd.run(config, "docs/handoffs/secret.md") == 0
    assert not src.exists()
    assert (mirror / "docs" / "handoffs" / "secret.md").is_file()
    assert (mirror / "docs" / "handoffs" / "secret.md").read_text() == "operator-only"


def test_move_refuses_to_overwrite_without_force(public_repo, tmp_path):
    mirror = tmp_path / "mirror"
    config = _make_config(public_repo, mirror, private_paths=["docs/handoffs/"])
    init_cmd.run(config)

    src = public_repo / "secret.md"
    src.write_text("v1")
    move_cmd.run(config, "secret.md")  # first move

    src.write_text("v2-conflict")
    assert move_cmd.run(config, "secret.md") == 1
    assert src.read_text() == "v2-conflict"  # not moved


def test_status_reports_leaks(public_repo, tmp_path, capsys):
    mirror = tmp_path / "mirror"
    (public_repo / "docs" / "handoffs").mkdir(parents=True)
    (public_repo / "docs" / "handoffs" / "x.md").write_text("x")
    config = _make_config(public_repo, mirror, private_paths=["docs/handoffs/"])

    rc = status_cmd.run(config)
    captured = capsys.readouterr().out
    assert "PUBLIC LEAK" in captured
    assert rc == 1


def test_config_loader_discovers_yaml_in_parent(tmp_path):
    (tmp_path / ".oss-twin.yaml").write_text(
        "version: 1\nmirror:\n  path: ../foo-internal\nprivate_paths:\n  - x/\n"
    )
    (tmp_path / "subdir").mkdir()

    import os
    cwd_save = os.getcwd()
    try:
        os.chdir(tmp_path / "subdir")
        config = load_config()
        assert config.mirror.path == "../foo-internal"
        assert config.private_paths == ["x/"]
    finally:
        os.chdir(cwd_save)
