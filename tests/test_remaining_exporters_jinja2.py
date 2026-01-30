#!/usr/bin/env python3
"""Tests for remaining exporter Jinja2 template conversions.

This module tests that the Jinja2 templates for kindle, deconstructor,
grammar_dict, and tpr exporters render correctly.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader


def create_jinja_env(templates_dir: Path) -> Environment:
    """Create a Jinja2 environment for testing."""
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


class TestKindleTemplates(unittest.TestCase):
    """Test Kindle exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        cls.templates_dir = Path("exporter/kindle/templates_jinja2")
        cls.jinja_env = create_jinja_env(cls.templates_dir)

    def test_ebook_entry_template(self):
        """Test ebook_entry.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_entry.html")

        result = template.render(
            counter=1,
            lemma_1="ābādha",
            lemma_clean="abadha",
            inflections=["ābādho", "ābādham"],
            summary="masc. sickness",
            grammar_table="<table><tr><td>test</td></tr></table>",
            examples="<p>example</p>",
        )

        self.assertIn("<idx:entry", result)
        self.assertIn('id="1"', result)
        self.assertIn("ābādha", result)
        self.assertIn("abadha", result)
        self.assertIn("<idx:infl>", result)
        self.assertIn('<idx:iform value="ābādho"', result)
        self.assertIn("sickness", result)

    def test_ebook_entry_no_inflections(self):
        """Test ebook_entry.html with empty inflections."""
        template = self.jinja_env.get_template("ebook_entry.html")

        result = template.render(
            counter=2,
            lemma_1="test",
            lemma_clean="test",
            inflections=[],
            summary="test summary",
            grammar_table="",
            examples="",
        )

        self.assertIn("<idx:entry", result)
        self.assertNotIn("<idx:infl>", result)

    def test_ebook_grammar_template(self):
        """Test ebook_grammar.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_grammar.html")

        mock_i = SimpleNamespace(
            lemma_ipa="aːbaːdʰa",
            family_root="ābādha",
            root_key="",
            root_clean="",
            root_sign="",
            rt=SimpleNamespace(
                root_has_verb="",
                root_group="",
                root_meaning="",
                root_in_comps="",
                sanskrit_root="",
                sanskrit_root_class="",
                sanskrit_root_meaning="",
            ),
            root_base="",
            construction="ā + bādha",
            derivative="",
            suffix="",
            phonetic="",
            compound_type="",
            compound_construction="",
            antonym="",
            synonym="",
            variant="",
            commentary="-",
            notes="",
            cognate="",
            link="",
            link_list=[],
            non_ia="",
            sanskrit="",
        )

        result = template.render(i=mock_i, grammar="masc")

        self.assertIn('<table class="grammar">', result)
        self.assertIn("IPA", result)
        self.assertIn("/aːbaːdʰa/", result)
        self.assertIn("Grammar", result)
        self.assertIn("masc", result)
        self.assertIn("Construction", result)
        self.assertIn("ā + bādha", result)

    def test_ebook_example_template(self):
        """Test ebook_example.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_example.html")

        mock_i = SimpleNamespace(
            example_1="Example one text",
            example_2="Example two text",
            source_1="DN 1",
            source_2="MN 2",
            sutta_1="Brahmajala",
            sutta_2="Satipatthana",
        )

        result = template.render(i=mock_i)

        self.assertIn("Examples", result)
        self.assertIn("Example one text", result)
        self.assertIn("Example two text", result)
        self.assertIn("DN 1", result)
        self.assertIn("MN 2", result)

    def test_ebook_example_single(self):
        """Test ebook_example.html with single example."""
        template = self.jinja_env.get_template("ebook_example.html")

        mock_i = SimpleNamespace(
            example_1="Example one text",
            example_2="",
            source_1="DN 1",
            source_2="",
            sutta_1="Brahmajala",
            sutta_2="",
        )

        result = template.render(i=mock_i)

        self.assertIn("Example</p>", result)  # Singular
        self.assertNotIn("Examples", result)
        self.assertIn("Example one text", result)

    def test_ebook_deconstructor_entry_template(self):
        """Test ebook_deconstructor_entry.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_deconstructor_entry.html")

        result = template.render(
            counter=1,
            construction="kāyena",
            deconstruction="kāya + eka",
        )

        self.assertIn("<idx:entry", result)
        self.assertIn('id="1"', result)
        self.assertIn("kāyena", result)
        self.assertIn("kāya + eka", result)

    def test_ebook_letter_template(self):
        """Test ebook_letter.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_letter.html")

        result = template.render(
            letter="a",
            entries="<idx:entry>test entry</idx:entry>",
        )

        self.assertIn('<?xml version="1.0" encoding="utf-8"?>', result)
        self.assertIn("Pāḷi-English", result)
        self.assertIn('<h2 class="heading2" id="toc_id_a">a</h2>', result)
        self.assertIn("<mbp:frameset>", result)
        self.assertIn("test entry", result)

    def test_ebook_letter_non_a(self):
        """Test ebook_letter.html with non-'a' letter."""
        template = self.jinja_env.get_template("ebook_letter.html")

        result = template.render(
            letter="k",
            entries="<idx:entry>test</idx:entry>",
        )

        self.assertNotIn("Pāḷi-English", result)
        self.assertIn('<h2 class="heading2">k</h2>', result)

    def test_ebook_abbreviation_entry_template(self):
        """Test ebook_abbreviation_entry.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_abbreviation_entry.html")

        abbrev_data = {
            "abbrev": "masc",
            "meaning": "masculine",
            "explanation": "a masculine noun",
            "pāli": "puma",
            "example": "puriso",
        }

        result = template.render(counter=1, i=abbrev_data)

        self.assertIn("<idx:entry", result)
        self.assertIn("masc", result)
        self.assertIn("masculine", result)
        self.assertIn("a masculine noun", result)
        self.assertIn("puma", result)
        self.assertIn("puriso", result)

    def test_ebook_titlepage_template(self):
        """Test ebook_titlepage.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_titlepage.html")

        result = template.render(date="2024-01-15", time="10:30")

        self.assertIn("Digital Pāḷi Dictionary", result)
        self.assertIn("2024-01-15", result)
        self.assertIn("10:30", result)
        self.assertIn("dpdlogo.png", result)

    def test_ebook_content_opf_template(self):
        """Test ebook_content_opf.html template renders correctly."""
        template = self.jinja_env.get_template("ebook_content_opf.html")

        result = template.render(date_time_zulu="2024-01-15T10:30:00Z")

        self.assertIn("2024-01-15T10:30:00Z", result)
        self.assertIn("Digital Pāḷi Dictionary", result)
        self.assertIn('<package version="3.0"', result)


class TestDeconstructorTemplates(unittest.TestCase):
    """Test Deconstructor exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        cls.templates_dir = Path("exporter/deconstructor/templates_jinja2")
        cls.jinja_env = create_jinja_env(cls.templates_dir)

    def test_deconstructor_header_template(self):
        """Test deconstructor_header.html template renders correctly."""
        template = self.jinja_env.get_template("deconstructor_header.html")

        result = template.render()

        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("DPD Deconstructor", result)
        self.assertIn("dpd-css-and-fonts.css", result)

    def test_deconstructor_template(self):
        """Test deconstructor.html template renders correctly."""
        template = self.jinja_env.get_template("deconstructor.html")

        mock_i = SimpleNamespace(
            lookup_key="kāyena",
        )

        result = template.render(
            i=mock_i,
            deconstructions=["kāya + ena", "kāya + eka"],
            today="2024-01-15",
        )

        self.assertIn("kāya + ena", result)
        self.assertIn("kāya + eka", result)
        self.assertIn("kāyena", result)
        self.assertIn("2024-01-15", result)
        self.assertIn("read the docs", result)

    def test_deconstructor_empty(self):
        """Test deconstructor.html with empty deconstructions."""
        template = self.jinja_env.get_template("deconstructor.html")

        mock_i = SimpleNamespace(lookup_key="test")

        result = template.render(
            i=mock_i,
            deconstructions=[],
            today="2024-01-15",
        )

        self.assertIn("test", result)
        self.assertIn("dpd-footer", result)


