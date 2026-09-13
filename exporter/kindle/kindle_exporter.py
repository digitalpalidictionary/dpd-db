#!/usr/bin/env python3
"""Create an EPUB and MOBI version of DPD.

The word set is limited to
- CST EBTS
- Sutta Central EBTS
- words in deconstructed compounds.

Entries are keyed so that every form reaches every sense it has: a single
index term resolves to a single entry on Kindle, so a form shared by several
headwords gets an entry of its own listing them all."""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from jinja2 import Environment
from sqlalchemy.orm import Session
from rich.markup import escape

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_test
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.deconstructed_words import make_words_in_deconstructions
from tools.diacritics_cleaner import diacritics_cleaner
from tools.first_letter import find_first_letter
from tools.pali_alphabet import pali_alphabet
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dict
from exporter.jinja2_env import get_jinja2_env
from exporter.kindle.data_classes import KindleData, html_friendly

# the dictionary is limited to the early texts
EBT_BOOKS = [
    "vin1",
    "vin2",
    "vin3",
    "vin4",
    "dn1",
    "dn2",
    "dn3",
    "mn1",
    "mn2",
    "mn3",
    "sn1",
    "sn2",
    "sn3",
    "sn4",
    "sn5",
    "an1",
    "an2",
    "an3",
    "an4",
    "an5",
    "an6",
    "an7",
    "an8",
    "an9",
    "an10",
    "an11",
    "kn1",
    "kn2",
    "kn3",
    "kn4",
    "kn5",
    "kn8",
    "kn9",
]


def _letter_files() -> dict[str, str]:
    """Letter -> output filename, matching the static manifest in content.opf."""
    return {
        letter: f"{i}_{diacritics_cleaner(letter)}.xhtml"
        for i, letter in enumerate(pali_alphabet)
    }


def _load_lookup(
    db_session: Session, words: set[str]
) -> tuple[dict[str, list[int]], dict[str, list[str]], dict[str, str]]:
    """One pass over Lookup for the text-set forms: which headwords each form
    belongs to, its spellings in the other scripts, and any deconstruction."""
    form_headwords: dict[str, list[int]] = {}
    scripts: dict[str, list[str]] = {}
    deconstructions: dict[str, str] = {}
    word_list = list(words)
    chunk_size = 900
    for start in range(0, len(word_list), chunk_size):
        chunk = word_list[start : start + chunk_size]
        for row in db_session.query(Lookup).filter(Lookup.lookup_key.in_(chunk)).all():
            if row.headwords:
                form_headwords[row.lookup_key] = row.headwords_unpack
            spellings = {
                s
                for s in row.devanagari_unpack + row.sinhala_unpack + row.thai_unpack
                if s and s.strip()
            }
            if spellings:
                scripts[row.lookup_key] = sorted(spellings, key=pali_sort_key)
            if row.deconstructor:
                unpacked = row.deconstructor_unpack
                if unpacked:
                    deconstructions[row.lookup_key] = "<br/>".join(unpacked)
    return form_headwords, scripts, deconstructions


