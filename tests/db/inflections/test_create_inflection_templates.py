"""Tests for db/inflections/create_inflection_templates.py

sync_templates and add_pending_templates on a temp sqlite db.
DB writes against the real dpd.db are not tested.
"""

import pickle
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from db.db_helpers import create_tables, get_db_session
from db.inflections.create_inflection_templates import (
    add_pending_templates,
    clear_db_pending_templates,
    clear_pickle_pending_templates,
    sync_templates,
)
from db.inflections.inflection_template_files import TemplateFile
from db.models import DbInfo, InflectionTemplates
from sqlalchemy.orm import Session
from tools.paths import ProjectPaths


def make_template(
    pattern: str, like: str, data: list[list[list[str]]] | None = None
) -> TemplateFile:
    if data is None:
        data = [
            [[""], ["sg"], [""], ["pl"]],
            [["pr 3rd"], ["ati"], ["pr 3rd sg"], ["anti"]],
        ]
    return TemplateFile(pattern=pattern, like=like, data=data)


@pytest.fixture
def db_session(tmp_path):
    """A temp sqlite db with the tables created."""
    db_path = tmp_path / "test.db"
    create_tables(db_path)
    session = get_db_session(db_path)
    yield session
    session.close()


@pytest.fixture
def tmp_pth(tmp_path):
    """ProjectPaths pointing into the temp dir (no dirs created)."""
    return ProjectPaths(base_dir=tmp_path, create_dirs=False)


def db_patterns(db_session: Session) -> set[str]:
    return {t.pattern for t in db_session.query(InflectionTemplates).all()}


def test_sync_add(db_session):
    """A new template is added and reported."""
    changed = sync_templates(db_session, [make_template("a pr", "ka")])
    assert changed == ["a pr"]
    row = db_session.query(InflectionTemplates).filter_by(pattern="a pr").one()
    assert row.like == "ka"
    assert row.inflection_template_unpack == make_template("a pr", "ka").data


def test_sync_update(db_session):
    """A changed like or data is updated and reported."""
    sync_templates(db_session, [make_template("a pr", "ka")])
    changed = sync_templates(db_session, [make_template("a pr", "gha")])
    assert changed == ["a pr"]
    row = db_session.query(InflectionTemplates).filter_by(pattern="a pr").one()
    assert row.like == "gha"


def test_sync_update_data(db_session):
    """Changed data alone is updated and reported."""
    sync_templates(db_session, [make_template("a pr", "ka")])
    new_data = [
        [[""], ["sg"], [""], ["pl"]],
        [["pr 3rd"], ["eti"], ["pr 3rd sg"], ["enti"]],
    ]
    changed = sync_templates(db_session, [make_template("a pr", "ka", new_data)])
    assert changed == ["a pr"]


def test_sync_no_change(db_session):
    """Syncing the same templates twice reports nothing."""
    sync_templates(db_session, [make_template("a pr", "ka")])
    changed = sync_templates(db_session, [make_template("a pr", "ka")])
    assert changed == []


def test_sync_delete(db_session):
    """A db row missing from the files is deleted and reported."""
    sync_templates(db_session, [make_template("a pr", "ka")])
    changed = sync_templates(db_session, [])
    assert changed == ["a pr"]
    assert db_patterns(db_session) == set()


def test_add_pending_adds_up(db_session, tmp_pth):
    """Two add_pending_templates calls union into both pending lists."""
    add_pending_templates(db_session, tmp_pth, ["ze pr", "a pr"])
    add_pending_templates(db_session, tmp_pth, ["i pr"])

    with tmp_pth.template_changed_path.open("rb") as f:
        pickle_list: list[str] = pickle.load(f)

    db_info_row = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert pickle_list == ["a pr", "i pr", "ze pr"]
    assert db_info_row.value_unpack == ["a pr", "i pr", "ze pr"]


def test_add_pending_missing_pickle_is_empty(db_session, tmp_pth):
    """A missing pickle and missing DbInfo row count as empty lists."""
    merged = add_pending_templates(db_session, tmp_pth, ["b pr"])
    assert merged == ["b pr"]
    db_info_row = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert db_info_row.value_unpack == ["b pr"]


def test_add_pending_keeps_the_two_lists_apart(db_session, tmp_pth):
    """A name the db reader already cleared must not return from the pickle."""
    add_pending_templates(db_session, tmp_pth, ["a pr", "i pr"])
    clear_db_pending_templates(db_session, ["a pr", "i pr"])
    add_pending_templates(db_session, tmp_pth, ["ze pr"])

    row = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert row.value_unpack == ["ze pr"]
    with tmp_pth.template_changed_path.open("rb") as f:
        assert pickle.load(f) == ["a pr", "i pr", "ze pr"]


def test_clear_db_pending_templates_removes_only_used(db_session):
    """Names added after the reader loaded its copy stay pending."""
    db_info_row = DbInfo(key="changed_templates_list")
    db_info_row.value_pack(["a pr", "i pr"])
    db_session.add(db_info_row)
    db_session.commit()

    clear_db_pending_templates(db_session, ["a pr"])

    row = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert row.value_unpack == ["i pr"]


def test_clear_db_pending_templates_creates_row(db_session):
    """The clear helper creates the DbInfo row if it is missing."""
    clear_db_pending_templates(db_session, ["a pr"])
    row = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert row.value_unpack == []


def test_clear_pickle_pending_templates_removes_only_used(tmp_pth):
    """The pickle clear keeps names the reader did not use."""
    tmp_pth.template_changed_path.parent.mkdir(parents=True, exist_ok=True)
    with tmp_pth.template_changed_path.open("wb") as f:
        pickle.dump(["a pr", "i pr"], f)

    clear_pickle_pending_templates(tmp_pth, ["a pr"])

    with tmp_pth.template_changed_path.open("rb") as f:
        assert pickle.load(f) == ["i pr"]


def test_import_has_no_db_side_effects() -> None:
    """Importing the module must not open the DB or create directories.

    Run from an empty cwd with no dpd.db — the old class-level GlobalVars
    exited with 'Database file doesn't exist' here.
    """
    repo_root = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, "-c", "import db.inflections.create_inflection_templates"],
            cwd=td,
            env={"PYTHONPATH": str(repo_root)},
            capture_output=True,
            text=True,
        )
        leftover = list(Path(td).iterdir())
    assert result.returncode == 0, result.stderr
    # importing must leave the cwd completely untouched — no directory
    # tree from ProjectPaths and no log artifacts from tools/printer.py
    assert leftover == []
