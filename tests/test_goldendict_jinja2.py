"""Tests for GoldenDict Jinja2 template conversion.

This module tests that the Jinja2 converted templates render correctly
and produce expected output.
"""

import unittest
from types import SimpleNamespace

from exporter.jinja2_env import create_jinja2_env
from tools.paths import ProjectPaths


class MockDpdHeadword:
    """Mock DpdHeadword for testing."""

    def __init__(self):
        self.pos = "noun"
        self.plus_case = "masc"
        self.meaning_combo_html = "test meaning"
        self.construction_summary = "test construction"
        self.degree_of_completion_html = "<span class='complete'>✔</span>"
        self.id = 12345
        self.lemma_1 = "test_word"
        self.lemma_1_ = "test_word"
        self.lemma_clean = "testword"
        self.lemma_link = "test_word"
        self.lemma_trad_clean = "testword"
        self.source_1 = "MN"
        self.source_2 = "DN"
        self.lemma_ipa = "test"
        self.audio_male1 = False
        self.audio_male2 = False
        self.audio_female1 = False
        self.family_root = None
        self.root_key = None
        self.root_clean = None
        self.root_sign = None
        self.root_base = None
        self.derivative = None
        self.suffix = None
        self.compound_type = None
        self.antonym = None
        self.synonym = None
        self.variant = None
        self.cognate = None
        self.link = None
        self.link_list = []
        self.non_ia = None
        self.root_family_key = "√test"
        self.family_word = "test_family"
        self.meaning_1 = "test meaning 1"
        self.sanskrit = "test sanskrit"
        self.phonetic = "test phonetic"
        self.compound_construction = "test compound"
        self.commentary = "test commentary"
        self.sutta_1 = "test sutta 1"
        self.sutta_2 = "test sutta 2"
        self.example_1 = "test example 1"
        self.example_2 = "test example 2"
        self.notes = "test notes"
        self.construction = "test construction"
        self.inflections_html = "<table>test</table>"
        self.needs_audio_button = True
        self.needs_sutta_info_button = True
        self.needs_grammar_button = True
        self.needs_example_button = True
        self.needs_examples_button = False
        self.needs_conjugation_button = False
        self.needs_declension_button = True
        self.needs_root_family_button = True
        self.needs_word_family_button = True
        self.needs_compound_family_button = True
        self.needs_compound_families_button = False
        self.needs_idioms_button = True
        self.needs_set_button = True
        self.needs_sets_button = False
        self.needs_frequency_button = True
        self.family_compound_list = ["word1", "word2"]
        self.family_idioms_list = ["idiom1", "idiom2"]
        self.family_set_list = ["set1", "set2"]
        self.freq_data_unpack = {
            "FreqHeading": "test heading",
            "CstFreq": [1, 2, 3],
            "CstGrad": [4, 5, 6],
            "BjtFreq": [7, 8, 9],
            "BjtGrad": [10, 11, 12],
            "SyaFreq": [13, 14, 15],
            "SyaGrad": [16, 17, 18],
            "ScFreq": [19, 20, 21],
            "ScGrad": [22, 23, 24],
        }
        self.inflections_list_all = ["word1", "word2"]
        self.inflections_sinhala_list = []
        self.inflections_devanagari_list = []
        self.inflections_thai_list = []
        self.su = SimpleNamespace(sutta_codes_list=["mn1", "dn2"])


class MockFamilyRoot:
    """Mock FamilyRoot for testing."""

    def __init__(self):
        self.root_family_key = "√test"
        self.root_family = "test family"


class MockFamilyWord:
    """Mock FamilyWord for testing."""

    def __init__(self):
        self.word_family = "test_family"


