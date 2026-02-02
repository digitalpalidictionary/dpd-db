"""Tests for Apple Dictionary export functionality.

This module contains functional tests for the exporter/apple_dictionary/ module.
Tests verify the actual functionality by calling functions directly and verifying output.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest

from exporter.apple_dictionary.apple_dictionary import (
    APPLE_NS,
    XHTML_NS,
    copy_css_file,
    generate_dictionary_xml,
    generate_info_plist,
)


class TestGenerateInfoPlist:
    """Test suite for generate_info_plist function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_creates_info_plist_file(self, temp_dir):
        """Test that Info.plist file is created."""
        generate_info_plist(temp_dir, version="1.0")

        plist_path = temp_dir / "Info.plist"
        assert plist_path.exists(), "Info.plist should be created"

    def test_contains_correct_bundle_identifier(self, temp_dir):
        """Test that plist contains correct bundle identifier."""
        generate_info_plist(temp_dir, version="1.0")

        plist_path = temp_dir / "Info.plist"
        content = plist_path.read_text()
        assert "org.digitalpalidictionary.dpd" in content
        assert "CFBundleIdentifier" in content

    def test_contains_dictionary_display_name(self, temp_dir):
        """Test that plist contains dictionary display name."""
        generate_info_plist(temp_dir, version="1.0")

        plist_path = temp_dir / "Info.plist"
        content = plist_path.read_text()
        assert "Digital Pali Dictionary" in content
        assert "CFBundleDisplayName" in content

    def test_contains_version(self, temp_dir):
        """Test that plist contains the specified version."""
        generate_info_plist(temp_dir, version="2.5")

        plist_path = temp_dir / "Info.plist"
        content = plist_path.read_text()
        assert "<string>2.5</string>" in content

    def test_contains_copyright(self, temp_dir):
        """Test that plist contains copyright information."""
        generate_info_plist(temp_dir, version="1.0")

        plist_path = temp_dir / "Info.plist"
        content = plist_path.read_text()
        assert "DCSDictionaryCopyright" in content
        assert "Digital Pali Dictionary" in content

    def test_valid_xml_structure(self, temp_dir):
        """Test that generated plist is valid XML."""
        generate_info_plist(temp_dir, version="1.0")

        plist_path = temp_dir / "Info.plist"
        content = plist_path.read_text()

        # Should be parseable as XML
        root = ET.fromstring(content)
        assert root.tag == "plist"


class TestCopyCssFile:
    """Test suite for copy_css_file function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    def test_creates_dictionary_css_file(self, temp_dir):
        """Test that Dictionary.css file is created."""
        copy_css_file(temp_dir)

        css_path = temp_dir / "Dictionary.css"
        assert css_path.exists(), "Dictionary.css should be created"

    def test_copies_css_content_correctly(self, temp_dir):
        """Test that CSS content is copied correctly from template."""
        copy_css_file(temp_dir)

        css_path = temp_dir / "Dictionary.css"
        content = css_path.read_text()

        # Check for DPD-specific CSS variables and colors
        assert "--primary: hsl(198, 100%, 50%)" in content
        assert "--primary-text:" in content

    def test_contains_entry_title_styling(self, temp_dir):
        """Test that CSS contains entry title styling."""
        copy_css_file(temp_dir)

        css_path = temp_dir / "Dictionary.css"
        content = css_path.read_text()

        assert "h1 {" in content
        assert "font-weight: bold" in content

    def test_contains_content_class_styling(self, temp_dir):
        """Test that CSS contains content class styling."""
        copy_css_file(temp_dir)

        css_path = temp_dir / "Dictionary.css"
        content = css_path.read_text()

        assert ".content {" in content
        assert "border:" in content


class TestGenerateDictionaryXml:
    """Test suite for generate_dictionary_xml function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session with sample headwords."""
        session = MagicMock()

        # Create mock headwords
        headword1 = MagicMock()
        headword1.id = 1
        headword1.lemma_1 = "a"
        headword1.pos = "prefix"
        headword1.plus_case = None
        headword1.meaning_combo_html = "(prefix) not, without"
        headword1.construction_summary = None
        headword1.degree_of_completion = None
        headword1.degree_of_completion_html = None
        headword1.inflections_list_all = None

        headword2 = MagicMock()
        headword2.id = 2
        headword2.lemma_1 = "ābādha"
        headword2.pos = "masc"
        headword2.plus_case = None
        headword2.meaning_combo_html = "<b>ābādha</b> disease, sickness"
        headword2.construction_summary = "ā + bādh + a"
        headword2.degree_of_completion = None
        headword2.degree_of_completion_html = None
        headword2.inflections_list_all = ["ābādhe", "ābādhaṃ"]

        # Mock the query to return our test headwords
        mock_query = MagicMock()
        mock_query.all.return_value = [headword1, headword2]
        session.query.return_value = mock_query

        return session

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_creates_dictionary_xml_file(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that Dictionary.xml file is created."""
        # Mock the Jinja2 template
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        assert xml_path.exists(), "Dictionary.xml should be created"

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_has_correct_namespace(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that XML has correct Apple Dictionary namespace."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        assert APPLE_NS in content
        assert XHTML_NS in content
        assert (
            'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng"' in content
        )

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_has_dictionary_root_element(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that XML has d:dictionary as root element."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # Parse and verify structure
        root = ET.fromstring(content)
        assert "dictionary" in root.tag

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_contains_entry_elements(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that XML contains entry elements."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # ElementTree uses ns0: prefix for first namespace, check for entry tag
        assert "entry" in content
        assert 'id="dpd_1"' in content

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_contains_index_elements(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that XML contains index elements for headwords."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # ElementTree uses ns0: prefix, check for index tag with value attribute
        assert "index" in content
        assert 'value="a"' in content

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_contains_inflection_indices(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that XML contains indices for inflections."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # The second headword has inflections: ābādhe, ābādhaṃ
        assert "ābādhe" in content or "ābādhaṃ" in content

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_has_entry_id_attributes(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that entries have id attributes."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # Should have entry IDs like dpd_1, dpd_2
        assert 'id="dpd_1"' in content
        assert 'id="dpd_2"' in content

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_xml_has_title_attributes(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that entries have title attributes."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        # ElementTree uses ns0:title format, but title="a" is still present
        assert 'title="a"' in content
        assert 'title="ābādha"' in content

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_queries_database_for_headwords(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that function queries database for headwords."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        # Verify the database was queried
        mock_db_session.query.assert_called_once()

    @patch("exporter.apple_dictionary.apple_dictionary.Environment")
    @patch("exporter.apple_dictionary.apple_dictionary.FileSystemLoader")
    def test_renders_template_for_each_headword(
        self, mock_loader, mock_env, temp_dir, mock_db_session
    ):
        """Test that template is rendered for each headword."""
        mock_template = MagicMock()
        mock_template.render.return_value = "<div>mock content</div>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance

        generate_dictionary_xml(temp_dir, mock_db_session)

        # Should render template twice for our 2 mock headwords
        assert mock_template.render.call_count == 2


class TestAppleDictionaryConstants:
    """Test suite for module constants."""

    def test_apple_namespace_constant(self):
        """Test that APPLE_NS constant has correct value."""
        assert APPLE_NS == "http://www.apple.com/DTDs/DictionaryService-1.0.rng"

    def test_xhtml_namespace_constant(self):
        """Test that XHTML_NS constant has correct value."""
        assert XHTML_NS == "http://www.w3.org/1999/xhtml"
