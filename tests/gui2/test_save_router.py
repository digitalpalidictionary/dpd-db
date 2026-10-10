from types import SimpleNamespace
from typing import Any

from db.models import DpdHeadword
from gui2.save_router import save_headword


class FakeDb:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def update_word_in_db(self, word: DpdHeadword) -> tuple[bool, str]:
        self.calls.append("update")
        return True, ""

    def add_word_to_db(self, word: DpdHeadword) -> tuple[bool, str]:
        self.calls.append("add")
        return True, ""


class FakeAdditions:
    def __init__(self, own_ids: set[int]) -> None:
        self.own_ids = own_ids
        self.saved: list[int] = []

    def is_not_in_additions(self, id_no: int) -> bool:
        return id_no not in self.own_ids

    def add_additions(self, word: DpdHeadword, comment: str) -> None:
        self.saved.append(word.id)


class FakeCorrections:
    def __init__(self) -> None:
        self.saved: list[int] = []

    def update_corrections(self, word: DpdHeadword, comment: str) -> None:
        self.saved.append(word.id)


def make_toolkit(primary: bool, own_ids: set[int] | None = None) -> Any:
    return SimpleNamespace(
        username_manager=SimpleNamespace(is_not_primary=lambda: not primary),
        db_manager=FakeDb(),
        additions_manager=FakeAdditions(own_ids or set()),
        corrections_manager=FakeCorrections(),
    )


def word(id_no: int) -> DpdHeadword:
    w = DpdHeadword()
    w.id = id_no
    return w


def test_primary_new_word_goes_to_db_only() -> None:
    tk = make_toolkit(primary=True)
    assert save_headword(tk, word(5), "", False) == (True, "")
    assert tk.db_manager.calls == ["add"]
    assert tk.additions_manager.saved == []
    assert tk.corrections_manager.saved == []


def test_primary_existing_word_updates_db_only() -> None:
    tk = make_toolkit(primary=True)
    assert save_headword(tk, word(5), "", True) == (True, "")
    assert tk.db_manager.calls == ["update"]
    assert tk.additions_manager.saved == []
    assert tk.corrections_manager.saved == []


def test_contributor_new_word_goes_to_additions_only() -> None:
    tk = make_toolkit(primary=False)
    assert save_headword(tk, word(9), "c", False) == (True, "")
    assert tk.additions_manager.saved == [9]
    assert tk.corrections_manager.saved == []
    assert tk.db_manager.calls == []


def test_contributor_edit_of_db_word_goes_to_corrections_only() -> None:
    tk = make_toolkit(primary=False)
    assert save_headword(tk, word(3), "c", True) == (True, "")
    assert tk.corrections_manager.saved == [3]
    assert tk.additions_manager.saved == []
    assert tk.db_manager.calls == []


def test_contributor_re_edit_of_own_addition_stays_an_addition() -> None:
    tk = make_toolkit(primary=False, own_ids={9})
    assert save_headword(tk, word(9), "c", True) == (True, "")
    assert tk.additions_manager.saved == [9]
    assert tk.corrections_manager.saved == []
    assert tk.db_manager.calls == []


def test_contributor_write_failure_returns_the_error() -> None:
    tk = make_toolkit(primary=False)

    def boom(word: DpdHeadword, comment: str) -> None:
        raise OSError("disk full")

    tk.additions_manager.add_additions = boom
    assert save_headword(tk, word(9), "c", False) == (False, "disk full")
