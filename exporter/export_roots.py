"""Compile HTML data for Roots dictionary."""

import re

from css_html_js_minify import css_minify, js_minify
from mako.template import Template
from minify_html import minify
from rich import print
from typing import Dict, Tuple, List

from sqlalchemy.orm import Session

from export_dpd import render_header_templ

from helpers import TODAY
from db.models import DpdRoots, FamilyRoot
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import bip, bop
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes
from typing import Optional


def generate_root_html(
                db_session: Session,
                pth: ProjectPaths,
                roots_count_dict: Dict[str, int],
                dps_data=False,
                dpspth: Optional[DPSPaths] = None
                ) -> Tuple[List[RenderResult], RenderedSizes]:
    """compile html componenents for each pali root"""

    print("[green]generating roots html")

    size_dict = default_rendered_sizes()

    root_data_list: List[RenderResult] = []

    with open(pth.roots_css_path) as f:
        roots_css = f.read()
    roots_css = css_minify(roots_css)

    with open(pth.buttons_js_path) as f:
        buttons_js = f.read()
    buttons_js = js_minify(buttons_js)

    header_templ = Template(filename=str(pth.header_templ_path))

    header = render_header_templ(
        pth, css=roots_css, js=buttons_js, header_templ=header_templ)

    roots_db = db_session.query(DpdRoots).all()
    root_db_length = len(roots_db)

    bip()

    for counter, r in enumerate(roots_db):

        # replace \n with html line break
        if r.panini_root:
            r.panini_root = r.panini_root.replace("\n", "<br>")
        if r.panini_sanskrit:
            r.panini_sanskrit = r.panini_sanskrit.replace("\n", "<br>")
        if r.panini_english:
            r.panini_english = r.panini_english.replace("\n", "<br>")

        html = header
        html += "<body>"

        if not dpspth:
            definition = render_root_definition_templ(pth, r, roots_count_dict, dps_data)
        elif dpspth:
            definition = render_root_definition_templ(dpspth, r, roots_count_dict, dps_data)
        # add here another language elif ...

        html += definition
        size_dict["root_definition"] += len(definition)

        if not dpspth:
            root_buttons = render_root_buttons_templ(pth, r, db_session)
        elif dpspth:
            root_buttons = render_root_buttons_templ(dpspth, r, db_session)
        # add here another language elif ...

        html += root_buttons
        size_dict["root_buttons"] += len(root_buttons)

        if not dpspth:
            root_info = render_root_info_templ(pth, r)
            html += root_info
        elif dpspth:
            root_info = render_root_info_templ(dpspth, r)
        # add here another language elif ...

        html += root_info
        size_dict["root_info"] += len(root_info)

        if not dpspth:
            root_matrix = render_root_matrix_templ(pth, r, roots_count_dict)
        elif dpspth:
            root_matrix = render_root_matrix_templ(dpspth, r, roots_count_dict)
        html += root_matrix
        size_dict["root_matrix"] += len(root_matrix)

        if not dpspth:
            root_families = render_root_families_templ(pth, r, db_session)
        elif dpspth:
            root_families = render_root_families_templ(dpspth, r, db_session)
        # add here another language elif ...

        html += root_families
        size_dict["root_families"] += len(root_families)

        html += "</body></html>"

        html = minify(html)

        synonyms: set = set()
        synonyms.add(r.root_clean)
        synonyms.add(re.sub("√", "", r.root))
        synonyms.add(re.sub("√", "", r.root_clean))

        frs = db_session.query(FamilyRoot)\
            .filter(FamilyRoot.root_key == r.root).all()

        for fr in frs:
            synonyms.add(fr.root_family)
            synonyms.add(re.sub("√", "", fr.root_family))

        synonyms = set(add_niggahitas(list(synonyms)))
        size_dict["root_synonyms"] += len(str(synonyms))

        res = RenderResult(
            word = r.root,
            definition_html = html,
            definition_plain = "",
            synonyms = list(synonyms),
        )

        root_data_list.append(res)

        if counter % 100 == 0:
            print(
                f"{counter:>10,} / {root_db_length:<10,}{r.root:<20} {bop():>10}")
            bip()

    return root_data_list, size_dict


def render_root_definition_templ(
                        _pth_,
                        r: DpdRoots, 
                        roots_count_dict, 
                        dps_data
                        ):
    """render html of main root info"""


    root_definition_templ = Template(filename=str(_pth_.root_definition_templ_path))

    count = roots_count_dict[r.root]

    return str(
        root_definition_templ.render(
            r=r,
            count=count,
            today=TODAY,
            dps_data=dps_data))


def render_root_buttons_templ(_pth_, r: DpdRoots, db_session: Session):
    """render html of root buttons"""
    
    root_buttons_templ = Template(filename=str(_pth_.root_button_templ_path))

    frs = db_session.query(
        FamilyRoot
        ).filter(
            FamilyRoot.root_key == r.root)

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(
        root_buttons_templ.render(
            r=r,
            frs=frs))


def render_root_info_templ(_pth_, r: DpdRoots):
    """render html of root grammatical info"""

    root_info_templ = Template(filename=str(_pth_.root_info_templ_path))

    return str(
        root_info_templ.render(
            r=r,
            today=TODAY))


def render_root_matrix_templ(_pth_, r: DpdRoots, roots_count_dict):
    """render html of root matrix"""

    root_matrix_templ = Template(filename=str(_pth_.root_matrix_templ_path))

    count = roots_count_dict[r.root]

    return str(
        root_matrix_templ.render(
            r=r,
            count=count,
            today=TODAY))


def render_root_families_templ(_pth_, r: DpdRoots, db_session: Session):
    """render html of root families"""

    root_families_templ = Template(filename=str(_pth_.root_families_templ_path))

    frs = db_session.query(
        FamilyRoot
        ).filter(
            FamilyRoot.root_key == r.root,
        ).all()

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(
        root_families_templ.render(
            r=r,
            frs=frs,
            today=TODAY))
