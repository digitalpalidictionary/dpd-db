"""Count, per book, the words that are missing from the database.

Updates the "Missing Words" page of the docs website (docs/missing_words.md)
and its PDF (docs/missing_words.pdf), with the date at the top. The PDF is made
with the `typst` command line tool. Run monthly on the uposatha day by
`just docs-update`.

Two numbers for each book, and the most frequent missing words:
- Unrecognised: the word is missing and has no data in the lookup table.
  A row with only `epd` data counts as no data.
- Needs a headword: the word is missing and the deconstructor has it, but no
  headword does.
- A word whose lookup row holds an abbreviation (`abbrev`, `abbrev_other`),
  such as "pī" or "syā", is counted in neither and never listed.

"Missing" reflects what is in the database: the word is in none of the headword
inflections, the sandhi OK list, the variant readings or the spelling mistakes.
Words that Pass1 Auto has saved but the database does not hold yet still count as
missing.

KEEP IN SYNC WITH gui2/pass1_auto_controller.py. If Pass1 Auto changes how it
finds missing words, update this script to match. The rule to copy is
`Pass1AutoController.is_missing`, without its saved-words check. The two counts
differ from Pass1 Auto on purpose: it also sends abbreviations and words with only
a variant, spelling, see or grammar row.

A row follows the Pass1 Auto books. Its words are the CST words of the matching
CST books plus the SuttaCentral words, as Pass1 Auto uses both. The CST rows with
no SuttaCentral text (the last four Khuddaka books, the Abhidhamma and all
commentaries) are CST text only.

Usage:
    uv run python tools/docs_update_missing_words.py
"""

import subprocess
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import ColumnElement, func, or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from gui2.books import sutta_central_books
from tools.cst_sc_text_sets import make_cst_text_list
from tools.pali_sort_key import pali_sort_key
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_2col_to_dict
from tools.variants_manager import VariantManager

CHUNK_SIZE = 900
TOP_WORDS = 5
TOTAL_LABEL = "All books added"

# cst_texts joins some commentaries into one key. These keys split them, one
# file each, so every book gets its own row. main() adds them to cst_texts, never
# at import: a shared dict changed on import breaks the tests that check it.
SPLIT_COMMENTARY_FILES: dict[str, list[str]] = {
    "vina1": ["vin01a.att.txt"],
    "vina2": ["vin02a1.att.txt"],
    "vina3": ["vin02a2.att.txt"],
    "vina4": ["vin02a3.att.txt"],
    "vina5": ["vin02a4.att.txt"],
    "dna1": ["s0101a.att.txt"],
    "dna2": ["s0102a.att.txt"],
    "dna3": ["s0103a.att.txt"],
    "mna1": ["s0201a.att.txt"],
    "mna2": ["s0202a.att.txt"],
    "mna3": ["s0203a.att.txt"],
    "sna1": ["s0301a.att.txt"],
    "sna2": ["s0302a.att.txt"],
    "sna3": ["s0303a.att.txt"],
    "sna4": ["s0304a.att.txt"],
    "sna5": ["s0305a.att.txt"],
    "ana1": ["s0401a.att.txt"],
    "ana2": ["s0402a.att.txt"],
    "ana3": ["s0403a.att.txt"],
    "ana4": ["s0404a.att.txt"],
    "abha1": ["abh01a.att.txt"],
    "abha2": ["abh02a.att.txt"],
    "abha3": ["abh03a.att.txt"],
}


class Book(NamedTuple):
    """A table row: the CST books and the SuttaCentral books whose words it adds."""

    name: str
    cst_codes: list[str]
    sc_books: list[str]  # keys of gui2.books.sutta_central_books


def cst_only(pairs: list[tuple[str, str]]) -> list[Book]:
    return [Book(name, [code], []) for code, name in pairs]


