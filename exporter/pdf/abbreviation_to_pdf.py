#!/usr/bin/env python3

"""Export abbreviations to PDF using Typst and Jinja templates."""

# import re
# import subprocess
import typst

# from jinja2 import Environment, FileSystemLoader

# from db.db_helpers import get_db_session
# from db.models import DpdHeadword, FamilyCompound, FamilyIdiom, FamilyRoot, FamilyWord, Lookup
# from tools.configger import config_test
# from tools.date_and_time import year_month_day_dash
# from tools.pali_sort_key import pali_sort_key
# from tools.paths import ProjectPaths
from tools.printer import printer as pr
# from tools.tsv_read_write import read_tsv_dot_dict
# from tools.zip_up import zip_up_file

from exporter.pdf.pdf_exporter import GlobalVars
from exporter.pdf.pdf_exporter import make_abbreviations, make_layout
from exporter.pdf.pdf_exporter import clean_up_typst_data
from exporter.pdf.pdf_exporter import save_typist_file


def export_to_pdf(g: GlobalVars):
    pr.green("rendering abbreviations pdf")

    try:
        typst.compile(
            str(g.pth.typst_lite_data_path),
            output=str(g.pth.typst_lite_abbreviations_path),
        )

        pr.yes("ok")
    except Exception as e:
        pr.red(f"\n{e}")


def main():
    pr.tic()
    pr.title("export abbreviations to pdf with typst")

    g = GlobalVars()
    make_layout(g)
    make_abbreviations(g)
    clean_up_typst_data(g)
    save_typist_file(g)
    export_to_pdf(g)
    pr.toc()


if __name__ == "__main__":
    main()
