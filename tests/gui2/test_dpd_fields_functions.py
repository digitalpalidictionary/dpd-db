from gui2.dpd_fields_functions import remove_brackets


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
