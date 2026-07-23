import csv
import pytest
from tools.proofreader import ProofreaderManager


def _write_tsv(tsv_path, field, rows):
    with open(tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "lemma_1", field, f"{field}_corrected"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def temp_tsv(tmp_path):
    tsv_path = tmp_path / "proofreader.tsv"
    _write_tsv(
        tsv_path,
        "meaning_1",
        [
            {
                "id": "1",
                "lemma_1": "test1",
                "meaning_1": "old1",
                "meaning_1_corrected": "new1",
            },
            {
                "id": "2",
                "lemma_1": "test2",
                "meaning_1": "old2",
                "meaning_1_corrected": "new2",
            },
        ],
    )
    return tsv_path


def test_load_and_pop(temp_tsv):
    manager = ProofreaderManager([("meaning_1", temp_tsv)])
    assert manager.count == 2

    correction, remaining, field = manager.get_next_correction()
    assert correction is not None
    assert correction["id"] == "1"
    assert field == "meaning_1"
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
    _write_tsv(tsv_path, "meaning_1", [])

    manager = ProofreaderManager([("meaning_1", tsv_path)])
    assert manager.count == 0
    correction, remaining, field = manager.get_next_correction()
    assert correction is None
    assert remaining == 0
    assert field is None


def test_cycles_queues_in_priority_order(tmp_path):
    """One PRead button drains all three queues; each row reports its field."""
    m1 = tmp_path / "proofreader.tsv"
    lit = tmp_path / "proofreader_meaning_lit.tsv"
    m2 = tmp_path / "proofreader_meaning_2.tsv"

    _write_tsv(
        lit,
        "meaning_lit",
        [
            {
                "id": "5",
                "lemma_1": "lit5",
                "meaning_lit": "litold",
                "meaning_lit_corrected": "litnew",
            }
        ],
    )
    _write_tsv(
        m2,
        "meaning_2",
        [
            {
                "id": "9",
                "lemma_1": "two9",
                "meaning_2": "twoold",
                "meaning_2_corrected": "twonew",
            }
        ],
    )
    _write_tsv(m1, "meaning_1", [])  # empty — should be skipped

    manager = ProofreaderManager(
        [("meaning_1", m1), ("meaning_lit", lit), ("meaning_2", m2)]
    )
    assert manager.count == 2

    # meaning_1 empty -> first non-empty is meaning_lit
    correction, remaining, field = manager.get_next_correction()
    assert correction is not None
    assert field == "meaning_lit"
    assert correction["meaning_lit_corrected"] == "litnew"
    assert remaining == 1

    # next drains meaning_2
    correction, remaining, field = manager.get_next_correction()
    assert correction is not None
    assert field == "meaning_2"
    assert correction["meaning_2_corrected"] == "twonew"
    assert remaining == 0

    # exhausted
    correction, remaining, field = manager.get_next_correction()
    assert correction is None
    assert field is None
