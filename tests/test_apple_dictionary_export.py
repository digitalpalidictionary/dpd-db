"""Tests for Apple Dictionary export functionality.

This module contains functional tests for the exporter/apple_dictionary/ module.
Tests verify the actual functionality by calling functions directly and verifying output.
"""

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from exporter.apple_dictionary.apple_dictionary import (
    APPLE_NS,
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
        assert "Digital Pāḷi Dictionary" in content
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
        assert "Digital Pāḷi Dictionary" in content

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
        assert "font-size: 150%" in content

    def test_contains_meaning_class_styling(self, temp_dir):
        """Test that CSS contains meaning class styling."""
        copy_css_file(temp_dir)

        css_path = temp_dir / "Dictionary.css"
        content = css_path.read_text()

        assert ".meaning {" in content
        assert "margin-left: 1rem" in content


class TestGenerateDictionaryXml:
    """Test suite for generate_dictionary_xml function using real database."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def db_session(self):
        """Get real database session."""
        from db.db_helpers import get_db_session
        from tools.paths import ProjectPaths
        pth = ProjectPaths()
        session = get_db_session(pth.dpd_db_path)
        yield session
        session.close()

    def test_creates_dictionary_xml_file(self, temp_dir, db_session):
        """Test that Dictionary.xml file is created."""
        generate_dictionary_xml(temp_dir, db_session)

        xml_path = temp_dir / "Dictionary.xml"
        assert xml_path.exists(), "Dictionary.xml should be created"

    def test_xml_has_correct_namespace(self, temp_dir, db_session):
        """Test that XML has correct Apple Dictionary namespace."""
        generate_dictionary_xml(temp_dir, db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        assert APPLE_NS in content
        assert (
            'xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng"' in content
        )

    def test_xml_has_dictionary_root_element(self, temp_dir, db_session):
        """Test that XML has d:dictionary as root element."""
        generate_dictionary_xml(temp_dir, db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        root = ET.fromstring(content)
        assert "dictionary" in root.tag

    def test_xml_contains_entry_elements(self, temp_dir, db_session):
        """Test that XML contains entry elements."""
        generate_dictionary_xml(temp_dir, db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        assert '<d:entry' in content
        assert 'id="dpd_' in content

    def test_xml_contains_index_elements(self, temp_dir, db_session):
        """Test that XML contains index elements for headwords."""
        generate_dictionary_xml(temp_dir, db_session)

        xml_path = temp_dir / "Dictionary.xml"
        content = xml_path.read_text()

        assert '<d:index' in content
        assert 'd:value=' in content


class TestAppleDictionaryConstants:
    """Test suite for module constants."""

    def test_apple_namespace_constant(self):
        """Test that APPLE_NS constant has correct value."""
        assert APPLE_NS == "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
