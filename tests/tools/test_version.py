"""Tests for the release version string and the db_info metadata block."""

import json
from pathlib import Path

import pytest

from db.db_helpers import create_tables, get_db_session
from tools import version
from db.models import DbInfo
from tools.version import (
    AUTHOR,
    LICENSE,
    make_citation,
    make_citation_cff,
    make_db_metadata,
    release_date,
    update_citation_cff,
    update_db_version,
)

VERSION = "v0.4.20260905"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_tables(path)
    return path


def test_citation_names_author_and_version() -> None:
    citation = make_citation(VERSION)
    assert AUTHOR in citation
    assert VERSION in citation
    assert "Digital Pāḷi Dictionary" in citation


def test_citation_author_carries_the_full_name() -> None:
    assert AUTHOR == "Bodhirasa Bhikkhu"


def test_metadata_block_carries_citation_and_licence() -> None:
    metadata = make_db_metadata(VERSION)
    assert metadata["citation"] == make_citation(VERSION)
    assert metadata["license"] == LICENSE
    assert metadata["author"] == AUTHOR
    assert metadata["dpd_release_version"] == VERSION


def test_writes_the_whole_block_into_an_empty_db(db_path: Path) -> None:
    update_db_version(db_path, VERSION)

    with get_db_session(db_path) as db_session:
        stored = {row.key: row.value for row in db_session.query(DbInfo).all()}

    assert stored == make_db_metadata(VERSION)


def test_updates_an_existing_db_rather_than_skipping_it(db_path: Path) -> None:
    """The old code only wrote the metadata when the version row was absent, so
    a new key never reached a database that already existed."""

    with get_db_session(db_path) as db_session:
        db_session.add(DbInfo(key="dpd_release_version", value="v0.4.20200101"))
        db_session.add(DbInfo(key="author", value="Bodhirasa"))
        db_session.commit()

    update_db_version(db_path, VERSION)

    with get_db_session(db_path) as db_session:
        stored = {row.key: row.value for row in db_session.query(DbInfo).all()}

    assert stored["dpd_release_version"] == VERSION
    assert stored["author"] == AUTHOR
    assert stored["citation"] == make_citation(VERSION)


def test_rerunning_does_not_duplicate_rows(db_path: Path) -> None:
    update_db_version(db_path, VERSION)
    update_db_version(db_path, VERSION)

    with get_db_session(db_path) as db_session:
        keys = [row.key for row in db_session.query(DbInfo).all()]

    assert len(keys) == len(set(keys))


def test_citation_uses_the_doi_when_there_is_one() -> None:
    citation = make_citation(VERSION, "10.5281/zenodo.1234567")
    assert "https://doi.org/10.5281/zenodo.1234567" in citation
    assert "dpdict.net" not in citation


def test_citation_falls_back_to_the_website_without_a_doi() -> None:
    assert "https://www.dpdict.net/" in make_citation(VERSION)


def test_metadata_carries_the_doi_only_when_known() -> None:
    assert "doi" not in make_db_metadata(VERSION)
    assert make_db_metadata(VERSION, "10.5281/zenodo.1")["doi"] == "10.5281/zenodo.1"


def test_release_date_comes_from_the_version_patch() -> None:
    assert release_date(VERSION) == "2026-09-05"


def test_citation_cff_names_the_version_and_omits_an_unknown_doi() -> None:
    cff = make_citation_cff(VERSION)
    assert f"version: {VERSION}" in cff
    assert "date-released: '2026-09-05'" in cff
    assert "doi:" not in cff

    with_doi = make_citation_cff(VERSION, "10.5281/zenodo.1234567")
    assert "doi: 10.5281/zenodo.1234567" in with_doi


def _set_uposatha(monkeypatch: pytest.MonkeyPatch, today: bool) -> None:
    monkeypatch.setattr(
        version.UposathaManger, "uposatha_today", classmethod(lambda cls: today)
    )


