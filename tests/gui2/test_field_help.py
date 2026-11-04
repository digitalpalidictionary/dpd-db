import ast
import json
from types import SimpleNamespace
from collections.abc import Iterator
from pathlib import Path

import flet as ft
import pytest

import gui2.dpd_fields
import gui2.field_help
from gui2.dpd_fields import DpdFields
from gui2.dpd_fields_classes import DpdTextField
from gui2.field_help import (
    HELP_PATH,
    MAX_HELP_LENGTH,
    _cached_help,
    get_field_help,
    load_help_file,
    validate_field_help,
)


def field_config_names() -> list[str]:
    """The FieldConfig names declared in DpdFields.__init__, read without running it."""
    tree = ast.parse(Path("gui2/dpd_fields.py").read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "DpdFields":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for call in ast.walk(item):
                        if (
                            isinstance(call, ast.Call)
                            and isinstance(call.func, ast.Name)
                            and call.func.id == "FieldConfig"
                        ):
                            first = call.args[0]
                            assert isinstance(first, ast.Constant)
                            assert isinstance(first.value, str)
                            names.append(first.value)
    return names


@pytest.fixture
def names() -> list[str]:
    return field_config_names()


@pytest.fixture
def good(names: list[str]) -> dict[str, object]:
    return {name: f"Help for {name}." for name in names}


@pytest.fixture(autouse=True)
def _fresh_cache() -> Iterator[None]:
    _cached_help.cache_clear()
    yield
    _cached_help.cache_clear()


def test_finds_all_fifty_field_names(names: list[str]) -> None:
    assert len(names) == 50
    assert len(set(names)) == 50


def test_good_texts_have_no_problems(good: dict[str, object], names: list[str]) -> None:
    assert validate_field_help(good, names) == []


def test_missing_key_is_reported(good: dict[str, object], names: list[str]) -> None:
    del good["lemma_1"]
    problems = validate_field_help(good, names)
    assert problems and "lemma_1" in problems[0]


def test_renamed_key_is_reported(good: dict[str, object], names: list[str]) -> None:
    good["lemma_one"] = good.pop("lemma_1")
    problems = validate_field_help(good, names)
    assert any("lemma_1" in p for p in problems)
    assert any("lemma_one" in p for p in problems)


def test_empty_text_is_reported(good: dict[str, object], names: list[str]) -> None:
    good["pos"] = "  "
    problems = validate_field_help(good, names)
    assert problems and "pos" in problems[0]


def test_text_over_the_limit_is_reported(
    good: dict[str, object], names: list[str]
) -> None:
    good["pos"] = "x" * (MAX_HELP_LENGTH + 1)
    problems = validate_field_help(good, names)
    assert problems and "pos" in problems[0]


def test_text_at_the_limit_is_good(good: dict[str, object], names: list[str]) -> None:
    good["pos"] = "x" * MAX_HELP_LENGTH
    assert validate_field_help(good, names) == []


def test_newline_is_allowed(good: dict[str, object], names: list[str]) -> None:
    good["pos"] = "one\n\ntwo"
    assert validate_field_help(good, names) == []


def test_add_key_is_reported(good: dict[str, object], names: list[str]) -> None:
    good["lemma_1_add"] = "Help."
    problems = validate_field_help(good, names)
    assert problems and "lemma_1_add" in problems[0]


def test_non_string_value_is_reported(
    good: dict[str, object], names: list[str]
) -> None:
    good["pos"] = 5
    problems = validate_field_help(good, names)
    assert problems and "pos" in problems[0]


def test_missing_file_gives_empty_dict(tmp_path: Path) -> None:
    assert load_help_file(tmp_path / "none.json") == {}


def test_malformed_json_gives_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "help.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_help_file(path) == {}


def test_list_at_top_gives_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "help.json"
    path.write_text('["a"]', encoding="utf-8")
    assert load_help_file(path) == {}


def test_non_string_value_gives_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "help.json"
    path.write_text('{"pos": 5}', encoding="utf-8")
    assert load_help_file(path) == {}


def test_good_file_is_read_as_utf8(tmp_path: Path) -> None:
    path = tmp_path / "help.json"
    path.write_text(json.dumps({"pos": "nāma"}, ensure_ascii=False), encoding="utf-8")
    assert load_help_file(path) == {"pos": "nāma"}


def test_get_field_help_reads_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "help.json"
    path.write_text('{"pos": "part of speech"}', encoding="utf-8")
    monkeypatch.setattr(gui2.field_help, "HELP_PATH", path)
    assert get_field_help("pos") == "part of speech"
    assert get_field_help("nothing") is None


def test_get_field_help_without_a_file_gives_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gui2.field_help, "HELP_PATH", tmp_path / "none.json")
    assert get_field_help("pos") is None


def test_row_label_gets_a_tooltip_from_the_help_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gui2.dpd_fields,
        "get_field_help",
        lambda name: "help for lemma_1" if name == "lemma_1" else None,
    )
    fake_self = SimpleNamespace(
        fields={
            "lemma_1": DpdTextField(name="lemma_1"),
            "x": DpdTextField(name="x"),
        }
    )

    row = DpdFields._create_field_row(fake_self, "lemma_1", False)  # type: ignore[arg-type]
    tooltip = row.controls[0].tooltip
    assert isinstance(tooltip, ft.Tooltip)
    assert tooltip.message == "help for lemma_1"
    assert tooltip.wait_duration == 500
    assert tooltip.size_constraints is not None
    assert tooltip.size_constraints.max_width == 360

    row = DpdFields._create_field_row(fake_self, "x", False)  # type: ignore[arg-type]
    assert row.controls[0].tooltip is None


def test_real_help_file_matches_the_field_names(names: list[str]) -> None:
    help_texts = load_help_file(HELP_PATH)
    assert help_texts, "gui2/field_help.json did not load"
    assert validate_field_help(dict(help_texts), names) == []


def test_get_field_help_reads_the_file_only_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "help.json"
    path.write_text('{"pos": "first"}', encoding="utf-8")
    monkeypatch.setattr(gui2.field_help, "HELP_PATH", path)
    assert get_field_help("pos") == "first"

    path.write_text('{"pos": "second"}', encoding="utf-8")
    assert get_field_help("pos") == "first"
