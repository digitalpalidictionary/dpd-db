#!/usr/bin/env python3

"""Build the monthly DPD newsletter from markdown.

Reads `newsletter/<YYYY-MM>/newsletter.md`, renders it into a DPD-branded,
responsive HTML email (CSS inlined for Gmail), and:

  1. `--init`: starts the month folder from newsletter_template.md
  2. with no flag, writes `newsletter/<YYYY-MM>/preview.html`; with `--watch`
     it serves the preview locally and reloads it in the browser on every save
  3. `--publish`: creates a Gmail draft with the pics embedded as inline
     attachments (CID); on uposatha days it also adds the newsletter to
     docs/newsletters.md

Usage:
    uv run newsletter/newsletter_build.py [month] [--init | --watch | --publish]

Month defaults to the newest month folder (`--init`: the current month).
"""

import argparse
import io
import posixpath
import importlib.util
import imaplib
import re
import subprocess
import threading
import time
import webbrowser
from dataclasses import dataclass
from html import escape
from datetime import date, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from types import ModuleType
from typing import BinaryIO
from urllib.parse import unquote, urlsplit

import css_inline
import markdown
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.uposatha_day import UposathaManger

GMAIL_CLIP_LIMIT = 95_000  # warn well before Gmail's ~102 KB clipping
GMAIL_SEND_LIMIT_MB = 25
GMAIL_IMAP_HOST = "imap.gmail.com"
DRAFTS_FOLDER = '"[Gmail]/Drafts"'

NEWSLETTER_DIR = Path("newsletter")
BUILDER_PATH = NEWSLETTER_DIR / "newsletter_build.py"
USEFUL_LINKS_PATH = NEWSLETTER_DIR / "useful_links.md"
TEMPLATE_PATH = NEWSLETTER_DIR / "newsletter_template.md"
MONTH_PATTERN = r"\d{4}-(0[1-9]|1[0-2])"
# the preview server hands out only these, never config.ini or the database
PREVIEW_PATHS = ("newsletter/", "identity/logo/")

# live preview only; the email never carries it
RELOAD_SCRIPT = """
<script>
(function () {
  var key = "newsletter-scroll";
  window.addEventListener("load", function () {
    var y = sessionStorage.getItem(key);
    if (y !== null) window.scrollTo(0, parseInt(y, 10));
  });
  setInterval(function () {
    fetch(location.href, { cache: "no-store" })
      .then(function (r) { return r.text(); })
      .then(function (text) {
        if (text.indexOf("__STAMP__") === -1) {
          sessionStorage.setItem(key, String(window.scrollY));
          location.reload();
        }
      })
      .catch(function () {});
  }, 1000);
})();
</script>
"""

MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# DPD branding, from identity/css/dpd-variables.css (light mode)
COLOR_LIGHT = "#e5f7ff"  # --light hsl(198,100%,95%) — page background
COLOR_LIGHT_SHADE = "#e0f2fa"  # --light-shade hsl(198,100%,93%) — borders
COLOR_PRIMARY = "#00a8f0"  # --primary hsl(198,100%,50%) — logo, subject line
COLOR_ALT = "#0066cc"  # --primary-alt hsl(205,100%,40%) — links
COLOR_TEXT = "#198adb"  # --primary-text hsl(205,79%,48%) — headings
COLOR_GRAY = "#808080"  # --gray hsl(0,0%,50%)
COLOR_GRAY_DARK = "#404040"  # --gray-dark hsl(0,0%,25%) — body text
# Inter from identity/fonts — email clients strip @font-face, so it degrades
# gracefully to the system stack
FONT_STACK = "Inter, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
LOGO_PATH = Path("identity/logo/dpd-logo-512.png")  # light icon
LOGO_CID = "dpd-logo"
LOGO_FILENAME = "dpd-logo.png"

