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

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pali_sort_key import pali_sort_key


# Apple Dictionary XML namespace
APPLE_NS = "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
XHTML_NS = "http://www.w3.org/1999/xhtml"


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
    <string>Digital Pali Dictionary</string>
    <key>CFBundleIdentifier</key>
    <string>org.digitalpalidictionary.dpd</string>
    <key>CFBundleName</key>
    <string>DPD</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>DCSDictionaryCopyright</key>
    <string>Copyright © Digital Pali Dictionary. All rights reserved.</string>
    <key>DCSDictionaryManufacturerName</key>
    <string>Digital Pali Dictionary</string>
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
    root: Element, headword: DpdHeadword, entry_html: str, entry_id: str
) -> None:
    """Create a single d:entry element in the XML dictionary.

    Args:
        root: The root d:dictionary element
        headword: DpdHeadword database object
        entry_html: Rendered HTML content for the entry
        entry_id: Unique identifier for this entry
    """
    # Create entry element
    entry = SubElement(
        root, "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}entry"
    )
    entry.set("id", entry_id)
    entry.set(
        "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}title", headword.lemma_1
    )

    # Add index for the headword
    index = SubElement(
        entry, "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}index"
    )
    index.set(
        "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}value", headword.lemma_1
    )

    # Add index for inflections if available
    if headword.inflections_list_all:
        for inflection in headword.inflections_list_all:
            if inflection and inflection != headword.lemma_1:
                inflection_index = SubElement(
                    entry, "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}index"
                )
                inflection_index.set(
                    "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}value",
                    inflection,
                )
                inflection_index.set(
                    "{http://www.apple.com/DTDs/DictionaryService-1.0.rng}title",
                    f"{inflection} ({headword.lemma_1})",
                )

    # Add title
    h1 = SubElement(entry, "h1")
    h1.text = headword.lemma_1

    # Add the rendered HTML content
    # We need to parse the HTML and add it as children
    # For simplicity, we'll wrap it in a div
    content_div = SubElement(entry, "div")
    content_div.set("class", "content")

    # The entry_html is already rendered HTML from Jinja2 template
    # We add it as raw text content within the div
    # Note: In production, you might want to parse this properly
    content_para = SubElement(content_div, "p")
    content_para.text = entry_html


def generate_dictionary_xml(output_dir: Path, db_session) -> None:
    """Generate Dictionary.xml with all DPD entries.

    Args:
        output_dir: Directory to write the XML file
        db_session: SQLAlchemy database session
    """
    # pr.green("generating Dictionary.xml")

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("exporter/apple_dictionary/templates"), autoescape=True
    )
    entry_template = env.get_template("entry.html")

    # Create root element with proper namespaces
    root = Element("{http://www.apple.com/DTDs/DictionaryService-1.0.rng}dictionary")
    root.set("xmlns", XHTML_NS)
    root.set("xmlns:d", APPLE_NS)

    # Query all headwords
    pr.green("querying database")
    headwords = db_session.query(DpdHeadword).all()
    headwords = sorted(headwords, key=lambda x: pali_sort_key(x.lemma_1))
    total = len(headwords)
    pr.yes(total)

    # Generate entries
    pr.green_title("rendering entries")
    for count, headword in enumerate(headwords):
        entry_id = f"dpd_{headword.id}"

        # Render HTML for this entry
        entry_html = entry_template.render(i=headword)

        # Create XML entry
        create_dictionary_xml_entry(root, headword, entry_html, entry_id)

        if count % 5000 == 0:
            pr.counter(count, total, headword.lemma_1)

    pr.counter(total, total, "complete")

    # Convert to pretty-printed XML
    pr.green("formatting XML")
    xml_string = tostring(root, encoding="unicode")
    # Add XML declaration
    xml_output = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'

    # Write to file
    xml_path = output_dir / "Dictionary.xml"
    xml_path.write_text(xml_output, encoding="utf-8")
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
