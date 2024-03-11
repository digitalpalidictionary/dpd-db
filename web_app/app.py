"""Flask app for browswer-based DPD lookup."""

from flask import Flask, render_template
from markupsafe import Markup
from flask import request
from flask_sqlalchemy import SQLAlchemy
from db.models import DpdHeadwords, Lookup, SBS, Russian
from tools.paths import ProjectPaths

from rich import print


from tools.configger import config_test
from tools.exporter_functions import get_family_compounds
from tools.exporter_functions import get_family_set
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import make_grammar_line
from tools.meaning_construction import degree_of_completion
from tools.date_and_time import year_month_day_dash



class HeadwordData():
    def __init__(self, js, i, fc, fs, sbs, ru):
        # self.css = css
        self.js = js
        self.meaning = make_meaning_html(i)
        self.summary = summarize_construction(i)
        self.complete = degree_of_completion(i)
        self.grammar = make_grammar_line(i)
        self.i = self.convert_newlines(i)
        self.fc = fc
        self.fs = fs
        self.app_name = "Jinja"
        self.date = year_month_day_dash()
        self.sbs = self.convert_newlines(sbs)
        self.ru = self.convert_newlines(ru)
        if config_test("dictionary", "make_link", "yes"):
            self.make_link = True
        else:
            self.make_link = False
        if config_test("dictionary", "show_dps_data", "yes"):
            self.dps_data = True
        else:
            self.dps_data = False

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
        

pth = ProjectPaths()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{pth.dpd_db_path}"
db = SQLAlchemy(app)

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
        result = db.session.query(Lookup)\
            .filter(Lookup.lookup_key==(query))\
            .first()
        if result:
            headwords = result.headwords_unpack
            results = db.session\
                .query(DpdHeadwords)\
                .filter(DpdHeadwords.id.in_(headwords))\
                .all()
            for i in results:
                fc = get_family_compounds(i)
                fs = get_family_set(i)
                sbs = db.session.query(SBS).filter_by(id=i.id).first()
                ru = db.session.query(Russian).filter_by(id=i.id).first()
                d = HeadwordData(js, i, fc, fs, sbs, ru)
                html += render_template("complete_word.html", d=d)
            return render_template("home.html", html=html)

    return render_template("home.html", html="")


def clean_query(query):
    return query.replace("'", "").lower()

def run_app():
    app.run(debug=True, port=8000)

@app.template_filter('safe_getattr')
def safe_getattr(obj, attr, default=None):
    """A safe version of getattr for Jinja templates that marks strings as safe."""
    value = getattr(obj, attr, default)
    if isinstance(value, str):
        # Automatically mark the string as safe if it contains HTML
        return Markup(value)
    return value


run_app()
