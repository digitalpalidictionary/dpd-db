"""Three nightly cycles between a server clone and a maintainer clone, through
the real window (stub heavy steps), the real push, `git merge`, the real
processing methods and the real merge script."""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from db.models import DpdHeadword
from gui2.additions_manager import AdditionsManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit
from scripts.server_contrib.maintenance_window import (
    Outcome,
    WindowConfig,
    WindowSteps,
    default_steps,
    run_maintenance,
)
from scripts.server_contrib.merge_contrib_files import SharedFiles, merge_all


def _git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=check
    )


def _configure(repo: Path) -> None:
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("config", "commit.gpgsign", "false", cwd=repo)


def _manager(base: Path, username: str) -> AdditionsManager:
    paths = Gui2Paths.for_user(username, base_dir=base)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    return AdditionsManager(cast(ToolKit, SimpleNamespace(paths=paths)))


def _word(id_no: int, lemma: str) -> DpdHeadword:
    word = DpdHeadword()
    word.id = id_no
    word.lemma_1 = lemma
    word.meaning_1 = "meaning"
    return word


def _stub_steps() -> WindowSteps:
    real = default_steps()
    return WindowSteps(
        pull=real.pull,
        push=real.push,
        rebuild=lambda c: None,
        generate=lambda c: None,
        health_check=lambda c: None,
    )


class World:
    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.bare = tmp_path / "remote.git"
        self.bare.mkdir()
        _git("init", "--bare", "-b", "main", cwd=self.bare)

        self.maintainer = tmp_path / "maintainer"
        self.maintainer.mkdir()
        _git("init", "-b", "main", cwd=self.maintainer)
        _configure(self.maintainer)
        _git("remote", "add", "origin", self.bare.as_uri(), cwd=self.maintainer)
        (self.maintainer / ".gitignore").write_text(
            "gui2/data/*.csv\ngui2/data/*.tsv\ngui2/data/*.txt\n"
        )
        self.shared = tmp_path / "shared"
        self.shared.mkdir()
        (self.shared / "variant_readings.tsv").write_bytes(b"variant\tmain\r\n")
        (self.shared / "checked.csv").write_text("seed\n")
        for name in ("user_dictionary.txt", "manual_corrections.tsv", "tests.tsv"):
            (self.shared / name).write_text("")
        (self.shared / "spelling_mistakes.tsv").write_bytes(b"mistake\tcorrection\r\n")
        self.commit_main("seed")

        self.server = tmp_path / "server"
        _git("clone", "-q", self.bare.as_uri(), str(self.server), cwd=tmp_path)
        _configure(self.server)
        self.data = tmp_path / "server_data"
        self.data.mkdir()
        monkeypatch.setenv("DPD_GUI2_DATA_DIR", str(self.data))
        self.config = WindowConfig(
            project_root=self.server,
            db_path=self.server / "dpd.db",
            data_dir=self.data,
            worktree=tmp_path / "worktree",
            log_dir=self.server / "logs",
            use_systemd=False,
        )
        self.alice = _manager(tmp_path / "unused_base", "alice")

    def shared_files(self) -> SharedFiles:
        return SharedFiles(
            user_dictionary=self.shared / "user_dictionary.txt",
            sandhi_checked=self.shared / "checked.csv",
            sandhi_corrections=self.shared / "manual_corrections.tsv",
            variant_readings=self.shared / "variant_readings.tsv",
            spelling_mistakes=self.shared / "spelling_mistakes.tsv",
            tests_columns=self.shared / "tests.tsv",
        )

    def commit_main(self, message: str) -> None:
        _git("add", "-A", cwd=self.maintainer)
        _git("commit", "-q", "-m", message, cwd=self.maintainer)
        _git("push", "-q", "origin", "main", cwd=self.maintainer)

    def window(self) -> Outcome:
        return run_maintenance(self.config, _stub_steps())

    def merge_branch(self) -> None:
        """`just contrib-merge`, minus the recipe: fetch, merge, merge script."""
        _git("fetch", "-q", "origin", "contributions", cwd=self.maintainer)
        merged = _git(
            "merge", "--no-edit", "origin/contributions",
            cwd=self.maintainer, check=False,
        )  # fmt: skip
        assert merged.returncode == 0, merged.stdout + merged.stderr
        self.run_merge_script()

    def run_merge_script(self) -> None:
        paths = Gui2Paths(self.maintainer)
        merge_all(
            paths.gui2_data_path, self.shared_files(), paths.contrib_lines_merged_path
        )

    def server_keys(self) -> set[str]:
        return set(json.loads((self.data / "additions_alice.json").read_text()))

    def branch_keys(self) -> set[str]:
        shown = _git(
            "show", "contributions:gui2/data/additions_alice.json", cwd=self.bare
        ).stdout
        return set(json.loads(shown))

    def maintainer_review(self, accept: str, reject: str) -> None:
        manager = _manager(self.maintainer, "1")
        origin = self.maintainer / "gui2" / "data" / "additions_alice.json"
        accepted = manager.additions_dict[accept]
        manager.save_processed_addition({"lemma_1": "x"}, origin, accept, accepted)
        manager.reject(origin, reject, manager.additions_dict[reject])
        self.commit_main("processed")


def test_three_cycles_leave_only_pending_work_and_never_bring_back_deleted_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = World(tmp_path, monkeypatch)
    for id_no, lemma in ((10_000_001, "a"), (10_000_002, "b"), (10_000_003, "c")):
        world.alice.add_additions(_word(id_no, lemma), "note")
    accept, reject, pending = "alice_10000001", "alice_10000002", "alice_10000003"
    (world.data / "checked_alice.csv").write_text("w1\n")
    (world.data / "variant_readings_alice.tsv").write_bytes(
        b"variant\tmain\r\nk1\tv1\r\n"
    )

    # Cycle 1: the server delivers; the maintainer merges, accepts one, rejects one.
    assert world.window() is Outcome.REBUILT
    assert world.branch_keys() == {accept, reject, pending}
    world.merge_branch()
    world.maintainer_review(accept, reject)
    assert b"k1\tv1" in (world.shared / "variant_readings.tsv").read_bytes()
    assert (world.shared / "checked.csv").read_text() == "seed\nw1\n"

    # Cycle 2: the server drops what main handled and keeps the pending entry.
    assert world.window() is Outcome.REBUILT
    assert world.server_keys() == {pending}
    assert world.branch_keys() == {pending}
    assert (world.data / "checked_alice.csv").read_text() == ""
    assert (world.data / "variant_readings_alice.tsv").read_bytes() == (
        b"variant\tmain\r\n"
    )

    # The maintainer deletes the merged flag line, then merges again. main's
    # copy of the contributor file still holds it (it lags one cycle).
    (world.shared / "checked.csv").write_text("seed\n")
    world.run_merge_script()
    assert (world.shared / "checked.csv").read_text() == "seed\n"
    world.alice.add_additions(_word(10_000_004, "d"), "note")
    (world.data / "variant_readings_alice.tsv").write_bytes(
        b"variant\tmain\r\nk2\tv2\r\n"
    )

    # Cycle 3: new work arrives, the merge has no conflict, nothing comes back.
    assert world.window() is Outcome.SKIPPED
    assert world.branch_keys() == {pending, "alice_10000004"}
    world.merge_branch()
    assert (world.shared / "checked.csv").read_text() == "seed\n"
    assert b"k2\tv2" in (world.shared / "variant_readings.tsv").read_bytes()
    assert world.server_keys() == {pending, "alice_10000004"}
