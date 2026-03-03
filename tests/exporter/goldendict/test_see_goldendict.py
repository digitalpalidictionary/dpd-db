# -*- coding: utf-8 -*-
"""Tests for GoldenDict SeeData and dpd_see.jinja template rendering."""

from exporter.goldendict.data_classes import SeeData


class _FakeEnv:
    """Minimal Jinja2-like env that returns a stub header template."""

    def get_template(self, name):
        return _FakeTemplate(name)


class _FakeTemplate:
    def __init__(self, name):
        self.name = name

    def render(self, **kwargs):
        return "<html><head></head><body></body></html>"


def test_see_data_stores_fields():
    """Test SeeData stores see and headword."""
    env = _FakeEnv()
    d = SeeData("karohi", "karoti", env)
    assert d.see == "karohi"
    assert d.headword == "karoti"


def test_see_jinja_template_renders():
    """Test that dpd_see.jinja renders see and headword."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader("exporter/goldendict/templates"), autoescape=False
    )

    class _MinimalEnv:
        def get_template(self, name):
            return env.get_template(name)

    # Build a minimal SeeData that generates a header
    d = SeeData.__new__(SeeData)
    d.see = "karohi"
    d.headword = "karoti"
    d.jinja_env = _MinimalEnv()
    # Avoid generating the real CSS header in tests
    d.header = "<html><head></head>"

    html = env.get_template("dpd_see.jinja").render(d=d)
    assert "karoti" in html
    assert "<b><i>" in html


def test_see_dict_built_from_tsv(tmp_path):
    """Test that test_and_make_see_dict reads TSV correctly."""
    from tools.paths import ProjectPaths
    from exporter.goldendict.export_variant_spelling import test_and_make_see_dict

    tsv = tmp_path / "see.tsv"
    tsv.write_text("see\theadword\nkarohi\tkaroti\n", encoding="utf-8")

    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    pth.see_path = tsv

    result = test_and_make_see_dict(pth)
    assert result == {"karohi": "karoti"}
