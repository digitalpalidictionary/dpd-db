import tempfile
from pathlib import Path

import pandas as pd

from db.suttas.dv_catalogue_suttas import read_dv_catalogue
from tools.paths import ProjectPaths


def test_read_dv_catalogue_sorting_and_deduplication():
    """Test that read_dv_catalogue sorts sutta codes naturally and removes consecutive duplicates."""

    # Create a temporary TSV file with unsorted entries and duplicates
    # After natural sort:
    # AN1.1, AN1.2, AN1.10, AN1.3, AN1.4 (AN1.4 is consecutive duplicate of AN1.3 -> removed)
    # MN1, MN2, MN10
    test_data = """suttacode\tdv_summary\tdv_key_excerpt1\tdv_key_excerpt2
AN1.10\tSummary A\tExcerpt 1\tExcerpt 2
AN1.2\tSummary B\tExcerpt 3\tExcerpt 4
AN1.1\tSummary A\tExcerpt 1\tExcerpt 2
AN1.4\tSummary C\tExcerpt 5\tExcerpt 6
AN1.3\tSummary C\tExcerpt 5\tExcerpt 6
MN1\tSummary D\tExcerpt 7\tExcerpt 8
MN10\tSummary E\tExcerpt 9\tExcerpt 10
MN2\tSummary F\tExcerpt 11\tExcerpt 12"""

    # Write to a temporary file
    pth = ProjectPaths()
    temp_path = pth.dpd_db_path.parent / "temp_test_dv_catalogue.tsv"

    try:
        temp_path.write_text(test_data, encoding="utf-8")

        # Temporarily replace the TSV path for testing
        original_path = pth.dv_catalogue_suttas_tsv_path
        pth.dv_catalogue_suttas_tsv_path = temp_path

        # Mock the download function to use our test file
        from db.suttas import dv_catalogue_suttas

        original_download = dv_catalogue_suttas.download_dv_catalogue

        def mock_download(filepath: Path) -> bool:
            return False  # Force use of local file

        dv_catalogue_suttas.download_dv_catalogue = mock_download

        # Read the catalogue
        result = read_dv_catalogue(pth)

        actual_codes = list(result.keys())

        # Check that AN1.10 comes after AN1.2 in natural sort
        assert actual_codes.index("AN1.10") > actual_codes.index("AN1.2"), (
            "AN1.10 should come after AN1.2 (natural sorting)"
        )

        # Check that MN10 comes after MN2 (not before)
        assert actual_codes.index("MN10") > actual_codes.index("MN2"), (
            "MN10 should come after MN2 (natural sorting)"
        )

        # Verify consecutive duplicate removal: AN1.4 is consecutive duplicate of AN1.3 after sorting
        # After natural sort: AN1.1, AN1.2, AN1.10, AN1.3, AN1.4, MN1, MN2, MN10
        # AN1.3 and AN1.4 have identical summary/key_excerpt1/key_excerpt2
        # AN1.4 should be removed as consecutive duplicate
        assert "AN1.1" in actual_codes, "AN1.1 should be present"
        assert "AN1.2" in actual_codes, "AN1.2 should be present"
        assert "AN1.10" in actual_codes, "AN1.10 should be present"
        assert "AN1.3" in actual_codes, "AN1.3 should be present"
        assert "AN1.4" not in actual_codes, (
            "AN1.4 should be removed (consecutive duplicate)"
        )
        assert "MN1" in actual_codes, "MN1 should be present"
        assert "MN2" in actual_codes, "MN2 should be present"
        assert "MN10" in actual_codes, "MN10 should be present"

        # Verify expected number of entries
        assert len(actual_codes) == 7, f"Expected 7 entries, got {len(actual_codes)}"

    finally:
        # Restore original functions
        dv_catalogue_suttas.download_dv_catalogue = original_download
        pth.dv_catalogue_suttas_tsv_path = original_path

        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()
