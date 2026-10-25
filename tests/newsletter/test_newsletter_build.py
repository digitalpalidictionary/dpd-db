"""Tests for newsletter/newsletter_build.py: preview, publish and the docs page."""

import argparse
import io
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw, ImageFilter

from newsletter import newsletter_build as nb
from tools.rss_feed import parse_newsletters

# copied from the top of docs/newsletters.md
PAGE = """# DPD Newsletters

## 2026-07-29
**Digital Pāḷi Dictionary update (July 2026)**

Dear Venerable monastics, professors, and Pāḷi enthusiasts,

**- Corrections and Additions**

As always, thank you for the abundant dictionary feedback.

With much *mettā*,

Bodhirasa

---

## 2026-05-31
**Digital Pāḷi Dictionary update (31 May 2026)**

There are a few interesting updates to the dictionary this month.
"""

NEWSLETTER_MD = """# Digital Pāḷi Dictionary update (November 2026)

Dear Venerable monastics, professors, and Pāḷi enthusiasts,

## DPD for KOReader

Long-press any Pāḷi word.

<!-- Drop the screenshot in pics/ and uncomment:
![KOReader popup](pics/hidden.jpg)
-->

![a caption](pics/koreader.jpg)

### A sub point

Text.
"""

SUBJECT = "Digital Pāḷi Dictionary update (November 2026)"


def screenshot(width: int, height: int) -> Image.Image:
    """Flat colours and sharp lines of text, like an app screenshot."""
    image = Image.new("RGB", (width, height), (24, 32, 40))
    draw = ImageDraw.Draw(image)
    for y in range(20, height - 20, 36):
        draw.rectangle((16, y, width - 16, y + 28), outline=(0, 168, 240))
        draw.text((24, y + 8), "karaṇīya 1 nt. duty; obligation " * 3, fill="white")
    return image


def photo(width: int, height: int) -> Image.Image:
    """Noisy, many-coloured pixels, like a camera photo."""
    bands = [Image.effect_noise((width, height), sigma) for sigma in (40, 50, 60)]
    return Image.merge("RGB", bands).filter(ImageFilter.GaussianBlur(1))


def make_month(tmp_path: Path, pics: tuple[str, ...] = ("koreader.jpg",)) -> Path:
    month_dir = tmp_path / "newsletter" / "2026-11"
    (month_dir / "pics").mkdir(parents=True)
    (month_dir / "newsletter.md").write_text(NEWSLETTER_MD, encoding="utf-8")
    for name in pics:
        screenshot(600, 200).save(month_dir / "pics" / name, "JPEG")
    return month_dir


def body_of(md: str) -> str:
    return nb.extract_subject(md)[1]


def test_docs_entry_shape() -> None:
    entry = nb.docs_entry(
        SUBJECT, body_of(NEWSLETTER_MD), "2026-11", date(2026, 11, 24)
    )
    lines = entry.splitlines()
    assert lines[0] == "## 2026-11-24"
    assert lines[1] == f"**{SUBJECT}**"
    assert "### DPD for KOReader" in lines
    assert "#### A sub point" in lines
    assert "![a caption](pics/newsletters/2026-11/koreader.jpg)" in lines
    assert "hidden.jpg" not in entry
    assert "<!--" not in entry
    assert entry.endswith("With much *mettā*,\n\nBodhirasa\n\n---\n\n")
    assert "\n\n\n" not in entry


def test_insert_puts_entry_first() -> None:
    entry = nb.docs_entry(
        SUBJECT, body_of(NEWSLETTER_MD), "2026-11", date(2026, 11, 24)
    )
    page = nb.insert_docs_entry(PAGE, entry, SUBJECT)
    assert page.startswith("# DPD Newsletters\n\n## 2026-11-24\n")
    assert page.index("## 2026-11-24") < page.index("## 2026-07-29")
    assert page.endswith(PAGE[PAGE.index("## 2026-07-29") :])


def test_republish_replaces_not_duplicates() -> None:
    first = nb.docs_entry(
        SUBJECT, body_of(NEWSLETTER_MD), "2026-11", date(2026, 11, 24)
    )
    page = nb.insert_docs_entry(PAGE, first, SUBJECT)
    edited = NEWSLETTER_MD.replace("Long-press", "Press and hold")
    second = nb.docs_entry(SUBJECT, body_of(edited), "2026-11", date(2026, 11, 24))
    page = nb.insert_docs_entry(page, second, SUBJECT)
    assert page.count(f"**{SUBJECT}**") == 1
    assert "Press and hold" in page
    assert "Long-press" not in page
    assert page.count("## 2026-07-29") == 1


