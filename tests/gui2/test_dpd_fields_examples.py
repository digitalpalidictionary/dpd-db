from pathlib import Path
from types import SimpleNamespace

from gui2.dpd_fields_examples import DpdExampleField
from gui2.example_stash_manager import ExampleStashManager


def _toolkit(tmp_path: Path) -> SimpleNamespace:
    toolkit = SimpleNamespace(
        paths=SimpleNamespace(example_stash_json_path=tmp_path / "stash.json"),
        speech_marks_manager=SimpleNamespace(get_speech_marks=lambda: {}),
    )
    toolkit.example_stash_manager = ExampleStashManager(toolkit)  # type: ignore[arg-type]
    return toolkit


def _example_field(
    tmp_path: Path, toolkit: SimpleNamespace | None = None, name: str = "example_1"
) -> DpdExampleField:
    toolkit = toolkit or _toolkit(tmp_path)
    ui = SimpleNamespace(toolkit=toolkit)
    return DpdExampleField(ui, name, dpd_fields=None, toolkit=toolkit)


def test_both_example_fields_share_one_stash(tmp_path: Path) -> None:
    toolkit = _toolkit(tmp_path)
    field_1 = _example_field(tmp_path, toolkit, "example_1")
    field_2 = _example_field(tmp_path, toolkit, "example_2")

    field_1.stash_manager.stash_shared_example("DN1", "sutta", "example")
    # a blur-save from the other box must not wipe the stash
    field_2.stash_manager.last_example = ("MN1", "sutta2", "other")

    assert field_2.stash_manager.reload_shared_example() == ("DN1", "sutta", "example")
    assert ExampleStashManager(toolkit).reload_shared_example() == (  # type: ignore[arg-type]
        "DN1",
        "sutta",
        "example",
    )


def test_bold_box_submits_via_key_handler_as_single_line(tmp_path: Path) -> None:
    field = _example_field(tmp_path)
    assert field.bold_field.shift_enter is True
    assert field.bold_field.max_lines == 1


def _open_tools(field: DpdExampleField) -> None:
    field._search_row.visible = True
    field._actions_row.visible = True


def test_bold_box_blur_keeps_tools_open(tmp_path: Path) -> None:
    field = _example_field(tmp_path)
    _open_tools(field)
    field.get_fields = lambda: (  # type: ignore[method-assign]
        SimpleNamespace(value=""),
        SimpleNamespace(value=""),
        SimpleNamespace(value=""),
    )

    field._handle_last_control_blur(None)  # type: ignore[arg-type]

    assert field._search_row.visible is True
    assert field._actions_row.visible is True


def test_collapse_tools_hides_both_rows(tmp_path: Path) -> None:
    field = _example_field(tmp_path)
    _open_tools(field)
    field._toggle_tools_visibility = lambda e: (  # type: ignore[method-assign]
        setattr(field._search_row, "visible", False),
        setattr(field._actions_row, "visible", False),
    )

    field.collapse_tools()

    assert field._search_row.visible is False
    assert field._actions_row.visible is False


def test_focusing_another_field_collapses_example_tools(tmp_path: Path) -> None:
    from gui2.dpd_fields import DpdFields

    example = _example_field(tmp_path)
    _open_tools(example)
    example._toggle_tools_visibility = lambda e: (  # type: ignore[method-assign]
        setattr(example._search_row, "visible", False),
        setattr(example._actions_row, "visible", False),
    )
    fake_self = SimpleNamespace(fields={"example_1": example})
    seen: list[object] = []

    handler = DpdFields._collapse_example_tools_on_focus(
        fake_self,  # type: ignore[arg-type]
        seen.append,
    )
    handler("focus-event")  # type: ignore[arg-type]

    assert example._search_row.visible is False
    assert seen == ["focus-event"]


def test_compound_construction_focus_runs_the_shared_on_focus(
    monkeypatch,
) -> None:
    from gui2.dpd_fields_compound_construction import DpdCompoundConstructionField

    seen: list[object] = []
    dpd_fields = SimpleNamespace(
        get_field=lambda name: SimpleNamespace(value=""),
    )
    field = DpdCompoundConstructionField(
        SimpleNamespace(),
        "compound_construction",
        dpd_fields,
        on_focus=seen.append,
    )
    monkeypatch.setattr(
        DpdCompoundConstructionField,
        "page",
        SimpleNamespace(update=lambda: None),
        raising=False,
    )
    event = SimpleNamespace(control=field.compound_construction_field)

    field.compound_construction_focus(event)  # type: ignore[arg-type]

    assert seen == [event]
