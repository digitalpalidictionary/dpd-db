#!/usr/bin/env python3
"""Export DPD to PDF using Typst and Jinja templates.

Typst holds every laid-out page in memory (~2 MB/page) and the full
dictionary is ~15,000 pages, so a single compile needs ~29 GB and OOMs
CI. The document is split into chunks at entry boundaries, each chunk
is compiled in its own `typst` CLI subprocess (~2 GB peak), page
numbering is chained across chunks, and the chunk PDFs are merged with
pypdf (bookmark tree and Contents page rebuilt, since neither survives
a merge). Evidence for every design choice:
kamma/threads/20260707_pdf_chunked_compile/evidence.md
"""

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from pypdf.generic import Destination, NameObject, TextStringObject
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import (
    DpdHeadword,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilyWord,
    Lookup,
)
from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict
from tools.zip_up import zip_up_file

debug = False

# ~500-1000 output pages per chunk: bounds each typst subprocess at
# roughly 2 GB peak RSS even in the dense family sections
CHUNK_LINE_BUDGET = 100_000

ENTRY_PREFIXES = ("#par[", "#heading3[")
OUTLINE_PLACEHOLDER = "#outline(depth: 1)"

# a single-line `#set par(...)`/`#set page(...)` whose effect must be
# replayed at the start of every later chunk; multi-line #set rules are
# NOT captured — body-level #set must stay on one line
STATE_LINE_RE = re.compile(r"^#set (par|page)\(([\w-]+):.*\)$", re.MULTILINE)

SECTION_HEADING_RE = re.compile(r"#heading\(level: 1\)\[(.+?)\]")


class GlobalVars:
    def __init__(self) -> None:
        # database
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)

        # typst
        self.typst_data: list[str] = []
        self.used_letters_single: list[str] = []

        # jinja env
        self.env: Environment = Environment(
            loader=FileSystemLoader("exporter/pdf/templates"),
            autoescape=True,
            block_start_string="////",
            block_end_string="\\\\\\\\",
        )

        # templates
        self.layout_templ = self.env.get_template("layout.typ")
        self.front_matter_templ = self.env.get_template("front_matter.typ")
        self.first_letter_templ = self.env.get_template("first_letter.typ")
        self.abbreviations_templ = self.env.get_template("abbreviations.typ")
        self.headword_templ = self.env.get_template("lite_headword.typ")
        self.epd_templ = self.env.get_template("lite_epd.typ")
        self.root_fam_templ = self.env.get_template("lite_family_root.typ")
        self.word_fam_templ = self.env.get_template("lite_family_word.typ")
        self.compound_fam_templ = self.env.get_template("lite_family_compound.typ")
        self.idiom_fam_templ = self.env.get_template("lite_family_idiom.typ")
        self.bibliography_templ = self.env.get_template("bibliography.typ")
        self.thanks_templ = self.env.get_template("thanks.typ")
        self.date: str = year_month_day_dash()


def make_layout(g: GlobalVars) -> None:
    pr.green_tmr("compiling layout")
    g.typst_data.append(g.layout_templ.render())
    pr.yes("ok")


def make_front_matter(g: GlobalVars) -> None:
    pr.green_tmr("compiling front matter")
    g.typst_data.append(g.front_matter_templ.render())
    pr.yes("ok")


def make_abbreviations(g: GlobalVars) -> None:
    pr.green_tmr("compiling abbreviations")

    abbreviations_tsv = read_tsv_dot_dict(g.pth.abbreviations_tsv_path)
    abbreviations_data = []
    for i in abbreviations_tsv:
        # leave out book names which have a double capital JA
        if not re.findall(r"[A-Z][A-Za-z]", i.abbrev):
            abbreviations_data.append(i)

    g.typst_data.append("#heading(level: 1)[Abbreviations]\n")
    g.typst_data.append(
        "#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n"
    )
    g.typst_data.append(g.abbreviations_templ.render(data=abbreviations_data))
    pr.yes(len(abbreviations_data))


