"""Tests for EPD (English to Pāḷi Dictionary) functionality in Kindle exporter."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tools.paths import ProjectPaths


class TestRenderEpdEntry:
    """Tests for render_epd_entry function."""

    def test_render_epd_entry_basic(self):
        """Test basic EPD entry rendering with single Pāḷi equivalent."""
        from exporter.kindle.kindle_exporter import render_epd_entry

        pth = Mock(spec=ProjectPaths)
        pth.ebook_epd_entry_templ_path = Path("/mock/template.html")

        with patch("exporter.kindle.kindle_exporter.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<idx:entry>test</idx:entry>"
            MockTemplate.return_value = mock_template_instance

            result = render_epd_entry(
                pth, 1, "love", "<b class='epd'>mettā</b> f. love"
            )

            MockTemplate.assert_called_once_with(
                filename=str(pth.ebook_epd_entry_templ_path)
            )
            mock_template_instance.render.assert_called_once_with(
                counter=1,
                english_headword="love",
                pali_equivalents="<b class='epd'>mettā</b> f. love",
            )
            assert result == "<idx:entry>test</idx:entry>"

    def test_render_epd_entry_multiple_equivalents(self):
        """Test EPD entry with multiple Pāḷi equivalents."""
        from exporter.kindle.kindle_exporter import render_epd_entry

        pth = Mock(spec=ProjectPaths)
        pth.ebook_epd_entry_templ_path = Path("/mock/template.html")

        equivalents = (
            "<b class='epd'>mettā</b> f. love<br/><b class='epd'>pema</b> nt. affection"
        )

        with patch("exporter.kindle.kindle_exporter.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<idx:entry>multi</idx:entry>"
            MockTemplate.return_value = mock_template_instance

            render_epd_entry(pth, 42, "love", equivalents)

            mock_template_instance.render.assert_called_once_with(
                counter=42, english_headword="love", pali_equivalents=equivalents
            )


class TestRenderEpdLetterTempl:
    """Tests for render_epd_letter_templ function."""

    def test_render_letter_a_with_header(self):
        """Test letter 'a' rendering with main section header."""
        from exporter.kindle.kindle_exporter import render_epd_letter_templ

        pth = Mock(spec=ProjectPaths)
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        with patch("exporter.kindle.kindle_exporter.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<html>letter_a</html>"
            MockTemplate.return_value = mock_template_instance

            entries = "<idx:entry>entry1</idx:entry>"
            result = render_epd_letter_templ(pth, "a", entries)

            MockTemplate.assert_called_once_with(
                filename=str(pth.ebook_epd_letter_templ_path)
            )
            mock_template_instance.render.assert_called_once_with(
                letter="a", entries=entries
            )
            assert result == "<html>letter_a</html>"

    def test_render_other_letters(self):
        """Test rendering for letters other than 'a'."""
        from exporter.kindle.kindle_exporter import render_epd_letter_templ

        pth = Mock(spec=ProjectPaths)
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        with patch("exporter.kindle.kindle_exporter.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<html>letter_z</html>"
            MockTemplate.return_value = mock_template_instance

            render_epd_letter_templ(pth, "z", "")

            mock_template_instance.render.assert_called_once_with(
                letter="z", entries=""
            )


class TestRenderEpdXhtml:
    """Tests for render_epd_xhtml function."""

    @patch("exporter.kindle.kindle_exporter.get_db_session")
    @patch("exporter.kindle.kindle_exporter.Template")
    def test_render_epd_xhtml_queries_lookup_table(
        self, mock_template, mock_get_session
    ):
        """Test that EPD data is queried from Lookup table where epd != ''."""
        from exporter.kindle.kindle_exporter import render_epd_xhtml
        from tools.paths import ProjectPaths

        # Setup mock session and query
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Create mock lookup entries
        mock_entry1 = MagicMock()
        mock_entry1.lookup_key = "love"
        mock_entry1.epd_unpack = [("mettā", "f", "love")]

        mock_entry2 = MagicMock()
        mock_entry2.lookup_key = "wisdom"
        mock_entry2.epd_unpack = [("paññā", "f", "wisdom"), ("vijjā", "f", "knowledge")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_entry1,
            mock_entry2,
        ]

        # Setup mock template
        mock_template_instance = MagicMock()
        mock_template_instance.render.return_value = "<html>content</html>"
        mock_template.return_value = mock_template_instance

        # Setup mock paths
        pth = Mock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        pth.epub_text_dir = Path("/mock/epub/text")
        pth.ebook_epd_entry_templ_path = Path("/mock/entry.html")
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        with patch("builtins.open", MagicMock()):
            result = render_epd_xhtml(pth, 1)

        # Verify query was made correctly
        mock_session.query.assert_called_once()
        mock_session.query.return_value.filter.assert_called_once()

        # Verify session was closed
        mock_session.close.assert_called_once()

        # Verify counter was incremented
        assert result > 1

    @patch("exporter.kindle.kindle_exporter.get_db_session")
    def test_group_by_first_letter(self, mock_get_session):
        """Test that entries are grouped by first letter of English headword."""
        from exporter.kindle.kindle_exporter import render_epd_xhtml

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Create entries for different letters
        mock_love = MagicMock()
        mock_love.lookup_key = "love"
        mock_love.epd_unpack = [("mettā", "f", "love")]

        mock_wisdom = MagicMock()
        mock_wisdom.lookup_key = "wisdom"
        mock_wisdom.epd_unpack = [("paññā", "f", "wisdom")]

        mock_anger = MagicMock()
        mock_anger.lookup_key = "anger"
        mock_anger.epd_unpack = [("kodha", "m", "anger")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_love,
            mock_wisdom,
            mock_anger,
        ]

        pth = Mock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        pth.epub_text_dir = Path("/mock/epub/text")
        pth.ebook_epd_entry_templ_path = Path("/mock/entry.html")
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        mock_open = MagicMock()
        with patch("builtins.open", mock_open):
            with patch("exporter.kindle.kindle_exporter.Template") as mock_template:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "<html></html>"
                mock_template.return_value = mock_template_instance

                render_epd_xhtml(pth, 1)

        # Check that files were created for letters a, l, w
        calls = mock_open.call_args_list
        file_paths = [str(call[0][0]) for call in calls]

        assert any("epd_0_a.xhtml" in fp for fp in file_paths)
        assert any("epd_11_l.xhtml" in fp for fp in file_paths)  # love -> l
        assert any("epd_22_w.xhtml" in fp for fp in file_paths)  # wisdom -> w

    @patch("exporter.kindle.kindle_exporter.get_db_session")
    def test_handles_empty_epd_data(self, mock_get_session):
        """Test handling when no EPD entries exist in database."""
        from exporter.kindle.kindle_exporter import render_epd_xhtml

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []

        pth = Mock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        pth.epub_text_dir = Path("/mock/epub/text")
        pth.ebook_epd_entry_templ_path = Path("/mock/entry.html")
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        with patch("builtins.open", MagicMock()):
            with patch("exporter.kindle.kindle_exporter.Template") as mock_template:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "<html></html>"
                mock_template.return_value = mock_template_instance

                result = render_epd_xhtml(pth, 100)

        # Should still create all 26 letter files even if empty
        assert result == 100  # Counter unchanged

    @patch("exporter.kindle.kindle_exporter.get_db_session")
    def test_case_insensitive_grouping(self, mock_get_session):
        """Test that uppercase English headwords are grouped correctly."""
        from exporter.kindle.kindle_exporter import render_epd_xhtml

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_entry = MagicMock()
        mock_entry.lookup_key = "Love"  # Capitalized
        mock_entry.epd_unpack = [("mettā", "f", "love")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_entry
        ]

        pth = Mock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        pth.epub_text_dir = Path("/mock/epub/text")
        pth.ebook_epd_entry_templ_path = Path("/mock/entry.html")
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        mock_open = MagicMock()
        with patch("builtins.open", mock_open):
            with patch("exporter.kindle.kindle_exporter.Template") as mock_template:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "<html></html>"
                mock_template.return_value = mock_template_instance

                render_epd_xhtml(pth, 1)

        # Check that 'Love' goes to 'epd_0_a.xhtml' (lowercase grouping)
        calls = mock_open.call_args_list
        file_paths = [str(call[0][0]) for call in calls]
        assert any("epd_0_a.xhtml" in fp for fp in file_paths)

    @patch("exporter.kindle.kindle_exporter.get_db_session")
    def test_non_english_characters_default_to_a(self, mock_get_session):
        """Test that non-English starting characters default to 'a' group."""
        from exporter.kindle.kindle_exporter import render_epd_xhtml

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_entry = MagicMock()
        mock_entry.lookup_key = "123number"  # Starts with number
        mock_entry.epd_unpack = [("ekadasan", "m", "number")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_entry
        ]

        pth = Mock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        pth.epub_text_dir = Path("/mock/epub/text")
        pth.ebook_epd_entry_templ_path = Path("/mock/entry.html")
        pth.ebook_epd_letter_templ_path = Path("/mock/letter.html")

        mock_open = MagicMock()
        with patch("builtins.open", mock_open):
            with patch("exporter.kindle.kindle_exporter.Template") as mock_template:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "<html></html>"
                mock_template.return_value = mock_template_instance

                render_epd_xhtml(pth, 1)

        # Should default to 'a' file
        calls = mock_open.call_args_list
        file_paths = [str(call[0][0]) for call in calls]
        assert any("epd_0_a.xhtml" in fp for fp in file_paths)


class TestEpdDataStructure:
    """Tests to verify EPD data structure from database."""

    def test_epd_unpack_returns_list_structure(self):
        """Verify that Lookup.epd_unpack returns list of [lemma, pos, meaning] structures."""
        from db.models import Lookup

        lookup = Lookup()
        lookup.epd = '[["mettā", "f", "love"], ["pema", "nt", "affection"]]'

        result = lookup.epd_unpack

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == ["mettā", "f", "love"]
        assert result[1] == ["pema", "nt", "affection"]

    def test_epd_entry_formatting(self):
        """Test the expected format: <b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"""
        lemma_clean = "mettā"
        pos = "f"
        meaning = "love"

        expected = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning}"

        assert expected == "<b class='epd'>mettā</b> f. love"
