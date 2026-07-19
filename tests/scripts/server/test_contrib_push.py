import json
import subprocess
from pathlib import Path

from scripts.server.contrib_push import build_commit_message, push_contributions
from scripts.server.contrib_reconcile import load_json_dict


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _make_repo_with_remote(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Return (repo, data_dir, snapshot_dir, bare_remote)."""
    bare = tmp_path / "remote.git"
    bare.mkdir()
    _git("init", "--bare", "-b", "main", cwd=bare)

    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("remote", "add", "origin", str(bare), cwd=repo)
    (repo / "README").write_text("x", encoding="utf-8")
    _git("add", "README", cwd=repo)
    _git("commit", "-m", "seed", cwd=repo)

    data_dir = repo / "gui2" / "data"
    data_dir.mkdir(parents=True)
    snapshot_dir = data_dir / "last_pushed"
    snapshot_dir.mkdir()
    return repo, data_dir, snapshot_dir, bare


class TestBuildCommitMessage:
    def test_has_contrib_prefix(self):
        assert build_commit_message().startswith("contrib: submit data ")


class TestPushContributions:
    def test_push_then_noop_and_snapshots(self, tmp_path: Path):
        repo, data_dir, snapshot_dir, bare = _make_repo_with_remote(tmp_path)
        work = {"alice_1": {"id": 1, "meaning_1": "a"}}
        (data_dir / "additions_alice.json").write_text(
            json.dumps(work), encoding="utf-8"
        )

        first = push_contributions(repo, data_dir, snapshot_dir)
        assert first.pushed is True
        assert "gui2/data/additions_alice.json" in first.committed_files

        # Landed on the contributions branch of the bare remote.
        branches = _git("branch", cwd=bare).stdout
        assert "contributions" in branches

        # Snapshot mirrors the pushed file.
        assert load_json_dict(snapshot_dir / "additions_alice.json") == work

        # Second call with no changes is a no-op.
        second = push_contributions(repo, data_dir, snapshot_dir)
        assert second.pushed is False

    def test_excludes_added_files(self, tmp_path: Path):
        repo, data_dir, snapshot_dir, _ = _make_repo_with_remote(tmp_path)
        (data_dir / "additions_alice.json").write_text(
            '{"alice_1": {}}', encoding="utf-8"
        )
        (data_dir / "additions_added_alice.json").write_text(
            '[{"id": 1}]', encoding="utf-8"
        )

        result = push_contributions(repo, data_dir, snapshot_dir)

        assert result.committed_files == ["gui2/data/additions_alice.json"]

    def test_nothing_to_push_when_no_files(self, tmp_path: Path):
        repo, data_dir, snapshot_dir, _ = _make_repo_with_remote(tmp_path)
        result = push_contributions(repo, data_dir, snapshot_dir)
        assert result.pushed is False
        assert result.message == "nothing to push"
