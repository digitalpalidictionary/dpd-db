"""Populate sutta_info.dv_pts from the vendored PTS↔CST concordance TSV.

The TSV is produced by db/suttas/convert_pts_concordance.py from the source XLSX
(https://github.com/jorgecaa/pts-vri-concordance, CC0). PTS references used to come
from the DV catalogue; the concordance is now the sole source.
"""

import csv

from db.db_helpers import get_db_session
from db.models import SuttaInfo
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def read_pts_concordance(pth: ProjectPaths) -> dict[tuple[str, str], str]:
    """Read the vendored TSV into a lookup of (cst_file, cst_paranum) -> PTS ref."""
    tsv_path = pth.pts_concordance_tsv_path

    if not tsv_path.exists():
        pr.red("no pts concordance tsv available")
        return {}

    pr.green_tmr("reading pts concordance")
    with open(tsv_path, encoding="utf-8", newline="") as f:
        concordance = {
            (row["cst_file"], row["cst_paranum"]): row["pts_ref"]
            for row in csv.DictReader(f, delimiter="\t")
            if row["pts_ref"]
        }
    pr.yes(len(concordance))
    return concordance


def update_pts_concordance_in_db(pth: ProjectPaths) -> None:
    """Update the PTS reference of every SuttaInfo row found in the concordance.

    Runs unconditionally: the TSV is vendored, so there is nothing to re-download
    and compare, and skipping when sutta_info was not rebuilt would leave the old
    DV-sourced references in place on every incremental run. The write is local,
    deterministic and idempotent.
    """
    concordance = read_pts_concordance(pth)
    if not concordance:
        pr.red("no pts references to apply")
        return

    db_session = get_db_session(pth.dpd_db_path)

    pr.green_tmr("updating pts in db")
    try:
        sutta_records = db_session.query(SuttaInfo).all()
        updated_count = 0

        for sutta_record in sutta_records:
            paranum = sutta_record.cst_paranum
            pts_ref = concordance.get((sutta_record.cst_file, paranum))
            if pts_ref is None and "-" in paranum:
                # 121 rows store a paragraph range; the concordance keys on the start.
                start_para = paranum.split("-", 1)[0]
                pts_ref = concordance.get((sutta_record.cst_file, start_para))
            if pts_ref:
                sutta_record.dv_pts = pts_ref
                updated_count += 1

        db_session.commit()
        pr.yes(updated_count)
        not_found_count = len(sutta_records) - updated_count
        if not_found_count:
            pr.red(
                f"{not_found_count} / {len(sutta_records)} sutta_info rows have no concordance pts"
            )

    except Exception as e:
        pr.no(f"failed to update pts references: {e}")
        db_session.rollback()
    finally:
        db_session.close()


def main() -> None:
    pth = ProjectPaths()
    update_pts_concordance_in_db(pth)


if __name__ == "__main__":
    main()
