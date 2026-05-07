"""Smoke test for tools/rss_feed.py."""

import xml.etree.ElementTree as ET
from pathlib import Path

from tools.rss_feed import parse_newsletters, render_rss

NEWSLETTERS_PATH = Path("docs/newsletters.md")


def test_parse_returns_items():
    items = parse_newsletters(NEWSLETTERS_PATH)
    assert len(items) >= 1


def test_item_fields():
    items = parse_newsletters(NEWSLETTERS_PATH)
    first = items[0]
    assert first["title"], "title should be non-empty"
    assert first["pubDate"], "pubDate should be non-empty"
    assert first["link"].startswith("https://docs.dpdict.net/newsletters/#")


def test_image_paths_rewritten():
    items = parse_newsletters(NEWSLETTERS_PATH)
    for item in items:
        if "<img" in item["html_body"]:
            assert 'src="https://docs.dpdict.net/' in item["html_body"], (
                "relative image paths must be rewritten to absolute"
            )


def test_render_is_valid_xml():
    items = parse_newsletters(NEWSLETTERS_PATH)
    xml_str = render_rss(items)
    root = ET.fromstring(xml_str)
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None
    assert len(channel.findall("item")) == len(items)
