#!/usr/bin/env python3

"""Lookup an inflection and render html."""

import webbrowser
import os
import tempfile

from mako.template import Template
from rich import print

from typing import List

from db.get_db_session import get_db_session
from db.models import PaliWord, InflectionToHeadwords
from exporter.export_dpd import render_header_templ

from tools.paths import ProjectPaths
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import degree_of_completion
pth = ProjectPaths()


def i2html(the_word):

    db_session = get_db_session(pth.dpd_db_path)
    headwords: List[str] = lookup_inflection(the_word, db_session)

    if headwords:
        word_template = Template(filename=str(pth.complete_word_templ_path))
        
        # header
        with open(pth.dpd_css_path) as f:
            css = f.read()
        with open(pth.buttons_js_path) as f:
            js = f.read()

        header_templ = Template(filename=str(pth.header_templ_path))
        html = render_header_templ(
            pth, css=css, js=js, header_templ=header_templ)

        # iterate over headwords
        results = db_session.query(PaliWord)\
            .filter(PaliWord.pali_1.in_(headwords)).all()

        for i in results:
            meaning = make_meaning_html(i)
            summary = summarize_construction(i)
            complete = degree_of_completion(i)

            html += render_word_template(
                word_template,
                css,
                js,
                i,
                meaning,
                summary,
                complete)
    else:
        html = "sorry, nothing found"
    
    open_html_in_browser(html)


def render_word_template(
        word_template,
        css,
        js,
        i,
        meaning,
        summary,
        complete
):
    return str(
        word_template.render(
            css=css,
            js=js,
            i=i,
            meaning=meaning,
            summary=summary,
            complete=complete))
    

def lookup_inflection(the_word: str, db_session) -> List[str]:
    """Lookup and an inflection and get all relevant headwords."""

    inflection = db_session.query(InflectionToHeadwords)\
        .filter(InflectionToHeadwords.inflection==the_word).first()
    if inflection:
        return inflection.headwords_list
    else:
        return []


def open_html_in_browser(html_content):
    fd, path = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(html_content)
        webbrowser.open_new_tab("file://" + path)
    finally:
        os.remove(path)


if __name__ == "__main__":
    the_word = "assaṃ"
    i2html(the_word)
