"""Tests for output generation in proofreader."""

import csv
import os
from pathlib import Path
from tools.proofreader import save_results

def test_save_results(tmp_path):
    """Test saving results to TSV."""
    results = [
        {"id": 1, "lemma_1": "test1", "meaning_1": "m1", "meaning_1_corrected": "m1c"},
        {"id": 2, "lemma_1": "test2", "meaning_1": "m2", "meaning_1_corrected": "m2c"}
    ]
    filename = tmp_path / "test_output.tsv"
    save_results(results, str(filename))
    
    assert filename.exists()
    with open(filename, newline="", encoding="utf-8") as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["id"] == "1"
        assert rows[0]["meaning_1_corrected"] == "m1c"
