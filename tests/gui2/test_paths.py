from pathlib import Path

from gui2.paths import Gui2Paths


class TestDefaultBaseDir:
    """Default construction (no base_dir) must resolve identically to the
    old hardcoded-relative-path behavior — same files, same layout."""

    def test_gui2_dir_defaults_to_cwd_gui2(self):
        paths = Gui2Paths()
        assert paths.gui2_dir == Path.cwd() / "gui2"

    def test_daily_log_path_matches_old_relative_default(self):
        paths = Gui2Paths()
        assert (
            paths.daily_log_path.resolve() == Path("gui2/data/daily_log.json").resolve()
        )

    def test_find_words_dump_path_matches_old_relative_default(self):
        paths = Gui2Paths()
        expected = Path("gui2/data/find_words_with_examples_dump.json").resolve()
        assert paths.find_words_dump_path.resolve() == expected


class TestInjectableBaseDir:
    def test_all_paths_derive_from_base_dir(self, tmp_path: Path):
        paths = Gui2Paths(base_dir=tmp_path)
        assert paths.gui2_dir == tmp_path / "gui2"
        assert paths.gui2_data_path == tmp_path / "gui2" / "data"
        assert paths.daily_log_path == tmp_path / "gui2" / "data" / "daily_log.json"
        assert (
            paths.corrections_added_path
            == tmp_path / "gui2" / "data" / "corrections_added.json"
        )

    def test_two_instances_with_different_base_dirs_do_not_collide(
        self, tmp_path: Path
    ):
        a = tmp_path / "a"
        b = tmp_path / "b"
        paths_a = Gui2Paths(base_dir=a)
        paths_b = Gui2Paths(base_dir=b)
        assert paths_a.daily_log_path != paths_b.daily_log_path


class TestForUser:
    def test_primary_user_keeps_default_paths(self, tmp_path: Path):
        paths = Gui2Paths.for_user("1", base_dir=tmp_path)
        assert paths.additions_path == tmp_path / "gui2" / "data" / "additions.json"

    def test_contributor_gets_username_suffixed_paths(self, tmp_path: Path):
        paths = Gui2Paths.for_user("alice", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert paths.additions_path == data / "additions_alice.json"
        assert paths.additions_added_path == data / "additions_added_alice.json"
        assert paths.corrections_path == data / "corrections_alice.json"
        assert paths.corrections_added_path == data / "corrections_added_alice.json"

    def test_contributor_session_state_files_are_per_user(self, tmp_path: Path):
        paths = Gui2Paths.for_user("alice", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert paths.daily_log_path == data / "daily_log_alice.json"
        assert paths.history_json_path == data / "history_alice.json"
        assert paths.filter_presets_path == data / "filter_presets_alice.json"

    def test_contributor_stash_files_are_per_user(self, tmp_path: Path):
        paths = Gui2Paths.for_user("alice", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert paths.headword_stash_json_path == data / "headword_stash_alice.json"
        assert paths.example_stash_json_path == data / "example_stash_alice.json"
        assert paths.commentary_stash_json_path == data / "commentary_stash_alice.json"

    def test_primary_session_state_files_unchanged(self, tmp_path: Path):
        paths = Gui2Paths.for_user("1", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert paths.daily_log_path == data / "daily_log.json"
        assert paths.history_json_path == data / "history.json"
        assert paths.filter_presets_path == data / "filter_presets.json"
        assert paths.headword_stash_json_path == data / "headword_stash.json"
        assert paths.example_stash_json_path == data / "example_stash.json"
        assert paths.commentary_stash_json_path == data / "commentary_stash.json"

    def test_two_contributors_do_not_share_session_state(self, tmp_path: Path):
        a = Gui2Paths.for_user("alice", base_dir=tmp_path)
        b = Gui2Paths.for_user("bob", base_dir=tmp_path)
        assert a.daily_log_path != b.daily_log_path
        assert a.history_json_path != b.history_json_path

    def test_empty_username_keeps_default_paths(self, tmp_path: Path):
        paths = Gui2Paths.for_user("", base_dir=tmp_path)
        assert paths.additions_path == tmp_path / "gui2" / "data" / "additions.json"


class TestUserDictionaryPath:
    def test_primary_uses_shared_dictionary(self, tmp_path: Path):
        paths = Gui2Paths.for_user("1", base_dir=tmp_path)
        assert paths.user_dictionary_path == (
            tmp_path / "shared_data" / "user_dictionary.txt"
        )

    def test_contributor_dictionary_is_per_user(self, tmp_path: Path):
        a = Gui2Paths.for_user("alice", base_dir=tmp_path)
        b = Gui2Paths.for_user("bob", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert a.user_dictionary_path == data / "user_dictionary_alice.txt"
        assert b.user_dictionary_path == data / "user_dictionary_bob.txt"


class TestSandhiHelperPaths:
    def test_primary_uses_shared_deconstructor_files(self, tmp_path: Path):
        paths = Gui2Paths.for_user("1", base_dir=tmp_path)
        decon = tmp_path / "shared_data" / "deconstructor"
        assert paths.sandhi_checked_path == decon / "checked.csv"
        assert paths.sandhi_corrections_path == decon / "manual_corrections.tsv"
        assert paths.variant_readings_path == decon / "variant_readings.tsv"
        assert paths.spelling_mistakes_path == decon / "spelling_mistakes.tsv"

    def test_contributor_files_are_per_user(self, tmp_path: Path):
        a = Gui2Paths.for_user("alice", base_dir=tmp_path)
        b = Gui2Paths.for_user("bob", base_dir=tmp_path)
        data = tmp_path / "gui2" / "data"
        assert a.sandhi_checked_path == data / "checked_alice.csv"
        assert a.sandhi_corrections_path == data / "manual_corrections_alice.tsv"
        assert a.variant_readings_path == data / "variant_readings_alice.tsv"
        assert a.spelling_mistakes_path == data / "spelling_mistakes_alice.tsv"
        assert b.sandhi_checked_path != a.sandhi_checked_path
