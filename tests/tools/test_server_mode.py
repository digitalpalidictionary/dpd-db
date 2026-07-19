import pytest

from tools.server_mode import is_headless_server, resolve_role


class TestIsHeadlessServer:
    def test_true_for_contributor_server_role(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        assert is_headless_server() is True

    def test_false_for_legacy_contributor_role(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor")
        assert is_headless_server() is False

    def test_false_when_role_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr("tools.server_mode.config_read", lambda *a, **k: None)
        assert is_headless_server() is False

    def test_true_via_config_fallback_when_env_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # A server whose role is set in config.ini (not the env var) must still
        # suppress shell-outs — is_headless_server and resolve_role agree.
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr(
            "tools.server_mode.config_read", lambda *a, **k: "contributor-server"
        )
        assert is_headless_server() is True


class TestResolveRole:
    def test_env_wins_over_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        monkeypatch.setattr("tools.server_mode.config_read", lambda *a, **k: "other")
        assert resolve_role() == "contributor-server"

    def test_config_fallback_when_env_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr(
            "tools.server_mode.config_read", lambda *a, **k: "contributor"
        )
        assert resolve_role() == "contributor"
