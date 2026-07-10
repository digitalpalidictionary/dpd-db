import pytest

from db.models import DpdHeadword
from gui2.dpd_fields_functions import (
    clean_construction_line1,
    clean_lemma_1,
    clean_root,
    clean_text,
    find_stem_pattern,
    increment_lemma_1,
    make_compound_construction_from_headword,
    make_construction,
    make_dpd_headword_from_dict,
    make_lemma_2,
    remove_bold_tags,
    remove_brackets,
)


class TestRemoveBrackets:
    def test_bracket_before_fullstop_leaves_no_space(self):
        text = "atthi c'ev'ettha uttarikaraṇīyan'ti [imassa anantaraṃ pāṭho dissati]."
        assert remove_brackets(text) == "atthi c'ev'ettha uttarikaraṇīyan'ti."

    def test_bracket_before_comma_leaves_no_space(self):
        assert remove_brackets("foo [note] , bar baz.") == "foo, bar baz."

    def test_leading_bracket_leaves_no_leading_space(self):
        assert remove_brackets("[ārādhanaṃ] pubbakaraṇa samāpetvā.") == (
            "pubbakaraṇa samāpetvā."
        )

    def test_whole_string_bracket_becomes_empty(self):
        assert remove_brackets("[pajānāti aṭṭhakathā oloketabbā]") == ""

    def test_interior_bracket_keeps_single_separating_space(self):
        assert remove_brackets("word [x] more text.") == "word more text."

    def test_ellipsis_spacing_preserved(self):
        assert remove_brackets("evaṃ … pe … gacchati.") == "evaṃ … pe … gacchati."

    def test_missing_space_after_punctuation_added(self):
        assert remove_brackets("vedayati,visaṃyutto naṃ.") == (
            "vedayati, visaṃyutto naṃ."
        )

    def test_decimal_reference_not_split(self):
        text = "siyā evam'assa (ma. ni. 1.55) evaṃ paresaṃ."
        assert remove_brackets(text) == text

    def test_messy_spacing_normalised(self):
        assert remove_brackets("evaṃ  ,  taṃ  .  gacchati  ,bar.") == (
            "evaṃ, taṃ. gacchati, bar."
        )

    def test_newlines_preserved(self):
        text = "first line.\nsecond line [note] here.\nthird line"
        assert remove_brackets(text) == ("first line.\nsecond line here.\nthird line")

    def test_trailing_space_before_newline_trimmed(self):
        assert remove_brackets("word [x]\nnext") == "word\nnext"

    def test_leading_space_after_newline_trimmed(self):
        assert remove_brackets("word\n [x] next") == "word\nnext"


class TestCleanLemma1:
    def test_strips_trailing_number(self):
        assert clean_lemma_1("karoti 1") == "karoti"

    def test_leaves_lemma_without_number_unchanged(self):
        assert clean_lemma_1("karoti") == "karoti"


class TestIncrementLemma1:
    def test_increments_trailing_digit(self):
        assert increment_lemma_1("karoti 1") == "karoti 2"

    def test_increments_double_digit_rollover(self):
        assert increment_lemma_1("karoti 9") == "karoti 10"

    def test_appends_2_when_no_trailing_digit(self):
        assert increment_lemma_1("karoti") == "karoti 2"


class TestCleanRoot:
    def test_strips_trailing_number(self):
        assert clean_root("√kar 1") == "√kar"


class TestCleanConstructionLine1:
    def test_keeps_only_first_line(self):
        assert (
            clean_construction_line1("saṃ + √kar > karo\nsecond line here")
            == "saṃ + √kar "
        )


class TestMakeLemma2:
    def test_masc_ending_a_becomes_o(self):
        assert make_lemma_2("putta 1", "masc", "sg") == "putto"

    def test_masc_ending_ar_becomes_a(self):
        assert make_lemma_2("satthar", "masc", "sg") == "satthā"

    def test_masc_other_ending_unchanged(self):
        assert make_lemma_2("isi", "masc", "sg") == "isi"

    def test_nt_gets_niggahita_suffix(self):
        assert make_lemma_2("citta", "nt", "sg") == "cittaṃ"

    def test_pl_in_grammar_short_circuits_masc_logic(self):
        assert make_lemma_2("puttā", "masc", "pl") == "puttā"

    def test_other_pos_returns_lemma_clean(self):
        assert make_lemma_2("kata", "pp", "sg") == "kata"


