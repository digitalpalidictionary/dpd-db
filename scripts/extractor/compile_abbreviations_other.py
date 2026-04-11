"""Compile master abbreviation list from in-repo sources into
shared_data/help/abbreviations_other.tsv. Issue #77."""

import csv
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

from bs4 import BeautifulSoup
from bs4.element import Tag

from tools.printer import printer as pr

GRAMMAR_TAGS: set[str] = {
    "abl",
    "abs",
    "absol",
    "abstr",
    "acc",
    "act",
    "adj",
    "adv",
    "aor",
    "app",
    "agent",
    "caus",
    "cond",
    "dat",
    "desid",
    "denom",
    "f",
    "fem",
    "fut",
    "gen",
    "ger",
    "imp",
    "impers",
    "ind",
    "inf",
    "instr",
    "intens",
    "interj",
    "loc",
    "masc",
    "mid",
    "neg",
    "nom",
    "nt",
    "opt",
    "part",
    "pass",
    "past",
    "perf",
    "pl",
    "pp",
    "ppr",
    "pres",
    "pron",
    "refl",
    "sg",
    "vb",
    "voc",
}

GRAMMAR_KEYWORDS: tuple[str, ...] = (
    "ablative",
    "absolutive",
    "abstract",
    "accusative",
    "active",
    "adjective",
    "adverb",
    "aorist",
    "causative",
    "conditional",
    "dative",
    "denominative",
    "desiderative",
    "feminine",
    "future",
    "genitive",
    "gerund",
    "imperative",
    "impersonal",
    "indicative",
    "infinitive",
    "instrumental",
    "intensive",
    "interjection",
    "locative",
    "masculine",
    "middle",
    "neuter",
    "nominative",
    "noun",
    "optative",
    "participle",
    "passive",
    "past",
    "perfect",
    "person",
    "plural",
    "pronoun",
    "reflexive",
    "singular",
    "verb",
    "vocative",
)


@dataclass
class AbbrevRow:
    source: str
    abbreviation: str
    meaning: str
    category: str
    notes: str


def infer_category(abbrev: str, meaning: str) -> str:
    stripped = abbrev.strip()
    # Symbol: entirely non-alphanumeric (allow spaces)
    if stripped and not any(c.isalnum() for c in stripped):
        return "symbol"
    # Grammar: matches known grammar tag list
    tag = re.sub(r"[.\s]+$", "", stripped).lower()
    if tag in GRAMMAR_TAGS:
        return "grammar"
    # Grammar: meaning describes a grammatical concept
    meaning_lower = meaning.lower()
    if any(kw in meaning_lower for kw in GRAMMAR_KEYWORDS):
        return "grammar"
    # Text: starts with uppercase, contains dot or multiple caps → text reference
    if (
        stripped
        and stripped[0].isupper()
        and ("." in stripped or any(c.isupper() for c in stripped[1:]))
    ):
        return "text"
    return "other"


def load_pts(root: Path) -> list[AbbrevRow]:
    path = root / "shared_data/abbreviations/abbreviations_pts.tsv"
    rows: list[AbbrevRow] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            abbrev = row.get("Abbreviation", "").strip().strip('"')
            meaning = row.get("Meaning", "").strip().strip('"')
            if not abbrev:
                continue
            rows.append(
                AbbrevRow(
                    source="pts",
                    abbreviation=abbrev,
                    meaning=meaning,
                    category=infer_category(abbrev, meaning),
                    notes="",
                )
            )
    return rows


def load_dpd_db(root: Path) -> list[AbbrevRow]:
    """Load abbreviations directly from the DPD database (pos='abbrev')."""
    db_path = root / "dpd.db"
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT lemma_1, meaning_1 FROM dpd_headwords WHERE pos='abbrev';")
    rows: list[AbbrevRow] = []
    for lemma_1, meaning_1 in cur.fetchall():
        # Strip numeric homonym suffix: "a 4.1" → "a", "ma 4.2" → "ma"
        abbrev = re.sub(r"\s+\d+(\.\d+)*$", "", lemma_1).strip()
        # Strip "abbreviation of " / "abbrev of " prefix (handle double prefix too)
        meaning = re.sub(
            r"^(abbreviation|abbrev) of ", "", meaning_1 or "", flags=re.IGNORECASE
        )
        meaning = re.sub(
            r"^(abbreviation|abbrev) of ", "", meaning, flags=re.IGNORECASE
        )
        meaning = meaning.strip()
        if not abbrev:
            continue
        rows.append(
            AbbrevRow(
                source="dpd_db",
                abbreviation=abbrev,
                meaning=meaning,
                category="text",
                notes="",
            )
        )
    con.close()
    return rows


def load_general(root: Path) -> list[AbbrevRow]:
    """Load from abbreviations_bryan.tsv — clean UTF-8, 4-column format."""
    path = root / "shared_data/abbreviations/abbreviations_bryan.tsv"
    rows: list[AbbrevRow] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            abbrev = row.get("abbreviation", "").strip()
            meaning = row.get("meaning", "").strip()
            category = row.get("category", "").strip() or infer_category(
                abbrev, meaning
            )
            notes = row.get("notes", "").strip()
            if not abbrev:
                continue
            rows.append(
                AbbrevRow(
                    source="general",
                    abbreviation=abbrev,
                    meaning=meaning,
                    category=category,
                    notes=notes,
                )
            )
    return rows


