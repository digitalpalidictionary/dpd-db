"""Tests for tools/docs_update_bibliography.py markdown formatting.

These drive `make_bibliography_md` with synthetic rows so that editing the real
bibliography never breaks them. The previous golden-master fixture froze the
whole rendered bibliography, so every data edit failed the suite — it had been
failing on main since the source TSV changed without the fixture being
regenerated. One structural smoke test still runs against the real file to catch
genuine breakage.
"""

from pathlib import Path

from tools.docs_update_bibliography import make_bibliography_md
from tools.paths import ProjectPaths

HEADER = [
    "category",
    "surname",
    "firstname",
    "title",
    "book",
    "journal",
    "page_range",
    "edited_by",
    "doi",
    "year",
    "publisher",
    "city",
    "site",
]

TITLE = "# (An Incomplete) Bibliography\n"


def _pth_with_rows(tmp_path: Path, rows: list[dict[str, str]]) -> ProjectPaths:
    """A ProjectPaths pointed at a throwaway bibliography TSV."""
    lines = ["\t".join(HEADER)]
    for row in rows:
        lines.append("\t".join(row.get(col, "") for col in HEADER))
    tsv = tmp_path / "bibliography.tsv"
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    pth = ProjectPaths()
    pth.bibliography_tsv_path = tsv
    return pth


def _render(tmp_path: Path, rows: list[dict[str, str]]) -> str:
    return make_bibliography_md(_pth_with_rows(tmp_path, rows))


def test_output_always_starts_with_the_title(tmp_path: Path) -> None:
    assert _render(tmp_path, []).startswith(TITLE)


def test_full_entry_renders_every_field_in_order(tmp_path: Path) -> None:
    md = _render(
        tmp_path,
        [
            {
                "category": "Pāḷi Dictionaries",
                "surname": "Cone",
                "firstname": "Margaret",
                "year": "2001",
                "title": "A Dictionary of Pāli Part I a-kh",
                "publisher": "Pāli Text Society",
                "city": "Oxford",
            }
        ],
    )
    assert "## Pāḷi Dictionaries\n\n" in md
    assert (
        "- **Cone**, Margaret, 2001. *A Dictionary of Pāli Part I a-kh*, "
        "Oxford: Pāli Text Society\n" in md
    )


def test_category_only_emitted_when_present(tmp_path: Path) -> None:
    md = _render(tmp_path, [{"surname": "Cone", "title": "A Dictionary"}])
    assert "##" not in md.removeprefix(TITLE)


def test_publisher_without_city_omits_the_colon(tmp_path: Path) -> None:
    md = _render(tmp_path, [{"surname": "Buddhadatta", "publisher": "BCC"}])
    assert "- **Buddhadatta**, BCC\n" in md
    assert ":" not in md.removeprefix(TITLE)


def test_city_without_publisher_is_dropped(tmp_path: Path) -> None:
    """`city` only renders paired with a publisher — alone it is ignored."""
    md = _render(tmp_path, [{"surname": "Buddhadatta", "city": "Dehiwala"}])
    assert "Dehiwala" not in md


def test_site_renders_as_a_self_linking_markdown_link(tmp_path: Path) -> None:
    md = _render(tmp_path, [{"surname": "Anon", "site": "https://example.org/pali"}])
    assert "accessed through [https://example.org/pali](https://example.org/pali)" in md


def test_blank_row_contributes_only_a_newline(tmp_path: Path) -> None:
    assert _render(tmp_path, [{}]) == TITLE + "\n"


def test_rows_keep_their_source_order(tmp_path: Path) -> None:
    md = _render(
        tmp_path,
        [
            {"surname": "Alpha"},
            {"surname": "Beta"},
            {"surname": "Gamma"},
        ],
    )
    assert md.index("Alpha") < md.index("Beta") < md.index("Gamma")


def test_real_bibliography_renders_with_sane_structure() -> None:
    """Smoke test against the live TSV — structure only, never content.

    Catches a genuinely broken build without pinning any bibliography entry.
    """
    md = make_bibliography_md(ProjectPaths())

    assert md.startswith(TITLE)
    body = md.removeprefix(TITLE)
    assert "## " in body, "expected at least one category heading"

    for line in body.split("\n"):
        if line:
            assert line.startswith(("## ", "- **")), f"unexpected line: {line!r}"