VINAYA_ROOT = [
    Book("Vibhaṅga (Bhikkhu and Bhikkhunī)", ["vin1", "vin2"], ["vin1&2", "vin-bi"]),
    Book("Khandhaka (Mahāvagga, Cūḷavagga)", ["vin3", "vin4"], ["vin3&4"]),
    Book("Parivāra", ["vin5"], ["vin5"]),
]
SUTTA_ROOT = [
    Book("Dīgha Nikāya", ["dn1", "dn2", "dn3"], ["dn"]),
    Book("Majjhima Nikāya", ["mn1", "mn2", "mn3"], ["mn"]),
    Book("Saṃyutta Nikāya", ["sn1", "sn2", "sn3", "sn4", "sn5"], ["sn"]),
    Book(
        "Aṅguttara Nikāya",
        [f"an{i}" for i in range(1, 12)],
        ["an"],
    ),
]
# Order and codes follow the Chaṭṭha Saṅgāyana, which puts Milindapañha before
# Nettippakaraṇa and Peṭakopadesa. The last four books have no SuttaCentral text.
KHUDDAKA_ROOT = [
    Book("Khuddakapāṭha", ["kn1"], ["khp"]),
    Book("Dhammapada", ["kn2"], ["dhp"]),
    Book("Udāna", ["kn3"], ["ud"]),
    Book("Itivuttaka", ["kn4"], ["iti"]),
    Book("Suttanipāta", ["kn5"], ["snp"]),
    Book("Vimānavatthu", ["kn6"], ["vv"]),
    Book("Petavatthu", ["kn7"], ["pv"]),
    Book("Theragāthā", ["kn8"], ["th"]),
    Book("Therīgāthā", ["kn9"], ["thi"]),
    Book("Apadāna (Therāpadāna, Therīapadāna)", ["kn10", "kn11"], ["ap"]),
    Book("Buddhavaṃsa", ["kn12"], ["bv"]),
    Book("Cariyāpiṭaka", ["kn13"], ["cp"]),
    Book("Jātaka", ["kn14"], ["ja"]),
    Book("Niddesa (Mahāniddesa, Cūḷaniddesa)", ["kn15", "kn16"], ["nidd1&2"]),
    *cst_only(
        [
            ("kn17", "Paṭisambhidāmagga"),
            ("kn18", "Milindapañha"),
            ("kn19", "Nettippakaraṇa"),
            ("kn20", "Peṭakopadesa"),
        ]
    ),
]

