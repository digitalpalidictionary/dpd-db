"""An approved hyphenation comes back only when the text holds another form."""

import pytest

from db_tests.single.add_hyphenations import Data, has_bold_tag_inside

CLEAN = "thambhabhittipādussāpanādinā"
APPROVED = "thambha-bhittipād'ussāpan'ādinā"
DRIFTED = "thambhabhitti-pādussāpanādinā"


def make_data(long_words: dict[str, set[int]], exceptions: dict[str, str]) -> Data:
    # Data() loads the whole db, so build it without __init__
    data = Data.__new__(Data)
    data.hyphenations_dict = {"max_length": 20, "exceptions": exceptions}
    data.long_words_dict = long_words
    data.clean_words_dict = {w: ids for w, ids in long_words.items()}
    return data


def test_approved_form_alone_is_skipped() -> None:
    data = make_data({APPROVED: {1}}, {CLEAN: APPROVED})
    assert data.find_variations() == {}


def test_other_form_brings_the_word_back_with_approved_listed() -> None:
    data = make_data({APPROVED: {1}, DRIFTED: {2}}, {CLEAN: APPROVED})
    variations = data.find_variations()
    assert variations[CLEAN]["dirty_words"] == sorted([APPROVED, DRIFTED])


APOSTROPHE = "thambhabhittipād'ussāpanādinā"


def test_apostrophe_form_of_an_approved_word_brings_it_back() -> None:
    data = make_data({APPROVED: {1}, APOSTROPHE: {2}}, {CLEAN: APPROVED})
    variations = data.find_variations()
    assert variations[CLEAN]["dirty_words"] == sorted([APPROVED, APOSTROPHE])


def test_apostrophe_form_of_an_unapproved_word_is_not_listed_alone() -> None:
    data = make_data({APOSTROPHE: {2}}, {})
    assert data.find_variations() == {}


def test_all_marked_forms_are_listed() -> None:
    data = make_data({DRIFTED: {1}, APOSTROPHE: {2}}, {})
    variations = data.find_variations()
    assert variations[CLEAN]["dirty_words"] == sorted([DRIFTED, APOSTROPHE])


def test_new_word_is_listed_without_approved_form() -> None:
    data = make_data({DRIFTED: {2}}, {})
    assert data.find_variations()[CLEAN]["dirty_words"] == [DRIFTED]


def make_auto_data(
    monkeypatch: pytest.MonkeyPatch,
    words: set[str],
    exceptions: dict[str, str],
) -> Data:
    # a real save would overwrite add_hyphenations.json
    monkeypatch.setattr(Data, "save_hyphenations_dict", lambda self: None)
    data = make_data({w: {1} for w in words if "-" in w}, exceptions)
    data.clean_words_dict = {w: {1} for w in words}
    data.variations_dict = data.find_variations()
    data.variations_list = list(data.variations_dict.items())
    return data


def test_single_marked_form_is_approved(monkeypatch: pytest.MonkeyPatch) -> None:
    data = make_auto_data(monkeypatch, {APPROVED}, {})
    assert data.auto_approve_single_forms() == 1
    assert data.exceptions == {CLEAN: APPROVED}
    assert data.variations_list == []


def test_two_marked_forms_are_not_approved(monkeypatch: pytest.MonkeyPatch) -> None:
    data = make_auto_data(monkeypatch, {APPROVED, DRIFTED}, {})
    assert data.auto_approve_single_forms() == 0
    assert data.exceptions == {}
    assert [clean for clean, _ in data.variations_list] == [CLEAN]


def test_marked_and_plain_form_approves_the_marked_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = make_auto_data(monkeypatch, {APPROVED, CLEAN}, {})
    assert data.auto_approve_single_forms() == 1
    assert data.exceptions == {CLEAN: APPROVED}
    assert data.variations_list == []


def test_existing_approval_is_not_overwritten(monkeypatch: pytest.MonkeyPatch) -> None:
    data = make_auto_data(monkeypatch, {DRIFTED, CLEAN}, {CLEAN: APPROVED})
    assert data.auto_approve_single_forms() == 0
    assert data.exceptions == {CLEAN: APPROVED}


def test_bold_tag_inside_the_word_is_found() -> None:
    text = "x sarīran</b>'ti-ādigāthāyo pana"
    assert has_bold_tag_inside(text, "sarīran'ti-ādigāthāyo")


def test_bold_tag_around_the_word_is_not_inside() -> None:
    text = "x <b>sarīran'ti-ādigāthāyo</b> pana"
    assert not has_bold_tag_inside(text, "sarīran'ti-ādigāthāyo")


def test_form_without_tags_is_not_inside() -> None:
    assert not has_bold_tag_inside("sarīran'ti-ādigāthāyo", "sarīran'ti-ādigāthāyo")
    assert not has_bold_tag_inside("nothing here", "sarīran'ti-ādigāthāyo")
