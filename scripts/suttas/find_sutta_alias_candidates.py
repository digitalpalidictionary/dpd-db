#!/usr/bin/env python3

"""Find candidate sutta name variants from sc_sutta field.

Reads the already-populated SuttaInfo table, computes cleaned candidates,
validates them, and writes temp/sutta_alias_candidates.tsv for manual review.
"""

import csv
import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SuttaInfo
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sutta_name_cleaning import clean_sc_sutta

pth = ProjectPaths()


def main() -> None:
    pr.tic()
    pr.green_title("Finding sutta alias candidates")

    db_path = pth.dpd_db_path
    with get_db_session(db_path) as db:
        sutta_rows: list[SuttaInfo] = db.query(SuttaInfo).all()
        headword_lemmas: set[str] = {r[0] for r in db.query(DpdHeadword.lemma_1).all()}

    all_dpd_sutta_set: set[str] = {r.dpd_sutta.lower() for r in sutta_rows}

    candidates: list[dict[str, str]] = []

    for row in sutta_rows:
        row_aliases: set[str] = set()
        if row.dpd_sutta_var:
            for alias in row.dpd_sutta_var.split(";"):
                alias = alias.strip().lower()
                if alias:
                    row_aliases.add(alias)

        seen_cleaned: set[str] = set()

        sources: list[tuple[str, str, str]] = [
            ("sc", row.sc_sutta, clean_sc_sutta(row.sc_sutta)),
        ]

        for source, raw, cleaned in sources:
            if not cleaned:
                continue
            dpd_base = re.sub(r"\s+\d+$", "", row.dpd_sutta).lower()
            if cleaned == dpd_base:
                continue
            if cleaned in row_aliases:
                continue

            if cleaned in seen_cleaned:
                candidates.append(
                    {
                        "dpd_sutta": row.dpd_sutta,
                        "source": source,
                        "raw": raw,
                        "cleaned": cleaned,
                        "status": "duplicate_in_row",
                        "note": "duplicate sc cleaned value",
                    }
                )
                continue
            seen_cleaned.add(cleaned)

            if cleaned in all_dpd_sutta_set:
                status = "collides_with_dpd_sutta"
                note = "matches dpd_sutta of another row"
            elif cleaned not in headword_lemmas:
                status = "missing_headword"
                note = "not found as DpdHeadword.lemma_1"
            else:
                status = "ok"
                note = ""

            candidates.append(
                {
                    "dpd_sutta": row.dpd_sutta,
                    "source": source,
                    "raw": raw,
                    "cleaned": cleaned,
                    "status": status,
                    "note": note,
                }
            )

    output_path = Path("temp/sutta_alias_candidates.tsv")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["dpd_sutta", "source", "raw", "cleaned", "status", "note"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(candidates)

    status_counts: dict[str, int] = {}
    for c in candidates:
        status_counts[c["status"]] = status_counts.get(c["status"], 0) + 1

    pr.green(f"Total candidates: {len(candidates)}")
    for status, count in sorted(status_counts.items()):
        pr.summary(status, str(count))

    pr.green(f"Written to {output_path}")

    paste_map: dict[str, list[str]] = {}
    for c in candidates:
        if c["status"] == "duplicate_in_row":
            continue
        dpd_sutta = c["dpd_sutta"]
        cleaned = c["cleaned"]
        if cleaned not in paste_map.get(dpd_sutta, []):
            paste_map.setdefault(dpd_sutta, []).append(cleaned)

    paste_path = Path("temp/sutta_alias_paste.tsv")
    with (
        open(pth.sutta_info_tsv_path, newline="", encoding="utf-8") as f_in,
        open(paste_path, "w", newline="", encoding="utf-8") as f_out,
    ):
        reader = csv.DictReader(f_in, delimiter="\t")
        writer_paste = csv.writer(f_out, delimiter="\t")
        writer_paste.writerow(["dpd_code", "dpd_sutta", "cleaned"])
        for row in reader:
            dpd_code = row.get("dpd_code", "")
            dpd_sutta = row.get("dpd_sutta", "")
            cleaned = ";".join(paste_map.get(dpd_sutta, []))
            writer_paste.writerow([dpd_code, dpd_sutta, cleaned])

    pr.green(f"Paste file written to {paste_path}")
    pr.toc()


if __name__ == "__main__":
    main()