# Pictures fit a box one content column wide and 560 px tall: every tall picture
# in the past newsletters (phone screenshots, a camera photo) was shown 562 px
# tall by Gmail's "best fit", and wide ones filled the column.
DISPLAY_MAX_W = 520  # 600 px card minus 2 x 40 px padding
DISPLAY_MAX_H = 560
# the card's text column on the narrowest phone (320 px screen); a picture wider
# than this is sized by the column, not by a fixed pixel width
PHONE_COLUMN_W = 265
# Gmail never shrinks picture bytes (tested on draft, send and forward), so the
# builder does: at most 2x the display size, sharp on phones and HiDPI screens
PIXEL_DENSITY = 2
# past newsletter pictures: median 49 KB, nearly all under 200 KB
PIC_KEEP_BYTES = 200_000
JPEG_QUALITY = 82
PIC_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# media queries can't be inlined and css_inline drops them, so this block is
# re-inserted into the head after inlining (Gmail supports <style> + media queries)
MEDIA_QUERIES = """
<style>
  @media only screen and (max-width: 620px) {
    .content { padding: 20px 16px !important; }
  }
</style>
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{subject}</title>
<style>
  body, table, td {{ font-family: {font}; }}
  a {{ color: {alt}; }}
  h1, h2, h3 {{ color: {text}; line-height: 1.3; }}
  h2 {{ font-size: 20px; border-bottom: 1px solid {primary}; padding-bottom: 6px; }}
  img {{ max-width: 100%; height: auto; border-radius: 6px; }}
  blockquote {{
    margin: 16px 0; padding: 4px 16px; border-left: 3px solid {primary};
    color: {gray}; font-style: italic;
  }}
</style>
</head>
<body style="margin: 0; padding: 0; background-color: {light};">
<div style="display: none; max-height: 0; overflow: hidden;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: {light};">
  <tr>
    <td align="center" style="padding: 24px 12px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
        <tr>
          <td class="content" align="center" style="padding: 32px 40px 0 40px;">
            <img src="{logo_src}" width="64" alt="Digital Pāḷi Dictionary"
                 style="width: 64px; height: auto; border-radius: 0;">
          </td>
        </tr>
        <tr>
          <td class="content" style="padding: 16px 40px 16px 40px;">
            <div style="font-size: 13px; font-weight: bold; letter-spacing: 1px;
                        text-transform: uppercase; color: {primary}; text-align: center;">
              {subject}
            </div>
          </td>
        </tr>
        <tr>
          <td class="content" style="padding: 8px 40px 32px 40px; font-size: 15px;
                                     line-height: 1.65; color: {gray_dark};">
            {body}
            <div style="margin-top: 16px; font-size: 13px; color: {gray};">
              <i>To unsubscribe from future updates, please reply with
              'alamettāvatā' in the subject line.</i>
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding: 16px 40px 24px 40px; border-top: 1px solid {light_shade};">
            <div style="font-size: 12px; color: {gray}; line-height: 1.6;">
              {footer_links}
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


def month_arg(value: str) -> str:
    """Accept only YYYY-MM with a real month, so no path can sneak in."""
    if not re.fullmatch(MONTH_PATTERN, value):
        raise argparse.ArgumentTypeError(f"{value!r} is not a month like 2026-10")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "month",
        nargs="?",
        type=month_arg,
        help="newsletter month folder, YYYY-MM (default: the newest folder)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--init", action="store_true", help="scaffold the month folder")
    mode.add_argument(
        "--watch", action="store_true", help="live preview in the browser"
    )
    mode.add_argument(
        "--publish",
        action="store_true",
        help="Gmail draft; docs newsletters page on uposatha days",
    )
    return parser.parse_args()


def latest_month(newsletter_dir: Path = NEWSLETTER_DIR) -> str | None:
    """Return the newest YYYY-MM folder name, or None if there is none."""
    months = sorted(
        p.name
        for p in newsletter_dir.iterdir()
        if p.is_dir() and re.fullmatch(MONTH_PATTERN, p.name)
    )
    return months[-1] if months else None


def init_month_folder(month_dir: Path, month: str) -> bool:
    """Create the month folder from newsletter_template.md and a pics/ dir."""
    if month_dir.exists():
        pr.amber(f"{month_dir} already exists")
        return False
    if not TEMPLATE_PATH.exists():
        pr.red(f"{TEMPLATE_PATH} not found")
        return False
    (month_dir / "pics").mkdir(parents=True)
    (month_dir / "newsletter.md").write_text(
        TEMPLATE_PATH.read_text(encoding="utf-8").replace(
            "{{MONTH}}", prettify_month(month)
        ),
        encoding="utf-8",
    )
    pr.green(f"scaffolded {month_dir} from {TEMPLATE_PATH}")
    return True


def prettify_month(month: str) -> str:
    year, _, mon = month.partition("-")
    return f"{MONTH_NAMES[int(mon)]} {year}"


def extract_subject(md_text: str) -> tuple[str, str]:
    """Split off the first H1 as the subject; anything above it is dropped."""
    match = re.search(r"^# (.+)$", md_text, flags=re.MULTILINE)
    if not match:
        return "", md_text
    subject = match.group(1).strip()
    remainder = md_text[match.end() :]
    return subject, remainder.lstrip()


def render_useful_links() -> str:
    """Render useful_links.md, the footer every newsletter shares."""
    md_text = USEFUL_LINKS_PATH.read_text(encoding="utf-8")
    # nl2br: each line of the file is its own line in the mail, as in the
    # footer of the sent newsletters
    html = markdown.markdown(md_text, extensions=["nl2br"])
    return html.replace("<p>", '<p style="margin: 0 0 10px 0;">')


@dataclass
class EmailPic:
    """A picture as it goes into the mail and onto the docs site."""

    name: str
    data: bytes
    subtype: str
    display: tuple[int, int]


def display_size(width: int, height: int) -> tuple[int, int]:
    """Size the picture is shown at: fit inside the display box, never enlarge."""
    scale = min(1.0, DISPLAY_MAX_W / width, DISPLAY_MAX_H / height)
    return max(1, round(width * scale)), max(1, round(height * scale))


def open_upright(data: bytes) -> Image.Image:
    """Open a picture turned the way a phone camera meant it."""
    image = Image.open(io.BytesIO(data))
    image.load()
    return ImageOps.exif_transpose(image)


def upright_size(path: Path) -> tuple[int, int]:
    """Pixel size as shown, read from the header without decoding the picture."""
    with Image.open(path) as image:
        width, height = image.size
        # EXIF orientations 5-8 turn the picture a quarter turn
        if image.getexif().get(0x0112) in (5, 6, 7, 8):
            return height, width
    return width, height


def prepare_pic(path: Path) -> EmailPic:
    """Shrink a picture to at most 2x its display size, in PNG or JPEG.

    Small pictures go out byte for byte. Larger ones are saved as a 256-colour
    PNG and as a JPEG, and the smaller file wins. The original is not touched.
    """
    data = path.read_bytes()
    raw = Image.open(io.BytesIO(data))
    image = open_upright(data)
    fmt = (raw.format or "").lower()
    display = display_size(*image.size)
    scale = min(1.0, PIXEL_DENSITY * display[0] / image.width)
    target = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))

    if fmt == "gif":
        # may be animated; re-encoding would keep only the first frame
        return EmailPic(path.name, data, fmt, display)
    if (
        fmt in ("png", "jpeg")
        and target == raw.size
        and image.size == raw.size
        and len(data) <= PIC_KEEP_BYTES
    ):
        return EmailPic(path.name, data, fmt, display)

    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        # the mail card is white, so transparent parts stay white
        flat = Image.new("RGB", rgba.size, "white")
        flat.paste(rgba, mask=rgba.getchannel("A"))
        image = flat
    else:
        image = image.convert("RGB")
    if image.size != target:
        image = image.resize(target, Image.Resampling.LANCZOS)

    png, jpeg = io.BytesIO(), io.BytesIO()
    image.quantize(
        colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
    ).save(png, "PNG", optimize=True)
    image.save(jpeg, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    if len(png.getvalue()) <= len(jpeg.getvalue()):
        return EmailPic(f"{path.stem}.png", png.getvalue(), "png", display)
    return EmailPic(f"{path.stem}.jpg", jpeg.getvalue(), "jpeg", display)


def size_pictures(body_html: str, pics_dir: Path) -> str:
    """Give every pics/ picture its display size and centre it."""
    soup = BeautifulSoup(body_html, "html.parser")
    for img in soup.find_all("img"):
        src = str(img.get("src", ""))
        if not src.startswith("pics/"):
            continue
        # clients that ignore auto margins still centre via the paragraph
        if img.parent is not None and img.parent.name == "p":
            img.parent["style"] = "text-align: center;"
        centre = "display: block; margin: 0 auto;"
        img["style"] = centre
        path = pics_dir / src.removeprefix("pics/")
        try:
            width, height = display_size(*upright_size(path))
        except OSError as e:
            pr.amber(f"cannot size {path}: {e}")
            continue
        img["width"] = str(width)
        img["height"] = str(height)
        img["style"] = f"{centre} width: {width}px; height: auto;"
        if width > PHONE_COLUMN_W:
            # a fixed 520 px wide picture stuck out of the phone column, and
            # the mail then showed with tiny text on the phone while max-width
            # alone did not stop it (only after the pics stopped swapping, so
            # the wide one was no longer in the 64 px logo slot)
            img["style"] = f"{centre} width: 100%; max-width: {width}px; height: auto;"
    return str(soup)


def render_html(md_text: str, subject: str, pics_dir: Path, image_mode: str) -> str:
    """Render markdown to inlined email HTML.

    image_mode: "local" keeps pics/ paths (preview),
    "cid" rewrites them to cid: references (Gmail draft).
    """
    body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    body = size_pictures(body, pics_dir)

    if image_mode == "cid":
        body = re.sub(r'src="pics/([^"]+)"', r'src="cid:\1"', body)

    soup = BeautifulSoup(body, "html.parser")
    preheader = soup.get_text(separator=" ")[:100]

    html = TEMPLATE.format(
        subject=escape(subject),
        preheader=escape(preheader),
        body=body,
        font=FONT_STACK,
        light=COLOR_LIGHT,
        light_shade=COLOR_LIGHT_SHADE,
        primary=COLOR_PRIMARY,
        alt=COLOR_ALT,
        text=COLOR_TEXT,
        gray=COLOR_GRAY,
        gray_dark=COLOR_GRAY_DARK,
        logo_src=(
            f"cid:{LOGO_CID}"
            if image_mode == "cid"
            else (Path("../..") / LOGO_PATH).as_posix()
        ),
        footer_links=render_useful_links(),
    )
    # every link opens in a new tab, body and footer alike
    html = re.sub(r"<a (?![^>]*\btarget=)", '<a target="_blank" ', html)
    inlined = css_inline.inline(html)
    return inlined.replace("</head>", MEDIA_QUERIES + "</head>")


def check_size(html: str) -> None:
    size = len(html.encode("utf-8"))
    if size > GMAIL_CLIP_LIMIT:
        pr.red(f"HTML is {size:,} bytes — Gmail may clip it (limit ~102 KB)")
    else:
        pr.green(f"HTML size {size:,} bytes (under Gmail's clip limit)")


def read_newsletter(month_dir: Path, month: str) -> tuple[str, str]:
    """Return (subject, markdown body) of the month's newsletter.md."""
    md_text = (month_dir / "newsletter.md").read_text(encoding="utf-8")
    subject, remainder = extract_subject(md_text)
    if not subject:
        subject = f"DPD Newsletter, {prettify_month(month)}"
    return subject, remainder