def render_dpd_xhtml(pth: ProjectPaths, jinja_env: Environment) -> int:
    """Render the dictionary, keyed so that every form reaches every sense it
    has. A single index term resolves to a single entry, so a form shared by
    several headwords needs an entry of its own that lists them all."""
    pr.green_tmr("querying dpd db")
    db_session = get_db_session(pth.dpd_db_path)
    db_session.autoflush = False
    headwords = sorted(
        db_session.query(DpdHeadword).all(), key=lambda h: pali_sort_key(h.lemma_1)
    )
    pr.yes(len(headwords))

    pr.green_tmr("making all words set")
    words = make_cst_text_set(pth, EBT_BOOKS) | make_sc_text_set(pth, EBT_BOOKS)
    words |= make_words_in_deconstructions(db_session)
    words = {w for w in words if w and w.strip()}
    pr.yes(len(words))

    pr.green_tmr("querying lookup")
    form_headwords, scripts, deconstructions = _load_lookup(db_session, words)
    pr.yes(len(form_headwords))

    pr.green_tmr("rendering headword bodies")
    bodies: dict[int, KindleData] = {}
    for counter, headword in enumerate(headwords):
        bodies[headword.id] = KindleData(headword, jinja_env, headword.id, [])
        if counter % 20000 == 0:
            pr.counter(counter, len(headwords), headword.lemma_1)
    pr.yes(len(bodies))

    pr.green_tmr("routing forms")
    lemma_labels = {h.lemma_1: h.id for h in headwords}
    sole_owner: dict[int, list[str]] = {}
    ambiguous: set[str] = set()
    for form, ids in form_headwords.items():
        if len(ids) == 1 and form not in deconstructions:
            sole_owner.setdefault(ids[0], []).append(form)
        else:
            ambiguous.add(form)
    ambiguous.update(f for f in deconstructions if f not in form_headwords)
    # a label reaches one entry, so where a form entry and a headword entry want
    # the same string the headword is folded into the form entry
    contested = ambiguous & set(lemma_labels)
    pr.yes(f"{len(ambiguous)} ambiguous, {len(contested)} contested")

    pr.green_title("creating letter dict entries")
    letter_dict: dict[str, list[str]] = {letter: [] for letter in pali_alphabet}
    letter_files = _letter_files()
    id_counter = 1

    for counter, headword in enumerate(headwords):
        if headword.lemma_1 in contested:
            continue
        aliases = _headword_aliases(headword, sole_owner, scripts)
        entry = render_ebook_entry(
            jinja_env,
            bodies[headword.id],
            aliases,
            deconstructions.get(headword.lemma_1, ""),
        )
        letter_dict[find_first_letter(headword.lemma_1)].append(entry)
        id_counter += 1
        if counter % 20000 == 0:
            pr.counter(counter, len(headwords), headword.lemma_1)

    pr.green_title("add form entries")
    for form in pali_list_sorter(list(ambiguous)):
        merged_id = lemma_labels.get(form) if form in contested else None
        aliases = set(scripts.get(form, []))
        if merged_id is not None:
            for owned in sole_owner.get(merged_id, []):
                if owned != form:
                    aliases.add(owned)
                aliases.update(scripts.get(owned, []))
        entry = render_form_entry(
            jinja_env,
            id_counter,
            form,
            [bodies[i] for i in form_headwords.get(form, []) if i in bodies],
            pali_list_sorter(list(aliases)),
            bodies.get(merged_id) if merged_id is not None else None,
            deconstructions.get(form, ""),
            letter_files,
        )
        letter_dict[find_first_letter(form)].append(entry)
        id_counter += 1

    pr.green_tmr("saving entries xhtml")
    total = 0
    for letter, entries in letter_dict.items():
        total += len(entries)
        xhtml = render_ebook_letter_templ(jinja_env, letter, "".join(entries))
        output_path = pth.epub_text_dir.joinpath(letter_files[letter])
        with output_path.open("w", encoding="utf-8") as f:
            f.write(xhtml)
    pr.yes(total)

    db_session.close()
    return id_counter + 1


def _headword_aliases(
    headword: DpdHeadword,
    sole_owner: dict[int, list[str]],
    scripts: dict[str, list[str]],
) -> list[str]:
    """Forms only this headword owns, plus their other-script spellings."""
    owned = sole_owner.get(headword.id, [])
    aliases = {f for f in owned if f != headword.lemma_1}
    for form in [*owned, headword.lemma_1]:
        aliases.update(scripts.get(form, []))
    aliases.discard(headword.lemma_1)
    return pali_list_sorter(list(aliases))


def render_ebook_entry(
    jinja_env: Environment,
    data: KindleData,
    aliases: list[str],
    deconstruction: str,
) -> str:
    """Render one headword's full entry."""
    template = jinja_env.get_template("ebook_entry.jinja")
    return template.render(data=data, aliases=aliases, deconstruction=deconstruction)


