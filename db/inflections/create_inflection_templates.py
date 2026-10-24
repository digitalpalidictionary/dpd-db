#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
1. Load inflection templates from the TSV files
2. Sync the database to match them (add, update, delete)
3. Add the changed templates to the pending lists
   (DbInfo changed_templates_list and the shared_data/changed_templates
   pickle), which the readers clear after regenerating.
"""

import pickle

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.inflections.inflection_template_files import (
    TemplateFile,
    load_templates,
)
from db.models import DbInfo, InflectionTemplates
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def sync_templates(db_session: Session, templates: list[TemplateFile]) -> list[str]:
    """Add, update or delete InflectionTemplates rows to match the files.

    Returns the changed pattern names. Does not commit.
    """
    changed: list[str] = []
    file_patterns: set[str] = set()

    for t in templates:
        file_patterns.add(t.pattern)
        template_in_db = (
            db_session.query(InflectionTemplates)
            .filter(InflectionTemplates.pattern == t.pattern)
            .first()
        )
        new_row = InflectionTemplates(pattern=t.pattern, like=t.like)
        new_row.inflection_template_pack(t.data)  # type: ignore[arg-type]

        # added
        if not template_in_db:
            pr.green_title(f"{t.pattern} added")
            db_session.add(new_row)
            changed.append(t.pattern)

        # updated
        elif template_in_db.like != new_row.like or template_in_db.data != new_row.data:
            pr.green_title(f"{t.pattern} updated")
            db_session.delete(template_in_db)
            db_session.add(new_row)
            changed.append(t.pattern)

    # deleted
    db_templates = db_session.query(InflectionTemplates).all()
    for t in db_templates:
        if t.pattern not in file_patterns:
            pr.green_title(f"{t.pattern} deleted")
            db_session.delete(t)
            changed.append(t.pattern)

    return changed


def add_pending_templates(
    db_session: Session, pth: ProjectPaths, changed: list[str]
) -> list[str]:
    """Union the changed patterns into each pending list.

    Each list is merged with itself only: the two readers clear their own
    list at different times, so mixing them would bring back names one
    reader had already used. A missing DbInfo row or missing pickle counts
    as an empty list. Returns the merged DbInfo list, sorted with
    pali_list_sorter.
    """
    # the DbInfo list
    db_info_row = (
        db_session.query(DbInfo).filter_by(key="changed_templates_list").first()
    )
    current_db: list[str] = db_info_row.value_unpack if db_info_row else []
    merged_db: list[str] = pali_list_sorter(set(current_db) | set(changed))

    if not db_info_row:
        db_info_row = DbInfo(key="changed_templates_list")
        db_session.add(db_info_row)
    db_info_row.value_pack(merged_db)

    # the pickle
    current_pickle = _read_pending_pickle(pth)
    merged_pickle: list[str] = pali_list_sorter(set(current_pickle) | set(changed))
    _write_pending_pickle(pth, merged_pickle)

    return merged_db


def _read_pending_pickle(pth: ProjectPaths) -> list[str]:
    if not pth.template_changed_path.exists():
        return []
    with pth.template_changed_path.open("rb") as f:
        return pickle.load(f)


def _write_pending_pickle(pth: ProjectPaths, pending: list[str]) -> None:
    pth.template_changed_path.parent.mkdir(parents=True, exist_ok=True)
    with pth.template_changed_path.open("wb") as f:
        pickle.dump(pending, f)


def clear_db_pending_templates(db_session: Session, used: list[str]) -> None:
    """Remove the names the reader used from the DbInfo pending list.

    The reader (generate_inflection_tables) calls this right before its
    commit, so the change lands in the same commit as the regenerated
    words; a rollback keeps the pending list. Names added after the reader
    loaded its copy stay pending.
    """
    db_info_row = (
        db_session.query(DbInfo).filter_by(key="changed_templates_list").first()
    )
    if not db_info_row:
        db_info_row = DbInfo(key="changed_templates_list")
        db_session.add(db_info_row)
        remaining: list[str] = []
    else:
        remaining = [p for p in db_info_row.value_unpack if p not in set(used)]
    db_info_row.value_pack(remaining)


def clear_pickle_pending_templates(pth: ProjectPaths, used: list[str]) -> None:
    """Remove the names the reader used from the pending pickle."""
    remaining = [p for p in _read_pending_pickle(pth) if p not in set(used)]
    _write_pending_pickle(pth, remaining)


def main() -> None:
    pr.tic()
    pr.yellow_title("create inflection templates")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    templates = load_templates(
        pth.inflection_templates_index_path, pth.inflection_templates_dir
    )
    changed = sync_templates(db_session, templates)
    pending = add_pending_templates(db_session, pth, changed)
    db_session.commit()
    db_session.close()

    pr.green(f"{len(changed)} templates changed")
    pr.green(f"{len(pending)} templates pending")
    pr.toc()


if __name__ == "__main__":
    main()
