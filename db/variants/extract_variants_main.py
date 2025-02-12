#!/usr/bin/env python3

"""Extract variants readings from all Pāḷi texts."""

from db.variants.extract_variants_from_bjt import process_bjt
from db.variants.extract_variants_from_sc import process_sc
from db.variants.extract_variants_from_sya import process_sya
from db.variants.variants_modules import VariantsDict

from db.variants.extract_variants_from_cst import process_cst
from db.variants.variants_exporter import save_json, export_to_goldendict_mdict

from tools.paths import ProjectPaths
from tools.printer import p_title
from tools .tic_toc import tic, toc

def main():

    tic()
    p_title("variants dict")
    
    variants_dict: VariantsDict = {}  
    pth: ProjectPaths = ProjectPaths()

    variants_dict = process_cst(variants_dict, pth)
    variants_dict = process_sc(variants_dict, pth)
    variants_dict = process_bjt(variants_dict, pth)
    variants_dict = process_sya(variants_dict, pth)

    save_json(variants_dict)
    export_to_goldendict_mdict(variants_dict, pth)

    toc()

if __name__ == "__main__":
    main()

