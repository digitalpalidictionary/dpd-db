#!/usr/bin/env python3

"""Generate the DPD release version string (v{major}.{minor}.{yymmdd}) and
write it to config.ini and the db_info table. Run directly by the justfile
and the GitHub release workflows."""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DbInfo
from tools.configger import config_read, config_update
from tools.date_and_time import year_month_day
from tools.paths import ProjectPaths
from tools.printer import printer as pr

major = 0
minor = 4

# 0.3 > 0.4 added abbreviations_other to lookup table

AUTHOR = "Bodhirasa Bhikkhu"
EMAIL = "digitalpalidictionary@gmail.com"
WEBSITE = "https://www.dpdict.net/"
DOCS = "https://digitalpalidictionary.github.io/"
GITHUB = "https://github.com/digitalpalidictionary/dpd-db"
LATEST_RELEASE = "https://github.com/digitalpalidictionary/dpd-db/releases"
LICENSE = "CC BY-NC-SA 4.0"

# The worked example used in every citation surface. gacchati 1 is a stable,
# common entry; ids are never reused, so this link cannot rot onto another word.
EXAMPLE_LEMMA = "gacchati 1"
EXAMPLE_ID = 24043
KEYWORDS = ["Pāḷi", "Pali", "dictionary", "lexicography", "Buddhism", "Theravāda"]
ABSTRACT = (
    "A feature-rich Pāḷi-English dictionary with full declension and conjugation "
    "tables, compound deconstruction, examples from the Pāḷi canon, word frequency, "
    "root families and grammatical analysis. Runs on the web, in GoldenDict, MDict, "
    "DictTango and on Kindle."
)

# Zenodo mints the concept DOI once, on the first release it archives, and it
# always resolves to the newest release — so it is looked up once and reused.
# The repo path must be a quoted phrase: an unquoted "/" makes Zenodo's query
# parser return HTTP 500.
ZENODO_API = "https://zenodo.org/api/records"
ZENODO_REPO = "digitalpalidictionary/dpd-db"
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+$")


def get_doi() -> str | None:
    doi = config_read("version", "doi")
    return doi or None


def _hit_is_dpd(hit: dict) -> bool:
    """True only when the record actually points back at this GitHub repo.

    A free-text Zenodo search happily returns unrelated Pāḷi projects, and a
    wrong DOI here would be copied into CITATION.cff, dpd.db and every export."""

    identifiers = hit.get("metadata", {}).get("related_identifiers", [])
    return any(ZENODO_REPO in str(entry.get("identifier", "")) for entry in identifiers)


def fetch_zenodo_doi(timeout: int = 20) -> str | None:
    """Look up the Zenodo concept DOI for the repo, or None if not published yet."""

    query = urllib.parse.urlencode(
        {"q": f'"{ZENODO_REPO}"', "size": 10, "sort": "mostrecent"}
    )
    try:
        with urllib.request.urlopen(
            f"{ZENODO_API}?{query}", timeout=timeout
        ) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        # Never fatal — the DOI is a nicety, not a build input. But say so out
        # loud: a swallowed error once got recorded as "not published yet".
        pr.amber(f"zenodo lookup failed: {e}")
        return None

    for hit in payload.get("hits", {}).get("hits", []):
        concept_doi = str(hit.get("conceptdoi") or "")
        if concept_doi and _hit_is_dpd(hit) and DOI_PATTERN.match(concept_doi):
            return concept_doi
    return None


def ensure_doi() -> str | None:
    """Return the stored concept DOI, fetching and storing it the first time.

    Skipped in CI: config.ini is gitignored and rebuilt from a profile there, so
    a fetched value could never be persisted — it would just be a network call
    on every workflow run."""

    doi = get_doi()
    if doi:
        return doi

    if os.environ.get("CI"):
        pr.summary("zenodo doi", "skipped in ci")
        return None

    doi = fetch_zenodo_doi()
    if doi:
        config_update("version", "doi", doi, silent=True)
        pr.summary("zenodo doi", doi)
    else:
        pr.summary("zenodo doi", "not published yet")
    return doi