def make_pali_to_english(g: GlobalVars) -> None:
    pr.green_tmr("compiling pali to english")

    if debug:
        dpd_db = g.db_session.query(DpdHeadword).limit(100).all()
    else:
        dpd_db = g.db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#set page(columns: 1)\n")
    g.typst_data.append("#heading(level: 1)[Pāḷi to English Dictionary]\n")
    g.typst_data.append(
        "#set par(first-line-indent: 0pt, hanging-indent: 1em, spacing: 0.65em)\n"
    )

    for i in dpd_db:
        first_letter = i.lemma_1[0]
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)

        g.typst_data.append(g.headword_templ.render(i=i, date=g.date))

    pr.yes(len(dpd_db))


def make_english_to_pali(g: GlobalVars) -> None:
    pr.green_tmr("compiling english to pali")

    if debug:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").limit(100).all()
    else:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").all()
    epd_db = sorted(epd_db, key=lambda x: x.lookup_key.casefold())

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[English to Pāḷi Dictionary]\n")
    g.typst_data.append(
        "#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n"
    )

    problem_characters = [" ", "'", "(", "*", "-", ".", "?", "√"]

    for i in epd_db:
        try:
            first_letter = i.lookup_key[
                0
            ].casefold()  # consider "A" and "a" as the same letter
        except IndexError:  # sometimes there a blank line in the lookup db
            continue

        if (
            first_letter in problem_characters
            # ignore sutta codes, they start with a double capital letter
            or re.findall("^[A-Z][A-Z]", i.lookup_key)
        ):
            continue

        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)

        g.typst_data.append(g.epd_templ.render(i=i, date=g.date))

    pr.yes(len(epd_db))


def make_root_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling root families")

    if debug:
        root_fam_db = g.db_session.query(FamilyRoot).limit(100).all()
    else:
        root_fam_db = g.db_session.query(FamilyRoot).all()
    root_fam_db = sorted(
        root_fam_db,
        key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)),
    )

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Root Families]\n")

    for i in root_fam_db:
        if i.root_key.startswith("√"):
            first_letter = i.root_key[1]

            if first_letter not in g.used_letters_single:
                first_letter_render = g.first_letter_templ.render(
                    first_letter=first_letter
                )
                g.typst_data.append(first_letter_render)
                g.used_letters_single.append(first_letter)

        g.typst_data.append(g.root_fam_templ.render(i=i, date=g.date))

    pr.yes(len(root_fam_db))


def make_word_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling word families")

    if debug:
        word_fam_db: list[FamilyWord] = g.db_session.query(FamilyWord).limit(100).all()
    else:
        word_fam_db: list[FamilyWord] = g.db_session.query(FamilyWord).all()

    word_fam_db = sorted(word_fam_db, key=lambda x: pali_sort_key(x.word_family))  # type: ignore

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Word Families]\n")

    for i in word_fam_db:
        first_letter = i.word_family[0]

        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)

        g.typst_data.append(g.word_fam_templ.render(i=i, date=g.date))

    pr.yes(len(word_fam_db))


def make_compound_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling compound families")

    if debug:
        compound_fam_db = g.db_session.query(FamilyCompound).limit(100).all()
    else:
        compound_fam_db = g.db_session.query(FamilyCompound).all()
    compound_fam_db = sorted(
        compound_fam_db, key=lambda x: pali_sort_key(x.compound_family)
    )

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Compound Families]\n")

    for i in compound_fam_db:
        first_letter = i.compound_family[0]

        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)

        g.typst_data.append(g.compound_fam_templ.render(i=i, date=g.date))

    pr.yes(len(compound_fam_db))


def make_idiom_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling idiom families")

    if debug:
        idioms_fam_db = g.db_session.query(FamilyIdiom).limit(100).all()
    else:
        idioms_fam_db = g.db_session.query(FamilyIdiom).all()
    idioms_fam_db = sorted(idioms_fam_db, key=lambda x: pali_sort_key(x.idiom))

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Idiom Families]\n")

    for i in idioms_fam_db:
        first_letter = i.idiom[0]

        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)

        g.typst_data.append(g.idiom_fam_templ.render(i=i, date=g.date))

    pr.yes(len(idioms_fam_db))


