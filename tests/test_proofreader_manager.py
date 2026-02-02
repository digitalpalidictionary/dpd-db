import csv
import pytest
from tools.proofreader import ProofreaderManager

@pytest.fixture
def temp_tsv(tmp_path):
    tsv_path = tmp_path / "proofreader.tsv"
    data = [
        {"id": "1", "lemma_1": "test1", "meaning_1": "old1", "meaning_1_corrected": "new1"},
        {"id": "2", "lemma_1": "test2", "meaning_1": "old2", "meaning_1_corrected": "new2"},
    ]
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "lemma_1", "meaning_1", "meaning_1_corrected"], delimiter="\t")
        writer.writeheader()
        writer.writerows(data)
    return tsv_path

def test_load_and_pop(temp_tsv):
    manager = ProofreaderManager(temp_tsv)
    assert manager.count == 2
    
    correction, remaining = manager.get_next_correction()
    assert correction["id"] == "1"
    assert remaining == 1
    assert manager.count == 1
    
    # Check if file was updated
    with open(temp_tsv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["id"] == "2"

def test_empty_tsv(tmp_path):
    tsv_path = tmp_path / "empty.tsv"
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "lemma_1", "meaning_1", "meaning_1_corrected"], delimiter="\t")
        writer.writeheader()
        
    manager = ProofreaderManager(tsv_path)
    assert manager.count == 0
    correction, remaining = manager.get_next_correction()
    assert correction is None
    assert remaining == 0
