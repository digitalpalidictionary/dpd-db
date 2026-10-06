"""Parity check of the ePitaka exporter against the upstream baseline file.

Modes:
  snapshot <tsv_dir>  Render headword and root HTML from the 1 May 2026 backup
                      TSVs (the data the baseline was built from) and compare
                      by id / root key. Extract the TSVs with
                      `git show babe7108:db/backup_tsv/<name>.tsv > <tsv_dir>/<name>.tsv`.
  output              Compare exporter/epitaka/output/dpd-dictionary.db with
                      the baseline: roots by key, lookup by key (ids mapped to
                      lemma_1 / root on both sides).

Run from the project root: uv run kamma/threads/20261006_epitaka_dpd_export/artifacts/parity.py <mode> ...
"""

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from db.db_helpers import get_db_session
from db.families.family_root import (
    compile_rf_html,
    make_roots_family_dict_and_bases_dict,
)
from db.models import DpdHeadword, DpdRoot, FamilyRoot
from exporter.epitaka.epitaka_exporter import make_headword_html, make_root_html
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

pth = ProjectPaths()
csv.field_size_limit(10**9)


def first_diff(a: str, b: str) -> int:
    for n, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return n
    return min(len(a), len(b))


def group_of(html: str, pos: int) -> str:
    """Name of the last class opened before the differing character."""
    classes = re.findall(r"class='([^']+)'", html[: pos + 1])
    if "</summary>" not in html[:pos]:
        return "summary"
    return classes[-1] if classes else "?"


def report(
    name: str, base: dict[str, str], new: dict[str, str], samples: int = 3
) -> dict[str, list[str]]:
    shared = base.keys() & new.keys()
    same = sum(1 for k in shared if base[k] == new[k])
    groups: dict[str, list[str]] = defaultdict(list)
    for k in sorted(shared):
        if base[k] != new[k]:
            pos = first_diff(base[k], new[k])
            groups[group_of(base[k], pos)].append(k)
    print(
        f"\n== {name}: shared {len(shared)}, identical {same} "
        f"({same / max(len(shared), 1):.4%}), only baseline "
        f"{len(base.keys() - new.keys())}, only new {len(new.keys() - base.keys())}"
    )
    for g, keys in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"-- group {g}: {len(keys)}")
        for k in keys[:samples]:
            pos = first_diff(base[k], new[k])
            start = max(pos - 60, 0)
            print(
                f"   {k}\n     base: {base[k][start : pos + 80]!r}"
                f"\n     new : {new[k][start : pos + 80]!r}"
            )
    return groups


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def snapshot(tsv_dir: Path) -> None:
    roots: dict[str, DpdRoot] = {}
    for row in read_tsv(tsv_dir / "dpd_roots_part_001.tsv"):
        row["root_group"] = int(row["root_group"])  # type: ignore[assignment]
        roots[row["root"]] = DpdRoot(**row)

    columns = {c.key for c in DpdHeadword.__table__.columns}
    headwords: list[DpdHeadword] = []
    for part in sorted(tsv_dir.glob("dpd_headwords_part_*.tsv")):
        for row in read_tsv(part):
            data = {k: v for k, v in row.items() if k in columns}
            data["id"] = int(data["id"])  # type: ignore[assignment]
            i = DpdHeadword(**data)
            if i.root_key:
                i.rt = roots[i.root_key]
            headwords.append(i)

    con = sqlite3.connect(f"file:{pth.epitaka_baseline_db_path}?mode=ro", uri=True)
    base_hw: dict[str, str] = {}
    base_roots: dict[str, str] = {}
    for id_, lemma, html in con.execute(
        "SELECT id, lemma_1, meaning_html FROM dpd_headwords"
    ):
        if html.startswith("<details class='dpd-root-meaning'>"):
            base_roots[lemma] = html
        else:
            base_hw[str(id_)] = html

    new_hw = {str(i.id): make_headword_html(i) for i in headwords}
    report("headwords (May snapshot)", base_hw, new_hw)

    # Root family tables are not in the backup TSVs; take them from live dpd.db.
    db_session = get_db_session(pth.dpd_db_path)
    families: dict[str, list[FamilyRoot]] = defaultdict(list)
    for f in db_session.query(FamilyRoot).all():
        families[f.root_key].append(f)
    word_counts: dict[str, int] = defaultdict(int)
    for i in headwords:
        if i.root_key:
            word_counts[i.root_key] += 1
    new_roots = {
        k: make_root_html(r, word_counts[k], families[k]) for k, r in roots.items()
    }
    report("roots (May snapshot fields, live families)", base_roots, new_roots)

    # The family tables changed since May, so prove the rest of the root rules
    # without them, and prove the table order by the family names alone.
    def without_tables(html: str) -> str:
        return re.sub(r"<p class='heading underlined'>.*?</table>", "", html)

    def family_names(html: str) -> str:
        return " | ".join(re.findall(r"belongs? to the root family <b>(.*?)</b>", html))

    report(
        "roots without family tables",
        {k: without_tables(v) for k, v in base_roots.items()},
        {k: without_tables(v) for k, v in new_roots.items()},
    )
    report(
        "roots: family table order",
        {k: family_names(v) for k, v in base_roots.items()},
        {k: family_names(v) for k, v in new_roots.items()},
    )

    # Order of the families both sides have; a difference here is a rule bug,
    # not a family added or removed since May.
    def common_order(a: str, b: str) -> str:
        shared = set(a.split(" | ")) & set(b.split(" | "))
        return " | ".join(x for x in a.split(" | ") if x in shared)

    base_names = {k: family_names(v) for k, v in base_roots.items()}
    new_names = {k: family_names(v) for k, v in new_roots.items()}
    # family_root rows are inserted in order of each family's first headword in
    # Pāḷi sort (db/families/family_root.py), so May data predicts May order.
    may_order: dict[str, list[str]] = defaultdict(list)
    for i in sorted(headwords, key=lambda x: pali_sort_key(x.lemma_1)):
        if i.root_key and i.family_root not in may_order[i.root_key]:
            may_order[i.root_key].append(i.family_root)
    report(
        "roots: baseline family order vs order predicted from May data",
        base_names,
        {k: " | ".join(may_order[k]) for k in base_names},
    )

    # Rebuild the May family tables with the project's own family builder.
    may_family_db = sorted(
        (i for i in headwords if i.family_root), key=lambda x: pali_sort_key(x.lemma_1)
    )
    rf_dict, _ = make_roots_family_dict_and_bases_dict(may_family_db)
    rf_dict = compile_rf_html(may_family_db, rf_dict)
    may_families: dict[str, list[FamilyRoot]] = defaultdict(list)
    for rf in rf_dict.values():
        may_families[rf["root_key"]].append(FamilyRoot(html=rf["html"]))
    report(
        "roots with May family tables (full parity)",
        base_roots,
        {
            k: make_root_html(r, word_counts[k], may_families[k])
            for k, r in roots.items()
        },
    )

    report(
        "roots: order of families present on both sides",
        {k: common_order(base_names[k], new_names[k]) for k in base_names},
        {k: common_order(new_names[k], base_names[k]) for k in base_names},
    )

    # root id order
    base_order = [
        lemma
        for (lemma,) in con.execute(
            "SELECT lemma_1 FROM dpd_headwords WHERE id > 89412 ORDER BY id"
        )
    ]
    print("\nroot id order plain-sorted:", base_order == sorted(base_order))


