"""Generate RSS 2.0 feed from docs/newsletters.md."""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

DOCS_BASE_URL = "https://docs.dpdict.net"
NEWSLETTERS_URL = f"{DOCS_BASE_URL}/newsletters/"


def _rewrite_image_paths(html: str) -> str:
    """Rewrite relative image src paths to absolute docs.dpdict.net URLs."""
    return re.sub(
        r'src="(?!https?://)([^"]+)"',
        lambda m: f'src="{DOCS_BASE_URL}/{m.group(1)}"',
        html,
    )


def _extract_title(body: str) -> str:
    """Extract the first **bold** text as the item title."""
    match = re.search(r"\*\*(.+?)\*\*", body)
    return match.group(1) if match else ""


def parse_newsletters(path: Path) -> list[dict]:
    """Parse newsletters.md into a list of item dicts ordered newest-first."""
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"^(## \d{4}-\d{2}-\d{2})", text, flags=re.MULTILINE)

    items: list[dict] = []
    i = 1
    while i < len(sections) - 1:
        heading = sections[i].strip()
        body = sections[i + 1]
        i += 2

        date_str = heading.lstrip("# ").strip()
        try:
            pub_date = datetime(*map(int, date_str.split("-")), tzinfo=timezone.utc)
        except ValueError:
            continue

        title = _extract_title(body) or f"DPD update {date_str}"
        html_body = markdown.markdown(body.strip(), extensions=["attr_list"])
        html_body = _rewrite_image_paths(html_body)
        anchor = date_str

        items.append(
            {
                "title": title,
                "link": f"{NEWSLETTERS_URL}#{anchor}",
                "pubDate": format_datetime(pub_date, usegmt=True),
                "html_body": html_body,
            }
        )

    return items


def render_rss(items: list[dict]) -> str:
    """Render items as an RSS 2.0 XML string."""
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel = ET.SubElement(rss, "channel")

    feed_url = f"{DOCS_BASE_URL}/rss.xml"

    ET.SubElement(channel, "title").text = "Digital Pāḷi Dictionary — Updates"
    ET.SubElement(channel, "link").text = "https://www.dpdict.net/"
    ET.SubElement(
        channel, "description"
    ).text = "Monthly updates from the Digital Pāḷi Dictionary."
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "managingEditor").text = "dpd@4nt.org (Bodhirasa)"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(tz=timezone.utc), usegmt=True
    )
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", feed_url)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for item in items:
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "guid", isPermaLink="true").text = item["link"]
        ET.SubElement(entry, "pubDate").text = item["pubDate"]
        ET.SubElement(entry, "description").text = item["html_body"]

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    raw = ET.tostring(rss, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{raw}\n'


if __name__ == "__main__":
    newsletters_path = Path("docs/newsletters.md")
    output_path = Path("docs/rss.xml")

    items = parse_newsletters(newsletters_path)
    xml_str = render_rss(items)
    output_path.write_text(xml_str, encoding="utf-8")
    print(f"wrote {len(items)} items → {output_path}")