def make_bibliography(g: GlobalVars) -> None:
    pr.green_tmr("compiling bibliography")

    bibliography_data = read_tsv_dot_dict(g.pth.bibliography_tsv_path)

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Bibliography]\n")
    g.typst_data.append("An incomplete list of references works")
    g.typst_data.append(g.bibliography_templ.render(data=bibliography_data))

    pr.yes(len(bibliography_data))


def make_thanks(g: GlobalVars) -> None:
    pr.green_tmr("compiling thanks")

    thanks_tsv = read_tsv_dot_dict(g.pth.thanks_tsv_path)
    thanks_data = []
    for i in thanks_tsv:
        # underlines <i> > __
        i.what = i.what.replace("<i>", "_").replace("</i>", "_")
        # links
        i.what = (
            i.what.replace("<a href=”", '#link("')
            .replace("”>", '")[')
            .replace("</a>", "]")
        )
        thanks_data.append(i)

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Thanks]\n")
    g.typst_data.append(g.thanks_templ.render(data=thanks_data))

    pr.yes(len(thanks_data))


def clean_up_typst_data(g: GlobalVars) -> None:
    pr.green_tmr("cleaning up")

    cleaned_data = []
    for i in g.typst_data:
        # remove double blank lines
        cleaned_string = re.sub(r"^$\n\n", "\n", i, flags=re.MULTILINE)

        # remove comments
        cleaned_string = re.sub(r"^//.+$\n", "", cleaned_string, flags=re.MULTILINE)

        # remove double lines with only spaces
        cleaned_string = re.sub(r"^ *$\n *\n", "", cleaned_string, flags=re.MULTILINE)

        cleaned_data.append(cleaned_string)

    g.typst_data = cleaned_data
    pr.yes("ok")


def save_typist_file(g: GlobalVars) -> None:
    pr.green_tmr("saving typst data")

    with g.pth.typst_lite_data_path.open("w", encoding="utf-8") as f:
        f.write("".join(g.typst_data))
    pr.yes("ok")


# ----------------------------------------------------------------------
# chunked compile
# ----------------------------------------------------------------------


@dataclass
class ChunkSpec:
    """One chunk of the document: body snippets plus the `#set` state
    lines that must be replayed before them (empty for chunk 0)."""

    body: list[str]
    state_lines: list[str] = field(default_factory=list)


def is_entry_snippet(snippet: str) -> bool:
    return snippet.lstrip("\n").startswith(ENTRY_PREFIXES)


def update_set_state(snippet: str, state: dict[str, str]) -> None:
    """Track the last-seen single-line #set par/page rules, keyed by
    (rule, first property), so later chunks can replay them."""
    for m in STATE_LINE_RE.finditer(snippet):
        state[f"{m.group(1)}:{m.group(2)}"] = m.group(0)


def split_body_into_chunks(
    body: list[str], line_budget: int = CHUNK_LINE_BUDGET
) -> list[ChunkSpec]:
    """Split rendered snippets into chunks of ~line_budget lines,
    cutting only where an entry snippet begins, never directly after
    section headers or first-letter pagebreaks."""
    chunks: list[ChunkSpec] = []
    state: dict[str, str] = {}
    current: list[str] = []
    current_lines = 0

    for snippet in body:
        if current_lines >= line_budget and is_entry_snippet(snippet):
            # back off trailing non-entry snippets (section headers,
            # first-letter pagebreaks) so they open the next chunk
            carry: list[str] = []
            while len(current) > 1 and not is_entry_snippet(current[-1]):
                carry.insert(0, current.pop())
            chunks.append(ChunkSpec(body=current, state_lines=list(state.values())))
            for s in current:
                update_set_state(s, state)
            current = carry
            current_lines = sum(s.count("\n") for s in carry)
        current.append(snippet)
        current_lines += snippet.count("\n")

    if current:
        chunks.append(ChunkSpec(body=current, state_lines=list(state.values())))
    return chunks


