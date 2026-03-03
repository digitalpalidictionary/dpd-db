# -*- coding: utf-8 -*-
"""Tests for SeeData and webapp see template rendering."""

from db.models import Lookup
from exporter.webapp.data_classes import SeeData


def _make_lookup_with_see(headwords: list[str]) -> Lookup:
    row = Lookup()
    row.lookup_key = "karohi"
    row.see_pack(headwords)
    return row


def test_see_data_headword():
    """Test SeeData.headword is set from lookup_key."""
    row = _make_lookup_with_see(["karoti"])
    d = SeeData(row)
    assert d.headword == "karohi"


def test_see_data_see_headwords():
    """Test SeeData.see_headwords unpacks the see list."""
    row = _make_lookup_with_see(["karoti", "kāreti"])
    d = SeeData(row)
    assert "karoti" in d.see_headwords
    assert "kāreti" in d.see_headwords


def test_see_template_renders_headword(tmp_path):
    """Test that the see.html template renders the headword and see entry."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
    row = _make_lookup_with_see(["karoti"])
    d = SeeData(row)
    html = env.get_template("see.html").render(d=d)
    assert "karohi" in html
    assert "karoti" in html
    assert "<b><i>" in html


def test_see_summary_template_renders(tmp_path):
    """Test that see_summary.html template renders the headword."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
    row = _make_lookup_with_see(["karoti"])
    d = SeeData(row)
    html = env.get_template("see_summary.html").render(d=d)
    assert "karohi" in html
    assert "see headword" in html
