import json

from tools.example_cleaning import (
    clean_commentary,
    clean_example,
    clean_speech_marks,
    clean_text,
    remove_bold_tags,
    remove_brackets,
)
from tools.paths import ProjectPaths
from tools.speech_marks import SpeechMarkManager


def test_functions_with_speech_marks(tmp_path):
    # Setup mock data
    paths = ProjectPaths(base_dir=tmp_path)
    paths.speech_marks_path.parent.mkdir(parents=True, exist_ok=True)

    data = {"sandhipada": ["sandhi'pada"], "hyphenpada": ["hyphen-pada"]}
    paths.speech_marks_path.write_text(json.dumps(data))

    manager = SpeechMarkManager(paths=paths)

    # Test clean_speech_marks
    assert clean_speech_marks("sandhipada", manager) == "sandhi'pada"
    assert clean_speech_marks("hyphenpada", manager) == "hyphen-pada"

    # Test clean_commentary (includes speech marks + general cleaning)
    # clean_text replaces ṁ with ṃ
    assert clean_commentary("sandhipada ṁ", manager) == "sandhi'pada ṃ"

    # Test clean_example
    assert clean_example("hyphenpada ṁ", manager) == "hyphen-pada ṃ"


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
