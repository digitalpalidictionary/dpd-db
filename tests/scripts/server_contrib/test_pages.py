from pathlib import Path

import pytest

PAGES = Path("scripts/server_contrib/pages")
USER_RULE = "^[a-z][a-z0-9_]{0,31}$"

HEADINGS = {
    "asleep.html": "The editor is asleep",
    "offline.html": "The editor is not running right now",
}


@pytest.mark.parametrize("name", HEADINGS)
def test_page_is_self_contained_and_has_its_heading(name: str) -> None:
    text = (PAGES / name).read_text(encoding="utf-8")

    assert "http" not in text
    assert USER_RULE in text
    assert f"<h1>{HEADINGS[name]}</h1>" in text
    assert "F5" not in text


def test_asleep_page_states_the_measured_wake_time() -> None:
    # Median of three wake times on the server (18.1, 18.3 and 59.6 s) is
    # 18.3 s, rounded up to 20. The 59.6 s start was cold, so 20 is typical.
    text = (PAGES / "asleep.html").read_text(encoding="utf-8")

    assert "N seconds" not in text
    assert "Waking takes about 20 seconds" in text
    assert "Wake the editor" in text


def test_offline_page_has_no_visible_button_until_the_editor_answers() -> None:
    text = (PAGES / "offline.html").read_text(encoding="utf-8")

    assert 'id="go" href="/" hidden>Open the editor</a>' in text
    # The page's own CSS sets display on the button, which beats the hidden
    # attribute unless this rule is there.
    assert "[hidden] { display: none !important; }" in text
    assert "setInterval(check, 15000)" in text
    assert "setTimeout(check, 3000)" in text
    assert "[502, 503, 504]" in text
    assert "Try again" not in text


def test_asleep_page_button_is_visible_at_once() -> None:
    text = (PAGES / "asleep.html").read_text(encoding="utf-8")

    assert "hidden" not in text
    assert "fetch(" not in text
