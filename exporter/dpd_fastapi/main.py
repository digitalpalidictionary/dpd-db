
import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .modules import (
    HeadwordData,
    RootsData,
    DeconstructorData,
    VariantData,
    SpellingData,
    GrammarData,
    HelpData,
    AbbreviationsData)

from db.get_db_session import get_db_session
from db.models import (
    DpdHeadwords,
    DpdRoots,
    Lookup,
    FamilyRoot
    )

from exporter.goldendict.helpers import make_roots_count_dict

from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set)
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

app = FastAPI()
app.mount("/static", StaticFiles(directory="exporter/dpd_fastapi/static"), name="static")
pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
roots_count_dict = make_roots_count_dict(db_session)
templates = Jinja2Templates(directory="exporter/dpd_fastapi/templates")
history_list: list[str] = []


@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse(
        "home.html", {
        "request": request,
        "history": history_list,
        "dpd_results": ""})



# @app.get("/search", response_class=HTMLResponse)
@app.get("/search")
def db_search(request: Request, search: str):

    html = ""
    search = search.replace("'", "")
    global history_list

    if search:
        if not search.isnumeric():
            history_list = update_history(str(search))

            lookup_results = db_session.query(Lookup) \
                .filter(Lookup.lookup_key==(search)) \
                .first()
            
            if not lookup_results:
                search = search.lower()
                lookup_results = db_session.query(Lookup) \
                    .filter(Lookup.lookup_key==(search)) \
                    .first()
            
            if lookup_results:
                # headwords
                if lookup_results.headwords:
                    headwords = lookup_results.headwords_unpack
                    headword_results = db_session\
                        .query(DpdHeadwords)\
                        .filter(DpdHeadwords.id.in_(headwords))\
                        .all()
                    for i in headword_results:
                        fc = get_family_compounds(i)
                        fi = get_family_idioms(i)
                        fs = get_family_set(i)
                        d = HeadwordData(i, fc, fi, fs)
                        html += templates.get_template(
                            "dpd_headword.html").render(d=d)
                
                # roots
                if lookup_results.roots:
                    roots_list = lookup_results.roots_unpack
                    root_results = db_session \
                        .query(DpdRoots) \
                        .filter(DpdRoots.root.in_(roots_list))\
                        .all()
                    for r in root_results:
                        frs = db_session \
                            .query(FamilyRoot) \
                            .filter(FamilyRoot.root_key == r.root)
                        frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))
                        d = RootsData(r, frs, roots_count_dict)
                        html += templates.get_template(
                            "root.html").render(d=d)

                # deconstructor
                if lookup_results.deconstructor:
                    d = DeconstructorData(lookup_results)
                    html += templates.get_template(
                            "deconstructor.html").render(d=d)

                # variant
                if lookup_results.variant:
                    d = VariantData(lookup_results)
                    html += templates.get_template(
                            "variant.html").render(d=d)

                # spelling mistake
                if lookup_results.spelling:
                    d = SpellingData(lookup_results)
                    html += templates.get_template(
                            "spelling.html").render(d=d)

                if lookup_results.grammar:
                    d = GrammarData(lookup_results)
                    html += templates.get_template(
                            "grammar.html").render(d=d)
                                    
                if lookup_results.help:
                    d = HelpData(lookup_results)
                    html += templates.get_template(
                            "help.html").render(d=d)

                if lookup_results.abbrev:
                    d = AbbreviationsData(lookup_results)
                    html += templates.get_template(
                            "abbreviations.html").render(d=d)
        
        else:
            search_int = int(search)
            headword_results = db_session\
                .query(DpdHeadwords)\
                .filter(DpdHeadwords.id == search_int)\
                .first()
            if headword_results:
                history_list = update_history(headword_results.lemma_1)
                fc = get_family_compounds(headword_results)
                fi = get_family_idioms(headword_results)
                fs = get_family_set(headword_results)
                d = HeadwordData(headword_results, fc, fi, fs)
                html += templates.get_template(
                    "dpd_headword.html").render(d=d)
    
    if not html:
        html = "no results found"
            
    return templates.TemplateResponse(
    "home.html", {
    "request": request,
    "search": search,
    "history": history_list,
    "dpd_results": html})
        


def update_history(search: str) -> list[str]:
    global history_list
    if search in history_list:
        history_list.remove(search)
    history_list.insert(0, search)
    return history_list[:30]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.1.1.1",
        port=8080,
        reload=True)

