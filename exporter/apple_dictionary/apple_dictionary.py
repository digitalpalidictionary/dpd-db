#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export DPD data for Apple Dictionary format.

This module generates Apple Dictionary Development Kit compatible source files:
- Dictionary.xml: Dictionary entries in Apple's XML format with d:entry/d:index tags
- Dictionary.css: Minimal stylesheet with DPD branding
- Info.plist: Dictionary metadata with bundle identifier

Usage:
    uv run python exporter/apple_dictionary/apple_dictionary.py

Output:
    exporter/share/apple_dictionary/Dictionary.xml
    exporter/share/apple_dictionary/Dictionary.css
    exporter/share/apple_dictionary/Info.plist
"""

import re
from collections.abc import Generator
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DbInfo, DpdHeadword
from tools.cst_sc_text_sets import make_mula_words_set
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_sort_key import pali_list_sorter, pali_sort_key


# Apple Dictionary XML namespace
APPLE_NS = "http://www.apple.com/DTDs/DictionaryService-1.0.rng"


def escape_xml_attr(text: str) -> str:
    """Escape text for use in XML attributes."""
    return escape(text, quote=True)


def fix_ampersands(html: str) -> str:
    """Fix unescaped ampersands in HTML for valid XML.

    Replaces & with &amp; except when already part of a valid entity like &amp; &lt; etc.
    """
    # Match & not followed by a valid entity pattern (word chars ending in ;)
    return re.sub(r"&(?!(?:[a-zA-Z]+|#[0-9]+|#x[0-9a-fA-F]+);)", "&amp;", html)


def group_headwords_by_lemma_clean(
    headwords: list[DpdHeadword],
) -> Generator[list[DpdHeadword], None, None]:
    """Yield groups of headwords sharing the same lemma_clean.

    Args:
        headwords: List of DpdHeadword objects, must be sorted by lemma_1

    Yields:
        Lists of headwords grouped by their lemma_clean property
    """
    if not headwords:
        return

    current_group: list[DpdHeadword] = [headwords[0]]
    current_lemma: str = headwords[0].lemma_clean

    for hw in headwords[1:]:
        if hw.lemma_clean == current_lemma:
            current_group.append(hw)
        else:
            yield current_group
            current_group = [hw]
            current_lemma = hw.lemma_clean

    yield current_group


def get_output_path() -> Path:
    """Get the output directory for Apple Dictionary source files."""
    pth = ProjectPaths()
    output_dir = pth.share_dir.joinpath("apple_dictionary")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_info_plist(output_dir: Path, version: str = "1.0") -> None:
    """Generate Info.plist with DPD dictionary metadata.

    Args:
        output_dir: Directory to write the plist file
        version: Dictionary version string
    """
    pr.green("generating Info.plist")

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleDisplayName</key>
    <string>Digital Pāḷi Dictionary</string>
    <key>CFBundleIdentifier</key>
    <string>net.dpdict.dpd</string>
    <key>CFBundleName</key>
    <string>DPD</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>DCSDictionaryCopyright</key>
    <string>CC BY-NC-SA 4.0</string>
    <key>DCSDictionaryManufacturerName</key>
    <string>Digital Pāḷi Dictionary</string>
</dict>
</plist>"""

    plist_path = output_dir / "Info.plist"
    plist_path.write_text(plist_content, encoding="utf-8")
    pr.yes("ok")


def copy_css_file(output_dir: Path) -> None:
    """Copy the CSS stylesheet to output directory.

    Args:
        output_dir: Directory to write the CSS file
    """
    pr.green("copying CSS file")

    css_source = Path("exporter/apple_dictionary/templates/dictionary.css")
    css_dest = output_dir / "Dictionary.css"

    css_content = css_source.read_text(encoding="utf-8")
    css_dest.write_text(css_content, encoding="utf-8")
    pr.yes("ok")


