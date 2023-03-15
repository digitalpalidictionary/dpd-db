import re

from rich import print
from sqlalchemy import and_
from minify_html import minify

from tools.add_niggahitas import add_niggahitas
from html_components import render_header_tmpl
from html_components import render_root_definition_templ
from html_components import render_root_buttons_templ
from html_components import render_root_info_templ
from html_components import render_root_matrix_templ
from html_components import render_root_families_templ
from db.models import PaliRoot, FamilyRoot
from tools.timeis import bip, bop
from tools.pali_sort_key import pali_sort_key


def generate_root_html(DB_SESSION, PTH):
    """compile html componenents for each pali root"""

    print("[green]generating roots html")

    root_data_list = []

    with open(PTH.roots_css_path) as f:
        roots_css = f.read()
    with open(PTH.buttons_js_path) as f:
        buttons_js = f.read()
    header = render_header_tmpl(css=roots_css, js=buttons_js)

    roots_db = DB_SESSION.query(
        PaliRoot, FamilyRoot
    ).outerjoin(
        FamilyRoot,
        and_(
            FamilyRoot.root_id == PaliRoot.root,
            FamilyRoot.root_family == "info"
        )
    ).all()
    root_db_length = len(roots_db)

    bip()
    for counter, (r, info) in enumerate(roots_db):
        
        # replace \n with html line break
        r.panini_root = r.panini_root.replace("\n", "<br>")
        r.panini_sanskrit = r.panini_sanskrit.replace("\n", "<br>")
        r.panini_english = r.panini_english.replace("\n", "<br>")

        html = header
        html += "<body>"
        html += render_root_definition_templ(r, info)
        html += render_root_buttons_templ(r, DB_SESSION)
        html += render_root_info_templ(r, info)
        html += render_root_matrix_templ(r, DB_SESSION)
        html += render_root_families_templ(r, DB_SESSION)
        html += "</body></html>"

        # html = minify(
        #     html,
        #     minify_js=True,
        #     minify_css=True,
        #     keep_closing_tags=True,
        #     remove_processing_instructions=True
        # )

        synonyms: set = set()
        synonyms.add(r.root_clean)
        synonyms.add(re.sub("√", "", r.root))
        synonyms.add(re.sub("√", "", r.root_clean))

        # !!! need list of subfamilies easily accessable as a list

        frs = DB_SESSION.query(
            FamilyRoot
        ).filter(
            FamilyRoot.root_id == r.root,
            FamilyRoot.root_family != "info",
            FamilyRoot.root_family != "matrix",
        ).all()

        for fr in frs:
            synonyms.add(fr.root_family)
            synonyms.add(re.sub("√", "", fr.root_family))

        synonyms = add_niggahitas(list(synonyms))

        root_data_list += [{
            "word": r.root,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms
        }]

        if counter % 100 == 0:
            with open(f"xxx delete/exporter_roots/{r.root}.html", "w") as f:
                f.write(html)
            print(f"{counter:>10,} / {root_db_length:<10,} {r.root:<20} {bop():>10}")
            bip()

    return root_data_list
