import uvicorn
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader

from modules import HeadwordData
from db.db_helpers import get_db_session
from db.models import (
    DpdHeadword,
    Lookup,
    DpdRoot,
    SBS,
    Russian)
from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set,)
from tools.paths import ProjectPaths



app = FastAPI()

# Jinja boilerplate
template_dir = "exporter/web_app/templates"
env = Environment(loader=FileSystemLoader(template_dir))

@app.get("/")
def home():
    return "hi"

@app.get("/db_search")
def search(search_query: str|int, regex_search: bool=False):
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    html = ""
    
    if search_query.isnumeric():
        headword = db_session\
            .query(DpdHeadword)\
            .filter(DpdHeadword.id == search_query)\
            .first()
        if headword:
            print(headword)
            fc = get_family_compounds(headword)
            fi = get_family_idioms(headword)
            fs = get_family_set(headword)
            sbs = db_session.query(SBS).filter_by(id=search_query).first()
            ru = db_session.query(Russian).filter_by(id=search_query).first()
            d = HeadwordData(headword, fc, fi, fs, sbs, ru)
            template = env.get_template("dpd_headword.html")
            html += template.render(d)
            return html


if __name__ == "__main__":
    uvicorn.run("api_version:app", host="127.0.0.1", port=4164, reload=True)