def test_cff_is_rewritten_on_an_uposatha(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_uposatha(monkeypatch, True)
    cff_path = tmp_path / "CITATION.cff"
    cff_path.write_text("stale", encoding="utf-8")

    update_citation_cff(cff_path, VERSION)

    assert cff_path.read_text(encoding="utf-8") == make_citation_cff(VERSION)


def test_cff_is_left_alone_on_an_ordinary_day(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """It is a tracked file naming the released version — a dev build must not
    churn it with a version that was never released."""

    _set_uposatha(monkeypatch, False)
    cff_path = tmp_path / "CITATION.cff"
    cff_path.write_text("committed contents", encoding="utf-8")

    update_citation_cff(cff_path, VERSION)

    assert cff_path.read_text(encoding="utf-8") == "committed contents"


def test_cff_is_not_created_on_an_ordinary_day(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_uposatha(monkeypatch, False)
    cff_path = tmp_path / "CITATION.cff"

    update_citation_cff(cff_path, VERSION)

    assert not cff_path.exists()


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None


def _hits(*records: dict) -> dict:
    return {"hits": {"hits": list(records)}}


def _record(concept_doi: str, repo: str) -> dict:
    return {
        "conceptdoi": concept_doi,
        "metadata": {
            "related_identifiers": [{"identifier": f"https://github.com/{repo}"}]
        },
    }


def test_zenodo_query_is_a_quoted_phrase(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unquoted slash makes Zenodo's parser return HTTP 500."""

    seen: list[str] = []

    def fake_urlopen(url: str, timeout: int = 0) -> FakeResponse:
        seen.append(url)
        return FakeResponse(_hits())

    monkeypatch.setattr(version.urllib.request, "urlopen", fake_urlopen)
    version.fetch_zenodo_doi()

    assert "%22digitalpalidictionary%2Fdpd-db%22" in seen[0]


def test_rejects_a_record_belonging_to_another_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _hits(_record("10.5281/zenodo.21495338", "someone/else"))
    monkeypatch.setattr(
        version.urllib.request, "urlopen", lambda *_, **__: FakeResponse(payload)
    )

    assert version.fetch_zenodo_doi() is None


def test_accepts_the_dpd_record(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _hits(
        _record("10.5281/zenodo.111", "someone/else"),
        _record("10.5281/zenodo.222", "digitalpalidictionary/dpd-db"),
    )
    monkeypatch.setattr(
        version.urllib.request, "urlopen", lambda *_, **__: FakeResponse(payload)
    )

    assert version.fetch_zenodo_doi() == "10.5281/zenodo.222"


def test_rejects_a_malformed_doi(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _hits(_record("not-a-doi: injected", "digitalpalidictionary/dpd-db"))
    monkeypatch.setattr(
        version.urllib.request, "urlopen", lambda *_, **__: FakeResponse(payload)
    )

    assert version.fetch_zenodo_doi() is None


def test_a_network_error_is_reported_not_swallowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A silently swallowed HTTP 500 once got recorded as 'not published yet'."""

    def boom(*_: object, **__: object) -> None:
        raise version.urllib.error.HTTPError(
            "url", 500, "INTERNAL SERVER ERROR", {}, None
        )

    monkeypatch.setattr(version.urllib.request, "urlopen", boom)

    assert version.fetch_zenodo_doi() is None
    assert "zenodo lookup failed" in capsys.readouterr().out


def test_ensure_doi_is_skipped_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(version, "get_doi", lambda: None)

    def must_not_run() -> None:
        raise AssertionError("no network call may happen in CI")

    monkeypatch.setattr(version, "fetch_zenodo_doi", must_not_run)

    assert version.ensure_doi() is None


def test_ensure_doi_returns_the_stored_value_without_a_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(version, "get_doi", lambda: "10.5281/zenodo.42")

    def must_not_run() -> None:
        raise AssertionError("a stored DOI must not be re-fetched")

    monkeypatch.setattr(version, "fetch_zenodo_doi", must_not_run)

    assert version.ensure_doi() == "10.5281/zenodo.42"


def test_cff_artifact_url_pins_the_version() -> None:
    cff = make_citation_cff(VERSION)
    assert f"repository-artifact: {version.LATEST_RELEASE}/tag/{VERSION}" in cff
    assert "/releases/latest" not in cff
