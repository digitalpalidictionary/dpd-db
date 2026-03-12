#!/usr/bin/env python3

"""Scrape DPD newsletters from Gmail and compile into docs/newsletters.md."""

import base64
import hashlib
import json
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import cast

import requests
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from google.auth.credentials import Credentials as BaseCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from markdownify import markdownify as md

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_LABEL = "DPD Mailers"

FOOTER_MARKERS = [
    "useful links",
    "unsubscribe",
    "manage preferences",
    "view in browser",
    "email preferences",
    "update your preferences",
]


def get_gmail_service(pth: ProjectPaths):
    """Authenticate with Gmail API and return service object."""
    creds: BaseCredentials | None = None

    if pth.gmail_token_path.exists():
        creds = Credentials.from_authorized_user_file(str(pth.gmail_token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not pth.gmail_credentials_path.exists():
                pr.warning("credentials.json not found — skipping newsletter scrape")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                str(pth.gmail_credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        pth.gmail_token_path.write_text(cast(Credentials, creds).to_json())

    return build("gmail", "v1", credentials=creds)


def get_label_id(service, label_name: str) -> str | None:
    """Find the Gmail label ID by name."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == label_name:
            return label["id"]
    return None


def get_all_message_ids(service, label_id: str) -> list[str]:
    """Fetch all message IDs from a label, handling pagination."""
    message_ids: list[str] = []
    page_token: str | None = None

    while True:
        kwargs: dict = {
            "userId": "me",
            "labelIds": [label_id],
            "maxResults": 100,
        }
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.users().messages().list(**kwargs).execute()
        messages = results.get("messages", [])
        message_ids.extend(msg["id"] for msg in messages)

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return message_ids


def get_html_body(payload: dict) -> str:
    """Extract HTML body from MIME message payload."""
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = get_html_body(part)
        if result:
            return result

    return ""


def get_header_value(headers: list[dict], name: str) -> str:
    """Get a header value by name from message headers."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def download_image(url: str, pics_dir: Path) -> str | None:
    """Download an image and return the local filename."""
    try:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        ext = ".jpg"
        url_path = url.split("?")[0]
        for candidate_ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]:
            if url_path.lower().endswith(candidate_ext):
                ext = candidate_ext
                break

        filename = f"{url_hash}{ext}"
        filepath = pics_dir / filename

        if filepath.exists():
            return filename

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        filepath.write_bytes(response.content)
        return filename

    except Exception as e:
        pr.warning(f"failed to download image {url}: {e}")
        return None


def fetch_cid_attachment(
    service, message_id: str, attachment_id: str, pics_dir: Path, cid: str
) -> str | None:
    """Fetch an inline CID attachment from Gmail and save locally."""
    try:
        att = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = base64.urlsafe_b64decode(att["data"])
        cid_hash = hashlib.md5(cid.encode()).hexdigest()[:12]
        filename = f"{cid_hash}.jpg"
        filepath = pics_dir / filename
        filepath.write_bytes(data)
        return filename
    except Exception as e:
        pr.warning(f"failed to fetch CID attachment {cid}: {e}")
        return None


def build_cid_map(payload: dict) -> dict[str, str]:
    """Build a mapping of Content-ID → attachment ID from MIME parts."""
    cid_map: dict[str, str] = {}
    for part in payload.get("parts", []):
        headers = {h["name"].lower(): h["value"] for h in part.get("headers", [])}
        content_id = headers.get("content-id", "")
        if content_id:
            clean_cid = content_id.strip("<>")
            att_id = part.get("body", {}).get("attachmentId", "")
            if att_id:
                cid_map[clean_cid] = att_id
        if part.get("parts"):
            cid_map.update(build_cid_map(part))
    return cid_map


def strip_footer(soup: BeautifulSoup) -> None:
    """Remove footer/unsubscribe sections from the email HTML."""
    for element in soup.find_all(string=True):
        if not isinstance(element, NavigableString):
            continue
        text_lower = str(element).lower()
        for marker in FOOTER_MARKERS:
            if marker in text_lower:
                parent = element.find_parent(["table", "div", "tr", "td", "p"])
                if parent:
                    top_parent = parent.find_parent("table") or parent
                    top_parent.decompose()
                    return


def strip_unsubscribe_links(soup: BeautifulSoup) -> None:
    """Remove unsubscribe-related links and surrounding elements."""
    patterns = re.compile(
        r"unsubscribe|manage\s+preferences|email\s+preferences|"
        r"update\s+your\s+preferences|view\s+in\s+browser",
        re.IGNORECASE,
    )
    for a_tag in soup.find_all("a", string=patterns):
        parent = a_tag.find_parent(["p", "div", "td", "tr"])
        if parent:
            parent.decompose()
        else:
            a_tag.decompose()


def process_email(
    service,
    message_id: str,
    pics_dir: Path,
) -> dict | None:
    """Process a single email: extract content, download images, clean HTML."""
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = msg.get("payload", {}).get("headers", [])
    subject = get_header_value(headers, "Subject")
    date_str = get_header_value(headers, "Date")

    try:
        email_date = parsedate_to_datetime(date_str)
    except Exception:
        email_date = datetime.now()

    html_body = get_html_body(msg.get("payload", {}))
    if not html_body:
        pr.warning(f"no HTML body found for: {subject}")
        return None

    soup = BeautifulSoup(html_body, "html.parser")

    cid_map = build_cid_map(msg.get("payload", {}))
    for img in cast(list[Tag], soup.find_all("img")):
        src = str(img.get("src", ""))

        if src.startswith("cid:"):
            cid = src[4:]
            att_id = cid_map.get(cid, "")
            if att_id:
                filename = fetch_cid_attachment(
                    service, message_id, att_id, pics_dir, cid
                )
                if filename:
                    img["src"] = f"pics/newsletters/{filename}"
                    continue

        if src.startswith(("http://", "https://")):
            filename = download_image(src, pics_dir)
            if filename:
                img["src"] = f"pics/newsletters/{filename}"

    strip_footer(soup)
    strip_unsubscribe_links(soup)

    markdown_content = md(str(soup), heading_style="ATX", strip=["style"])
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content).strip()

    return {
        "message_id": message_id,
        "subject": subject,
        "date": email_date.strftime("%Y-%m-%d"),
        "date_sort": email_date.isoformat(),
        "content": markdown_content,
    }


def build_newsletters_md(emails: list[dict], output_path: Path) -> None:
    """Build the newsletters.md file from all processed emails."""
    lines: list[str] = ["# DPD Newsletters\n"]

    emails_sorted = sorted(emails, key=lambda e: e["date_sort"], reverse=True)

    for email in emails_sorted:
        lines.append(f"## {email['subject']}")
        lines.append(f"*{email['date']}*\n")
        lines.append(email["content"])
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pr.tic()
    pr.title("newsletter scraper")

    if not config_test("exporter", "scrape_newsletters", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    pth.docs_newsletters_pics_dir.mkdir(parents=True, exist_ok=True)

    pr.green("authenticating with gmail")
    service = get_gmail_service(pth)
    if service is None:
        pr.toc()
        return
    pr.yes("ok")

    pr.green("finding label")
    label_id = get_label_id(service, GMAIL_LABEL)
    if label_id is None:
        pr.warning(f"gmail label '{GMAIL_LABEL}' not found")
        pr.toc()
        return
    pr.yes("ok")

    pr.green("fetching message list")
    all_message_ids = get_all_message_ids(service, label_id)
    pr.yes(str(len(all_message_ids)))

    processed: dict[str, dict] = {}
    if pth.newsletter_processed_json.exists():
        processed = json.loads(
            pth.newsletter_processed_json.read_text(encoding="utf-8")
        )

    new_ids = [mid for mid in all_message_ids if mid not in processed]
    pr.green("new emails to process")
    pr.yes(str(len(new_ids)))

    for i, message_id in enumerate(new_ids):
        pr.counter(i + 1, len(new_ids), message_id[:16])
        result = process_email(service, message_id, pth.docs_newsletters_pics_dir)
        if result:
            processed[message_id] = result

    all_emails = list(processed.values())
    pr.green("building newsletters.md")
    build_newsletters_md(all_emails, pth.docs_newsletters_md_path)
    pr.yes(str(len(all_emails)))

    pth.newsletter_processed_json.write_text(
        json.dumps(processed, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    pr.toc()


if __name__ == "__main__":
    main()