def render_form_entry(
    jinja_env: Environment,
    counter: int,
    form: str,
    senses: list[KindleData],
    aliases: list[str],
    merged: KindleData | None,
    deconstruction: str,
    letter_files: dict[str, str],
) -> str:
    """Render one ambiguous form, listing every sense it has with a link."""
    template = jinja_env.get_template("ebook_form_entry.jinja")
    linked = [
        {
            "lemma_1": html_friendly(data.i.lemma_1),
            "summary": data.summary,
            "href": f"{letter_files[find_first_letter(data.i.lemma_1)]}#hw{data.i.id}",
        }
        for data in senses
    ]
    return template.render(
        counter=counter,
        form=form,
        senses=linked,
        aliases=aliases,
        merged=merged,
        deconstruction=deconstruction,
    )


def render_ebook_letter_templ(jinja_env: Environment, letter: str, entries: str) -> str:
    """Render all entries for a single letter."""
    template = jinja_env.get_template("ebook_letter.jinja")
    return template.render(letter=letter, entries=entries)


def save_abbreviations_xhtml_page(
    pth: ProjectPaths, jinja_env: Environment, id_counter: int
) -> None:
    """Render xhtml of all DPD abbreviations and save as a page."""
    pr.green_tmr("saving abbrev xhtml")
    file_path = pth.abbreviations_tsv_path
    abbreviations_list = read_tsv_dict(file_path)

    abbreviation_entries = []
    for i in abbreviations_list:
        for key, value in i.items():
            if not isinstance(value, str):
                continue
            if value == ">":
                value = "&gt;"
            i[key] = html_friendly(value)
        abbreviation_entries.append(render_abbreviation_entry(jinja_env, id_counter, i))
        id_counter += 1

    entries = "".join(abbreviation_entries)
    xhtml = render_ebook_letter_templ(jinja_env, "Abbreviations", entries)
    with pth.epub_abbreviations_path.open("w", encoding="utf-8") as f:
        f.write(xhtml)
    pr.yes(len(abbreviations_list))


def render_abbreviation_entry(
    jinja_env: Environment,
    counter: int,
    i: dict[str, str],
) -> str:
    """Render a single abbreviations entry."""
    template = jinja_env.get_template("ebook_abbreviation_entry.jinja")
    return template.render(counter=counter, i=i)


def save_title_page_xhtml(pth: ProjectPaths, jinja_env: Environment) -> None:
    """Save date and time in title page xhtml."""
    pr.green_tmr("saving titlepage xhtml")
    current_datetime = datetime.now()
    date = current_datetime.strftime("%Y-%m-%d")
    time = current_datetime.strftime("%H:%M")
    template = jinja_env.get_template("ebook_titlepage.jinja")
    xhtml = template.render(date=date, time=time)
    with pth.epub_titlepage_path.open("w", encoding="utf-8") as f:
        f.write(xhtml)
    pr.yes("OK")
    save_content_opf_xhtml(pth, jinja_env, current_datetime)


def save_content_opf_xhtml(
    pth: ProjectPaths,
    jinja_env: Environment,
    current_datetime: datetime,
) -> None:
    """Save date and time in content.opf."""
    pr.green_tmr("saving content.opf")
    date_time_zulu = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    template = jinja_env.get_template("ebook_content_opf.jinja")
    content = template.render(date_time_zulu=date_time_zulu)
    with pth.epub_content_opf_path.open("w", encoding="utf-8") as f:
        f.write(content)
    pr.yes("OK")


