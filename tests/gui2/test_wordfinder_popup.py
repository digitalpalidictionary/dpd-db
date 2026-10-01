from types import SimpleNamespace
from typing import Any

from gui2.wordfinder_popup import WordFinderPopup


class _FakePage:
    def __init__(self) -> None:
        self._dialogs = SimpleNamespace(controls=[], update=lambda: None)

    def show_dialog(self, dialog: Any) -> None:
        if dialog in self._dialogs.controls:
            raise RuntimeError("Dialog is already opened")
        dialog.open = True
        self._dialogs.controls.append(dialog)

    def update(self) -> None:
        pass


def _popup() -> WordFinderPopup:
    toolkit: Any = SimpleNamespace(page=_FakePage(), wordfinder_manager=None)
    return WordFinderPopup(toolkit)


def test_second_ctrl_f_while_open_does_not_raise() -> None:
    popup = _popup()
    popup.open_popup("dhamma")
    popup.open_popup("kamma")
    assert popup.page._dialogs.controls == [popup.dialog]
    assert popup.search_field.value == "dhamma"


def test_ctrl_f_after_close_reopens() -> None:
    popup = _popup()
    popup.open_popup()
    # closed, but Flutter never reported the dismiss
    popup._handle_close(None)
    popup.open_popup("kamma")
    assert popup.dialog.open is True
    assert popup.page._dialogs.controls == [popup.dialog]
    assert popup.search_field.value == "kamma"
