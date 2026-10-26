"""Tests for the path-limited git commit of the TSV backup."""

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from db.backup_tsv.backup_dpd_headwords_and_roots import (
    check_no_duplicate_lemma_1,
    find_duplicate_lemma_1,
    git_commit,
)
from db.models import Base
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


@pytest.fixture
def headword_session() -> Session:  # type: ignore
    """In-memory db whose lemma_1 has no UNIQUE rule, like the live dpd.db."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.execute(text("DROP TABLE dpd_headwords"))
    session.execute(
        text(
            "CREATE TABLE dpd_headwords (id INTEGER PRIMARY KEY, lemma_1 VARCHAR NOT NULL)"
        )
    )
    session.commit()
    yield session  # type: ignore
    session.close()


def add_names(session: Session, names: list[str]) -> None:
    for i, name in enumerate(names, start=1):
        session.execute(
            text("INSERT INTO dpd_headwords (id, lemma_1) VALUES (:i, :n)"),
            {"i": i, "n": name},
        )
    session.commit()


def test_duplicate_lemma_1_lists_names_with_their_ids(
    headword_session: Session,
) -> None:
    add_names(headword_session, ["a 1", "b 1", "a 1", "c 1", "b 1", "a 1"])
    assert find_duplicate_lemma_1(headword_session) == {"a 1": [1, 3, 6], "b 1": [2, 5]}


def test_unique_lemma_1_passes_the_check(headword_session: Session) -> None:
    add_names(headword_session, ["a 1", "a 2", "b 1"])
    check_no_duplicate_lemma_1(headword_session)


def test_duplicate_lemma_1_stops_the_backup(headword_session: Session) -> None:
    add_names(headword_session, ["a 1", "a 1"])
    with pytest.raises(SystemExit) as stopped:
        check_no_duplicate_lemma_1(headword_session)
    assert stopped.value.code == 1
