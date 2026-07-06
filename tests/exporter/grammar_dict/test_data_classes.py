"""Tests for the grammar-dict header hoist (constant header rendered once)."""

from types import SimpleNamespace

from exporter.grammar_dict.data_classes import GrammarData, generate_grammar_header
from exporter.jinja2_env import get_jinja2_env


def _env():
    return get_jinja2_env("exporter/grammar_dict")


def test_header_is_constant_and_repeatable() -> None:
    """The header has no per-entry variables, so it is identical every call."""
    env = _env()
    h1 = generate_grammar_header(env)
    h2 = generate_grammar_header(env)
    assert h1 == h2
    assert "<style>" in h1


def test_grammar_data_uses_injected_header() -> None:
    """GrammarData stores the header it is given and no longer builds its own."""
    row = SimpleNamespace(
        lookup_key="dhammassa",
        grammar_unpack=[("dhamma", "masc", "gen sg")],
    )
    data = GrammarData(row, "HEADER_SENTINEL")  # type: ignore[arg-type]
    assert data.header == "HEADER_SENTINEL"
    assert data.headword == "dhammassa"
    assert data.rows == [
        {"pos": "masc", "components": ["gen", "sg", ""], "headword": "dhamma"}
    ]
