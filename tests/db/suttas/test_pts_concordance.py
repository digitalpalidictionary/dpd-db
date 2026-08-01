"""Behavioural tests for db/suttas/pts_concordance.py and its converter.

Uses a real SQLite file db with the real SuttaInfo model — no mocks — because
update_pts_concordance_in_db opens its own session from ProjectPaths.
"""

from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, SuttaInfo
from db.suttas.convert_pts_concordance import build_rows, classify_cst_ref
from db.suttas.pts_concordance import update_pts_concordance_in_db
from tools.paths import ProjectPaths

TSV = """cst_file\tcst_paranum\tpts_ref\tnikaya\twork\tnumber\ttitle
romn/s0101m.mul.xml\t1\tD i 1,7\tDN\tD\t1\tBrahmajāla
romn/s0101m.mul.xml\t150\tD i 47,3\tDN\tD\t2\tSāmaññaphala
"""


@pytest.fixture
def pth(tmp_path: Path) -> Iterator[ProjectPaths]:
    paths = ProjectPaths(base_dir=tmp_path)
    engine = create_engine(f"sqlite:///{paths.dpd_db_path}", echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()
    paths.pts_concordance_tsv_path.parent.mkdir(parents=True, exist_ok=True)
    paths.pts_concordance_tsv_path.write_text(TSV, encoding="utf-8")
    yield paths


def _session(pth: ProjectPaths) -> Session:
    return sessionmaker(bind=create_engine(f"sqlite:///{pth.dpd_db_path}"))()


def _add_rows(pth: ProjectPaths, rows: list[tuple[str, str, str, str]]) -> None:
    session = _session(pth)
    for dpd_code, cst_file, cst_paranum, dv_pts in rows:
        row = SuttaInfo()
        row.dpd_sutta = dpd_code  # primary key
        row.dpd_code = dpd_code
        row.cst_file = cst_file
        row.cst_paranum = cst_paranum
        row.dv_pts = dv_pts
        session.add(row)
    session.commit()
    session.close()


def _pts_by_code(pth: ProjectPaths) -> dict[str, str]:
    session = _session(pth)
    result = {row.dpd_code: row.dv_pts for row in session.query(SuttaInfo).all()}
    session.close()
    return result


def test_matched_row_gets_concordance_pts(pth: ProjectPaths) -> None:
    _add_rows(pth, [("DN2", "romn/s0101m.mul.xml", "150", "")])

    update_pts_concordance_in_db(pth)

    assert _pts_by_code(pth)["DN2"] == "D i 47,3"


def test_unmatched_row_is_left_untouched(pth: ProjectPaths) -> None:
    _add_rows(
        pth,
        [
            ("AN3.48", "romn/s0402m2.mul.xml", "48", "A i 152"),
            ("AN3.63", "", "", "A i 178"),
        ],
    )

    update_pts_concordance_in_db(pth)

    pts = _pts_by_code(pth)
    assert pts["AN3.48"] == "A i 152"
    assert pts["AN3.63"] == "A i 178"


def test_multi_row_key_writes_every_row(pth: ProjectPaths) -> None:
    """A vagga and its first sutta share (cst_file, cst_paranum); both get the ref."""
    _add_rows(
        pth,
        [
            ("DN1-13", "romn/s0101m.mul.xml", "1", ""),
            ("DN1", "romn/s0101m.mul.xml", "1", ""),
        ],
    )

    update_pts_concordance_in_db(pth)

    pts = _pts_by_code(pth)
    assert pts["DN1-13"] == "D i 1,7"
    assert pts["DN1"] == "D i 1,7"


def test_range_paranum_falls_back_to_its_start_paragraph(pth: ProjectPaths) -> None:
    """121 rows store cst_paranum as a range; the concordance keys on the start."""
    _add_rows(pth, [("DN1-13", "romn/s0101m.mul.xml", "1-149", "")])

    update_pts_concordance_in_db(pth)

    assert _pts_by_code(pth)["DN1-13"] == "D i 1,7"


def test_stale_dv_reference_is_overwritten_on_an_incremental_run(
    pth: ProjectPaths,
) -> None:
    """The step is unguarded, so a row still holding a DV-format ref gets updated."""
    _add_rows(pth, [("DN2", "romn/s0101m.mul.xml", "150", "D i 47")])

    update_pts_concordance_in_db(pth)

    assert _pts_by_code(pth)["DN2"] == "D i 47,3"


def test_chapter_relative_forms_are_not_joinable() -> None:
    assert classify_cst_ref("s0517m:c2") is None
    assert classify_cst_ref("s0517m:c2.5") is None
    assert classify_cst_ref("s0517m:c2.5-7") is None


def test_range_and_item_forms_key_on_their_start_paragraph() -> None:
    assert classify_cst_ref("s0101m:1-149") == ("s0101m", "a-b", "1")
    assert classify_cst_ref("s0302m:73.2") == ("s0302m", "n.item", "73")
    assert classify_cst_ref("s0101m:150") == ("s0101m", "n", "150")


def test_build_rows_skips_chapter_forms_and_ranks_duplicate_keys() -> None:
    df = pd.DataFrame(
        [
            {
                "Status": "Collated",
                "CST reference": "s0401m:1-5",
                "PTS reference": "A i 1,15",
                "Nikāya": "AN",
                "Work": "A",
                "Number": "1.1-5",
                "Title": "Rūpādi",
            },
            {
                "Status": "Collated",
                "CST reference": "s0401m:1",
                "PTS reference": "A i 1,5",
                "Nikāya": "AN",
                "Work": "A",
                "Number": "1.1",
                "Title": "Rūpādi",
            },
            {
                "Status": "Collated",
                "CST reference": "s0517m:c2.5",
                "PTS reference": "Cp 2.5",
                "Nikāya": "KN",
                "Work": "Cp",
                "Number": "2.5",
                "Title": "Cariyāpiṭaka",
            },
            {
                "Status": "Not collated",
                "CST reference": "s0520m:1",
                "PTS reference": "Ja i 1",
                "Nikāya": "KN",
                "Work": "Ja",
                "Number": "1",
                "Title": "Apaṇṇaka",
            },
        ]
    )

    rows, collated_count, skipped_chapter_form = build_rows(df)

    assert collated_count == 3
    assert skipped_chapter_form == 1
    assert len(rows) == 1
    assert rows[0]["cst_file"] == "romn/s0401m.mul.xml"
    assert rows[0]["cst_paranum"] == "1"
    assert rows[0]["pts_ref"] == "A i 1,5"


def test_blank_cells_become_empty_strings() -> None:
    df = pd.DataFrame(
        [
            {
                "Status": "Collated",
                "CST reference": "s0515m:190",
                "PTS reference": "Nidd I 16",
                "Nikāya": "KN",
                "Work": "Nidd I",
                "Number": None,
                "Title": "Sāriputtasuttaniddesa",
            }
        ]
    )

    rows, _, _ = build_rows(df)

    assert rows[0]["number"] == ""