VINAYA_COMMENTARY: list[tuple[str, str]] = [
    ("vina1", "Pārājikakaṇḍa-aṭṭhakathā"),
    ("vina2", "Pācittiya-aṭṭhakathā"),
    ("vina3", "Mahāvagga-aṭṭhakathā"),
    ("vina4", "Cūḷavagga-aṭṭhakathā"),
    ("vina5", "Parivāra-aṭṭhakathā"),
]
# One file covers several nipātas in the last four Aṅguttara commentaries.
SUTTA_COMMENTARY: list[tuple[str, str]] = [
    ("dna1", "Dīgha 1: Sīlakkhandhavagga-aṭṭhakathā"),
    ("dna2", "Dīgha 2: Mahāvagga-aṭṭhakathā"),
    ("dna3", "Dīgha 3: Pāthikavagga-aṭṭhakathā"),
    ("mna1", "Majjhima 1: Mūlapaṇṇāsa-aṭṭhakathā"),
    ("mna2", "Majjhima 2: Majjhimapaṇṇāsa-aṭṭhakathā"),
    ("mna3", "Majjhima 3: Uparipaṇṇāsa-aṭṭhakathā"),
    ("sna1", "Saṃyutta 1: Sagāthāvagga-aṭṭhakathā"),
    ("sna2", "Saṃyutta 2: Nidānavagga-aṭṭhakathā"),
    ("sna3", "Saṃyutta 3: Khandhavagga-aṭṭhakathā"),
    ("sna4", "Saṃyutta 4: Saḷāyatanavagga-aṭṭhakathā"),
    ("sna5", "Saṃyutta 5: Mahāvagga-aṭṭhakathā"),
    ("ana1", "Aṅguttara: Ekakanipāta-aṭṭhakathā"),
    ("ana2", "Aṅguttara: Dukanipāta-aṭṭhakathā (nipātas 2 to 4)"),
    ("ana3", "Aṅguttara: Pañcakanipāta-aṭṭhakathā (nipātas 5 to 7)"),
    ("ana4", "Aṅguttara: Aṭṭhakanipāta-aṭṭhakathā (nipātas 8 to 11)"),
]
# Order and codes follow the Chaṭṭha Saṅgāyana. It puts Milindapañha before
# Nettippakaraṇa and Peṭakopadesa.
# The CST has no commentary for Therīapadāna, Milindapañha or Peṭakopadesa.
KHUDDAKA_COMMENTARY: list[tuple[str, str]] = [
    ("kn1a", "Khuddakapāṭha-aṭṭhakathā"),
    ("kn2a", "Dhammapada-aṭṭhakathā"),
    ("kn3a", "Udāna-aṭṭhakathā"),
    ("kn4a", "Itivuttaka-aṭṭhakathā"),
    ("kn5a", "Suttanipāta-aṭṭhakathā"),
    ("kn6a", "Vimānavatthu-aṭṭhakathā"),
    ("kn7a", "Petavatthu-aṭṭhakathā"),
    ("kn8a", "Theragāthā-aṭṭhakathā"),
    ("kn9a", "Therīgāthā-aṭṭhakathā"),
    ("kn10a", "Apadāna-aṭṭhakathā"),
    ("kn12a", "Buddhavaṃsa-aṭṭhakathā"),
    ("kn13a", "Cariyāpiṭaka-aṭṭhakathā"),
    ("kn14a", "Jātaka-aṭṭhakathā"),
    ("kn15a", "Mahāniddesa-aṭṭhakathā"),
    ("kn16a", "Cūḷaniddesa-aṭṭhakathā"),
    ("kn17a", "Paṭisambhidāmagga-aṭṭhakathā"),
    ("kn19a", "Nettippakaraṇa-aṭṭhakathā"),
]

ABHIDHAMMA_ROOT: list[tuple[str, str]] = [
    ("abh1", "Dhammasaṅgaṇī"),
    ("abh2", "Vibhaṅga"),
    ("abh3", "Dhātukathā"),
    ("abh4", "Puggalapaññatti"),
    ("abh5", "Kathāvatthu"),
    ("abh6", "Yamaka"),
    ("abh7", "Paṭṭhāna"),
]
# One file covers the five last books, Dhātukathā to Paṭṭhāna.
ABHIDHAMMA_COMMENTARY: list[tuple[str, str]] = [
    ("abha1", "Aṭṭhasālinī (Dhammasaṅgaṇī-aṭṭhakathā)"),
    ("abha2", "Sammohavinodanī (Vibhaṅga-aṭṭhakathā)"),
    ("abha3", "Pañcappakaraṇa-aṭṭhakathā (Dhātukathā to Paṭṭhāna)"),
]

TABLES: list[tuple[str, list[Book]]] = [
    ("Vinaya", VINAYA_ROOT),
    ("Four Nikāyas", SUTTA_ROOT),
    ("Khuddaka Nikāya", KHUDDAKA_ROOT),
    ("Abhidhamma", cst_only(ABHIDHAMMA_ROOT)),
    ("Vinaya commentaries", cst_only(VINAYA_COMMENTARY)),
    ("Four Nikāyas commentaries", cst_only(SUTTA_COMMENTARY)),
    ("Khuddaka Nikāya commentaries", cst_only(KHUDDAKA_COMMENTARY)),
    ("Abhidhamma commentaries", cst_only(ABHIDHAMMA_COMMENTARY)),
]


def lookup_has_data() -> ColumnElement[bool]:
    """True for a lookup row with data in any column except `epd`. Rows made
    with raw sql hold NULL, not empty strings, so each column is coalesced."""
    data_columns = [
        getattr(Lookup, column)
        for column in Lookup.__table__.columns.keys()
        if column not in ("lookup_key", "epd")
    ]
    return or_(*[func.coalesce(col, "") != "" for col in data_columns])


