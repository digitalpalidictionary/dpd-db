#!/usr/bin/env python3

"""Extract variants readings from all Pāḷi texts."""

from db.variants.extract_variants_from_bjt import process_bjt
from db.variants.extract_variants_from_cst import process_cst
from db.variants.extract_variants_from_sc import process_sc
from db.variants.extract_variants_from_sya import process_sya
from db.variants.add_to_db import AddVariantsToDb
from db.variants.variants_modules import VariantsDict, save_json
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("variants dict")

    if config_test("exporter", "make_variants", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    variants_dict: VariantsDict = {}
    pth: ProjectPaths = ProjectPaths()

    variants_dict = process_cst(variants_dict, pth)
    variants_dict = process_bjt(variants_dict, pth)
    variants_dict = process_sya(variants_dict, pth)
    variants_dict = process_sc(variants_dict, pth)

    save_json(variants_dict)

    AddVariantsToDb(variants_dict)

    pr.toc()


if __name__ == "__main__":
    main()
