"""Characterization tests for exporter/anki/anki_updater.py.

Covers pure logic only — no live Anki collection. Uses SimpleNamespace stubs
for Note/Card objects and a handwritten fake collection to verify the delete
branch calls col.remove_notes() with the correct note id.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from exporter.anki.anki_updater import (
    deck_selector,
    make_data_dict,
    make_search_query,
    update_family_note,
    update_note_values,
)

FIXTURE_PATH = Path(__file__).parent / "test_anki_updater_fixtures.json"


def _fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# make_search_query
# ---------------------------------------------------------------------------


def test_make_search_query_single() -> None:
    assert make_search_query(["Vocab"]) == 'deck:"Vocab"'


def test_make_search_query_multiple() -> None:
    result = make_search_query(["Vocab", "Commentary", "Pass1"])
    assert result == 'deck:"Vocab" or deck:"Commentary" or deck:"Pass1"'


# ---------------------------------------------------------------------------
# deck_selector — frozen against real DB examples
# ---------------------------------------------------------------------------


def test_deck_selector_all_cases() -> None:
    fixtures = _fixtures()
    for case_name, data in fixtures.items():
        stub = SimpleNamespace(
            meaning_1=data["meaning_1"],
            source_1=data["source_1"],
            origin=data["origin"],
        )
        result = deck_selector(stub)
        expected = data["expected_deck"]
        assert result == expected, (
            f"deck_selector case {case_name!r}: expected {expected!r}, got {result!r}"
        )


def test_deck_selector_no_deck_returns_none() -> None:
    stub = SimpleNamespace(meaning_1="", source_1="", origin="manual")
    assert deck_selector(stub) is None


# ---------------------------------------------------------------------------
# make_data_dict — re-keying by string dpd_id
# ---------------------------------------------------------------------------


def _fake_note(anki_id: int, dpd_id: str) -> SimpleNamespace:
    n = SimpleNamespace()
    n.id = anki_id
    n.mid = 1
    n.guid = f"guid_{anki_id}"
    n.fields = [dpd_id, "lemma", "pos"]
    return n


def test_make_data_dict_rekeys_by_string_dpd_id() -> None:
    """After re-keying, data is accessible by string dpd_id, not int."""
    note = _fake_note(anki_id=9876543210, dpd_id="42")
    result = make_data_dict([note], [])
    assert "42" in result
    assert 42 not in result  # int key must NOT be present


def test_make_data_dict_links_card_to_note() -> None:
    note = _fake_note(anki_id=9876543210, dpd_id="99")
    card = SimpleNamespace(id=111, nid=9876543210, did=5)
    result = make_data_dict([note], [card])
    assert result["99"]["cid"] == 111
    assert result["99"]["did"] == 5


def test_make_data_dict_missing_card_leaves_none() -> None:
    note = _fake_note(anki_id=9876543210, dpd_id="77")
    result = make_data_dict([note], [])
    assert result["77"]["cid"] is None
    assert result["77"]["did"] is None


# ---------------------------------------------------------------------------
# update_note_values — is_updated logic
# ---------------------------------------------------------------------------


def _fake_col_for_note_update() -> SimpleNamespace:
    return SimpleNamespace()


def _stub_headword(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=1,
        lemma_1="test",
        lemma_2="",
        pos="n",
        grammar="",
        derived_from="",
        neg="",
        verb="",
        trans="",
        plus_case="",
        meaning_1="test meaning",
        meaning_lit="",
        non_ia="",
        sanskrit="",
        root_clean="",
        root_sign="",
        root_base="",
        root_key=None,
        family_root="",
        family_word="",
        family_compound="",
        family_idioms="",
        construction="",
        derivative="",
        suffix="",
        phonetic="",
        compound_type="",
        compound_construction="",
        non_root_in_comps="",
        source_1="SN1.1",
        sutta_1="sutta",
        example_1="example",
        source_2="",
        sutta_2="",
        example_2="",
        antonym="",
        synonym="",
        var_phonetic="",
        var_text="",
        variant="",
        commentary="",
        notes="",
        cognate="",
        family_set="",
        link="",
        stem="",
        pattern="",
        meaning_2="",
        origin="",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class _FakeNote:
    """Minimal Anki Note stub supporting [] read/write without touching fields."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = list(fields)
        self._data: dict[str, str] = {}

    def __setitem__(self, key: str, val: str) -> None:
        self._data[key] = val  # does NOT mutate self.fields

    def __getitem__(self, key: str) -> str:
        return self._data.get(key, "")


class _FakeFamilyNote:
    """Note stub where [] assignments DO mutate fields (Front=0, Back=1)."""

    def __init__(self, front: str, back: str) -> None:
        self.fields = [front, back]

    def __setitem__(self, key: str, val: str) -> None:
        if key == "Front":
            self.fields[0] = val
        elif key == "Back":
            self.fields[1] = val

    def __getitem__(self, key: str) -> str:
        return self.fields[0] if key == "Front" else self.fields[1]


def test_update_note_values_returns_bool_not_none() -> None:
    """is_updated must be a bool, never None."""
    col = _fake_col_for_note_update()
    hw = _stub_headword()
    note = _FakeNote(["1", "test", "n", "", "SN1.1"])
    _note, is_updated = update_note_values(col, note, hw)
    assert isinstance(is_updated, bool)


# ---------------------------------------------------------------------------
# update_family_note — is_updated logic
# ---------------------------------------------------------------------------


def test_update_family_note_unchanged_returns_false() -> None:
    note = _FakeFamilyNote("key1", "<b>html</b>")
    _note, is_updated = update_family_note(note, ("key1", "<b>html</b>"))
    assert is_updated is False


def test_update_family_note_changed_returns_true() -> None:
    note = _FakeFamilyNote("key1", "<b>old</b>")
    _note, is_updated = update_family_note(note, ("key1", "<b>new</b>"))
    assert is_updated is True


# ---------------------------------------------------------------------------
# Delete branch — col.remove_notes() must be called with string key lookup
# ---------------------------------------------------------------------------


def test_delete_branch_calls_remove_notes() -> None:
    """
    Headword with no deck (deck_selector→None) and matching string key in
    data_dict must trigger col.remove_notes([note.id]).
    After the fix: id (str) is used, not i.id (int).
    """
    from exporter.anki.anki_updater import update_from_db

    hw = SimpleNamespace(
        id=42,
        meaning_1="",
        source_1="",
        origin="manual",
        lemma_1="test",
    )

    fake_note = SimpleNamespace(id=777)
    data_dict: dict = {
        "42": {
            "note": fake_note,
            "dpd_id": "42",
            "nid": 9876543210,
            "cid": 1,
            "did": 5,
            "card": SimpleNamespace(id=1, nid=9876543210, did=5),
            "mid": 1,
            "guid": "g",
        }
    }

    removed_ids: list[int] = []

    fake_col = SimpleNamespace(
        remove_notes=lambda ids: removed_ids.extend(ids),
        update_notes=lambda notes: None,
        find_notes=lambda q: [],
    )

    update_from_db([hw], fake_col, data_dict, {5: "Vocab"}, {})

    assert removed_ids == [777], (
        f"expected remove_notes([777]), got remove_notes({removed_ids})"
    )


def test_delete_branch_int_key_does_not_fire() -> None:
    """
    Guard against regression: int key lookup must NOT match the string-keyed
    data_dict. This confirms the original bug was real.
    """
    note = _fake_note(anki_id=9876543210, dpd_id="42")
    result = make_data_dict([note], [])
    # int 42 must NOT be a key — only "42" (string) should be
    assert 42 not in result
    assert "42" in result