class MissingWordFinder:
    """The Pass1AutoController.is_missing rule, plus the two counts of this report."""

    def __init__(self, pth: ProjectPaths) -> None:
        pr.green_title("loading the skip lists")
        self.db_session = get_db_session(pth.dpd_db_path)

        self.all_inflections: set[str] = set()
        for inflections, api_ca_eva_iti in self.db_session.query(
            DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti
        ):
            self.all_inflections.update(inflections.split(","))
            self.all_inflections.update(api_ca_eva_iti.split(","))

        self.sandhi_ok_list: set[str] = set(
            pth.decon_checked.read_text(encoding="utf-8").splitlines()
        )
        self.variants: set[str] = set(VariantManager(pth).variants_dict)
        self.spelling_mistakes: set[str] = set(
            read_tsv_2col_to_dict(pth.spelling_mistakes_path).data
        )

        self.has_data = lookup_has_data()

        pr.summary("inflections", len(self.all_inflections))
        pr.summary("sandhi ok", len(self.sandhi_ok_list))
        pr.summary("variants", len(self.variants))
        pr.summary("spelling mistakes", len(self.spelling_mistakes))

    @staticmethod
    def sc_word_counts(sc_book: str) -> dict[str, int]:
        """How often each Pāḷi word occurs in a SuttaCentral book."""
        source = sutta_central_books[sc_book]
        # Apadāna and Niddesa have two folders. One missing folder would quietly
        # halve the SuttaCentral words, and the CST text alone looks normal.
        if not source.pali_file_list or any(
            not source.make_file_list(folder) for folder in source.pali_paths
        ):
            raise FileNotFoundError(
                f"no SuttaCentral text for '{sc_book}': is resources/sc-data checked out?"
            )
        return {word: len(segments) for word, segments in source.word_dict.items()}

    def is_missing(self, word: str) -> bool:
        return (
            word not in self.all_inflections
            and word not in self.sandhi_ok_list
            and word not in self.variants
            and word not in self.spelling_mistakes
        )

    def classify_missing_words(self, words: list[str]) -> tuple[set[str], set[str]]:
        """Split missing words into (unrecognised, needs a headword).

        A word whose lookup row holds an abbreviation is neither: it is not a
        word to add. Unrecognised: no lookup row, or no data except `epd`.
        Needs a headword: the deconstructor has it and no headword does.
        A word known only as a variant, spelling, see or grammar row is in
        neither group."""
        unknown: set[str] = set(words)
        needs: set[str] = set()
        for i in range(0, len(words), CHUNK_SIZE):
            chunk = words[i : i + CHUNK_SIZE]
            rows = self.db_session.query(
                Lookup.lookup_key,
                Lookup.headwords,
                Lookup.deconstructor,
                Lookup.abbrev,
                Lookup.abbrev_other,
                self.has_data.label("has_data"),
            ).filter(Lookup.lookup_key.in_(chunk))
            for key, headwords, deconstructor, abbrev, abbrev_other, has_data in rows:
                if has_data:
                    unknown.discard(key)
                if abbrev or abbrev_other:
                    continue
                if deconstructor and not headwords:
                    needs.add(key)
        return unknown, needs

    def count_book(self, book: Book) -> tuple[int, int, int, list[tuple[str, int]]]:
        """Return distinct words, unrecognised words, words needing a headword
        and the most frequent missing words with their counts.

        The words are the CST words plus the words only SuttaCentral has. A word
        is counted in the CST text when it has one, as both texts hold the same
        suttas and adding them would double every count."""
        occurrences = Counter(
            make_cst_text_list(book.cst_codes, dedupe=False, show_errors=False)
        )
        sc_counts: Counter[str] = Counter()
        for sc_book in book.sc_books:
            sc_counts.update(self.sc_word_counts(sc_book))
        for word, count in sc_counts.items():
            if word not in occurrences:
                occurrences[word] = count
        missing = [w for w in sorted(occurrences) if self.is_missing(w)]
        unknown, needs = self.classify_missing_words(missing)
        # equal counts in Pāḷi order, so a monthly run lists the same words
        top = sorted(
            unknown | needs, key=lambda w: (-occurrences[w], pali_sort_key(w))
        )[:TOP_WORDS]
        return (
            len(occurrences),
            len(unknown),
            len(needs),
            [(word, occurrences[word]) for word in top],
        )