def test_rss_feed_reads_new_entry(tmp_path: Path) -> None:
    entry = nb.docs_entry(
        SUBJECT, body_of(NEWSLETTER_MD), "2026-11", date(2026, 11, 24)
    )
    page_path = tmp_path / "newsletters.md"
    page_path.write_text(nb.insert_docs_entry(PAGE, entry, SUBJECT), encoding="utf-8")
    items = parse_newsletters(page_path)
    assert len(items) == 3
    assert items[0]["title"] == SUBJECT
    assert items[0]["link"].endswith("#2026-11-24")
    assert items[1]["title"] == "Digital Pāḷi Dictionary update (July 2026)"


def test_copy_docs_pics_skips_commented_out(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path, pics=("koreader.jpg", "hidden.jpg"))
    dest = tmp_path / "docs_pics" / "2026-11"
    nb.copy_docs_pics(body_of(NEWSLETTER_MD), month_dir, dest)
    assert sorted(p.name for p in dest.iterdir()) == ["koreader.jpg"]


def fake_paths(tmp_path: Path) -> SimpleNamespace:
    page_path = tmp_path / "docs" / "newsletters.md"
    page_path.parent.mkdir()
    page_path.write_text(PAGE, encoding="utf-8")
    return SimpleNamespace(
        docs_newsletters_md_path=page_path,
        docs_newsletters_pics_dir=tmp_path / "docs" / "pics" / "newsletters",
    )


@pytest.mark.parametrize("uposatha", [True, False])
def test_publish_docs_only_on_uposatha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uposatha: bool
) -> None:
    month_dir = make_month(tmp_path)
    pth = fake_paths(tmp_path)
    drafts: list[object] = []
    monkeypatch.setattr(nb, "append_draft", lambda msg: drafts.append(msg) or True)
    monkeypatch.setattr(nb, "ProjectPaths", lambda: pth)
    monkeypatch.setattr(
        nb.UposathaManger, "uposatha_today", classmethod(lambda cls: uposatha)
    )

    nb.publish(month_dir, "2026-11")

    assert len(drafts) == 1
    page = pth.docs_newsletters_md_path.read_text(encoding="utf-8")
    pic = pth.docs_newsletters_pics_dir / "2026-11" / "koreader.jpg"
    if uposatha:
        assert page.count(f"**{SUBJECT}**") == 1
        assert pic.exists()
    else:
        assert page == PAGE
        assert not pic.exists()