class TestMakeConstruction:
    def test_root_with_no_base(self):
        assert make_construction("karoti", "pr", "", "√kar", "", "√kar") == "√kar + "

    def test_root_with_neg_prefix(self):
        assert (
            make_construction("akaroti", "pr", "neg", "√kar", "", "√kar")
            == "na + √kar + "
        )

    def test_root_with_base_substitutes_root_family(self):
        # root_base carries a "prefix > form (meaning)" shape; the trailing
        # "(meaning)" and leading "prefix > " are stripped, then the result
        # replaces the "√..." tail of root_family.
        assert (
            make_construction(
                "saṅkaroti",
                "pr",
                "",
                "√kar",
                "saṃ + kar > karo (does)",
                "saṃ √kar",
            )
            == "saṃ + karo + "
        )

    def test_compound_with_sutta_suffix_splits(self):
        assert (
            make_construction("dhammavinayasutta", "nt comp", "", "", "", "")
            == "dhammavinaya + sutta"
        )

    def test_compound_without_special_suffix_unchanged(self):
        assert make_construction("gocara", "nt comp", "", "", "", "") == "gocara"

    def test_non_compound_with_vagga_suffix_splits(self):
        assert make_construction("mahāvagga", "nt", "", "", "", "") == "mahā + vagga"

    def test_non_compound_non_root_unchanged(self):
        assert make_construction("citta", "nt", "", "", "", "") == "citta"


class TestFindStemPattern:
    """Characterizes the current stem/pattern lookup table.

    Some POS branches are unreachable given the elif ordering (a more
    general ending is checked earlier and always wins) — see the
    `dead branch` cases below, which assert the ACTUAL current output,
    not the output the unreachable branch would have produced.
    NOTICED — NOT TOUCHING: gui2/dpd_fields_functions.py find_stem_pattern
    masc "rāja masc" (~line 157) and fem "mātar fem" (~line 187) branches
    are unreachable dead code (a broader endswith check earlier in the
    same elif chain always matches first).
    """

    @pytest.mark.parametrize(
        ("pos", "grammar", "lemma_1", "expected"),
        [
            ("adj", "", "gandhaka", ("gandh", "aka adj")),
            ("adj", "", "sundara", ("sundar", "a adj")),
            ("adj", "", "setthi", ("setth", "i adj")),
            ("adj", "", "nadī", ("nad", "ī adj")),
            ("adj", "", "sant", ("s", "ant adj")),
            ("adj", "", "garu", ("gar", "u adj")),
            ("adj", "", "vadhū", ("vadh", "ū adj")),
            ("masc", "", "putta", ("putt", "a masc")),
            ("masc", "", "isi", ("is", "i masc")),
            ("masc", "", "sāmī", ("sām", "ī masc")),
            ("masc", "", "bhikkhu", ("bhikkh", "u masc")),
            ("masc", "", "sayambhū", ("sayambh", "ū masc")),
            ("masc", "", "satthar", ("satth", "ar masc")),
            ("masc", "", "manas", ("man", "as masc")),
            ("masc", "", "bhagavant", ("bhagav", "ant masc")),
            ("masc", "", "devā", ("dev", "a masc pl")),
            # dead branch: "rāja masc" never wins because "dhammarāja" also
            # ends in plain "a", and that check comes first.
            ("masc", "", "dhammarāja", ("dhammarāj", "a masc")),
            ("fem", "", "kaññā", ("kaññ", "ā fem")),
            ("fem", "", "ratti", ("ratt", "i fem")),
            ("fem", "", "nadī", ("nad", "ī fem")),
            ("fem", "", "dhenu", ("dhen", "u fem")),
            ("fem", "", "vadhū", ("vadh", "ū fem")),
            # dead branch: "mātar fem" never wins because "mātar" also ends
            # in "ar", and that check comes first.
            ("fem", "", "mātar", ("māt", "ar fem")),
            ("nt", "", "citta", ("citt", "a nt")),
            ("nt", "", "cakkhu", ("cakkh", "u nt")),
            ("nt", "", "cittāni", ("citt", "a nt pl")),
            ("nt", "", "aggi", ("agg", "i nt")),
            ("card", "x pl", "dvi", ("dv", "a1 card")),
            ("card", "nt sg", "eka", ("ek", "a2 card")),
            ("card", "", "koṭi", ("koṭ", "i2 card")),
            ("card", "", "satthi", ("satth", "i card")),
            ("card", "", "catassā", ("catass", "ā card")),
            ("ordin", "", "pathama", ("patham", "a ordin")),
            ("pp", "", "kata", ("kat", "a pp")),
            ("prp", "", "gacchanta", ("gacch", "anta prp")),
            ("prp", "", "karenta", ("kar", "enta prp")),
            ("prp", "", "honta", ("h", "onta prp")),
            ("prp", "", "kayirāmāna", ("kayirā", "māna prp")),
            ("prp", "", "vadamāna", ("vada", "māna prp")),
            ("ptp", "", "kayira", ("kayir", "a ptp")),
            ("pron", "", "eta", ("et", "a pron")),
            ("pr", "", "gacchati", ("gacch", "ati pr")),
            ("pr", "", "deseti", ("des", "eti pr")),
            ("pr", "", "karoti", ("kar", "oti pr")),
            ("pr", "", "jānāti", ("jān", "āti pr")),
            ("aor", "", "ahosi", ("ahos", "i aor")),
            ("aor", "", "akāsi", ("ak", "āsi aor")),
            ("aor", "", "adesesi", ("ades", "esi aor")),
            ("aor", "", "agacchi", ("agacch", "i aor")),
            ("perf", "", "cakāra", ("cakār", "a perf")),
            ("imperf", "", "abravā", ("abrav", "ā imperf")),
            ("ind", "", "eva", ("-", "")),
        ],
    )
    def test_stem_pattern_table(self, pos, grammar, lemma_1, expected):
        assert find_stem_pattern(pos, grammar, lemma_1) == expected

    def test_unmatched_pos_returns_empty(self):
        assert find_stem_pattern("nonexistent_pos", "", "whatever") == ("", "")


