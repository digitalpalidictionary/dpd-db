"""Family headings in the PDF templates agree in number with each family's count."""

from types import SimpleNamespace

import pytest

from exporter.pdf import pdf_exporter


def _render_root_family(monkeypatch: pytest.MonkeyPatch, count: int) -> str:
    monkeypatch.setattr(pdf_exporter, "get_db_session", lambda _: None)
    monkeypatch.setattr(pdf_exporter, "config_read", lambda *_: "v0.4.20260905")
    i = SimpleNamespace(
        root_family="√kar",
        root_meaning="do",
        root_family_key="√kar 1 √kar",
        count=count,
        data_unpack=[["word", "masc", "meaning", "✔"]],
    )
    return pdf_exporter.GlobalVars().root_fam_templ.render(i=i, date="2026-10-20")


def test_root_family_one_member_is_singular(monkeypatch: pytest.MonkeyPatch) -> None:
    html = _render_root_family(monkeypatch, 1)

    assert "1 word belongs to the root family " in html


def test_root_family_many_members_is_plural(monkeypatch: pytest.MonkeyPatch) -> None:
    html = _render_root_family(monkeypatch, 5)

    assert "5 words belong to the root family " in html


def _render_heavy(monkeypatch: pytest.MonkeyPatch, template: str, count: int) -> str:
    monkeypatch.setattr(pdf_exporter, "get_db_session", lambda _: None)
    monkeypatch.setattr(pdf_exporter, "config_read", lambda *_: "v0.4.20260905")
    i = SimpleNamespace(
        root_family="√kar",
        root_family_key_typst="√kar-1",
        root_meaning="do",
        compound_family="kata",
        count=count,
        data_unpack=[["word", "masc", "meaning", "✔"]],
    )
    env = pdf_exporter.GlobalVars().env
    return env.get_template(template).render(i=i, date="2026-10-20")


def test_heavy_root_family_one_member_is_singular(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = _render_heavy(monkeypatch, "heavy_family_root.typ", 1)

    assert "1 word belongs to the root family " in html


def test_heavy_root_family_many_members_is_plural(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = _render_heavy(monkeypatch, "heavy_family_root.typ", 5)

    assert "5 words belong to the root family " in html


def test_heavy_compound_family_one_member_is_singular(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = _render_heavy(monkeypatch, "heavy_family_compound.typ", 1)

    assert "*1* compound which contains " in html


def test_heavy_compound_family_many_members_is_plural(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = _render_heavy(monkeypatch, "heavy_family_compound.typ", 5)

    assert "*5* compounds which contain " in html
