"""Adding a set to family_set must keep every existing set, keep the
case-insensitive English order, and never duplicate the new set."""

from scripts.fix.add_agent_nouns_set import SET_NAME, add_set


def test_empty_family_set_gets_only_the_new_set() -> None:
    assert add_set("", SET_NAME) == "agent nouns"


def test_existing_set_is_kept_and_sorted() -> None:
    assert add_set("occupations", SET_NAME) == "agent nouns; occupations"


def test_multiple_existing_sets_are_all_kept() -> None:
    assert (
        add_set("types of ascetics; types of monastics", SET_NAME)
        == "agent nouns; types of ascetics; types of monastics"
    )


def test_set_already_present_is_unchanged() -> None:
    value = "agent nouns; occupations"
    assert add_set(value, SET_NAME) == value


def test_uppercase_set_sorts_case_insensitively() -> None:
    """A plain sort puts "S" (83) before "a" (97)."""
    assert add_set("Sanskritisms", SET_NAME) == "agent nouns; Sanskritisms"
