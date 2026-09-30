from pathlib import Path
from types import SimpleNamespace

from gui2.dpd_fields_examples import DpdExampleField


def _example_field(tmp_path: Path) -> DpdExampleField:
    toolkit = SimpleNamespace(
        paths=SimpleNamespace(example_stash_json_path=tmp_path / "stash.json"),
        speech_marks_manager=SimpleNamespace(get_speech_marks=lambda: {}),
    )
    ui = SimpleNamespace(toolkit=toolkit)
    return DpdExampleField(ui, "example_1", dpd_fields=None, toolkit=toolkit)


def test_bold_box_submits_via_key_handler_as_single_line(tmp_path: Path) -> None:
    field = _example_field(tmp_path)
    assert field.bold_field.shift_enter is True
    assert field.bold_field.max_lines == 1