class MockSuttaInfo:
    """Mock SuttaInfo for testing."""

    def __init__(self):
        self.sutta_codes_list = ["mn1", "dn2"]
        # Add all the sutta info attributes used in the template
        self.cst_code = None
        self.cst_nikaya = None
        self.cst_book = None
        self.cst_section = None
        self.cst_vagga = None
        self.cst_sutta = None
        self.cst_paranum = None
        self.cst_file = None
        self.dpr_link = None
        self.tpp_org = None
        self.cst_m_page = None
        self.cst_t_page = None
        self.cst_v_page = None
        self.cst_p_page = None
        self.sc_code = None
        self.sc_book = None
        self.sc_vagga = None
        self.sc_sutta = None
        self.sc_eng_sutta = None
        self.sc_blurb = None
        self.sc_card_link = None
        self.sc_pali_link = None
        self.sc_eng_link = None
        self.sc_file_path = None
        self.sc_github = None
        self.tbw = None
        self.tbw_legacy = None
        self.dhamma_gift = None
        self.sc_express_link = None
        self.sc_voice_link = None
        self.bjt_sutta_code = None
        self.bjt_piṭaka = None
        self.bjt_nikāya = None
        self.bjt_major_section = None
        self.bjt_book = None
        self.bjt_minor_section = None
        self.bjt_vagga = None
        self.bjt_sutta = None
        self.bjt_book_id = None
        self.bjt_page_num = None
        self.bjt_filename = None
        self.bjt_github_link = None
        self.bjt_web_code = None
        self.bjt_tipitaka_lk_link = None
        self.bjt_open_tipitaka_lk_link = None
        self.dv_exists = False
        self.dv_pts = None
        self.dv_main_theme = None
        self.dv_subtopic = None
        self.dv_summary = None
        self.dv_key_excerpt1 = None
        self.dv_key_excerpt2 = None
        self.dv_similes = None
        self.dv_stage = None
        self.dv_training = None
        self.dv_aspect = None
        self.dv_teacher = None
        self.dv_audience = None
        self.dv_method = None
        self.dv_length = None
        self.dv_prominence = None
        self.dv_suggested_suttas = None
        self.dv_parallels_exists = False
        self.dv_nikayas_parallels = None
        self.dv_āgamas_parallels = None
        self.dv_taisho_parallels = None
        self.dv_sanskrit_parallels = None
        self.dv_vinaya_parallels = None
        self.dv_others_parallels = None