def chunk_source(preamble: str, spec: ChunkSpec, start_page: int) -> str:
    """Full typst source for one chunk. Chunk 0 (start_page 1, no state)
    is byte-identical to the corresponding monolith prefix."""
    if start_page == 1 and not spec.state_lines:
        return preamble + "".join(spec.body)
    body = list(spec.body)
    # a carried section header or first-letter snippet starts with a
    # pagebreak; the chunk boundary already breaks the page, so keeping
    # it would insert a blank first page
    if body and body[0].startswith("#pagebreak()\n"):
        body[0] = body[0].removeprefix("#pagebreak()\n")
    header = "\n".join(spec.state_lines)
    counter = f"#counter(page).update({start_page})\n"
    return f"{preamble}\n{header}\n{counter}\n" + "".join(body)


def extract_section_titles(snippets: list[str]) -> list[str]:
    titles: list[str] = []
    for snippet in snippets:
        titles.extend(SECTION_HEADING_RE.findall(snippet))
    return titles


def contents_block(sections: list[tuple[str, int]]) -> str:
    """Typst markup for the Contents page: every level-1 section with
    its final absolute page number and dot leaders."""
    lines = ["#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 1.2em)\n"]
    for title, page in sections:
        lines.append(f"{title} #box(width: 1fr, repeat[.]) {page} \\\n")
    return "".join(lines)


def check_typst_cli() -> None:
    if shutil.which("typst") is None:
        pr.red(
            "\ntypst CLI not found on PATH — install from "
            "https://github.com/typst/typst/releases"
        )
        raise SystemExit(1)


