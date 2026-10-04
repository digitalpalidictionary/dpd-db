"""Tests for db_tests/single/test_verb_grammar_sync.py"""

from db_tests.single.test_verb_grammar_sync import grammar_naming, root_choice


def test_grammar_naming_drops_pass_of() -> None:
    # The chosen verb carries the kind, so "pass of" goes.
    assert (
        grammar_naming("prp of pass of anuyuñjati", "prp", "anuyuñjiyati 1")
        == "prp of anuyuñjiyati"
    )


def test_grammar_naming_keeps_na_and_suffix() -> None:
    assert (
        grammar_naming("pp of na karoti, in comps", "pp", "kāreti")
        == "pp of na kāreti, in comps"
    )


def test_grammar_naming_writes_a_kind_on_a_root() -> None:
    assert (
        grammar_naming("aor of padhaṃseti", "aor", "caus of pa √dhaṃs")
        == "aor of caus of pa √dhaṃs"
    )


def row(pos: str, grammar: str, verb_col: str, family_root: str) -> dict[str, str]:
    return {
        "pos": pos,
        "grammar_current": grammar,
        "verb_col": verb_col,
        "family_root": family_root,
    }


def test_root_choice_writes_the_kind() -> None:
    assert (
        root_choice(row("aor", "aor of padhaṃseti", "caus", "pa √dhaṃs"))
        == "aor of caus of pa √dhaṃs"
    )


def test_root_choice_reads_the_kind_from_the_grammar() -> None:
    assert (
        root_choice(row("prp", "prp of pass of anuyuñjati", "", "anu √yuj"))
        == "prp of pass of anu √yuj"
    )


def test_root_choice_refuses_two_kinds() -> None:
    assert root_choice(row("prp", "prp of kāriyati", "caus, pass", "√kar")) is None


def test_root_choice_refuses_a_negative() -> None:
    assert root_choice(row("prp", "prp of na codiyati", "pass", "√cud")) is None


def test_root_choice_leaves_a_present_verb_alone() -> None:
    assert (
        root_choice(row("pr", "pr, caus of anusuṇāti", "", "anu √su"))
        == "pr, caus of anu √su"
    )


def test_root_choice_plain_form() -> None:
    assert root_choice(row("pp", "pp of russati", "", "√rus")) == "pp of √rus"