def write_preview(month_dir: Path, month: str, live: bool = False) -> Path:
    """Write preview.html; `live` adds the browser reload script."""
    subject, remainder = read_newsletter(month_dir, month)
    html = render_html(remainder, subject, month_dir / "pics", "local")
    if live:
        # a fresh stamp per build: the page reloads once the served file
        # no longer contains the stamp it was loaded with
        stamp = f"build-{time.time_ns()}"
        html = html.replace(
            "</body>", RELOAD_SCRIPT.replace("__STAMP__", stamp) + "</body>"
        )
    preview_path = month_dir / "preview.html"
    # write then rename, so the browser never fetches a half-written file
    tmp_path = preview_path.with_suffix(".tmp")
    tmp_path.write_text(html, encoding="utf-8")
    tmp_path.replace(preview_path)
    return preview_path


def source_stamp(month_dir: Path) -> tuple[tuple[str, int, int], ...]:
    """Names, mtimes and sizes of everything the preview is built from."""
    files = [
        month_dir / "newsletter.md",
        *sorted((month_dir / "pics").glob("*")),
        BUILDER_PATH,
        USEFUL_LINKS_PATH,
    ]
    stamp: list[tuple[str, int, int]] = []
    for f in files:
        try:
            st = f.stat()
            stamp.append((f.name, st.st_mtime_ns, st.st_size))
        except FileNotFoundError:
            # editors that save by rename leave the file briefly missing
            continue
    return tuple(stamp)


