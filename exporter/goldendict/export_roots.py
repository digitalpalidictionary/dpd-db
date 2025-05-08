"""Compile HTML data for Roots dictionary."""

import re
from typing import Dict, List, Tuple

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import Session

from db.models import DpdRoot, FamilyRoot
from exporter.goldendict.helpers import TODAY
from tools.css_manager import CSSManager
from tools.goldendict_exporter import DictEntry
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces


def generate_root_html(
    db_session: Session,
    pth: ProjectPaths,
    roots_count_dict: Dict[str, int],
) -> Tuple[List[DictEntry], RenderedSizes]:
    """compile html components for each pali root"""

    pr.green("generating roots html")
    size_dict = default_rendered_sizes()
    root_data_list: List[DictEntry] = []

    header_templ = Template(filename=str(pth.root_header_templ_path))

    roots_db = db_session.query(DpdRoot).all()

    for counter, r in enumerate(roots_db):
        # replace \n with html line break
        if r.panini_root:
            r.panini_root = r.panini_root.replace("\n", "<br>")
        if r.panini_sanskrit:
            r.panini_sanskrit = r.panini_sanskrit.replace("\n", "<br>")
        if r.panini_english:
            r.panini_english = r.panini_english.replace("\n", "<br>")

        html = ""
        html += "<body>"

        root_header = render_root_header_templ(
            pth, r=r, date=str(TODAY), header_templ=header_templ
        )

        # Add variables and fonts
        css_manager = CSSManager()
        root_header = css_manager.update_style(root_header, "root")

        definition = render_root_definition_templ(
            pth,
            r,
            roots_count_dict,
        )
        html += definition
        size_dict["root_definition"] += len(definition)

        root_buttons = render_root_buttons_templ(
            pth,
            r,
            db_session,
        )
        html += root_buttons
        size_dict["root_buttons"] += len(root_buttons)

        root_info = render_root_info_templ(
            pth,
            r,
        )
        html += root_info
        size_dict["root_info"] += len(root_info)

        root_matrix = render_root_matrix_templ(
            pth,
            r,
            roots_count_dict,
        )
        html += root_matrix
        size_dict["root_matrix"] += len(root_matrix)

        root_families = render_root_families_templ(
            pth,
            r,
            db_session,
        )
        html += root_families
        size_dict["root_families"] += len(root_families)

        html += "</body></html>"

        html = squash_whitespaces(root_header) + minify(html)

        synonyms: set = set()
        synonyms.add(r.root_clean)
        synonyms.add(re.sub("√", "", r.root))
        synonyms.add(re.sub("√", "", r.root_clean))

        frs = db_session.query(FamilyRoot).filter(FamilyRoot.root_key == r.root).all()

        for fr in frs:
            synonyms.add(fr.root_family)
            synonyms.add(re.sub("√", "", fr.root_family))

        synonyms = set(add_niggahitas(list(synonyms)))
        size_dict["root_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=r.root,
            definition_html=html,
            definition_plain="",
            synonyms=list(synonyms),
        )

        root_data_list.append(res)

    pr.yes(len(root_data_list))
    return root_data_list, size_dict


def render_root_header_templ(
    __pth__: ProjectPaths, r: DpdRoot, date: str, header_templ: Template
) -> str:
    """render the html header with variables"""

    return str(header_templ.render(r=r, date=date))


def render_root_definition_templ(
    pth: ProjectPaths,
    r: DpdRoot,
    roots_count_dict,
):
    """render html of main root info"""

    root_definition_templ = Template(filename=str(pth.root_definition_templ_path))

    try:
        count = roots_count_dict[r.root]
    except KeyError:
        count = 0

    return str(
        root_definition_templ.render(
            r=r,
            count=count,
            today=TODAY,
        )
    )


def render_root_buttons_templ(
    pth: ProjectPaths,
    r: DpdRoot,
    db_session: Session,
):
    """render html of root buttons"""

    root_buttons_templ = Template(filename=str(pth.root_button_templ_path))

    frs = db_session.query(FamilyRoot).filter(FamilyRoot.root_key == r.root)

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(root_buttons_templ.render(r=r, frs=frs))


def render_root_info_templ(pth: ProjectPaths, r: DpdRoot):
    """render html of root grammatical info"""

    root_info_templ = Template(filename=str(pth.root_info_templ_path))
    root_info = ""

    return str(root_info_templ.render(r=r, root_info=root_info, today=TODAY))


def render_root_matrix_templ(
    pth: ProjectPaths,
    r: DpdRoot,
    roots_count_dict,
):
    """render html of root matrix"""

    root_matrix_templ = Template(filename=str(pth.root_matrix_templ_path))
    root_matrix = ""

    try:
        count = roots_count_dict[r.root]
    except KeyError:
        count = 0

    return str(
        root_matrix_templ.render(r=r, count=count, root_matrix=root_matrix, today=TODAY)
    )


def render_root_families_templ(
    pth: ProjectPaths,
    r: DpdRoot,
    db_session: Session,
):
    """render html of root families"""

    root_families_templ = Template(filename=str(pth.root_families_templ_path))

    frs = (
        db_session.query(FamilyRoot)
        .filter(
            FamilyRoot.root_key == r.root,
        )
        .all()
    )

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(root_families_templ.render(r=r, frs=frs, today=TODAY))