def make_citation(version: str, doi: str | None = None) -> str:
    """The recommended citation for this release.

    DPD is revised continuously, so the version is the part that makes a quoted
    reading findable again. Built here because this is where the version is
    generated — anywhere else would be a second copy that goes stale."""

    location = f"https://doi.org/{doi}" if doi else WEBSITE
    return f"{AUTHOR}. Digital Pāḷi Dictionary. Version {version}. {location}"


def make_version() -> tuple[str, str]:
    patch = year_month_day()

    version = f"v{major}.{minor}.{patch}"
    version_light = f"v{major}.{minor}"

    pr.summary("version", version)
    pr.summary("version light", version_light)

    return version, version_light


def make_db_metadata(version: str, doi: str | None = None) -> dict[str, str]:
    """The project metadata block carried inside dpd.db, for downstream apps."""

    metadata = {
        "dpd_release_version": version,
        "author": AUTHOR,
        "email": EMAIL,
        "website": WEBSITE,
        "docs": DOCS,
        "github": GITHUB,
        "latest_release": LATEST_RELEASE,
        "license": LICENSE,
        "citation": make_citation(version, doi),
        "___": "___",
    }
    if doi:
        metadata["doi"] = doi
    return metadata


def update_db_version(db_path: Path, version: str, doi: str | None = None) -> None:
    db_session = get_db_session(db_path)

    metadata = make_db_metadata(version, doi)

    # Upserted rather than written once at creation, so that a key added later
    # (or a corrected value) also reaches databases that already exist.
    existing: dict[str, DbInfo] = {
        row.key: row
        for row in db_session.query(DbInfo).filter(DbInfo.key.in_(metadata)).all()
    }

    for key, value in metadata.items():
        if key in existing:
            existing[key].value = value
        else:
            db_session.add(DbInfo(key=key, value=value))

    db_session.commit()
    pr.summary("dpd.db", "ok")


def release_date(version: str) -> str:
    """ISO date from the version's yyyymmdd patch, for CITATION.cff."""

    patch = version.rsplit(".", 1)[-1]
    return f"{patch[:4]}-{patch[4:6]}-{patch[6:]}"


def make_citation_cff(version: str, doi: str | None = None) -> str:
    """The repo's CITATION.cff, which GitHub and Zenodo both read.

    Generated rather than hand-kept so that the version it advertises is always
    the version that was actually released."""

    lines = [
        "# Generated by tools/version.py — do not edit by hand.",
        "cff-version: 1.2.0",
        "title: Digital Pāḷi Dictionary",
        "message: >-",
        "  Digital Pāḷi Dictionary is a work in progress and is revised",
        "  continuously. Please cite the version you consulted, so that the",
        "  reading you quote can be found again. When citing a single entry,",
        "  give its headword and permalink as well as the version.",
        "type: dataset",
        "authors:",
        "  - family-names: Bodhirasa",
        "    name-suffix: Bhikkhu",
        f"    email: {EMAIL}",
        f"version: {version}",
        f"date-released: '{release_date(version)}'",
        f"url: {WEBSITE}",
        f"repository-code: {GITHUB}",
        f"repository-artifact: {LATEST_RELEASE}/tag/{version}",
        "license: CC-BY-NC-SA-4.0",
    ]
    if doi:
        lines.append(f"doi: {doi}")
    lines.append("abstract: >-")
    lines.append(f"  {ABSTRACT}")
    lines.append("keywords:")
    lines.extend(f"  - {keyword}" for keyword in KEYWORDS)
    return "\n".join(lines) + "\n"


def update_citation_cff(cff_path: Path, version: str, doi: str | None = None) -> None:
    cff_path.write_text(make_citation_cff(version, doi), encoding="utf-8")
    pr.summary("CITATION.cff", "ok")


def main() -> None:
    pr.tic()
    pr.yellow_title("updating dpd release version")
    pth = ProjectPaths()
    version, version_light = make_version()

    config_update("version", "version", version, silent=True)
    pr.summary("config.ini", "ok")

    doi = ensure_doi()

    update_db_version(pth.dpd_db_path, version, doi)
    update_citation_cff(pth.citation_cff_path, version, doi)

    pr.toc()


if __name__ == "__main__":
    main()