def load_fresh_builder() -> ModuleType:
    """Load this builder anew from disk, so layout edits show without a restart."""
    spec = importlib.util.spec_from_file_location(
        "newsletter_build_fresh", BUILDER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preview_may_serve(url_path: str, host: str) -> bool:
    """Serve only the newsletter and the logo, only to a browser on this machine.

    The Host check stops a web page from reaching the server through a DNS name
    that points at 127.0.0.1.
    """
    if host.rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):
        return False
    rel = posixpath.normpath(unquote(urlsplit(url_path).path)).lstrip("/")
    return rel.startswith(PREVIEW_PATHS)


class PreviewHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def send_head(self) -> io.BytesIO | BinaryIO | None:
        if not preview_may_serve(self.path, self.headers.get("Host", "")):
            self.send_error(404)
            return None
        return super().send_head()


def picture_names(pics_dir: Path) -> set[str]:
    """Names of the pictures in pics/, ignoring half-downloaded and hidden files."""
    return {
        p.name
        for p in pics_dir.glob("*")
        if p.suffix.lower() in PIC_SUFFIXES and not p.name.startswith(".")
    }


def link_safe_name(pics_dir: Path, name: str) -> str:
    """Rename a picture whose name would break a markdown link (spaces, brackets)."""
    safe = re.sub(r"[\s()\[\]<>]+", "-", name)
    if safe == name:
        return name
    if (pics_dir / safe).exists():
        pr.amber(f"cannot rename {name}: {safe} already exists")
        return name
    (pics_dir / name).rename(pics_dir / safe)
    pr.green(f"renamed {name} → {safe}")
    return safe


def copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"], input=text.encode(), check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        pr.amber(f"clipboard copy failed: {e}")
        return False
    return True


def announce_new_pics(pics_dir: Path, known: set[str]) -> set[str]:
    """Put the markdown for each new picture on the clipboard; return all names."""
    new = sorted(picture_names(pics_dir) - known)
    if not new:
        return known
    lines = [f"![](pics/{link_safe_name(pics_dir, name)})" for name in new]
    copied = copy_to_clipboard("\n\n".join(lines))
    for line in lines:
        pr.green(f"{'on clipboard' if copied else 'paste this'}: {line}")
    return picture_names(pics_dir)


def watch(month_dir: Path, month: str) -> None:
    """Serve the preview locally and rebuild it on every save until Ctrl-C."""
    preview_path = write_preview(month_dir, month, live=True)
    handler = partial(PreviewHandler, directory=str(Path.cwd()))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/{preview_path.as_posix()}"
    pr.green(f"live preview: {url}")
    pr.green("edit and save newsletter.md or the builder — Ctrl-C to stop")
    pr.green("save a picture into pics/ and its markdown lands on the clipboard")
    webbrowser.open(url)

    pics_dir = month_dir / "pics"
    known = picture_names(pics_dir)
    last = source_stamp(month_dir)
    try:
        while True:
            time.sleep(0.5)
            current = source_stamp(month_dir)
            if current == last:
                continue
            last = current
            try:
                fresh = load_fresh_builder()
                known = fresh.announce_new_pics(pics_dir, known)
                fresh.write_preview(month_dir, month, live=True)
                pr.green(f"rebuilt {datetime.now():%H:%M:%S}")
            # a half-finished edit to the builder can raise anything; show it
            # and keep watching instead of killing the preview
            except Exception as e:
                pr.red(f"rebuild failed: {type(e).__name__}: {e}")
    except KeyboardInterrupt:
        server.shutdown()


