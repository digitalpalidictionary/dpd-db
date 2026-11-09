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


def test_asleep_page_still_has_the_wake_time_placeholder() -> None:
    # Task 5.5 fills N from the measured wake times and flips this assertion.
    text = (PAGES / "asleep.html").read_text(encoding="utf-8")

    assert "N seconds" in text
    assert "Wake the editor" in text


def test_offline_page_button_says_try_again() -> None:
    assert "Try again" in (PAGES / "offline.html").read_text(encoding="utf-8")