def compile_chunk(typ_path: Path, pdf_path: Path) -> int:
    """Compile one chunk in a typst subprocess, return its page count.

    Tags are disabled because pypdf's merge cannot carry them over
    anyway, and untagged chunks are ~4.5x smaller."""
    result = subprocess.run(
        ["typst", "compile", "--no-pdf-tags", str(typ_path), str(pdf_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pr.red(f"\ntypst failed on {typ_path.name}:\n{result.stderr}")
        raise SystemExit(1)
    return len(PdfReader(pdf_path).pages)


def chunk_paths(g: GlobalVars, index: int) -> tuple[Path, Path]:
    base = g.pth.typst_lite_data_path.parent / f"typst_chunk_{index:02d}"
    return base.with_suffix(".typ"), base.with_suffix(".pdf")


def compile_all_chunks(g: GlobalVars, chunks: list[ChunkSpec]) -> list[int]:
    """Serially compile every chunk with chained page numbering.
    Returns per-chunk page counts."""
    pr.green_title("compiling chunks with typst")

    preamble = g.typst_data[0]
    page_counts: list[int] = []
    start_page = 1
    for index, spec in enumerate(chunks):
        pr.white_tmr(f"chunk {index + 1}/{len(chunks)}")
        typ_path, pdf_path = chunk_paths(g, index)
        typ_path.write_text(chunk_source(preamble, spec, start_page), encoding="utf-8")
        pages = compile_chunk(typ_path, pdf_path)
        page_counts.append(pages)
        start_page += pages
        pr.yes(pages)
    return page_counts


def _walk_outline(
    reader: PdfReader,
    items: list[Destination | list],
    offset: int,
    section_set: set[str],
    entries: list[tuple[str, int, bool]],
) -> None:
    for item in items:
        if isinstance(item, list):
            _walk_outline(reader, item, offset, section_set, entries)
        else:
            page_in_chunk = reader.get_destination_page_number(item)
            if page_in_chunk is None:
                continue
            title = str(item["/Title"])
            entries.append((title, offset + page_in_chunk, title in section_set))


def collect_outline_entries(
    g: GlobalVars, chunk_count: int, section_titles: list[str]
) -> list[tuple[str, int, bool]]:
    """All outlined headings across chunk PDFs in document order as
    (title, absolute 0-based page, is_section)."""
    section_set = set(section_titles)
    entries: list[tuple[str, int, bool]] = []
    offset = 0
    for index in range(chunk_count):
        _, pdf_path = chunk_paths(g, index)
        reader = PdfReader(pdf_path)
        _walk_outline(reader, reader.outline, offset, section_set, entries)
        offset += len(reader.pages)
    return entries


def rebuild_contents_page(
    g: GlobalVars,
    chunks: list[ChunkSpec],
    page_counts: list[int],
    entries: list[tuple[str, int, bool]],
) -> None:
    """Replace the chunk-local #outline() in chunk 0 with a Contents
    page listing every section, and recompile chunk 0. Pagination must
    not change, or all later page numbers would be wrong."""
    pr.green_tmr("rebuilding contents page")

    sections = [(title, page + 1) for title, page, is_sec in entries if is_sec]
    source = chunk_source(g.typst_data[0], chunks[0], 1)
    if OUTLINE_PLACEHOLDER not in source:
        pr.red("\n#outline placeholder not found in chunk 0")
        raise SystemExit(1)
    source = source.replace(OUTLINE_PLACEHOLDER, contents_block(sections))

    typ_path, pdf_path = chunk_paths(g, 0)
    typ_path.write_text(source, encoding="utf-8")
    pages = compile_chunk(typ_path, pdf_path)
    if pages != page_counts[0]:
        pr.red(
            f"\ncontents page changed chunk 0 pagination ({page_counts[0]} -> {pages})"
        )
        raise SystemExit(1)
    pr.yes(len(sections))


def merge_chunks(
    g: GlobalVars, chunk_count: int, entries: list[tuple[str, int, bool]]
) -> None:
    """Merge chunk PDFs into the final PDF, rebuilding the bookmark
    tree (letters nested under sections) and document metadata, which
    pypdf does not carry across a merge."""
    pr.green_tmr("merging chunks")

    writer = PdfWriter()
    for index in range(chunk_count):
        _, pdf_path = chunk_paths(g, index)
        writer.append(str(pdf_path), import_outline=False)

    writer.add_metadata(
        {"/Title": "Digital Pāḷi Dictionary", "/Author": "Bodhirasa Bhikkhu"}
    )
    writer.root_object[NameObject("/Lang")] = TextStringObject("en")

    parent = None
    for title, page, is_section in entries:
        if is_section:
            parent = writer.add_outline_item(title, page)
        else:
            writer.add_outline_item(title, page, parent=parent)

    writer.write(str(g.pth.typst_lite_pdf_path))
    writer.close()
    pr.yes("ok")


def clean_up_chunk_files(g: GlobalVars, chunk_count: int) -> None:
    pr.green_tmr("removing chunk files")

    for index in range(chunk_count):
        typ_path, pdf_path = chunk_paths(g, index)
        typ_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
    pr.yes("ok")


def export_to_pdf(g: GlobalVars) -> None:
    """Chunked compile: split, compile serially, rebuild contents,
    merge, clean up."""
    check_typst_cli()

    chunks = split_body_into_chunks(g.typst_data[1:], CHUNK_LINE_BUDGET)
    section_titles = extract_section_titles(g.typst_data)

    page_counts = compile_all_chunks(g, chunks)
    entries = collect_outline_entries(g, len(chunks), section_titles)
    rebuild_contents_page(g, chunks, page_counts, entries)
    merge_chunks(g, len(chunks), entries)
    clean_up_chunk_files(g, len(chunks))

    pr.summary("total pages", sum(page_counts))


def zip_up_pdf(g: GlobalVars) -> None:
    pr.green_tmr("zipping up pdf")

    zip_up_file(
        g.pth.typst_lite_pdf_path, g.pth.typst_lite_zip_path, compression_level=5
    )

    pr.yes("ok")


def main() -> None:
    pr.tic()
    pr.yellow_title("export to pdf with typst")

    if not config_test("exporter", "make_pdf", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()
    make_layout(g)
    make_front_matter(g)
    make_abbreviations(g)
    make_pali_to_english(g)
    make_english_to_pali(g)
    make_root_families(g)
    make_word_families(g)
    make_compound_families(g)
    make_idiom_families(g)
    make_bibliography(g)
    make_thanks(g)
    clean_up_typst_data(g)
    export_to_pdf(g)
    zip_up_pdf(g)
    pr.toc()


if __name__ == "__main__":
    main()
