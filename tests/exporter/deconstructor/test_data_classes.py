"""Tests for the deconstructor header hoist (constant header rendered once)."""

from types import SimpleNamespace

from exporter.deconstructor.data_classes import (
    DeconstructorData,
    generate_deconstructor_header,
)
from exporter.jinja2_env import get_jinja2_env


def _env():
    return get_jinja2_env("exporter/deconstructor")


def test_header_is_constant_and_repeatable() -> None:
    """The header has no per-entry variables, so it is identical every call."""
    env = _env()
    h1 = generate_deconstructor_header(env)
    h2 = generate_deconstructor_header(env)
    assert h1 == h2
    assert "<style>" in h1
    assert "dpd-css-and-fonts.css" in h1


def test_deconstructor_data_holds_only_per_entry_fields() -> None:
    """DeconstructorData no longer computes a header; it carries per-entry data."""
    row = SimpleNamespace(
        lookup_key="akataṃpi",
        deconstructor_unpack=["a + kataṃ + pi"],
    )
    data = DeconstructorData(row)  # type: ignore[arg-type]
    assert data.headword == "akataṃpi"
    assert data.deconstructions == ["a + kataṃ + pi"]
    assert hasattr(data, "today")
    assert not hasattr(data, "header")
