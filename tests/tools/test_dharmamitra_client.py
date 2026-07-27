"""Tests for the Dharmamitra API client (tools/dharmamitra_client.py).

All requests.post calls are mocked -- no real network calls in this suite.
"""

from typing import Any

import pytest
import requests

import tools.dharmamitra_client as dharmamitra_client


class _FakeResponse:
    def __init__(self, status_code: int, json_data: Any) -> None:
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> Any:
        return self._json_data


def test_get_contextual_gloss_returns_translation_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(200, {"translation": "gloss text"})

    monkeypatch.setattr(dharmamitra_client.requests, "post", fake_post)

    result = dharmamitra_client.get_contextual_gloss("sentence", "lemma")

    assert result == "gloss text"


def test_get_contextual_gloss_returns_none_on_non_200_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(500, {})

    monkeypatch.setattr(dharmamitra_client.requests, "post", fake_post)

    result = dharmamitra_client.get_contextual_gloss("sentence", "lemma")

    assert result is None


def test_get_contextual_gloss_returns_none_on_request_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(dharmamitra_client.requests, "post", fake_post)

    result = dharmamitra_client.get_contextual_gloss("sentence", "lemma")

    assert result is None
