"""The family_set sort must be case-insensitive English alphabetical order.

These tests pin the exact ordering logic shared by the gui "Add Set" field
(gui2/dpd_fields_family_set.py) and the one-off migration
(scripts/fix/sort_family_sets.py), so both stay in sync.
"""

from scripts.fix.sort_family_sets import english_sort_key, sort_family_set


def test_english_sort_key_is_case_insensitive() -> None:
    assert english_sort_key("epithets of Nibbāna") == "epithets of nibbāna"


def test_single_set_unchanged() -> None:
    assert sort_family_set("grammatical terms") == "grammatical terms"


def test_already_sorted_unchanged() -> None:
    value = "grammatical terms; prefixes"
    assert sort_family_set(value) == value


def test_pali_order_corrected_to_english_order() -> None:
    """v < s in the Pāḷi alphabet, s < v in English."""
    assert (
        sort_family_set("vaggas of Aṅguttara Nikāya 1; suttas of the Dīgha Nikāya")
        == "suttas of the Dīgha Nikāya; vaggas of Aṅguttara Nikāya 1"
    )


def test_uppercase_sorts_case_insensitively() -> None:
    assert (
        sort_family_set("epithets of Nibbāna; epithets of arahants")
        == "epithets of arahants; epithets of Nibbāna"
    )


def test_whitespace_and_empty_parts_normalised() -> None:
    assert sort_family_set("  letters ; grammatical terms ;  ") == (
        "grammatical terms; letters"
    )
