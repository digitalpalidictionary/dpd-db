"""Tests for the path-limited git commit of the TSV backup."""

import subprocess
from pathlib import Path

import pytest

from db.backup_tsv.backup_dpd_headwords_and_roots import git_commit
from tools.paths import ProjectPaths


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "test")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_parts(backup_dir: Path, text: str) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "dpd_headwords_part_001.tsv").write_text(text)
    (backup_dir / "dpd_roots_part_001.tsv").write_text(text)


def test_commits_only_the_part_files_and_leaves_other_staged_files(
    repo: Path,
) -> None:
    pth = ProjectPaths(base_dir=repo, create_dirs=False)
    backup_dir = pth.pali_word_path.parent
    write_parts(backup_dir, "old")
    (repo / "other.txt").write_text("old")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "initial")

    write_parts(backup_dir, "new")
    (repo / "other.txt").write_text("new")
    git(repo, "add", "other.txt")

    git_commit(pth)

    assert git(repo, "log", "-1", "--format=%s") == "pali update"
    committed = set(git(repo, "show", "--name-only", "--format=", "HEAD").split())
    assert committed == {
        "db/backup_tsv/dpd_headwords_part_001.tsv",
        "db/backup_tsv/dpd_roots_part_001.tsv",
    }
    assert git(repo, "diff", "--cached", "--name-only") == "other.txt"


def test_a_failed_commit_is_reported_not_raised(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pth = ProjectPaths(base_dir=repo, create_dirs=False)
    (repo / "other.txt").write_text("old")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "initial")

    # untracked paths after `--` make git commit fail
    write_parts(pth.pali_word_path.parent, "new")

    git_commit(pth)

    assert git(repo, "log", "-1", "--format=%s") == "initial"
    assert "pathspec" in capsys.readouterr().out