def output() -> None:
    con = sqlite3.connect(f"file:{pth.epitaka_dpd_db_path}?mode=ro", uri=True)
    con.execute(f"ATTACH 'file:{pth.epitaka_baseline_db_path}?mode=ro' AS b")

    def names(schema: str) -> dict[int, str]:
        return dict(con.execute(f"SELECT id, lemma_1 FROM {schema}.dpd_headwords"))

    def roots(schema: str) -> dict[str, str]:
        return {
            lemma: html
            for lemma, html in con.execute(
                f"SELECT lemma_1, meaning_html FROM {schema}.dpd_headwords "
                "WHERE meaning_html LIKE '<details class=''dpd-root-meaning''>%'"
            )
        }

    report("roots (output vs baseline)", roots("b"), roots("main"))

    def lookup(schema: str) -> dict[str, str]:
        id_name = names(schema)
        out: dict[str, str] = {}
        for key, hw, dec in con.execute(
            f"SELECT lookup_key, headwords, deconstructor FROM {schema}.dpd_lookup"
        ):
            hw_names = (
                "["
                + ", ".join(id_name[int(x)] for x in hw.strip("[]").split(", "))
                + "]"
                if hw
                else "NULL"
            )
            out[key] = f"<summary>{hw_names} | {dec}</summary>"
        return out

    report("lookup (ids mapped to names)", lookup("b"), lookup("main"))

    print("\nschema main:")
    for (sql,) in con.execute("SELECT sql FROM main.sqlite_master ORDER BY name"):
        print(sql)
    print("\nschema baseline:")
    for (sql,) in con.execute("SELECT sql FROM b.sqlite_master ORDER BY name"):
        print(sql)


if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        snapshot(Path(sys.argv[2]))
    else:
        output()