Row = tuple[str, int, int, int, list[tuple[str, int]]]
# name, words, unrecognised, needs a headword, most frequent missing words

HEADINGS: list[tuple[str, str]] = [
    (
        "Distinct words",
        "The number of different words in the CST and SuttaCentral text of the book.",
    ),
    (
        "Unrecognised",
        "Words that are not recognized at all by DPD.",
    ),
    (
        "Needs a headword",
        "Words that are recognized by the deconstructor, but not as a headword.",
    ),
    (
        "Missing %",
        "Unrecognised plus needs a headword, as a share of the distinct words.",
    ),
]
COLUMNS = ["Book", "Distinct words", "Unrecognised", "Needs a headword", "Missing %"]


def missing_percent(words: int, unknown: int, needs: int) -> str:
    return f"{(unknown + needs) / words:.1%}" if words else ""


DEFINITIONS_TITLE = "What the columns mean"
TABLES_TITLE = "Missing words by book"
CONTRIBUTE_FORM_URL = "https://forms.gle/Z7ENe8CVFpe2yQqKA"
CONTRIBUTE_BEFORE = (
    "If you would like to contribute to the dictionary, please fill in the "
)
CONTRIBUTE_LINK_TEXT = "contribution form"
CONTRIBUTE_AFTER = " and let us know what you would like to help with."
TOP_TITLE = "Most frequent missing words"
TOP_INTRO = (
    f"The {TOP_WORDS} missing words that occur most often in each book,"
    " with how many times each occurs."
)


def count_rows(finder: MissingWordFinder, books: list[Book]) -> list[Row]:
    rows: list[Row] = []
    for book in books:
        words, unknown, needs, top = finder.count_book(book)
        pr.summary(book.name[:19], f"{words:>7,} {unknown:>6,} {needs:>7,}")
        rows.append((book.name, words, unknown, needs, top))
    rows.append(
        (
            TOTAL_LABEL,
            sum(row[1] for row in rows),
            sum(row[2] for row in rows),
            sum(row[3] for row in rows),
            [],
        )
    )
    return rows


def render_markdown(today: str, tables: list[tuple[str, list[Row]]]) -> str:
    lines = [
        "# Missing Words in DPD",
        "",
        f"{CONTRIBUTE_BEFORE}[{CONTRIBUTE_LINK_TEXT}]({CONTRIBUTE_FORM_URL})"
        f'{{target="_blank"}}{CONTRIBUTE_AFTER}',
        "",
        f"**Date: {today}**",
        "",
        "[Download as PDF](missing_words.pdf)",
        "",
        # the CSS class gives every table the same full width
        '<div class="missing-words" markdown>',
        "",
    ]
    lines += [f"## {DEFINITIONS_TITLE}", ""]
    for heading, text in HEADINGS:
        lines += [f"### {heading}", "", text, ""]
    lines += [f"## {TABLES_TITLE}", ""]
    for title, rows in tables:
        lines += [
            f"### {title}",
            "",
            f"| {' | '.join(COLUMNS)} |",
            "|---|---:|---:|---:|---:|",
        ]
        for name, *numbers, _top in rows:
            cells = [
                name,
                *(f"{n:,}" for n in numbers),
                missing_percent(*numbers),
            ]
            if name == TOTAL_LABEL:
                cells = [f"**{c}**" for c in cells]
            lines.append(f"| {' | '.join(cells)} |")
        lines.append("")
    lines += [f"## {TOP_TITLE}", "", TOP_INTRO, ""]
    for title, rows in tables:
        lines += [f"### {title}", ""]
        for name, *_numbers, top in rows:
            if name == TOTAL_LABEL:
                continue
            lines += [f"**{name}**", ""]
            if top:
                lines += [f"{i}. {w} ({n:,})" for i, (w, n) in enumerate(top, 1)]
            else:
                lines.append("No missing words.")
            lines.append("")
    lines.append("</div>")
    return "\n".join(lines)