def _headword(**kwargs) -> DpdHeadword:
    """Build a transient DpdHeadword with just the given fields set."""
    hw = DpdHeadword()
    for field in (
        "lemma_1",
        "grammar",
        "construction",
        "root_key",
        "compound_type",
        "neg",
    ):
        setattr(hw, field, kwargs.get(field, ""))
    return hw


class TestMakeCompoundConstructionFromHeadword:
    def test_su_root_prefix(self):
        hw = _headword(lemma_1="sukata 1", root_key="√kar", construction="su kata")
        assert make_compound_construction_from_headword(hw) == "su + kata"

    def test_dur_root_prefix(self):
        hw = _headword(lemma_1="dukkata 1", root_key="√kar", construction="dur kata")
        assert make_compound_construction_from_headword(hw) == "dur + kata"

    def test_na_root_prefix(self):
        hw = _headword(lemma_1="akata 1", root_key="√kar", construction="na kata")
        assert make_compound_construction_from_headword(hw) == "na + kata"

    def test_compound_uses_construction_line1(self):
        hw = _headword(
            lemma_1="dhammavinaya 1",
            grammar="nt comp",
            construction="dhamma + vinaya\nsecond",
        )
        assert make_compound_construction_from_headword(hw) == "dhamma + vinaya"

    def test_dvanda_gets_ca_appended(self):
        # grammar must NOT contain the word "comp" — that's checked earlier
        # in the elif chain and would short-circuit the dvanda branch.
        hw = _headword(
            lemma_1="candimasuriya 1",
            grammar="nt",
            construction="candima + suriya",
            compound_type="dvanda",
        )
        assert (
            make_compound_construction_from_headword(hw)
            == "candima  <b>ca</b> suriya <b>ca</b>"
        )

    def test_neg_kammadharaya_an_prefix(self):
        hw = _headword(
            lemma_1="anicca 1",
            grammar="nt",
            construction="na icca",
            compound_type="kammadhāraya",
            neg="neg",
        )
        assert make_compound_construction_from_headword(hw) == "na + icca"

    def test_default_fallback_returns_lemma_clean(self):
        hw = _headword(lemma_1="rukkha 1", grammar="nt", construction="rukkha")
        assert make_compound_construction_from_headword(hw) == "rukkha"


class TestMakeDpdHeadwordFromDict:
    def test_sets_known_fields_and_ignores_unknown(self):
        field_data = {
            "lemma_1": "  karoti 1  ",
            "pos": "v",
            "meaning_1": "does,  makes",
            "not_a_real_field": "x",
        }
        hw = make_dpd_headword_from_dict(field_data)
        assert hw.lemma_1 == "karoti 1"
        assert hw.pos == "v"
        assert hw.meaning_1 == "does, makes"
        assert not hasattr(hw, "not_a_real_field")


class TestCleanText:
    def test_collapses_double_spaces(self):
        assert clean_text("this  is,a  test .") == "this is,a test."

    def test_replaces_niggahita_variant(self):
        assert clean_text("evaṁ ca") == "evaṃ ca"

    def test_fixes_bold_ti(self):
        assert clean_text("word</b>ti more") == "word</b>'ti more"

    def test_fixes_bold_nti(self):
        assert clean_text("word</b>nti more") == "wordn</b>'ti more"

    def test_fixes_tipi(self):
        assert clean_text("word'tipi more") == "word'ti'pi more"


class TestRemoveBoldTags:
    def test_removes_open_and_close_tags(self):
        assert remove_bold_tags("<b>bold</b> text") == "bold text"
