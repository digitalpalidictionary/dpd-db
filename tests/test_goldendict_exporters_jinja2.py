"""Tests for GoldenDict exporter Jinja2 template conversion.

This module tests that the Jinja2 converted templates render correctly
for the remaining exporter files:
- export_roots.py
- export_epd.py
- export_help.py
- export_variant_spelling.py
"""

import unittest

from exporter.jinja2_env import create_jinja2_env
from tools.paths import ProjectPaths


class MockDpdRoot:
    """Mock DpdRoot for testing."""

    def __init__(self):
        self.root = "√test"
        self.root_ = "test"
        self.root_clean = "test"
        self.root_meaning = "to test"
        self.root_family = "test family"
        self.root_has_verb = ""
        self.root_group = "1"
        self.root_sign = "a"
        self.root_no_sign_ = "test"
        self.root_info = ""
        self.root_matrix = ""
        self.root_link = "test"
        self.panini_root = "test panini"
        self.panini_sanskrit = "test sanskrit"
        self.panini_english = "test english"


class MockFamilyRoot:
    """Mock FamilyRoot for testing."""

    def __init__(self):
        self.root_key = "√test"
        self.root_family = "test family"
        self.root_family_ = "test_family"
        self.family_root = "test family"


class MockAbbreviation:
    """Mock Abbreviation for testing."""

    def __init__(self):
        self.abbrev = "test"
        self.meaning = "test meaning"
        self.pali = "test pali"
        self.example = "test example"
        self.information = "test information"


class MockHelp:
    """Mock Help for testing."""

    def __init__(self):
        self.help = "test_help"
        self.meaning = "test meaning"


class TestGoldenDictRootsExporter(unittest.TestCase):
    """Test root exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()
        cls.jinja2_env = create_jinja2_env(cls.pth.goldendict_templates_jinja2_dir)

        # Create mock objects
        cls.mock_r = MockDpdRoot()
        cls.mock_fr = MockFamilyRoot()

    def test_root_header_template(self):
        """Test root_header template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_header.html")

        # Render
        date = "2026-01-29"
        result = jinja2_templ.render(r=self.mock_r, date=date)

        # Verify output
        self.assertIn("√test", result)
        self.assertIn("2026-01-29", result)

    def test_root_definition_template(self):
        """Test root_definition template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_definition.html")

        # Render
        today = "2026-01-29"
        count = 5
        result = jinja2_templ.render(r=self.mock_r, count=count, today=today)

        # Verify output - template uses r.root_clean, not r.root
        self.assertIn("test", result)  # root_clean
        self.assertIn("to test", result)  # root_meaning
        self.assertIn("5", result)  # count

    def test_root_buttons_template(self):
        """Test root_buttons template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_buttons.html")

        # Render
        frs = [self.mock_fr]
        result = jinja2_templ.render(r=self.mock_r, frs=frs)

        # Verify output - template uses r.root_ in id
        self.assertIn("test", result)  # r.root_
        self.assertIn("root info", result)
        self.assertIn("test family", result)  # fr.root_family

    def test_root_info_template(self):
        """Test root_info template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_info.html")

        # Render - template outputs r.root_info which is empty string in mock
        today = "2026-01-29"
        root_info = ""  # mock has empty string for root_info
        result = jinja2_templ.render(r=self.mock_r, root_info=root_info, today=today)

        # Verify output - template uses r.root_ in id
        self.assertIn("test", result)  # r.root_
        self.assertIn("2026-01-29", result)

    def test_root_matrix_template(self):
        """Test root_matrix template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_matrix.html")

        # Render
        today = "2026-01-29"
        count = 5
        root_matrix = ""
        result = jinja2_templ.render(
            r=self.mock_r, count=count, root_matrix=root_matrix, today=today
        )

        # Verify output - template uses r.root_ in id and r.root_clean in content
        self.assertIn("test", result)  # r.root_
        self.assertIn("to test", result)  # r.root_meaning
        self.assertIn("2026-01-29", result)

    def test_root_families_template(self):
        """Test root_families template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("root_families.html")

        # Render
        today = "2026-01-29"
        frs = [self.mock_fr]
        result = jinja2_templ.render(r=self.mock_r, frs=frs, today=today)

        # Verify output - template uses r.root_ and fr.root_family_
        self.assertIn("test", result)  # r.root_
        self.assertIn("test_family", result)  # fr.root_family_
        self.assertIn("root family loading", result)


class TestGoldenDictEpdExporter(unittest.TestCase):
    """Test EPD exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()
        cls.jinja2_env = create_jinja2_env(cls.pth.goldendict_templates_jinja2_dir)

    def test_dpd_header_plain_template(self):
        """Test dpd_header_plain template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_header_plain.html")

        # Render
        result = jinja2_templ.render()

        # Verify output
        self.assertIn("<!DOCTYPE html>", result)


class TestGoldenDictHelpExporter(unittest.TestCase):
    """Test Help exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()
        cls.jinja2_env = create_jinja2_env(cls.pth.goldendict_templates_jinja2_dir)

        # Create mock objects
        cls.mock_abbrev = MockAbbreviation()
        cls.mock_help = MockHelp()

    def test_help_abbrev_template(self):
        """Test help_abbrev template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("help_abbrev.html")

        # Render
        result = jinja2_templ.render(i=self.mock_abbrev)

        # Verify output
        self.assertIn("test", result)
        self.assertIn("test meaning", result)

    def test_help_help_template(self):
        """Test help_help template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("help_help.html")

        # Render
        result = jinja2_templ.render(i=self.mock_help)

        # Verify output
        self.assertIn("test_help", result)
        self.assertIn("test meaning", result)