def create_dictionary_xml_entry(
    headwords: list[DpdHeadword],
    entry_html: str,
    entry_id: str,
    mula_word_set: set[str],
) -> str:
    """Create a single d:entry string for the XML dictionary.

    Groups all headwords with the same lemma_clean into one entry.
    Only indexes inflections found in mūla texts.

    Args:
        headwords: List of DpdHeadword objects with the same lemma_clean
        entry_html: Rendered HTML content for the entry
        entry_id: Unique identifier for this entry
        mula_word_set: Set of words from mūla texts (CST + SC)

    Returns:
        XML string for the entry
    """
    # Get the lemma_clean from the first headword (they all share it)
    lemma_clean = headwords[0].lemma_clean
    lemma_escaped = escape_xml_attr(lemma_clean)
    index_elements = [f'<d:index d:value="{lemma_escaped}"/>']

    # Add niggahita variant for lemma_clean
    if "ṃ" in lemma_clean:
        lemma_niggahita = lemma_clean.replace("ṃ", "ṁ")
        index_elements.append(
            f'<d:index d:value="{escape_xml_attr(lemma_niggahita)}"/>'
        )

    # Collect inflections and filter to mūla words only
    all_inflections: set[str] = set()
    for hw in headwords:
        if hw.inflections_list_all:
            all_inflections.update(hw.inflections_list_all)

    mula_inflections = all_inflections & mula_word_set

    # Add niggahita variants (ṃ → ṁ)
    niggahita_variants: set[str] = set()
    for inflection in mula_inflections:
        if "ṃ" in inflection:
            niggahita_variants.add(inflection.replace("ṃ", "ṁ"))
    mula_inflections |= niggahita_variants

    for inflection in pali_list_sorter(mula_inflections):
        if inflection and inflection != lemma_clean:
            infl_escaped = escape_xml_attr(inflection)
            index_elements.append(
                f'<d:index d:value="{infl_escaped}" d:title="{inflection}"/>'
            )

    # Build the complete entry as a string
    # The entry_html from Jinja2 is already well-formed XHTML
    indices_str = "\n".join(index_elements)
    entry_xml = f"""<d:entry id="{entry_id}" d:title="{lemma_escaped}">
{indices_str}
{entry_html}
</d:entry>"""

    return entry_xml


def generate_dictionary_xml(
    output_dir: Path, db_session, pth: ProjectPaths, limit: int | None = None
) -> None:
    """Generate Dictionary.xml with all DPD entries grouped by lemma_clean.

    Groups all headwords with the same lemma_clean into single dictionary entries.
    Only indexes inflections found in mūla texts (CST + SC).

    Args:
        output_dir: Directory to write the XML file
        db_session: SQLAlchemy database session
        pth: ProjectPaths for locating text files
        limit: Optional limit on number of headwords (for testing)
    """
    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("exporter/apple_dictionary/templates"), autoescape=True
    )
    entry_template = env.get_template("entry.html")

    xml_path = output_dir / "Dictionary.xml"

    # Build mūla word set for filtering inflections
    mula_word_set = make_mula_words_set(pth)

    # Query headwords and sort by lemma_1 using pali_sort_key
    pr.green("querying database")
    query = db_session.query(DpdHeadword)
    if limit:
        query = query.limit(limit)
    headwords = query.all()
    headwords = sorted(
        headwords,
        key=lambda x: (pali_sort_key(x.lemma_clean), pali_sort_key(x.lemma_1)),
    )
    total = len(headwords)
    pr.yes(total)

    pr.green_title("rendering and streaming entries")

    # Group headwords and render entries
    groups = list(group_headwords_by_lemma_clean(headwords))
    total_groups = len(groups)

    with open(xml_path, "w", encoding="utf-8") as f:
        # Write XML header and root element
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(
            f'<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="{APPLE_NS}">\n'
        )

        for count, group in enumerate(groups):
            lemma_clean = group[0].lemma_clean
            entry_id = f"dpd_group_{lemma_clean}"

            # Render HTML for this group and fix any unescaped ampersands
            entry_html = fix_ampersands(
                entry_template.render(headwords=group, lemma_clean=lemma_clean)
            )

            # Create XML entry string
            entry_xml = create_dictionary_xml_entry(
                group, entry_html, entry_id, mula_word_set
            )

            # Write to file
            f.write(entry_xml + "\n")

            if count % 5000 == 0:
                pr.counter(count, total_groups, lemma_clean)

        # Close root element
        f.write("</d:dictionary>")

    pr.counter(total_groups, total_groups, "complete")


def main() -> None:
    """Main entry point for Apple Dictionary export."""
    pr.tic()
    pr.title("exporting DPD for Apple Dictionary")

    # Get database session
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Get version from database
    db_info = (
        db_session.query(DbInfo).filter(DbInfo.key == "dpd_release_version").first()
    )
    version = db_info.value if db_info else "1.0"

    # Get output directory
    output_dir = get_output_path()

    # Generate source files
    generate_info_plist(output_dir, version)
    copy_css_file(output_dir)
    generate_dictionary_xml(output_dir, db_session, pth)

    # Close database session
    db_session.close()

    pr.green_title("files generated:")
    pr.info(f"  - {output_dir}/Info.plist")
    pr.info(f"  - {output_dir}/Dictionary.css")
    pr.info(f"  - {output_dir}/Dictionary.xml")
    pr.toc()


if __name__ == "__main__":
    main()