def append_draft(msg: MIMEMultipart) -> bool:
    """Append the message to [Gmail]/Drafts (no recipient — address on send)."""
    mail = config_read("gmail", "mail")
    password = config_read("gmail", "password")
    if not mail or not password:
        pr.red("config.ini [gmail] mail / password missing — no draft made")
        return False
    conn = imaplib.IMAP4_SSL(GMAIL_IMAP_HOST, 993)
    try:
        conn.login(mail, password)
        # imaplib raises only on BAD; a refused APPEND (e.g. over quota) is NO
        status, data = conn.append(DRAFTS_FOLDER, "\\Draft", None, msg.as_bytes())
    finally:
        conn.logout()
    if status != "OK":
        pr.red(f"Gmail refused the draft: {status} {data}")
        return False
    pr.green("Gmail draft created — open Gmail, address, send")
    return True


def plain_text(html: str) -> str:
    """The mail as plain text: no CSS, no page title, no hidden preview line."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["style", "title"]):
        tag.decompose()
    for tag in soup.find_all("div", style=re.compile(r"display:\s*none")):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    lines = [" ".join(line.split()) for line in soup.get_text().splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def name_cid_image(html: str, old: str, new: str) -> str:
    """Point the <img> that used cid:`old` at cid:`new`, with `new` as its alt."""

    def fix(match: re.Match[str]) -> str:
        tag = match.group(0).replace(f'src="cid:{old}"', f'src="cid:{new}"')
        return re.sub(r'alt="[^"]*"', f'alt="{new}"', tag)

    return re.sub(rf'<img\b[^>]*src="cid:{re.escape(old)}"[^>]*>', fix, html)


def make_mime_message(html: str, subject: str, month_dir: Path) -> MIMEMultipart:
    """Build a multipart/related message with pics as inline CID images."""
    # Each image gets ONE name for its filename, Content-ID and alt text, and
    # the parts follow the page order, logo first. Do not "tidy" this back to
    # separate names or sorted parts: when the three names differed (pic
    # conversion had turned epitaka-app.png into .jpg, the alt was the
    # markdown caption) and the parts were sorted alphabetically, Gmail's
    # compose window swapped the pics on send, once even putting a screenshot
    # in the logo slot. The names alone did not fix it: a draft with one name
    # per image but no X-Attachment-Id still came out swapped (compose stored
    # a blank X-Attachment-Id on every pic). Adding the X-Attachment-Id header
    # below did, in one test; that it is THE cause is likely, not proven.
    # If pics swap again, stop embedding and link them from the docs site.
    pics_dir = month_dir / "pics"
    cids = dict.fromkeys(re.findall(r'src="cid:([^"]+)"', html))
    images: list[tuple[str, bytes, str]] = []
    html = name_cid_image(html, LOGO_CID, LOGO_FILENAME)
    images.append((LOGO_FILENAME, LOGO_PATH.read_bytes(), "png"))
    for src in [c for c in cids if c != LOGO_CID]:
        path = pics_dir / src
        if not path.exists():
            pr.amber(f"missing image: {path}")
            continue
        pic = prepare_pic(path)
        html = name_cid_image(html, src, pic.name)
        images.append((pic.name, pic.data, pic.subtype))

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain_text(html), "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)
    for name, data, subtype in images:
        image = MIMEImage(data, _subtype=subtype)
        image.add_header("Content-ID", f"<{name}>")
        # Gmail's own inline images carry these two headers. Without them
        # compose stored a blank X-Attachment-Id on every pic and the pics
        # lost their slots. Same fix as GAM-team/GAM pull request 2001.
        image.add_header("X-Attachment-Id", name)
        image.add_header("X-Attachment-Content-Disposition", "inline")
        image.add_header("Content-Disposition", "inline", filename=name)
        msg.attach(image)
    return msg


def strip_comments(md_text: str) -> str:
    """Remove HTML comments (template hints, commented-out pics)."""
    return re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)


def docs_entry(
    subject: str,
    body_md: str,
    month: str,
    day: date,
    pics: dict[str, EmailPic] | None = None,
) -> str:
    """Render one docs/newsletters.md entry from the newsletter markdown.

    Keeps the shape tools/rss_feed.py parses: a `## YYYY-MM-DD` heading,
    then the subject in bold as the first bold text. `pics` maps each source
    picture to its published file, for the new name and the display width.
    """
    pics = pics or {}
    body = strip_comments(body_md)
    # one level down, so sections sit under the date heading
    body = re.sub(r"^(#{1,5}) ", r"#\1 ", body, flags=re.MULTILINE)

    def published(match: re.Match[str]) -> str:
        name = match.group(2)
        pic = pics.get(name)
        path = f"{match.group(1)}pics/newsletters/{month}/{pic.name if pic else name}"
        if pic and match.group(1) == "](" and match.group(3) == ")":
            return f'{path}){{ width="{pic.display[0]}" }}'
        return path + match.group(3)

    body = re.sub(r'(\]\(|src=")pics/([^)"\s]+)([)"]?)', published, body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return f"## {day.isoformat()}\n**{subject}**\n\n{body}\n\n---\n\n"


def insert_docs_entry(page: str, entry: str, subject: str) -> str:
    """Put the entry above all others, replacing an earlier copy of it."""
    sections = re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2}$)", page)
    head, entries = sections[0], sections[1:]
    marker = f"**{subject}**"
    kept = [e for e in entries if e.splitlines()[1:2] != [marker]]
    return head + entry + "".join(kept)


def copy_docs_pics(
    body_md: str, month_dir: Path, dest_dir: Path
) -> dict[str, EmailPic]:
    """Write the newsletter's pics, shrunk as in the mail, to the docs folder."""
    names = sorted(
        set(re.findall(r'(?:\]\(|src=")pics/([^)"\s]+)', strip_comments(body_md)))
    )
    pics: dict[str, EmailPic] = {}
    for name in names:
        src = month_dir / "pics" / name
        if not src.exists():
            pr.amber(f"missing image: {src}")
            continue
        pic = prepare_pic(src)
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / pic.name).write_bytes(pic.data)
        pics[name] = pic
    return pics


