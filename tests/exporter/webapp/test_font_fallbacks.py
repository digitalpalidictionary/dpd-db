"""The local fallback fonts in home.css must keep matching the web fonts."""

import re
from pathlib import Path

import pytest

STATIC = Path("exporter/webapp/static")
# ascent and descent as a share of the font size, from each font's hhea table
WEB_FONT_METRICS = {
    "Inter Arial": (0.96875, 0.24121),
    "Inter Roboto": (0.96875, 0.24121),
    "Serif Georgia": (1.036, 0.335),
    "Serif Noto": (1.036, 0.335),
}


def fallback_faces():
    css = (STATIC / "home.css").read_text(encoding="utf-8")
    return re.findall(r"@font-face \{(.*?)\}", css, flags=re.DOTALL)


def descriptor(face, name):
    return re.search(rf"{name}: \"?([^\";]+)\"?;", face).group(1)


def test_every_fallback_family_has_regular_and_bold():
    weights = {}
    for face in fallback_faces():
        family = descriptor(face, "font-family")
        weights.setdefault(family, set()).add(descriptor(face, "font-weight"))
    assert weights == {family: {"400", "700"} for family in WEB_FONT_METRICS}


@pytest.mark.parametrize("face", fallback_faces())
def test_overrides_are_web_font_metrics_divided_by_size_adjust(face):
    ascent, descent = WEB_FONT_METRICS[descriptor(face, "font-family")]
    size_adjust = float(descriptor(face, "size-adjust").rstrip("%")) / 100
    ascent_override = float(descriptor(face, "ascent-override").rstrip("%")) / 100
    descent_override = float(descriptor(face, "descent-override").rstrip("%")) / 100
    assert ascent_override == pytest.approx(ascent / size_adjust, abs=0.0002)
    assert descent_override == pytest.approx(descent / size_adjust, abs=0.0002)


def rule(css, selector):
    match = re.search(rf"(?m)^{re.escape(selector)} \{{(.*?)\}}", css, flags=re.DOTALL)
    return match.group(1)


def test_serif_setting_only_reaches_the_main_search_box_and_button():
    css = (STATIC / "home.css").read_text(encoding="utf-8")
    # Bold Definitions and Translations boxes share .search-box and stay sans.
    assert "var(--font-sans)" in rule(css, ".search-box")
    assert "var(--font-body)" in rule(css, "#search-button")
    assert re.search(r"#search-box,\s*#search-button\s*\{", css)
