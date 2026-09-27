"""One-off harness for the dependency cleanup thread.

Calls each function guarded by a changed package on fixed input and writes
one text file per function into <out_dir>. Run before and after the changes,
then `diff -r` the two folders. Not a test: nothing here is committed to tests/.

Usage: uv run kamma/threads/20260927_dependency_cleanup/artifacts/capture_outputs.py <out_dir>
"""

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import select

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilySet
from tools.paths import ProjectPaths


def mangle(word: str, n: int) -> str:
    """Make a deterministic misspelling: drop, double or swap a character."""
    if len(word) < 3:
        return word + word[-1]
    i = n % (len(word) - 1)
    match n % 3:
        case 0:
            return word[:i] + word[i + 1 :]
        case 1:
            return word[:i] + word[i] + word[i:]
        case _:
            return word[:i] + word[i + 1] + word[i] + word[i + 2 :]


def capture_fuzzy(out: Path, pth: ProjectPaths) -> None:
    from tools.fuzzy_tools import find_closest_matches

    db = get_db_session(pth.dpd_db_path)
    sets = sorted(db.scalars(select(FamilySet.set)).all())
    pos = sorted(set(db.scalars(select(DpdHeadword.pos)).all()))

    lines = [f"family_set count: {len(sets)}", f"pos values: {pos}", ""]
    step = max(1, len(sets) // 22)
    set_terms = [mangle(s, n) for n, s in enumerate(sets[::step][:22])]
    pos_terms = [mangle(p, n) for n, p in enumerate(pos[::3][:8])]
    for term in set_terms:
        lines.append(f"set  {term!r} -> {find_closest_matches(term, sets)}")
    for term in pos_terms:
        lines.append(f"pos  {term!r} -> {find_closest_matches(term, pos)}")
    (out / "fuzzy_tools.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def capture_newsletters(out: Path) -> list[dict]:
    from tools.rss_feed import parse_newsletters, render_rss

    items = parse_newsletters(Path("docs/newsletters.md"))
    rss = render_rss(items)
    rss = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "<lastBuildDate/>", rss)
    (out / "rss_feed.xml").write_text(rss, encoding="utf-8")
    return items


def capture_markdownify(out: Path, items: list[dict]) -> None:
    from markdownify import markdownify as md

    from scripts.build.newsletter_scraper import strip_footer

    parts = [strip_footer(md(item["html_body"])) for item in items]
    (out / "markdownify_strip_footer.md").write_text(
        "\n\n=====\n\n".join(parts) + "\n", encoding="utf-8"
    )


def capture_goldendict(out: Path) -> None:
    from tools.goldendict_exporter import (
        DictEntry,
        DictInfo,
        DictVariables,
        add_data,
        create_glossary,
        write_to_file,
    )

    entries = [
        DictEntry("dhamma", "<b>dhamma</b> nature", "dhamma nature", ["dhammo"]),
        DictEntry("buddha", "<i>buddha</i> awakened", "buddha awakened", []),
        DictEntry("saṅgha", "<p>saṅgha</p> community", "saṅgha community", ["saṅgho"]),
    ]
    info = DictInfo("capture", "author", "desc", "web", "pi", "en")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dict_var = DictVariables(None, None, tmp_path, tmp_path, "capture", None)
        glos = create_glossary(info)
        glos = add_data(glos, entries)
        write_to_file(glos, dict_var)

        lines: list[str] = []
        for f in sorted(dict_var.gd_path.rglob("*")):
            if not f.is_file():
                continue
            data = f.read_bytes()
            lines.append(f"== {f.relative_to(tmp_path)} ({len(data)} bytes)")
            if f.suffix == ".ifo":
                text = data.decode("utf-8")
                lines.append(re.sub(r"^date=.*$", "date=<stripped>", text, flags=re.M))
            else:
                lines.append(hashlib.sha256(data).hexdigest())
    (out / "goldendict_exporter.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def capture_pdf_merge(out: Path) -> None:
    import typst
    from pypdf import PdfReader

    from exporter.pdf.pdf_exporter import chunk_paths, merge_chunks

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        g = SimpleNamespace(
            pth=SimpleNamespace(
                typst_lite_data_path=tmp_path / "data.typ",
                typst_lite_pdf_path=tmp_path / "merged.pdf",
            )
        )
        sources = [
            "= Section A\nalpha text\n#pagebreak()\n== a\nsecond page",
            "= Section B\nbeta text",
        ]
        for index, source in enumerate(sources):
            typ_path, pdf_path = chunk_paths(g, index)  # pyright: ignore[reportArgumentType]
            typ_path.write_text(source, encoding="utf-8")
            typst.compile(str(typ_path), output=str(pdf_path))
        entries = [("Section A", 0, True), ("a", 1, False), ("Section B", 2, True)]
        merge_chunks(g, len(sources), entries)  # pyright: ignore[reportArgumentType]

        reader = PdfReader(g.pth.typst_lite_pdf_path)
        meta = reader.metadata or {}
        lines = [
            f"pages: {len(reader.pages)}",
            f"title: {meta.get('/Title')}",
            f"author: {meta.get('/Author')}",
            f"lang: {reader.root_object.get('/Lang')}",
        ]

        def walk(items: list, depth: int) -> None:
            for item in items:
                if isinstance(item, list):
                    walk(item, depth + 1)
                else:
                    page = reader.get_destination_page_number(item)
                    lines.append(f"outline {'  ' * depth}{item['/Title']} -> {page}")

        walk(reader.outline, 0)
        for n, page in enumerate(reader.pages):
            lines.append(f"page {n}: {page.extract_text()!r}")
    (out / "pdf_merge_chunks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def capture_dv_catalogue(out: Path, pth: ProjectPaths) -> None:
    from db.suttas.dv_catalogue_suttas import read_dv_catalogue

    data = read_dv_catalogue(pth)
    (out / "dv_catalogue.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1, default=str) + "\n",
        encoding="utf-8",
    )


def capture_silent_files(out: Path, pth: ProjectPaths) -> None:
    from audio.error_check.delete_silent_files import check_file

    if not pth.dpd_audio_mp3_dir.exists():
        (out / "silent_files.txt").write_text("skipped: no audio folder\n")
        return
    files: list[Path] = []
    for folder in sorted(pth.dpd_audio_mp3_dir.iterdir()):
        if folder.is_dir():
            files.extend(sorted(folder.glob("*.mp3"))[: 20 - len(files)])
        if len(files) >= 20:
            break
    lines = [
        f"{f.relative_to(pth.dpd_audio_mp3_dir)} -> {check_file(f)}" for f in files
    ]
    (out / "silent_files.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def capture_webapp(out: Path) -> None:
    from fastapi.testclient import TestClient

    from exporter.webapp.main import app

    client = TestClient(app)
    requests = [
        ("home", "/"),
        ("search_json", "/search_json?q=gacchati"),
        ("search_html", "/search_html?q=dhamma"),
        ("gd", "/gd?search=kusala"),
        ("permalink", "/24043"),
        ("status", "/status"),
    ]
    for name, url in requests:
        response = client.get(url, follow_redirects=False)
        body = response.text
        if name == "status":
            # every figure on the status page is a time, a count or memory,
            # and the traffic-light colours follow the current load
            body = re.sub(r"\d+(\.\d+)?", "N", body)
            body = re.sub(r"\b(green|orange|red)\b", "COLOUR", body)
        headers = {
            k: v
            for k, v in sorted(response.headers.items())
            if k not in ("date", "content-length", "x-process-time")
        }
        (out / f"webapp_{name}.txt").write_text(
            f"status: {response.status_code}\nheaders: {headers}\n\n{body}\n",
            encoding="utf-8",
        )


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    pth = ProjectPaths()

    capture_fuzzy(out, pth)
    items = capture_newsletters(out)
    capture_markdownify(out, items)
    capture_goldendict(out)
    capture_pdf_merge(out)
    capture_dv_catalogue(out, pth)
    capture_silent_files(out, pth)
    capture_webapp(out)


if __name__ == "__main__":
    main()