def publish_docs(month_dir: Path, month: str, pth: ProjectPaths) -> None:
    """Add the newsletter to docs/newsletters.md, with its pics."""
    subject, remainder = read_newsletter(month_dir, month)
    pics = copy_docs_pics(remainder, month_dir, pth.docs_newsletters_pics_dir / month)
    entry = docs_entry(subject, remainder, month, date.today(), pics)
    page = pth.docs_newsletters_md_path.read_text(encoding="utf-8")
    pth.docs_newsletters_md_path.write_text(
        insert_docs_entry(page, entry, subject), encoding="utf-8"
    )
    pr.green(f"docs page updated: {pth.docs_newsletters_md_path}")


def publish(month_dir: Path, month: str) -> None:
    """Gmail draft always; the docs page only on uposatha days."""
    subject, remainder = read_newsletter(month_dir, month)
    draft_html = render_html(remainder, subject, month_dir / "pics", "cid")
    check_size(draft_html)
    msg = make_mime_message(draft_html, subject, month_dir)
    mail_mb = len(msg.as_bytes()) / 1_000_000
    if mail_mb > GMAIL_SEND_LIMIT_MB:
        pr.red(
            f"mail is {mail_mb:.1f} MB — over Gmail's {GMAIL_SEND_LIMIT_MB} MB limit"
        )
    else:
        pr.green(f"mail size {mail_mb:.1f} MB")
    if not append_draft(msg):
        pr.red("no draft — docs newsletters page not updated")
        return
    if not UposathaManger.uposatha_today():
        pr.amber("not an uposatha day — docs newsletters page not updated")
        return
    publish_docs(month_dir, month, ProjectPaths())


def main() -> None:
    pr.tic()
    args = parse_args()

    if args.init:
        month = args.month or datetime.now().strftime("%Y-%m")
        init_month_folder(NEWSLETTER_DIR / month, month)
        return

    month = args.month or latest_month()
    if not month:
        pr.red("no month folder — run just newsletter-new first")
        return
    month_dir = NEWSLETTER_DIR / month
    md_path = month_dir / "newsletter.md"
    if not md_path.exists():
        pr.red(f"{md_path} not found — run just newsletter-new first")
        return

    if args.watch:
        watch(month_dir, month)
    elif args.publish:
        publish(month_dir, month)
    else:
        pr.green(f"preview written: {write_preview(month_dir, month)}")

    pr.toc()


if __name__ == "__main__":
    main()
