import pytest

from tools.fast_api_utils import _api_port, request_dpd_server, start_dpd_server


class TestApiPort:
    def test_defaults_to_8080(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("DPD_API_PORT", raising=False)
        assert _api_port() == "8080"

    def test_env_override_wins(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DPD_API_PORT", "8082")
        assert _api_port() == "8082"


class TestServerModeGating:
    def test_start_dpd_server_noop_in_server_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        called = False

        def _fail(*a, **k):
            nonlocal called
            called = True

        monkeypatch.setattr("tools.fast_api_utils.subprocess.Popen", _fail)
        start_dpd_server()
        assert called is False

    def test_request_dpd_server_noop_in_server_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
        called = False

        def _fail(*a, **k):
            nonlocal called
            called = True

        monkeypatch.setattr("tools.fast_api_utils.webbrowser.open", _fail)
        request_dpd_server("123")
        assert called is False

    def test_request_dpd_server_opens_browser_on_desktop(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
        opened: list[str] = []
        monkeypatch.setattr(
            "tools.fast_api_utils.webbrowser.open", lambda url: opened.append(url)
        )
        request_dpd_server("123")
        assert len(opened) == 1 and "q=123" in opened[0]