class TestGoldenDictJinja2Templates(unittest.TestCase):
    """Test that Jinja2 templates render correctly."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()
        cls.jinja2_env = create_jinja2_env(cls.pth.goldendict_templates_jinja2_dir)

        # Create mock objects
        cls.mock_i = MockDpdHeadword()
        cls.mock_fr = MockFamilyRoot()
        cls.mock_fw = MockFamilyWord()
        cls.mock_su = MockSuttaInfo()

    def test_dpd_definition_template(self):
        """Test dpd_definition template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_definition.html")

        # Render
        result = jinja2_templ.render(i=self.mock_i, show_id=True)

        # Verify output contains expected content
        self.assertIn("test meaning", result)
        self.assertIn("noun", result)
        self.assertIn("12345", result)  # id is shown when show_id=True

    def test_dpd_header_template(self):
        """Test dpd_header template renders correctly."""
        # Load Jinja2 template with autoescape disabled for JS data compatibility
        from exporter.jinja2_env import create_jinja2_env

        jinja2_env = create_jinja2_env(
            self.pth.goldendict_templates_jinja2_dir, autoescape=False
        )
        jinja2_templ = jinja2_env.get_template("dpd_header.html")

        # Render
        date = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, date=date)

        # Verify output
        self.assertIn("test_word", result)
        self.assertIn("2026-01-29", result)

    def test_dpd_button_box_template(self):
        """Test dpd_button_box template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_button_box.html")

        # Test data
        button_data = {
            "play_button": "<button>play</button>",
            "sutta_info_button": "<button>sutta</button>",
            "grammar_button": "<button>grammar</button>",
            "example_button": "<button>example</button>",
            "examples_button": "",
            "conjugation_button": "",
            "declension_button": "<button>declension</button>",
            "root_family_button": "<button>root family</button>",
            "word_family_button": "<button>word family</button>",
            "compound_family_button": "<button>compound family</button>",
            "idioms_button": "<button>idioms</button>",
            "set_family_button": "<button>set</button>",
            "frequency_button": "<button>frequency</button>",
            "feedback_button": "<button>feedback</button>",
        }

        # Render
        result = jinja2_templ.render(**button_data)

        # Verify output
        self.assertIn("play", result)
        self.assertIn("grammar", result)
        self.assertIn("declension", result)

    def test_dpd_example_template(self):
        """Test dpd_example template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_example.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, today=today)

        # Verify output
        self.assertIn("test example 1", result)
        self.assertIn("test example 2", result)

    def test_dpd_grammar_template(self):
        """Test dpd_grammar template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_grammar.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(
            i=self.mock_i,
            rt=None,
            grammar="test grammar",
            meaning="test meaning",
            today=today,
        )

        # Verify output
        self.assertIn("testword", result)  # i.lemma_clean
        self.assertIn("test grammar", result)

    def test_dpd_feedback_template(self):
        """Test dpd_feedback template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_feedback.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, today=today)

        # Verify output - template renders with lemma_1_ in div id
        self.assertIn("feedback_test_word", result)
        self.assertIn("feedback loading", result)

    def test_dpd_frequency_template(self):
        """Test dpd_frequency template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_frequency.html")

        # Render
        today = "2026-01-29"
        header = "Frequency of <b>test</b>."
        result = jinja2_templ.render(i=self.mock_i, header=header, today=today)

        # Verify output - template renders with lemma_1_ in div id
        self.assertIn("frequency_test_word", result)
        self.assertIn("frequency loading", result)

    def test_dpd_inflection_template(self):
        """Test dpd_inflection template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_inflection.html")

        # Render
        today = "2026-01-29"
        declensions = ["noun"]  # mock_i.pos is "noun"
        conjugations = ["pres", "imp", "opt"]
        table = "<table>test</table>"
        result = jinja2_templ.render(
            i=self.mock_i,
            table=table,
            today=today,
            declensions=declensions,
            conjugations=conjugations,
        )

        # Verify output
        self.assertIn("test_word", result)
        self.assertIn("<table>test</table>", result)

    def test_dpd_family_word_template(self):
        """Test dpd_family_word template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_family_word.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, fw=self.mock_fw, today=today)

        # Verify output - template renders with lemma_1_ in div id
        self.assertIn("family_word_test_word", result)
        self.assertIn("family word loading", result)

    def test_dpd_family_root_template(self):
        """Test dpd_family_root template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_family_root.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, fr=self.mock_fr, today=today)

        # Verify output - template renders with lemma_1_ in div id
        self.assertIn("family_root_test_word", result)
        self.assertIn("root family loading", result)

    def test_dpd_sutta_info_template(self):
        """Test dpd_sutta_info template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_sutta_info.html")

        # Render
        today = "2026-01-29"
        result = jinja2_templ.render(i=self.mock_i, su=self.mock_su, today=today)

        # Verify output
        self.assertIn("test_word", result)
        self.assertIn("2026-01-29", result)


class TestGoldenDictExportDpdIntegration(unittest.TestCase):
    """Integration tests for the export_dpd module with Jinja2."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()

    def test_dpd_headword_templates_initialization(self):
        """Test that DpdHeadwordTemplates can be initialized with Jinja2."""
        # Skip this test if minify_html is not available
        try:
            from exporter.goldendict.export_dpd import DpdHeadwordTemplates
        except ModuleNotFoundError as e:
            if "minify_html" in str(e):
                self.skipTest("minify_html module not available")
            raise

        # This should not raise any errors
        templates = DpdHeadwordTemplates(self.pth)

        # Verify all templates are loaded
        self.assertIsNotNone(templates.header_templ)
        self.assertIsNotNone(templates.dpd_definition_templ)
        self.assertIsNotNone(templates.button_box_templ)
        self.assertIsNotNone(templates.sutta_info_templ)
        self.assertIsNotNone(templates.grammar_templ)
        self.assertIsNotNone(templates.example_templ)
        self.assertIsNotNone(templates.inflection_templ)
        self.assertIsNotNone(templates.family_root_templ)
        self.assertIsNotNone(templates.family_word_templ)
        self.assertIsNotNone(templates.family_compound_templ)
        self.assertIsNotNone(templates.family_idiom_templ)
        self.assertIsNotNone(templates.family_set_templ)
        self.assertIsNotNone(templates.frequency_templ)
        self.assertIsNotNone(templates.feedback_templ)


if __name__ == "__main__":
    unittest.main()
