import subprocess
from pathlib import Path

from scripts.server.absorption_check import (
    absorption_allowed,
    all_absorbed,
    blocking_files,
    is_contributor_work_file,
    is_empty_blob,
)


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    data = repo / "gui2" / "data"
    data.mkdir(parents=True)
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    return repo, data


class TestIsContributorWorkFile:
    def test_work_files(self):
        assert is_contributor_work_file("additions_alice.json")
        assert is_contributor_work_file("corrections_bob.json")

    def test_added_and_others_excluded(self):
        assert not is_contributor_work_file("additions_added_alice.json")
        assert not is_contributor_work_file("corrections_added_bob.json")
        assert not is_contributor_work_file("daily_log_alice.json")
        assert not is_contributor_work_file("additions_alice.txt")


class TestIsEmptyBlob:
    def test_empty_variants(self):
        assert is_empty_blob("{}")
        assert is_empty_blob("")
        assert is_empty_blob("   \n")
        assert is_empty_blob("[]")

    def test_non_empty(self):
        assert not is_empty_blob('{"alice_1": {"id": 1}}')


class TestPureCore:
    def test_all_absorbed_true(self):
        assert all_absorbed({"a": "{}", "b": ""})
        assert all_absorbed({})

    def test_all_absorbed_false_and_blocking(self):
        blobs = {"a": "{}", "b": '{"k": {}}'}
        assert not all_absorbed(blobs)
        assert blocking_files(blobs) == ["b"]


class TestAbsorptionAllowed:
    def test_non_empty_blocks(self, tmp_path: Path):
        repo, data = _repo(tmp_path)
        (data / "additions_alice.json").write_text('{"alice_1": {}}', encoding="utf-8")
        _git("add", "gui2/data/additions_alice.json", cwd=repo)
        _git("commit", "-m", "pending", cwd=repo)

        allowed, blocking = absorption_allowed(repo, ref="main", fetch=False)
        assert allowed is False
        assert blocking == ["gui2/data/additions_alice.json"]

    def test_all_empty_allowed(self, tmp_path: Path):
        repo, data = _repo(tmp_path)
        (data / "additions_alice.json").write_text("{}", encoding="utf-8")
        (data / "corrections_bob.json").write_text("{}", encoding="utf-8")
        # _added file is non-empty but must be ignored.
        (data / "additions_added_alice.json").write_text("[{}]", encoding="utf-8")
        for name in (
            "additions_alice.json",
            "corrections_bob.json",
            "additions_added_alice.json",
        ):
            _git("add", f"gui2/data/{name}", cwd=repo)
        _git("commit", "-m", "processed", cwd=repo)

        allowed, blocking = absorption_allowed(repo, ref="main", fetch=False)
        assert allowed is True
        assert blocking == []

    def test_git_error_fails_closed(self, tmp_path: Path):
        # A bad ref (git ls-tree fails) must RAISE, never report "absorbed".
        import pytest

        repo, _ = _repo(tmp_path)
        (repo / "README").write_text("x", encoding="utf-8")
        _git("add", "README", cwd=repo)
        _git("commit", "-m", "seed", cwd=repo)

        with pytest.raises(RuntimeError):
            absorption_allowed(repo, ref="nonexistent-ref", fetch=False)

    def test_no_contributor_files_allowed(self, tmp_path: Path):
        repo, _ = _repo(tmp_path)
        (repo / "README").write_text("x", encoding="utf-8")
        _git("add", "README", cwd=repo)
        _git("commit", "-m", "seed", cwd=repo)

        allowed, blocking = absorption_allowed(repo, ref="main", fetch=False)
        assert allowed is True
        assert blocking == []