class TestGrammarDictTemplates(unittest.TestCase):
    """Test Grammar Dict exporter Jinja2 templates."""

    @classmethod
    def setUpClass(cls):
        cls.templates_dir = Path("exporter/grammar_dict/templates_jinja2")
        cls.jinja_env = create_jinja_env(cls.templates_dir)

    def test_grammar_dict_header_template(self):
        """Test grammar_dict_header.html template renders correctly."""
        template = self.jinja_env.get_template("grammar_dict_header.html")

        result = template.render()

        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("DPD Grammar", result)
        self.assertIn("dpd-css-and-fonts.css", result)
        self.assertIn("sorter.js", result)


class TestTemplateSyntax(unittest.TestCase):
    """Test that all Jinja2 templates have valid syntax."""

    def test_all_jinja2_templates_load(self):
        """Test that all Jinja2 templates can be loaded without errors."""
        template_dirs = [
            Path("exporter/kindle/templates_jinja2"),
            Path("exporter/deconstructor/templates_jinja2"),
            Path("exporter/grammar_dict/templates_jinja2"),
        ]

        for templates_dir in template_dirs:
            if not templates_dir.exists():
                continue

            jinja_env = create_jinja_env(templates_dir)

            for template_file in templates_dir.glob("*.html"):
                with self.subTest(template=template_file):
                    try:
                        jinja_env.get_template(template_file.name)
                    except Exception as e:
                        self.fail(f"Failed to load {template_file}: {e}")


if __name__ == "__main__":
    unittest.main()
