#!/usr/bin/env python3

"""Export family data to JSON."""

import json
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import FamilyCompound, FamilyIdiom, FamilyRoot, FamilySet, FamilyWord
from tools.paths import ProjectPaths
from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from tools.printer import p_green, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.configger import config_test

class ProgData():
    pth = ProjectPaths()
    rupth = RuPaths()
    db_session = get_db_session(pth.dpd_db_path)
    fc_db = db_session.query(FamilyCompound).all()
    fi_db = db_session.query(FamilyIdiom).all()
    fr_db = db_session.query(FamilyRoot).all()
    fs_db = db_session.query(FamilySet).all()
    fw_db = db_session.query(FamilyWord).all()

    # language
    if config_test("exporter", "language", "en"):
        lang = "en"
    elif config_test("exporter", "language", "ru"):
        lang = "ru"
    # add another lang here "elif ..." and 
    # add conditions if lang = "{your_language}" in every instance in the code.
    else:
        raise ValueError("Invalid language parameter")
    
    # paths
    if lang == "en":
        paths = pth
    elif lang == "ru":
        paths = rupth


def main():
    tic()
    p_title("exporting families .json")
    g = ProgData()
    export_family_compound(g)
    export_family_idiom(g)
    export_family_root(g)
    export_family_set(g)
    export_family_word(g)
    toc()


def json_dumper(filepath: Path, dict: dict[str, str]):
    js_content = f"""var {filepath.stem} = {json.dumps(dict, ensure_ascii=False, indent=1)}"""

    with open(filepath, "w") as f:
        f.write(js_content)    

def export_family_compound(g: ProgData):
    p_green("exporting family_compound.json")
    fc_dict = {}
    for i in g.fc_db:
        if g.lang == "en":
            fc_dict[i.compound_family] = {
                "count": i.count,
                "data": i.data_unpack}
        elif g.lang == "ru":
            fc_dict[i.compound_family] = {
                "count": i.count,
                "data": i.data_ru_unpack}
    json_dumper(g.paths.family_compound_json, fc_dict)
    p_yes(len(fc_dict))


def export_family_idiom(g: ProgData):
    p_green("exporting family_idiom.json")
    fi_dict = {}
    for i in g.fi_db:
        if g.lang == "en":
            fi_dict[i.idiom] = {
                "count": i.count,
                "data": i.data_unpack}
        elif g.lang == "ru":
            fi_dict[i.idiom] = {
                "count": i.count,
                "data": i.data_ru_unpack}
    json_dumper(g.paths.family_idiom_json, fi_dict)
    p_yes(len(fi_dict))


def export_family_root(g: ProgData):
    p_green("exporting family_root.json")
    fr_dict = {}
    for i in g.fr_db:
        if g.lang == "en":
            fr_dict[i.root_family_key] = {
                "root_key": i.root_key,
                "root_family": i.root_family,
                "root_meaning": i.root_meaning,
                "count": i.count,
                "data": i.data_unpack}
        elif g.lang == "ru":
            fr_dict[i.root_family_key] = {
                "root_key": i.root_key,
                "root_family": i.root_family,
                "root_meaning": i.root_ru_meaning,
                "count": i.count,
                "data": i.data_ru_unpack}
    json_dumper(g.paths.family_root_json, fr_dict)
    p_yes(len(fr_dict))


def export_family_set(g: ProgData):
    p_green("exporting family_set.json")
    fs_dict = {}
    for i in g.fs_db:
        if g.lang == "en":
            fs_dict[i.set] = {
                "data": i.data_unpack,
                "count": i.count}
        elif g.lang == "ru":
            fs_dict[i.set] = {
                "data": i.data_ru_unpack,
                "count": i.count}
    json_dumper(g.paths.family_set_json, fs_dict)
    p_yes(len(fs_dict))


def export_family_word(g: ProgData):
    p_green("exporting family_word.json")
    fw_dict = {}
    for i in g.fw_db:
        if g.lang == "en":
            fw_dict[i.word_family] = {
                "data": i.data_unpack,
                "count": i.count}
        elif g.lang == "ru":
            fw_dict[i.word_family] = {
                "data": i.data_ru_unpack,
                "count": i.count}
    json_dumper(g.paths.family_word_json, fw_dict)
    p_yes(len(fw_dict))


if __name__ == "__main__":
    main()
