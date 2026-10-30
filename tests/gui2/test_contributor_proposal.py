from gui2.contributor_proposal import proposal_fields


def test_addition_drops_the_id_and_keeps_the_rest() -> None:
    entry = {"id": 10_000_001, "lemma_1": "ṭīkā 1", "comment": "c"}
    assert proposal_fields(entry, "addition") == {"lemma_1": "ṭīkā 1", "comment": "c"}


def test_correction_with_changed_keeps_only_those_fields() -> None:
    entry = {
        "id": 7,
        "lemma_1": "assa 1",
        "meaning_1": "mare",
        "comment": "c",
        "_changed": ["meaning_1"],
    }
    assert proposal_fields(entry, "correction") == {"meaning_1": "mare"}


def test_correction_without_changed_keeps_everything() -> None:
    entry = {"id": 7, "lemma_1": "assa 1", "meaning_1": "mare", "comment": "c"}
    assert proposal_fields(entry, "correction") == entry


def test_correction_with_empty_changed_keeps_nothing() -> None:
    assert proposal_fields({"id": 7, "_changed": []}, "correction") == {}


def test_the_entry_itself_is_not_changed() -> None:
    entry = {"id": 1, "lemma_1": "a"}
    proposal_fields(entry, "addition")
    assert entry == {"id": 1, "lemma_1": "a"}
