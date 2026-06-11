#!/usr/bin/env python3

"""Export family data to JSON."""

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import FamilyCompound, FamilyIdiom, FamilyRoot, FamilySet, FamilyWord
from tools.paths import ProjectPaths
from tools.printer import printer as pr


@dataclass
class GlobalVars:
    paths: ProjectPaths
    db_session: Session
    fc_db: list[FamilyCompound]
    fi_db: list[FamilyIdiom]
    fr_db: list[FamilyRoot]
    fs_db: list[FamilySet]
    fw_db: list[FamilyWord]


def main() -> None:
    pr.tic()
    pr.yellow_title("exporting families .json")
    paths = ProjectPaths()
    db_session = get_db_session(paths.dpd_db_path)
    g = GlobalVars(
        paths=paths,
        db_session=db_session,
        fc_db=db_session.query(FamilyCompound).all(),
        fi_db=db_session.query(FamilyIdiom).all(),
        fr_db=db_session.query(FamilyRoot).all(),
        fs_db=db_session.query(FamilySet).all(),
        fw_db=db_session.query(FamilyWord).all(),
    )
    export_family_compound(g)
    export_family_idiom(g)
    export_family_root(g)
    export_family_set(g)
    export_family_word(g)
    pr.toc()


def json_dumper(filepath: Path, data: dict[str, object]) -> None:
    js_content = (
        f"""var {filepath.stem} = {json.dumps(data, ensure_ascii=False, indent=1)}"""
    )
    filepath.open("w").write(js_content)


def export_family_compound(g: GlobalVars) -> None:
    pr.green_tmr("exporting family_compound.json")
    fc_dict = {}
    for i in g.fc_db:
        fc_dict[i.compound_family] = {"count": i.count, "data": i.data_unpack}
    json_dumper(g.paths.family_compound_json, fc_dict)
    pr.yes(len(fc_dict))


def export_family_idiom(g: GlobalVars) -> None:
    pr.green_tmr("exporting family_idiom.json")
    fi_dict = {}
    for i in g.fi_db:
        fi_dict[i.idiom] = {"count": i.count, "data": i.data_unpack}
    json_dumper(g.paths.family_idiom_json, fi_dict)
    pr.yes(len(fi_dict))


def export_family_root(g: GlobalVars) -> None:
    pr.green_tmr("exporting family_root.json")
    fr_dict = {}
    for i in g.fr_db:
        fr_dict[i.root_family_key] = {
            "root_key": i.root_key,
            "root_family": i.root_family,
            "root_meaning": i.root_meaning,
            "count": i.count,
            "data": i.data_unpack,
        }

    json_dumper(g.paths.family_root_json, fr_dict)
    pr.yes(len(fr_dict))


def export_family_set(g: GlobalVars) -> None:
    pr.green_tmr("exporting family_set.json")
    fs_dict = {}
    for i in g.fs_db:
        fs_dict[i.set] = {"data": i.data_unpack, "count": i.count}
    json_dumper(g.paths.family_set_json, fs_dict)
    pr.yes(len(fs_dict))


def export_family_word(g: GlobalVars) -> None:
    pr.green_tmr("exporting family_word.json")
    fw_dict = {}
    for i in g.fw_db:
        fw_dict[i.word_family] = {"data": i.data_unpack, "count": i.count}
    json_dumper(g.paths.family_word_json, fw_dict)
    pr.yes(len(fw_dict))


if __name__ == "__main__":
    main()