def typst_escape(text: str) -> str:
    for char in "\\#$*_@<>[]`~":
        text = text.replace(char, "\\" + char)
    return text


def render_typst(today: str, tables: list[tuple[str, list[Row]]]) -> str:
    lines = [
        '#set page(paper: "a4", margin: 1.8cm)',
        "#set text(size: 10pt)",
        '#show link: it => underline(text(fill: rgb("#0b6bcb"), it))',
        "= Missing Words in DPD",
        f"{CONTRIBUTE_BEFORE}"
        f'#link("{CONTRIBUTE_FORM_URL}")[{CONTRIBUTE_LINK_TEXT}]{CONTRIBUTE_AFTER}',
        "",
        f"*Date: {today}*",
        "",
    ]
    lines += [f"== {DEFINITIONS_TITLE}", ""]
    for heading, text in HEADINGS:
        lines += [f"=== {typst_escape(heading)}", "", typst_escape(text), ""]
    lines += [f"== {TABLES_TITLE}", ""]
    for title, rows in tables:
        lines += [
            f"=== {typst_escape(title)}",
            "#table(",
            "  columns: (3fr, 1fr, 1fr, 1fr, 1fr),",
            "  align: (left, right, right, right, right),",
            "  inset: 4pt,",
            "  table.header(" + ", ".join(f"[*{c}*]" for c in COLUMNS) + "),",
        ]
        for name, *numbers, _top in rows:
            cells = [
                typst_escape(name),
                *(f"{n:,}" for n in numbers),
                typst_escape(missing_percent(*numbers)),
            ]
            if name == TOTAL_LABEL:
                cells = [f"*{c}*" for c in cells]
            lines.append("  " + ", ".join(f"[{c}]" for c in cells) + ",")
        lines += [")", ""]
    lines += ["#pagebreak()", f"== {TOP_TITLE}", "", TOP_INTRO, ""]
    for title, rows in tables:
        lines += [f"=== {typst_escape(title)}", ""]
        for name, *_numbers, top in rows:
            if name == TOTAL_LABEL:
                continue
            lines += [f"*{typst_escape(name)}*", ""]
            if top:
                lines += [f"+ {typst_escape(w)} ({n:,})" for w, n in top]
            else:
                lines.append("No missing words.")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    pr.tic()
    cst_texts.update(SPLIT_COMMENTARY_FILES)
    pth = ProjectPaths()
    finder = MissingWordFinder(pth)

    tables: list[tuple[str, list[Row]]] = []
    for title, books in TABLES:
        pr.green_title(title)
        tables.append((title, count_rows(finder, books)))

    today = date.today().isoformat()
    # The PDF is compiled first, to a temporary file: if typst fails, the page and
    # the PDF on the docs site both stay as they were, never one new, one old.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_pdf = Path(tmp) / "missing_words.pdf"
        subprocess.run(
            ["typst", "compile", "-", str(tmp_pdf)],
            input=render_typst(today, tables).encode("utf-8"),
            check=True,
        )
        pth.docs_missing_words_pdf_path.write_bytes(tmp_pdf.read_bytes())
    pr.green(f"written {pth.docs_missing_words_pdf_path}")
    pth.docs_missing_words_md_path.write_text(
        render_markdown(today, tables), encoding="utf-8"
    )
    pr.green(f"written {pth.docs_missing_words_md_path}")
    pr.toc()


if __name__ == "__main__":
    main()