def zip_epub(pth: ProjectPaths, output_path: Path | None = None) -> None:
    """Zip up the epub dir and name it dpd-kindle.epub."""
    pr.green_tmr("zipping up epub")
    epub_dir_path = pth.epub_dir
    dest = output_path or pth.dpd_epub_path
    with ZipFile(dest, "w", ZIP_DEFLATED) as zipf:
        for file_path in epub_dir_path.rglob("*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(epub_dir_path))
    pr.yes("OK")


def make_mobi(pth: ProjectPaths) -> None:
    """Compile the rendered epub into a Kindle dictionary with kindling.

    The OPF is passed rather than the zipped epub: kindling embeds an epub
    input as a SRCS record, and DPD's epub is over the 16 MB PalmDB record
    limit that Kindle firmware refuses to open.
    """
    pr.green_title("converting epub to mobi")

    # os.access, not .exists(): a downloaded release asset lands mode 0644 and
    # would otherwise pass the check and die inside Popen.
    if not os.access(pth.kindling_path, os.X_OK):
        pr.red(f"no executable kindling binary at {pth.kindling_path}")
        raise FileNotFoundError(pth.kindling_path)

    command = [
        str(pth.kindling_path),
        "build",
        str(pth.epub_content_opf_path),
        "-o",
        str(pth.dpd_mobi_path),
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if process.stdout is not None:
        for line in process.stdout:
            pr.white(escape(line.rstrip()))
    returncode = process.wait()

    # kindling exits non-zero when its own readback check finds a MOBI that
    # would fail to open on device, and then declines to ship the file.
    if returncode != 0:
        pr.red(f"kindling failed with exit code {returncode}")
        raise RuntimeError(f"kindling failed with exit code {returncode}")

    pr.yes("Converted with kindling")


def render_epd_xhtml(pth: ProjectPaths, jinja_env: Environment, id_counter: int) -> int:
    """Render EPD (English to Pāḷi Dictionary) entries and save to XHTML files."""
    pr.green_tmr("querying epd data from lookup table")
    db_session = get_db_session(pth.dpd_db_path)
    lookup_db = db_session.query(Lookup).filter(Lookup.epd != "").all()
    pr.yes(len(lookup_db))

    english_alphabet = [chr(i) for i in range(ord("a"), ord("z") + 1)]
    epd_letter_dict: dict[str, list[str]] = {letter: [] for letter in english_alphabet}

    for lookup_entry in lookup_db:
        english_headword = lookup_entry.lookup_key
        first_letter = english_headword[0].lower() if english_headword else "a"
        if first_letter not in english_alphabet:
            first_letter = "a"

        epd_entries = lookup_entry.epd_unpack
        pali_equivalents_list = []
        for lemma_clean, pos, meaning_plus_case in epd_entries:
            entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            pali_equivalents_list.append(entry_html)

        pali_equivalents = "<br/>".join(pali_equivalents_list)
        entry = render_epd_entry(
            jinja_env, id_counter, english_headword, pali_equivalents
        )
        epd_letter_dict[first_letter].append(entry)
        id_counter += 1

    pr.green_tmr("saving epd entries xhtml")
    total = 0
    for counter, letter in enumerate(english_alphabet):
        entries_list = epd_letter_dict[letter]
        total += len(entries_list)
        entries_str = "".join(entries_list)
        xhtml = render_epd_letter_templ(jinja_env, letter, entries_str)
        output_path = pth.epub_text_dir.joinpath(f"epd_{counter}_{letter}.xhtml")
        with output_path.open("w", encoding="utf-8") as f:
            f.write(xhtml)

    pr.yes(total)
    db_session.close()
    return id_counter


def render_epd_entry(
    jinja_env: Environment,
    counter: int,
    english_headword: str,
    pali_equivalents: str,
) -> str:
    """Render single EPD entry."""
    template = jinja_env.get_template("ebook_epd_entry.jinja")
    return template.render(
        counter=counter,
        english_headword=english_headword,
        pali_equivalents=pali_equivalents,
    )


def render_epd_letter_templ(jinja_env: Environment, letter: str, entries: str) -> str:
    """Render all EPD entries for a single English letter."""
    template = jinja_env.get_template("ebook_epd_letter.jinja")
    return template.render(letter=letter, entries=entries)


def main() -> None:
    pr.tic()
    pr.yellow_title("rendering dpd for ebook")
    if config_test("exporter", "make_ebook", "yes"):
        pth = ProjectPaths()
        jinja_env = get_jinja2_env("exporter/kindle/templates")

        id_counter: int = render_dpd_xhtml(pth, jinja_env)
        id_counter = render_epd_xhtml(pth, jinja_env, id_counter)
        save_abbreviations_xhtml_page(pth, jinja_env, id_counter)
        save_title_page_xhtml(pth, jinja_env)
        zip_epub(pth)
        make_mobi(pth)
    else:
        pr.green_title("disabled in config.ini")
    pr.toc()


if __name__ == "__main__":
    main()
