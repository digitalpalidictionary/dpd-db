import json
import subprocess
from pathlib import Path

from scripts.server.contrib_reconcile import (
    contributor_files,
    load_json_dict,
    reconcile,
    reconcile_all,
    write_json_dict,
)


def entry(meaning: str) -> dict:
    return {"id": 1, "meaning_1": meaning}


class TestReconcilePureCore:
    def test_upstream_processed_all(self):
        pushed = {"alice_1": entry("a"), "alice_2": entry("b")}
        local = {"alice_1": entry("a"), "alice_2": entry("b")}
        upstream: dict[str, dict] = {}
        assert reconcile(local, pushed, upstream) == {}

    def test_upstream_processed_some(self):
        pushed = {"alice_1": entry("a"), "alice_2": entry("b")}
        local = {"alice_1": entry("a"), "alice_2": entry("b")}
        upstream = {"alice_2": entry("b")}
        assert reconcile(local, pushed, upstream) == {"alice_2": entry("b")}

    def test_upstream_processed_none(self):
        pushed = {"alice_1": entry("a"), "alice_2": entry("b")}
        local = {"alice_1": entry("a"), "alice_2": entry("b")}
        upstream = {"alice_1": entry("a"), "alice_2": entry("b")}
        assert reconcile(local, pushed, upstream) == local

    def test_local_keys_added_during_day(self):
        pushed = {"alice_1": entry("a")}
        local = {"alice_1": entry("a"), "alice_2": entry("new")}
        upstream: dict[str, dict] = {}
        # alice_1 processed and dropped; alice_2 added since push is kept.
        assert reconcile(local, pushed, upstream) == {"alice_2": entry("new")}

    def test_both_processed_and_added(self):
        pushed = {"alice_1": entry("a"), "alice_2": entry("b")}
        local = {
            "alice_1": entry("a"),
            "alice_2": entry("b"),
            "alice_3": entry("fresh"),
        }
        upstream = {"alice_2": entry("b")}
        # alice_1 dropped (processed), alice_2 kept (still upstream),
        # alice_3 kept (added locally).
        assert reconcile(local, pushed, upstream) == {
            "alice_2": entry("b"),
            "alice_3": entry("fresh"),
        }

    def test_empty_files(self):
        assert reconcile({}, {}, {}) == {}

    def test_keep_local_edit_after_processed(self):
        # Pushed and processed upstream, but re-edited locally under the same
        # stable key: the fresh edit must survive.
        pushed = {"alice_1": entry("old")}
        local = {"alice_1": entry("edited")}
        upstream: dict[str, dict] = {}
        assert reconcile(local, pushed, upstream) == {"alice_1": entry("edited")}

    def test_drop_only_when_unchanged(self):
        # Same key present upstream still (not processed) but locally changed:
        # kept regardless.
        pushed = {"alice_1": entry("old")}
        local = {"alice_1": entry("edited")}
        upstream = {"alice_1": entry("old")}
        assert reconcile(local, pushed, upstream) == {"alice_1": entry("edited")}


class TestJsonHelpers:
    def test_load_missing_returns_empty(self, tmp_path: Path):
        assert load_json_dict(tmp_path / "nope.json") == {}

    def test_load_invalid_raises(self, tmp_path: Path):
        # Fail closed: a corrupt file must NOT be silently treated as empty.
        import pytest

        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with pytest.raises(RuntimeError):
            load_json_dict(bad)

    def test_write_empty_uses_braces(self, tmp_path: Path):
        path = tmp_path / "out.json"
        write_json_dict(path, {})
        assert path.read_text(encoding="utf-8") == "{}"

    def test_write_then_load_roundtrip(self, tmp_path: Path):
        path = tmp_path / "out.json"
        data = {"alice_1": entry("ā")}
        write_json_dict(path, data)
        assert load_json_dict(path) == data


class TestContributorFiles:
    def test_globs_work_files_excluding_added(self, tmp_path: Path):
        for name in (
            "additions_alice.json",
            "additions_added_alice.json",
            "corrections_bob.json",
            "corrections_added_bob.json",
            "additions.json",
        ):
            (tmp_path / name).write_text("{}", encoding="utf-8")
        # The primary additions.json (no username) is not a contributor file
        # and is correctly excluded by the additions_*.json glob.
        names = [p.name for p in contributor_files(tmp_path)]
        assert names == [
            "additions_alice.json",
            "corrections_bob.json",
        ]


class TestReconcileAll:
    def _git(self, *args: str, cwd: Path) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_end_to_end_with_scratch_repo(self, tmp_path: Path):
        # Scratch repo standing in for origin/main.
        repo = tmp_path / "repo"
        data_dir = repo / "gui2" / "data"
        data_dir.mkdir(parents=True)
        self._git("init", "-b", "main", cwd=repo)
        self._git("config", "user.email", "t@t.t", cwd=repo)
        self._git("config", "user.name", "t", cwd=repo)

        rel = "gui2/data/additions_alice.json"
        # main has alice_2 still pending (alice_1 already processed away).
        (data_dir / "additions_alice.json").write_text(
            json.dumps({"alice_2": entry("b")}), encoding="utf-8"
        )
        self._git("add", rel, cwd=repo)
        self._git("commit", "-m", "seed", cwd=repo)

        snapshot_dir = data_dir / "last_pushed"
        snapshot_dir.mkdir()
        # last_pushed had both keys.
        write_json_dict(
            snapshot_dir / "additions_alice.json",
            {"alice_1": entry("a"), "alice_2": entry("b")},
        )
        # local: both pushed keys + a fresh local one.
        write_json_dict(
            data_dir / "additions_alice.json",
            {
                "alice_1": entry("a"),
                "alice_2": entry("b"),
                "alice_3": entry("fresh"),
            },
        )

        remaining = reconcile_all(repo, data_dir, snapshot_dir, "main")

        assert remaining == {"additions_alice.json": 2}
        result = load_json_dict(data_dir / "additions_alice.json")
        assert result == {"alice_2": entry("b"), "alice_3": entry("fresh")}
        # Snapshot refreshed to the reconciled state.
        assert load_json_dict(snapshot_dir / "additions_alice.json") == result

    def test_upstream_absent_file_treated_empty(self, tmp_path: Path):
        repo = tmp_path / "repo"
        data_dir = repo / "gui2" / "data"
        data_dir.mkdir(parents=True)
        self._git("init", "-b", "main", cwd=repo)
        self._git("config", "user.email", "t@t.t", cwd=repo)
        self._git("config", "user.name", "t", cwd=repo)
        (repo / "README").write_text("x", encoding="utf-8")
        self._git("add", "README", cwd=repo)
        self._git("commit", "-m", "seed", cwd=repo)

        snapshot_dir = data_dir / "last_pushed"
        snapshot_dir.mkdir()
        write_json_dict(snapshot_dir / "additions_alice.json", {"alice_1": entry("a")})
        write_json_dict(data_dir / "additions_alice.json", {"alice_1": entry("a")})

        remaining = reconcile_all(repo, data_dir, snapshot_dir, "main")

        # File absent upstream => alice_1 pushed then removed => dropped.
        assert remaining == {"additions_alice.json": 0}
        assert load_json_dict(data_dir / "additions_alice.json") == {}