def load_cone(root: Path) -> list[AbbrevRow]:
    path = (
        root
        / "resources/other-dictionaries/dictionaries/cone/source/cone_front_matter.json"
    )
    data: dict = json.loads(path.read_text(encoding="utf-8"))
    html = data["abbreviations"]
    soup = BeautifulSoup(html, "html.parser")
    rows: list[AbbrevRow] = []
    for tr in soup.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        abbrev = tds[0].get_text(strip=True)
        # Use "; " as separator for <br>-split sub-entries in meaning
        meaning = tds[1].get_text(separator="; ", strip=True)
        # Collapse multiple whitespace
        meaning = re.sub(r"\s{2,}", " ", meaning).strip()
        if not abbrev and not meaning:
            continue
        if not abbrev:
            continue
        rows.append(
            AbbrevRow(
                source="cone",
                abbreviation=abbrev,
                meaning=meaning,
                category=infer_category(abbrev, meaning),
                notes="",
            )
        )
    return rows


def load_cpd(root: Path) -> list[AbbrevRow]:
    db_path = root / "resources/other-dictionaries/dictionaries/cpd/source/cpd_clean.db"
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT html FROM entries WHERE article_id=90003;")
    result = cur.fetchone()
    con.close()
    if not result:
        raise RuntimeError("CPD: article_id=90003 not found in cpd_clean.db")
    html = result[0]
    soup = BeautifulSoup(html, "html.parser")

    # Find <h2>A. Abbreviations</h2>
    h2 = None
    for tag in soup.find_all("h2"):
        if "Abbreviation" in tag.get_text():
            h2 = tag
            break
    if not h2:
        raise RuntimeError("CPD: <h2> containing 'Abbreviations' not found")

    rows: list[AbbrevRow] = []
    current_h3 = ""

    for sibling in h2.next_siblings:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name == "h2":
            break
        if sibling.name == "h3":
            current_h3 = sibling.get_text(strip=True)
            continue
        if sibling.name == "p":
            # Skip preamble paragraphs; they describe method of quoting
            continue
        if sibling.name == "table":
            # 3-column table: col0=abbrev, col1=ref_code (optional), col2=meaning
            h3_lower = current_h3.lower()
            if "text" in h3_lower:
                default_category = "text"
            elif "gramm" in h3_lower:
                default_category = "grammar"
            else:
                default_category = "other"

            for tr in sibling.find_all("tr"):
                if not isinstance(tr, Tag):
                    continue
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue
                abbrev = tds[0].get_text(strip=True)
                # col1 is reference code; col2 is meaning when present
                if len(tds) >= 3:
                    ref_code = tds[1].get_text(strip=True)
                    meaning = tds[2].get_text(separator="; ", strip=True)
                else:
                    ref_code = ""
                    meaning = tds[1].get_text(separator="; ", strip=True)
                meaning = re.sub(r"\s{2,}", " ", meaning).strip()
                if not abbrev:
                    continue
                # Skip "see X" cross-reference-only rows with no real meaning
                notes_val = f"{current_h3}; ref={ref_code}" if ref_code else current_h3
                rows.append(
                    AbbrevRow(
                        source="cpd",
                        abbreviation=abbrev,
                        meaning=meaning,
                        category=infer_category(abbrev, meaning)
                        if default_category == "grammar"
                        else default_category,
                        notes=notes_val,
                    )
                )

    if not rows:
        raise RuntimeError("CPD: zero rows extracted — HTML structure may have changed")
    return rows


def dedupe_and_sort(rows: list[AbbrevRow]) -> list[AbbrevRow]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[AbbrevRow] = []
    for row in rows:
        key = (row.source, row.abbreviation, row.meaning)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    unique.sort(key=lambda r: (r.source, r.abbreviation.lower(), r.meaning))
    return unique


def write_tsv(rows: list[AbbrevRow], out: Path) -> None:
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["source", "abbreviation", "meaning", "category", "notes"])
        for row in rows:
            writer.writerow(
                [row.source, row.abbreviation, row.meaning, row.category, row.notes]
            )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_path = root / "shared_data/help/abbreviations_other.tsv"

    pr.yellow_title("Compile abbreviations from other sources — Issue #77")

    all_rows: list[AbbrevRow] = []

    loaders: list[tuple[str, Callable[[Path], list[AbbrevRow]]]] = [
        ("pts", load_pts),
        ("dpd_db", load_dpd_db),
        ("general", load_general),
        ("cone", load_cone),
        ("cpd", load_cpd),
    ]

    for name, loader in loaders:
        pr.green_tmr(f"Loading {name}")
        rows = loader(root)  # type: ignore[operator]
        pr.yes(str(len(rows)))
        pr.summary(name, len(rows))
        all_rows.extend(rows)

    pr.green_tmr("Deduplicating and sorting")
    all_rows = dedupe_and_sort(all_rows)
    pr.yes(str(len(all_rows)))

    pr.green_tmr("Writing TSV")
    write_tsv(all_rows, out_path)
    pr.yes("done")

    pr.summary("total rows", len(all_rows))
    pr.summary("output", str(out_path.relative_to(root)))


if __name__ == "__main__":
    main()
