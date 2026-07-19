import pytest

from gui2.ai_search_window import launch_ai_search_window


class TestLaunchGatedInServerMode:
    def test_noop_in_server_mode(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        called = False

        def _fail(*a, **k):
            nonlocal called
            called = True

        monkeypatch.setattr("gui2.ai_search_window.subprocess.Popen", _fail)
        launch_ai_search_window()
        assert called is False

    def test_spawns_on_desktop(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        monkeypatch.setattr("gui2.ai_search_window._process", None)
        spawned: list[bool] = []

        class _FakeProc:
            def poll(self):
                return None

        monkeypatch.setattr(
            "gui2.ai_search_window.subprocess.Popen",
            lambda *a, **k: (spawned.append(True), _FakeProc())[1],
        )
        launch_ai_search_window()
        assert spawned == [True]
