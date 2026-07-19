import pytest

from gui2.user import UsernameManager, resolve_username
from tools.server_mode import resolve_role


class TestResolveUsername:
    def test_env_override_wins_over_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_USERNAME", "alice")
        assert resolve_username() == "alice"

    def test_unset_env_falls_back_to_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_USERNAME", raising=False)
        monkeypatch.setattr("gui2.user.config_read", lambda *a, **k: "1")
        assert resolve_username() == "1"

    def test_neither_set_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_USERNAME", raising=False)
        monkeypatch.setattr("gui2.user.config_read", lambda *a, **k: None)
        assert resolve_username() is None


class TestResolveRole:
    def test_env_override_wins_over_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        assert resolve_role() == "contributor-server"

    def test_unset_env_falls_back_to_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr(
            "tools.server_mode.config_read", lambda *a, **k: "contributor"
        )
        assert resolve_role() == "contributor"

    def test_neither_set_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr("tools.server_mode.config_read", lambda *a, **k: None)
        assert resolve_role() is None


class TestIsServerContributor:
    def _manager_with_role(self, role: str | None) -> UsernameManager:
        mgr = UsernameManager.__new__(UsernameManager)
        mgr.role = role
        return mgr

    def test_true_only_for_contributor_server_role(self):
        assert self._manager_with_role("contributor-server").is_server_contributor()

    def test_false_for_legacy_contributor_role(self):
        assert not self._manager_with_role("contributor").is_server_contributor()

    def test_false_when_role_unset(self):
        assert not self._manager_with_role(None).is_server_contributor()
