from types import SimpleNamespace
from typing import Any

from db.models import DpdHeadword
from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from gui2.save_router import changed_columns, save_headword


class FakeSession:
    def __init__(self, rows: dict[int, DpdHeadword]) -> None:
        self.rows = rows

    def get(self, _model: type, id_no: int) -> DpdHeadword | None:
        return self.rows.get(id_no)


class FakeDb:
    def __init__(self, rows: dict[int, DpdHeadword] | None = None) -> None:
        self.calls: list[str] = []
        self.db_session = FakeSession(rows or {})

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
        self.changed: list[list[str] | None] = []

    def update_corrections(
        self, word: DpdHeadword, comment: str, changed: list[str] | None = None
    ) -> None:
        self.saved.append(word.id)
        self.changed.append(changed)


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


def headword(id_no: int, **columns: str) -> DpdHeadword:
    w = DpdHeadword()
    w.id = id_no
    for name, value in columns.items():
        setattr(w, name, value)
    return w


def test_changed_meaning_is_listed() -> None:
    tk = make_toolkit(primary=False)
    tk.db_manager = FakeDb({7: headword(7, lemma_1="assa 1", meaning_1="horse")})

    save_headword(tk, headword(7, lemma_1="assa 1", meaning_1="mare"), "c", True)

    assert tk.corrections_manager.changed == [["meaning_1"]]


def test_untouched_empty_fields_are_not_changes() -> None:
    row = headword(7, lemma_1="assa 1")
    row.meaning_2 = None  # pyright: ignore[reportAttributeAccessIssue]
    word = headword(7, lemma_1="assa 1", meaning_2="")

    assert changed_columns(row, word) == []


def test_re_edit_of_an_own_correction_compares_with_the_db_row() -> None:
    # The earlier correction said "mare"; the contributor now sets it back to
    # the db's "horse". Against the db row that is no change at all.
    tk = make_toolkit(primary=False)
    tk.db_manager = FakeDb({7: headword(7, lemma_1="assa 1", meaning_1="horse")})
    save_headword(tk, headword(7, lemma_1="assa 1", meaning_1="mare"), "c", True)
    save_headword(tk, headword(7, lemma_1="assa 1", meaning_1="horse"), "c", True)

    assert tk.corrections_manager.changed == [["meaning_1"], []]


def test_stray_spaces_the_form_removes_are_not_changes() -> None:
    row = headword(7, sanskrit="ṭīkā ", example_1="a  b")
    word = headword(7, sanskrit="ṭīkā", example_1="a b")

    assert changed_columns(row, word) == []


def test_columns_the_form_never_supplies_are_not_changes() -> None:
    # A word built from form fields (as the Pass2 form does) never carries the
    # dates, inflection tables or frequency data, which the db row always has.
    row = headword(7, lemma_1="assa 1", meaning_1="horse")
    for column in ("created_at", "updated_at", "inflections", "freq_data", "ebt_count"):
        setattr(row, column, 5)
    word = make_dpd_headword_from_dict(
        {"id": 7, "lemma_1": "assa 1", "meaning_1": "mare"}
    )

    assert changed_columns(row, word) == ["meaning_1"]
