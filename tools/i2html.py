#!/usr/bin/env python3

"""Lookup an inflection and render html."""

import webbrowser
import os
import tempfile

from jinja2 import Environment, FileSystemLoader
from rich import print

from typing import List

from db.get_db_session import get_db_session
from db.models import PaliWord, InflectionToHeadwords
from exporter.export_dpd import render_header_templ

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import degree_of_completion
from tools.date_and_time import year_month_day


class WordData():
    def __init__(self, css, js, i):
        self.css = css
        self.js = js
        self.meaning = make_meaning_html(i)
        self.summary = summarize_construction(i)
        self.complete = degree_of_completion(i)
        self.i = self.convert_newlines(i)
        self.date = year_month_day()
        if config_test("dictionary", "make_link", "yes"):
            self.make_link = True
        else:
            self.make_link = False

    @staticmethod
    def convert_newlines(obj):
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):  # skip private and protected attributes
                attr_value = getattr(obj, attr_name)
                if isinstance(attr_value, str):
                    try:
                        setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                    except AttributeError:
                        continue  # skip attributes that don't have a setter
        return obj

def i2html(the_word):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    headwords: List[str] = lookup_inflection(the_word, db_session)

    if headwords:
        env = Environment(loader=FileSystemLoader(pth.jinja_templates_dir))
        word_template = env.get_template("complete_word.html")
        header_templ = env.get_template("header.html")

        # header
        with open(pth.dpd_css_path) as f:
            css = f.read()
        with open(pth.buttons_js_path) as f:
            js = f.read()

        html = header_templ.render(css=css, js=js)

        # iterate over headwords
        results = db_session.query(PaliWord)\
            .filter(PaliWord.pali_1.in_(headwords)).all()

        for i in results:
            d = WordData(css, js, i)
            html += word_template.render(d=d)
    else:
        html = "sorry, nothing found"
    
    open_html_in_browser(pth, html)


def lookup_inflection(the_word: str, db_session) -> List[str]:
    """Lookup and an inflection and get all relevant headwords."""

    inflection = db_session.query(InflectionToHeadwords)\
        .filter(InflectionToHeadwords.inflection==the_word).first()
    if inflection:
        return inflection.headwords_list
    else:
        return []


def open_html_in_browser(pth, html_content):
    path = f"{pth.temp_html_file_path}"
    try:
        with open(path, 'w') as tmp:
            tmp.write(html_content)
        webbrowser.open_new_tab("file://" + path)
    except Exception as e:
        print(f"An error occurred while opening the HTML in the browser: {e}")


if __name__ == "__main__":
    the_word = "sutta"
    i2html(the_word)