class TestGoldenDictVariantSpellingExporter(unittest.TestCase):
    """Test Variant/Spelling exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()
        cls.jinja2_env = create_jinja2_env(cls.pth.goldendict_templates_jinja2_dir)

    def test_dpd_variant_reading_template(self):
        """Test dpd_variant_reading template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_variant_reading.html")

        # Render
        main = "test_main"
        result = jinja2_templ.render(main=main)

        # Verify output
        self.assertIn("test_main", result)

    def test_dpd_spelling_mistake_template(self):
        """Test dpd_spelling_mistake template renders correctly."""
        # Load Jinja2 template
        jinja2_templ = self.jinja2_env.get_template("dpd_spelling_mistake.html")

        # Render
        correction = "test_correction"
        result = jinja2_templ.render(correction=correction)

        # Verify output
        self.assertIn("test_correction", result)


class TestGoldenDictExporterIntegration(unittest.TestCase):
    """Integration tests for the exporter modules with Jinja2."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.pth = ProjectPaths()

    def test_roots_templates_initialization(self):
        """Test that RootsTemplates can be initialized with Jinja2."""
        try:
            from exporter.goldendict.export_roots import RootsTemplates
        except ModuleNotFoundError as e:
            if "minify_html" in str(e):
                self.skipTest("minify_html module not available")
            raise

        # This should not raise any errors
        templates = RootsTemplates(self.pth)

        # Verify all templates are loaded
        self.assertIsNotNone(templates.header_templ)
        self.assertIsNotNone(templates.definition_templ)
        self.assertIsNotNone(templates.buttons_templ)
        self.assertIsNotNone(templates.info_templ)
        self.assertIsNotNone(templates.matrix_templ)
        self.assertIsNotNone(templates.families_templ)

    def test_epd_templates_initialization(self):
        """Test that EpdTemplates can be initialized with Jinja2."""
        try:
            from exporter.goldendict.export_epd import EpdTemplates
        except ModuleNotFoundError as e:
            if "minify_html" in str(e):
                self.skipTest("minify_html module not available")
            raise

        # This should not raise any errors
        templates = EpdTemplates(self.pth)

        # Verify template is loaded
        self.assertIsNotNone(templates.header_plain_templ)

    def test_help_templates_initialization(self):
        """Test that HelpTemplates can be initialized with Jinja2."""
        try:
            from exporter.goldendict.export_help import HelpTemplates
        except ModuleNotFoundError as e:
            if "minify_html" in str(e):
                self.skipTest("minify_html module not available")
            raise

        # This should not raise any errors
        templates = HelpTemplates(self.pth)

        # Verify all templates are loaded
        self.assertIsNotNone(templates.header_plain_templ)
        self.assertIsNotNone(templates.abbrev_templ)
        self.assertIsNotNone(templates.help_templ)

    def test_variant_spelling_templates_initialization(self):
        """Test that VariantSpellingTemplates can be initialized with Jinja2."""
        try:
            from exporter.goldendict.export_variant_spelling import (
                VariantSpellingTemplates,
            )
        except ModuleNotFoundError as e:
            if "minify_html" in str(e):
                self.skipTest("minify_html module not available")
            raise

        # This should not raise any errors
        templates = VariantSpellingTemplates(self.pth)

        # Verify all templates are loaded
        self.assertIsNotNone(templates.header_plain_templ)
        self.assertIsNotNone(templates.variant_templ)
        self.assertIsNotNone(templates.spelling_templ)


if __name__ == "__main__":
    unittest.main()