def test_reload_script_only_in_live_preview(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    live = nb.write_preview(month_dir, "2026-11", live=True).read_text(encoding="utf-8")
    assert "location.reload()" in live
    assert "__STAMP__" not in live
    static = nb.write_preview(month_dir, "2026-11").read_text(encoding="utf-8")
    assert "<script" not in static
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    assert "<script" not in nb.render_html(body, subject, month_dir / "pics", "cid")


def test_each_live_build_gets_a_new_stamp(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    first = nb.write_preview(month_dir, "2026-11", live=True).read_text(
        encoding="utf-8"
    )
    second = nb.write_preview(month_dir, "2026-11", live=True).read_text(
        encoding="utf-8"
    )
    stamp = first.split('text.indexOf("')[1].split('"')[0]
    assert stamp.startswith("build-")
    assert stamp not in second


def test_source_stamp_sees_edits_and_new_pics(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    before = nb.source_stamp(month_dir)
    (month_dir / "pics" / "new.png").write_bytes(b"png")
    assert nb.source_stamp(month_dir) != before


def test_latest_month(tmp_path: Path) -> None:
    for name in ["2026-10", "2026-11", "__pycache__", "2026-09"]:
        (tmp_path / name).mkdir()
    assert nb.latest_month(tmp_path) == "2026-11"
    assert nb.latest_month(tmp_path / "2026-09") is None


def test_preview_picks_up_builder_edits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    month_dir = make_month(tmp_path)
    builder = tmp_path / "newsletter_build.py"
    builder.write_text(nb.BUILDER_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(nb, "BUILDER_PATH", builder)
    before = nb.source_stamp(month_dir)

    source = builder.read_text(encoding="utf-8")
    builder.write_text(
        source.replace("To unsubscribe from", "To leave"), encoding="utf-8"
    )
    assert nb.source_stamp(month_dir) != before

    preview = nb.load_fresh_builder().write_preview(month_dir, "2026-11", live=True)
    html = preview.read_text(encoding="utf-8")
    assert "To leave" in html
    assert "To unsubscribe from" not in html


def test_useful_links_come_from_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    links = tmp_path / "useful_links.md"
    links.write_text(
        "***Useful DPD links:***\n\n**Get DPD**\n"
        "Online: [www.dpdict.net](https://dpdict.net/)\n"
        "On Android: [beta testing](https://digitalpalidictionary.github.io/install/dpd_app/)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(nb, "USEFUL_LINKS_PATH", links)
    month_dir = make_month(tmp_path)
    before = nb.source_stamp(month_dir)
    html = nb.render_useful_links()
    assert "<strong>Get DPD</strong><br />" in html
    assert '<a href="https://dpdict.net/">www.dpdict.net</a><br />' in html
    links.write_text(links.read_text(encoding="utf-8") + "New line\n", encoding="utf-8")
    assert nb.source_stamp(month_dir) != before


def test_every_link_opens_in_a_new_tab(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    (month_dir / "newsletter.md").write_text(
        NEWSLETTER_MD + "\n[a link](https://example.org) and <https://dpdict.net>\n",
        encoding="utf-8",
    )
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    for mode in ("local", "cid"):
        html = nb.render_html(body, subject, month_dir / "pics", mode)
        anchors = re.findall(r"<a\b[^>]*>", html)
        assert len(anchors) > 40  # body links plus the whole footer
        assert all('target="_blank"' in a for a in anchors)
        assert not any(a.count("target=") > 1 for a in anchors)


# display sizes Gmail's "best fit" gave real pictures in past newsletters
@pytest.mark.parametrize(
    ("size", "shown"),
    [
        ((1008, 2244), (252, 560)),  # phone screenshot, shown 252 wide
        ((1008, 2131), (265, 560)),  # phone screenshot, shown 266 wide
        ((3072, 4080), (422, 560)),  # camera photo, shown 423 wide
        ((1912, 1080), (520, 294)),  # wide desktop screenshot fills the column
        ((947, 130), (520, 71)),
        ((161, 56), (161, 56)),  # small pictures are never enlarged
    ],
)
def test_display_size_matches_past_newsletters(
    size: tuple[int, int], shown: tuple[int, int]
) -> None:
    assert nb.display_size(*size) == shown


def save(image: Image.Image, path: Path, fmt: str, **kwargs: object) -> Path:
    image.save(path, fmt, **kwargs)
    return path


def test_small_screenshot_goes_out_unchanged(tmp_path: Path) -> None:
    path = save(screenshot(947, 248), tmp_path / "small.png", "PNG")
    pic = nb.prepare_pic(path)
    assert pic.data == path.read_bytes()
    assert pic.name == "small.png"


def test_phone_screenshot_is_shown_narrow_and_shrunk(tmp_path: Path) -> None:
    path = save(screenshot(1008, 2244), tmp_path / "Screenshot_1.png", "PNG")
    pic = nb.prepare_pic(path)
    assert pic.display == (252, 560)
    assert Image.open(io.BytesIO(pic.data)).size == (504, 1122)
    assert len(pic.data) < path.stat().st_size


def test_camera_photo_shrinks_to_jpeg_under_keep_size(tmp_path: Path) -> None:
    path = save(photo(1536, 2040), tmp_path / "PXL_1.jpg", "JPEG", quality=95)
    pic = nb.prepare_pic(path)
    assert pic.subtype == "jpeg"
    assert pic.name == "PXL_1.jpg"
    assert Image.open(io.BytesIO(pic.data)).size == (844, 1121)
    assert len(pic.data) < path.stat().st_size


def test_sideways_phone_photo_comes_out_upright(tmp_path: Path) -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # stored landscape, camera held upright
    path = save(photo(400, 300), tmp_path / "rotated.jpg", "JPEG", exif=exif)
    pic = nb.prepare_pic(path)
    assert pic.display == (300, 400)
    assert Image.open(io.BytesIO(pic.data)).size == (300, 400)


def test_transparent_png_is_flattened_on_white(tmp_path: Path) -> None:
    image = Image.new("RGBA", (1400, 400), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((0, 0, 100, 100), fill=(255, 0, 0, 255))
    path = save(image, tmp_path / "logo.png", "PNG")
    pic = nb.prepare_pic(path)
    out = Image.open(io.BytesIO(pic.data)).convert("RGB")
    assert out.getpixel((out.width - 1, out.height - 1)) == (255, 255, 255)


def test_gif_goes_out_unchanged(tmp_path: Path) -> None:
    path = save(screenshot(1400, 900), tmp_path / "anim.gif", "GIF")
    assert nb.prepare_pic(path).data == path.read_bytes()


def test_pictures_get_their_display_size_in_the_mail(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    screenshot(1008, 2244).save(month_dir / "pics" / "phone.png")
    md = "# Subject\n\n![phone](pics/phone.png)\n\n![k](pics/koreader.jpg)\n"
    (month_dir / "newsletter.md").write_text(md, encoding="utf-8")
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    for mode in ("local", "cid"):
        html = nb.render_html(body, subject, month_dir / "pics", mode)
        tags = re.findall(r"<img alt=[^>]*>", html)
        assert 'width="252"' in tags[0] and 'height="560"' in tags[0]
        assert 'width="520"' in tags[1]
        assert all("margin: 0 auto" in t for t in tags)
        assert html.count('text-align: center;"><img alt=') == 2


def test_mail_carries_the_shrunk_picture(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    original = month_dir / "pics" / "phone.png"
    screenshot(1008, 2244).save(original)
    md = "# Subject\n\n![phone](pics/phone.png)\n"
    (month_dir / "newsletter.md").write_text(md, encoding="utf-8")
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    html = nb.render_html(body, subject, month_dir / "pics", "cid")
    msg = nb.make_mime_message(html, subject, month_dir)
    parts = [p for p in msg.walk() if p.get("Content-ID") == "<phone.png>"]
    data = parts[0].get_payload(decode=True)
    assert isinstance(data, bytes)
    assert Image.open(io.BytesIO(data)).size == (504, 1122)
    assert len(data) < original.stat().st_size


def test_docs_entry_uses_published_name_and_width(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    photo(3072, 4080).save(month_dir / "pics" / "big.png")
    md = NEWSLETTER_MD + "\n![a photo](pics/big.png)\n"
    dest = tmp_path / "docs_pics" / "2026-11"
    pics = nb.copy_docs_pics(body_of(md), month_dir, dest)
    assert pics["big.png"].name == "big.jpg"
    assert (dest / "big.jpg").exists() and not (dest / "big.png").exists()
    entry = nb.docs_entry(SUBJECT, body_of(md), "2026-11", date(2026, 11, 24), pics)
    assert '![a photo](pics/newsletters/2026-11/big.jpg){ width="422" }' in entry
    assert "![a caption](pics/newsletters/2026-11/koreader.jpg)" in entry
    page_path = tmp_path / "newsletters.md"
    page_path.write_text(nb.insert_docs_entry(PAGE, entry, SUBJECT), encoding="utf-8")
    assert 'width="422"' in parse_newsletters(page_path)[0]["html_body"]


def test_new_picture_markdown_goes_to_clipboard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pics_dir = make_month(tmp_path) / "pics"
    clipboard: list[str] = []
    monkeypatch.setattr(
        nb, "copy_to_clipboard", lambda text: clipboard.append(text) or True
    )
    known = nb.picture_names(pics_dir)
    assert nb.announce_new_pics(pics_dir, known) == known
    assert clipboard == []

    screenshot(400, 200).save(pics_dir / "Screenshot from 2026-10-25 10-30-00.png")
    (pics_dir / "photo.jpg.part").write_bytes(b"half a download")
    known = nb.announce_new_pics(pics_dir, known)
    assert clipboard == ["![](pics/Screenshot-from-2026-10-25-10-30-00.png)"]
    assert (pics_dir / "Screenshot-from-2026-10-25-10-30-00.png").exists()
    assert "Screenshot-from-2026-10-25-10-30-00.png" in known

    screenshot(400, 200).save(pics_dir / "a.png")
    screenshot(400, 200).save(pics_dir / "b.png")
    nb.announce_new_pics(pics_dir, known)
    assert clipboard[-1] == "![](pics/a.png)\n\n![](pics/b.png)"


def test_pasted_link_renders_the_picture(tmp_path: Path) -> None:
    month_dir = make_month(tmp_path)
    screenshot(1008, 2244).save(month_dir / "pics" / "Screenshot-1.png")
    md = "# Subject\n\n![](pics/Screenshot-1.png)\n"
    (month_dir / "newsletter.md").write_text(md, encoding="utf-8")
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    html = nb.render_html(body, subject, month_dir / "pics", "local")
    assert 'src="pics/Screenshot-1.png"' in html and 'width="252"' in html


def render_month(tmp_path: Path, md: str, mode: str = "cid") -> str:
    month_dir = make_month(tmp_path)
    (month_dir / "newsletter.md").write_text(md, encoding="utf-8")
    subject, body = nb.read_newsletter(month_dir, "2026-11")
    return nb.render_html(body, subject, month_dir / "pics", mode)


def test_mobile_style_is_valid_css(tmp_path: Path) -> None:
    for mode in ("local", "cid"):
        html = render_month(tmp_path / mode, NEWSLETTER_MD, mode)
        assert "{{" not in html and "}}" not in html
        assert "@media only screen and (max-width: 620px) {" in html


def test_text_above_the_subject_is_dropped() -> None:
    subject, body = nb.extract_subject("a private note\n\n# The Subject\n\nBody.\n")
    assert subject == "The Subject"
    assert body == "Body.\n"


def test_subject_is_escaped(tmp_path: Path) -> None:
    html = render_month(tmp_path, "# Sub & <b>x</b>\n\nBody <i>text</i>.\n")
    assert "Sub &amp; &lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>x</b>" not in html


def test_plain_text_part_has_no_css_or_hidden_lines(tmp_path: Path) -> None:
    html = render_month(tmp_path, NEWSLETTER_MD)
    plain = nb.plain_text(html)
    assert "@media" not in plain and "font-family" not in plain
    assert plain.count("Dear Venerable monastics") == 1
    assert plain.count(SUBJECT) == 1
    assert "Useful DPD links:" in plain
    assert "\n\n\n" not in plain


@pytest.mark.parametrize(
    ("path", "host", "ok"),
    [
        ("/newsletter/2026-10/preview.html", "127.0.0.1:4000", True),
        ("/newsletter/2026-10/pics/a.png?x=1", "localhost:4000", True),
        ("/identity/logo/dpd-logo-512.png", "127.0.0.1:4000", True),
        ("/config.ini", "127.0.0.1:4000", False),
        ("/dpd.db", "127.0.0.1:4000", False),
        ("/newsletter/../config.ini", "127.0.0.1:4000", False),
        ("/newsletter/%2e%2e/config.ini", "127.0.0.1:4000", False),
        ("/", "127.0.0.1:4000", False),
        ("/newsletter/2026-10/preview.html", "evil.example:4000", False),
    ],
)
def test_preview_server_serves_only_the_newsletter(
    path: str, host: str, ok: bool
) -> None:
    assert nb.preview_may_serve(path, host) is ok


class FakeImap:
    def __init__(self, status: str) -> None:
        self.status = status

    def login(self, mail: str, password: str) -> None:
        pass

    def append(self, *args: object) -> tuple[str, list[bytes]]:
        return self.status, [b"[OVERQUOTA] mailbox full"]

    def logout(self) -> None:
        pass


@pytest.mark.parametrize("status", ["OK", "NO"])
def test_refused_draft_is_reported_and_stops_the_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    month_dir = make_month(tmp_path)
    pth = fake_paths(tmp_path)
    monkeypatch.setattr(nb, "config_read", lambda section, option: "x")
    monkeypatch.setattr(nb.imaplib, "IMAP4_SSL", lambda host, port: FakeImap(status))
    monkeypatch.setattr(nb, "ProjectPaths", lambda: pth)
    monkeypatch.setattr(
        nb.UposathaManger, "uposatha_today", classmethod(lambda cls: True)
    )
    nb.publish(month_dir, "2026-11")
    page = pth.docs_newsletters_md_path.read_text(encoding="utf-8")
    assert (page != PAGE) is (status == "OK")


def test_missing_config_makes_no_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nb, "config_read", lambda section, option: None)
    assert nb.append_draft(nb.MIMEMultipart()) is False


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("2026-10", True),
        ("2026-12", True),
        ("2026-13", False),
        ("2026-00", False),
        ("../x", False),
        ("2026-1", False),
    ],
)
def test_month_argument_is_validated(value: str, ok: bool) -> None:
    if ok:
        assert nb.month_arg(value) == value
    else:
        with pytest.raises(argparse.ArgumentTypeError):
            nb.month_arg(value)


def test_docs_entry_shifts_a_stray_h1() -> None:
    entry = nb.docs_entry(
        SUBJECT, "# Another\n\nText.\n", "2026-11", date(2026, 11, 24)
    )
    assert "## Another" in entry.splitlines()


def test_display_size_reads_rotation_without_decoding(tmp_path: Path) -> None:
    exif = Image.Exif()
    exif[0x0112] = 6
    path = save(photo(400, 300), tmp_path / "rotated.jpg", "JPEG", exif=exif)
    assert nb.upright_size(path) == (300, 400)
