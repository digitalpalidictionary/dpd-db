from unittest.mock import MagicMock

import flet as ft
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


class TestIsNotPrimary:
    def test_no_username_is_primary(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_USERNAME", raising=False)
        monkeypatch.setattr("gui2.user.config_read", lambda *a, **k: None)
        assert not UsernameManager(MagicMock()).is_not_primary()

    def test_env_username_is_not_primary(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_USERNAME", "alice")
        assert UsernameManager(MagicMock()).is_not_primary()

    def test_primary_username_one_is_primary(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_USERNAME", "1")
        assert not UsernameManager(MagicMock()).is_not_primary()

    def test_first_run_dialog_does_not_change_where_this_session_saves(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("DPD_GUI2_USERNAME", raising=False)
        monkeypatch.setattr("gui2.user.config_read", lambda *a, **k: None)
        monkeypatch.setattr("gui2.user.config_update", MagicMock())
        mgr = UsernameManager(MagicMock())
        mgr.username_field.value = "alice"

        mgr._save_username_and_close_dialog(MagicMock())

        assert mgr.username == "alice"
        assert not mgr.is_not_primary()

    def test_dialog_says_it_takes_effect_on_next_start(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("DPD_GUI2_USERNAME", raising=False)
        monkeypatch.setattr("gui2.user.config_read", lambda *a, **k: None)
        mgr = UsernameManager(MagicMock())
        content = mgr.username_dialog.content
        assert isinstance(content, ft.Column)
        texts = [c.value for c in content.controls if isinstance(c, ft.Text)]
        assert "This takes effect the next time you start the app." in texts
