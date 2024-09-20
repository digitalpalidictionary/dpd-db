"""Flask app for browser-based DPD lookup."""

from curses.ascii import isalpha
from flask import Flask, render_template
from markupsafe import Markup
from flask import request
from flask_sqlalchemy import SQLAlchemy
from db.db_helpers import get_db_session
from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyRoot,
    Lookup,
    SBS,
    Russian)
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

from rich import print

from modules import HeadwordData
from modules import RootsData
from modules import DeconstructorData
from modules import VariantData
from modules import SpellingData
from modules import GrammarData
from modules import HelpData
from modules import AbbreviationsData

from exporter.goldendict.helpers import make_roots_count_dict

from tools.exporter_functions import get_family_compounds
from tools.exporter_functions import get_family_idioms
from tools.exporter_functions import get_family_set


pth = ProjectPaths()
app = Flask(__name__)



app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{pth.dpd_db_path}"
db = SQLAlchemy(app)

db_session = get_db_session(pth.dpd_db_path)
roots_count_dict = make_roots_count_dict(db_session)

with open(pth.buttons_js_path) as f:
    js = f.read()

@app.route("/", methods=['GET'])
def home():
    query = request.args.get('query', '')
    query = clean_query(query)
    print(query)
    result = []
    html = ""
    
    if query:
        if query.isalpha():
            result = db.session.query(Lookup)\
                .filter(Lookup.lookup_key==(query))\
                .first()
            
            if not result:
                query = query.lower()
                result = db.session.query(Lookup)\
                    .filter(Lookup.lookup_key==(query))\
                    .first()
            
            if result:
                # headwords
                if result.headwords:
                    headwords = result.headwords_unpack
                    results = db.session\
                        .query(DpdHeadword)\
                        .filter(DpdHeadword.id.in_(headwords))\
                        .all()
                    for i in results:
                        fc = get_family_compounds(i)
                        fi = get_family_idioms(i)
                        fs = get_family_set(i)
                        sbs = db.session.query(SBS).filter_by(id=i.id).first()
                        ru = db.session.query(Russian).filter_by(id=i.id).first()
                        d = HeadwordData(i, fc, fi, fs, sbs, ru)
                        html += render_template("dpd_headword.html", d=d)
                
                # roots
                if result.roots:
                    roots_list = result.roots_unpack
                    root_results = db.session\
                        .query(DpdRoot)\
                        .filter(DpdRoot.root.in_(roots_list))\
                        .all()
                    for r in root_results:
                        frs = db.session \
                            .query(FamilyRoot) \
                            .filter(FamilyRoot.root_key == r.root)
                        frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
                        d = RootsData(r, frs, roots_count_dict)
                        html += render_template("root.html", d=d)

                # deconstructor
                if result.deconstructor:
                    d = DeconstructorData(result)
                    html += render_template("deconstructor.html", d=d)

                # variant
                if result.variant:
                    d = VariantData(result)
                    html += render_template("variant.html", d=d)

                # spelling mistake
                if result.spelling:
                    d = SpellingData(result)
                    html += render_template("spelling.html", d=d)

                if result.grammar:
                    d = GrammarData(result)
                    html += render_template("grammar.html", d=d)
                
                if result.help:
                    d = HelpData(result)
                    html += render_template("help.html", d=d)

                if result.abbrev:
                    d = AbbreviationsData(result)
                    html += render_template("abbreviations.html", d=d)

                return render_template("home.html", html=html)
        
        else:
            query = int(query)
            headword = db.session\
                .query(DpdHeadword)\
                .filter(DpdHeadword.id == query)\
                .first()
            if headword:
                print(headword)
                fc = get_family_compounds(headword)
                fi = get_family_idioms(headword)
                fs = get_family_set(headword)
                sbs = db.session.query(SBS).filter_by(id=query).first()
                ru = db.session.query(Russian).filter_by(id=query).first()
                d = HeadwordData(   headword, fc, fi, fs, sbs, ru)
                html += render_template("dpd_headword.html", d=d)

                return render_template("home.html", html=html)
    
    return render_template("home.html", html="")


def clean_query(query):
    return query.replace("'", "")


def run_app():
    app.run(debug=True, port=8888)


@app.template_filter('safe_getattr')
def safe_getattr(obj, attr, default=None):
    """A safe version of getattr for Jinja templates that marks strings as safe."""
    value = getattr(obj, attr, default)
    if isinstance(value, str):
        # Automatically mark the string as safe if it contains HTML
        return Markup(value)
    return value

run_app()
