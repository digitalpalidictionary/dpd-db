"""Compile HTML data for English to Pāḷi dictionary."""

from minify_html import minify
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.models import Lookup
from tools.goldendict_exporter import DictEntry
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes import EpdData


def generate_epd_html(
    db_session: Session,
    pth: ProjectPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for english to pali dictionary using lookup table data"""

    size_dict = default_rendered_sizes()

    pr.green("generating epd html from lookup")

    jinja_env = get_jinja2_env("exporter/goldendict/templates")
    template = jinja_env.get_template("epd.jinja")

    lookup_db = db_session.query(Lookup).filter(Lookup.epd != "").all()

    epd_data_list: List[DictEntry] = []

    for lookup_entry in lookup_db:
        # Use ViewModel
        data = EpdData(lookup_entry, pth, jinja_env)

        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["epd"] += len(final_html)
        size_dict["epd_header"] += len(squash_whitespaces(header))

        res = DictEntry(
            word=lookup_entry.lookup_key,
            definition_html=final_html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)

    pr.yes(len(epd_data_list))

    return epd_data_list, size_dict
