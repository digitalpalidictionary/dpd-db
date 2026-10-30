"""push_contributions against a bare `file://` origin and a worktree."""

import subprocess
from pathlib import Path

import pytest

from scripts.server_contrib.contrib_push import build_commit_message, push_contributions


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _configure(repo: Path) -> None:
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("config", "commit.gpgsign", "false", cwd=repo)


class Setup:
    def __init__(self, tmp_path: Path) -> None:
        self.bare = tmp_path / "remote.git"
        self.bare.mkdir()
        _git("init", "--bare", "-b", "main", cwd=self.bare)

        self.maintainer = tmp_path / "maintainer"
        self.maintainer.mkdir()
        _git("init", "-b", "main", cwd=self.maintainer)
        _configure(self.maintainer)
        _git("remote", "add", "origin", self.bare.as_uri(), cwd=self.maintainer)
        (self.maintainer / ".gitignore").write_text(
            "gui2/data/*.txt\ngui2/data/*.csv\ngui2/data/*.tsv\n"
        )
        (self.maintainer / "README").write_text("x")
        self.main_commit("seed")

        self.server = tmp_path / "server"
        _git("clone", "-q", self.bare.as_uri(), str(self.server), cwd=tmp_path)
        _configure(self.server)
        self.worktree = tmp_path / "worktree"
        self.data = tmp_path / "server_data"
        self.data.mkdir()

    def main_commit(self, message: str, **files: str) -> None:
        for name, text in files.items():
            path = self.maintainer / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        _git("add", "-A", cwd=self.maintainer)
        _git("commit", "-q", "-m", message, cwd=self.maintainer)
        _git("push", "-q", "origin", "main", cwd=self.maintainer)

    def pull(self) -> None:
        _git("pull", "-q", "--ff-only", cwd=self.server)

    def push(self) -> None:
        push_contributions(self.server, self.data, self.worktree)

    def remote_sha(self, branch: str) -> str:
        return _git("rev-parse", branch, cwd=self.bare)

    def remote_files(self, branch: str) -> set[str]:
        out = _git("ls-tree", "-r", "--name-only", branch, cwd=self.bare)
        return set(out.split("\n"))


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    return Setup(tmp_path)


def test_commit_message_has_contrib_prefix() -> None:
    assert build_commit_message().startswith("contrib:")


def test_first_push_creates_the_branch_with_delivered_files_only(
    setup: Setup,
) -> None:
    (setup.data / "additions_alice.json").write_text('{"alice_1": {}}')
    (setup.data / "user_dictionary_alice.txt").write_text("word\n")
    (setup.data / "variant_readings_alice.tsv").write_text("variant\tmain\n")
    for name in (
        "additions_added_alice.json",
        "history_alice.json",
        "daily_log_alice.json",
        "filter_presets_alice.json",
        "headword_stash_alice.json",
    ):
        (setup.data / name).write_text("{}")

    setup.push()

    assert setup.remote_files("contributions") - setup.remote_files("main") == {
        "gui2/data/additions_alice.json",
        "gui2/data/user_dictionary_alice.txt",
        "gui2/data/variant_readings_alice.tsv",
    }


def test_nothing_changed_makes_no_commit(setup: Setup) -> None:
    setup.push()

    assert setup.remote_sha("contributions") == setup.remote_sha("main")


def test_a_second_push_after_main_moved_is_a_clean_reset(setup: Setup) -> None:
    (setup.data / "additions_alice.json").write_text('{"alice_1": {}}')
    setup.push()
    setup.main_commit("more", other="y")
    setup.pull()
    (setup.data / "additions_alice.json").write_text('{"alice_2": {}}')

    setup.push()

    assert _git("rev-parse", "contributions~1", cwd=setup.bare) == setup.remote_sha(
        "main"
    )
    shown = _git("show", "contributions:gui2/data/additions_alice.json", cwd=setup.bare)
    assert shown == '{"alice_2": {}}'


def test_a_discarded_entry_leaves_the_branch(setup: Setup) -> None:
    (setup.data / "additions_alice.json").write_text('{"alice_1": {}}')
    setup.push()
    (setup.data / "additions_alice.json").unlink()

    setup.push()

    assert setup.remote_sha("contributions") == setup.remote_sha("main")


def test_an_emptied_file_shows_as_emptied_over_main(setup: Setup) -> None:
    setup.main_commit("pending", **{"gui2/data/additions_alice.json": '{"a": {}}'})
    setup.pull()
    (setup.data / "additions_alice.json").write_text("{}")

    setup.push()

    shown = _git("show", "contributions:gui2/data/additions_alice.json", cwd=setup.bare)
    assert shown == "{}"


def test_branch_deleted_on_the_remote_does_not_block_the_next_push(
    setup: Setup,
) -> None:
    (setup.data / "additions_alice.json").write_text('{"alice_1": {}}')
    setup.push()
    _git("branch", "-D", "contributions", cwd=setup.bare)

    setup.push()

    assert "gui2/data/additions_alice.json" in setup.remote_files("contributions")


def test_a_move_of_main_after_the_pull_does_not_change_the_base(
    setup: Setup,
) -> None:
    pulled = _git("rev-parse", "HEAD", cwd=setup.server)
    setup.main_commit("later", late="z")
    (setup.data / "additions_alice.json").write_text('{"alice_1": {}}')

    setup.push()

    assert _git("rev-parse", "contributions~1", cwd=setup.bare) == pulled
    assert "late" not in setup.remote_files("contributions")
