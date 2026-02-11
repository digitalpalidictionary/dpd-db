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
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_sort_key import pali_sort_key


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
    <string>org.digitalpalidictionary.dpd</string>
    <key>CFBundleName</key>
    <string>DPD</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>DCSDictionaryCopyright</key>
    <string>Copyright © Digital Pāḷi Dictionary. All rights reserved.</string>
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
    headword: DpdHeadword, entry_html: str, entry_id: str
) -> str:
    """Create a single d:entry string for the XML dictionary.

    Args:
        headword: DpdHeadword database object
        entry_html: Rendered HTML content for the entry
        entry_id: Unique identifier for this entry

    Returns:
        XML string for the entry
    """
    # Build index elements as strings
    lemma_escaped = escape_xml_attr(headword.lemma_1)
    index_elements = [f'<d:index d:value="{lemma_escaped}"/>']

    # Add index for inflections if available
    if headword.inflections_list_all:
        inflections = set(headword.inflections_list_all)
        for inflection in sorted(inflections):
            if inflection and inflection != headword.lemma_1:
                infl_escaped = escape_xml_attr(inflection)
                title_escaped = escape_xml_attr(f"{inflection} ({headword.lemma_1})")
                index_elements.append(
                    f'<d:index d:value="{infl_escaped}" d:title="{title_escaped}"/>'
                )

    # Build the complete entry as a string
    # The entry_html from Jinja2 is already well-formed XHTML
    indices_str = "\n".join(index_elements)
    entry_xml = f"""<d:entry id="{entry_id}" d:title="{lemma_escaped}">
{indices_str}
{entry_html}
</d:entry>"""

    return entry_xml


def generate_dictionary_xml(output_dir: Path, db_session) -> None:
    """Generate Dictionary.xml with all DPD entries using memory-efficient streaming.

    Args:
        output_dir: Directory to write the XML file
        db_session: SQLAlchemy database session
    """
    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("exporter/apple_dictionary/templates"), autoescape=True
    )
    entry_template = env.get_template("entry.html")

    xml_path = output_dir / "Dictionary.xml"

    # Query all headword IDs first to avoid loading everything at once
    pr.green("querying database")
    headword_ids = db_session.query(DpdHeadword.id).all()
    total = len(headword_ids)
    pr.yes(total)

    pr.green_title("rendering and streaming entries")

    # Open file for streaming
    with open(xml_path, "w", encoding="utf-8") as f:
        # Write XML header and root element
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(
            f'<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="{APPLE_NS}">\n'
        )

        # Process headwords in chunks to save memory
        chunk_size = 1000
        for i in range(0, total, chunk_size):
            chunk_ids = [hid[0] for hid in headword_ids[i : i + chunk_size]]
            chunk_headwords = (
                db_session.query(DpdHeadword)
                .filter(DpdHeadword.id.in_(chunk_ids))
                .all()
            )

            # Sort the chunk (optional but nice for consistency)
            chunk_headwords = sorted(
                chunk_headwords, key=lambda x: pali_sort_key(x.lemma_1)
            )

            for count, headword in enumerate(chunk_headwords):
                entry_id = f"dpd_{headword.id}"

                # Render HTML for this entry and fix any unescaped ampersands
                entry_html = fix_ampersands(entry_template.render(i=headword))

                # Create XML entry string
                entry_xml = create_dictionary_xml_entry(headword, entry_html, entry_id)

                # Write to file immediately
                f.write(entry_xml + "\n")

                global_count = i + count
                if global_count % 5000 == 0:
                    pr.counter(global_count, total, headword.lemma_1)

        # Close root element
        f.write("</d:dictionary>")

    pr.counter(total, total, "complete")
    pr.yes("ok")


def main() -> None:
    """Main entry point for Apple Dictionary export."""
    pr.tic()
    pr.title("exporting DPD for Apple Dictionary")

    # Get database session
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Get output directory
    output_dir = get_output_path()

    # Generate source files
    generate_info_plist(output_dir)
    copy_css_file(output_dir)
    generate_dictionary_xml(output_dir, db_session)

    # Close database session
    db_session.close()

    pr.green_title("files generated:")
    pr.info(f"  - {output_dir}/Info.plist")
    pr.info(f"  - {output_dir}/Dictionary.css")
    pr.info(f"  - {output_dir}/Dictionary.xml")
    pr.toc()


if __name__ == "__main__":
    main()
