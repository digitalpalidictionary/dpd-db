# from datetime import date

from rich import print

from helpers import get_paths, ResourcePaths
from helpers import INDECLINEABLES, CONJUGATIONS, DECLENSIONS
from html_components import render_header_tmpl
from html_components import render_dpd_defintion_templ

from db.db_helpers import get_db_session
from db.models import PaliWord
from tools.timeis import tic, toc

tic()
PTH: ResourcePaths = get_paths()
DB_SESSION = get_db_session("dpd.db")
# TODAY = date.today()
ERROR_LOG = open(PTH.error_log_path, "w")


def main():
    print("[bright_yellow]exporting dpd")
    generate_dpd_html()

    ERROR_LOG.close()
    DB_SESSION.close()
    toc()


def generate_dpd_html():
    print("[green]generating dpd html")
    dpd_db = DB_SESSION.query(PaliWord).all()
    dpd_length = len(dpd_db)

    with open(PTH.dpd_css_path) as f:
        dpd_css = f.read()

    with open(PTH.buttons_js_path) as f:
        button_js = f.read()

    for x in enumerate(dpd_db):
        counter: int = x[0]
        i: list = x[1]
        html: str = ""

        if counter % 5000 == 0 or counter % dpd_length == 0:
            print(f"{counter:>9,} / {dpd_length:9<,} {i.pali_1}")

        html += render_header_tmpl(dpd_css, button_js)
        html += "<body>"
        html += render_dpd_defintion_templ(i)
        html += "</body></html>"

        with open(f"xxx delete/exporter_html/{i.pali_1}.html", "w") as f:
            f.write(html)


if __name__ == "__main__":
    main()
