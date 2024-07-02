import re
import uvicorn
import difflib
from unidecode import unidecode

from collections import defaultdict
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from exporter.dpd_fastapi.modules import AbbreviationsData
from exporter.dpd_fastapi.modules import DeconstructorData
from exporter.dpd_fastapi.modules import EpdData
from exporter.dpd_fastapi.modules import GrammarData
from exporter.dpd_fastapi.modules import HeadwordData
from exporter.dpd_fastapi.modules import HelpData
from exporter.dpd_fastapi.modules import RootsData
from exporter.dpd_fastapi.modules import SpellingData
from exporter.dpd_fastapi.modules import VariantData

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from db.models import DpdRoots
from db.models import FamilyRoot
from db.models import Lookup

from exporter.goldendict.helpers import make_roots_count_dict

from tools.exporter_functions import get_family_compounds
from tools.exporter_functions import get_family_idioms
from tools.exporter_functions import get_family_set
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths


def make_headwords_clean_set(db_session: Session) -> set[str]:
    """Make a set of Pāḷi headwords and English meanings."""
    
    # add headwords
    results = db_session.query(DpdHeadwords).all()
    headwords_clean_set = set([i.lemma_clean for i in results])

    # add all english meanings
    results = db_session \
        .query(Lookup) \
        .filter(Lookup.epd != "") \
        .all()
    headwords_clean_set.update([i.lookup_key for i in results])
    return headwords_clean_set


def make_ascii_to_unicode_dict(db_session: Session) -> dict[str, list[str]]:
    """Key is ASCII value of all headwords, value is Unicode."""

    results = db_session.query(DpdHeadwords).all()
    headwords_clean_set: set[str] = set()
    for i in results:
        headwords_clean_set.add(i.lemma_clean)
        headwords_clean_set.add(i.lemma_2)
    headwords_sorted_list = pali_list_sorter(headwords_clean_set)

    ascii_to_unicode_dict = defaultdict(list)
    for headword in headwords_sorted_list:
        headword_ascii = unidecode(headword)
        if (
            headword_ascii != headword
            and headword not in ascii_to_unicode_dict[headword_ascii]
        ):
            ascii_to_unicode_dict[headword_ascii].append(headword)

    return ascii_to_unicode_dict


app = FastAPI()
app.mount("/static", StaticFiles(directory="exporter/dpd_fastapi/static"), name="static")
pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
roots_count_dict = make_roots_count_dict(db_session)
headwords_clean_set = make_headwords_clean_set(db_session)
ascii_to_unicode_dict = make_ascii_to_unicode_dict(db_session)
db_session.close()
templates = Jinja2Templates(directory="exporter/dpd_fastapi/templates")

with open("exporter/dpd_fastapi/static/dpd.css") as f:
    dpd_css = f.read()

with open("exporter/dpd_fastapi/static/dpd.js") as f:
    dpd_js = f.read()

with open("exporter/dpd_fastapi/static/home_simple.css") as f:
    home_simple_css = f.read()


@app.get("/")
def home_page(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse(
        "home.html", {
        "request": request,
        "dpd_results": ""})


@app.get("/search_html", response_class=HTMLResponse)
def db_search_html(request: Request, search: str):

    dpd_html, summary_html = make_dpd_html(search)

    return templates.TemplateResponse(
        "home.html", {
        "request": request,
        "search": search,
        "dpd_results": dpd_html,
        })


@app.get("/search_json", response_class=JSONResponse)
def db_search_json(request: Request, search: str):

    dpd_html, summary_html = make_dpd_html(search)
    response_data = {
        "summary_html": summary_html,
        "dpd_html": dpd_html}

    return JSONResponse(content=response_data)


@app.get("/gd", response_class=HTMLResponse)
def db_search_gd(request: Request, search: str):

    dpd_html, summary_html = make_dpd_html(search)
    global dpd_css, dpd_js, home_simple_css

    return templates.TemplateResponse(
        "home_simple.html", {
        "request": request,
        "search": search,
        "dpd_results": dpd_html,
        "summary": summary_html,
        "dpd_css": dpd_css,
        "dpd_js": dpd_js,
        "home_simple_css": home_simple_css,
        })
    

def make_dpd_html(search: str) -> tuple[str, str]:
    db_session = get_db_session(pth.dpd_db_path)
    dpd_html = ""
    summary_html = ""
    search = search.replace("'", "").replace("ṁ", "ṃ").strip()

    lookup_results = db_session.query(Lookup) \
        .filter(Lookup.lookup_key.ilike(search)) \
        .all()
    
    # first try the lookup table, if no results, then try other options
    
    if lookup_results:
        for lookup_result in lookup_results:
        
            # headwords
            if lookup_result.headwords:
                headwords = lookup_result.headwords_unpack
                headword_results = db_session\
                    .query(DpdHeadwords)\
                    .filter(DpdHeadwords.id.in_(headwords))\
                    .all()
                headword_results = sorted(
                    headword_results, key=lambda x: pali_sort_key(x.lemma_1))
                for i in headword_results:
                    fc = get_family_compounds(i)
                    fi = get_family_idioms(i)
                    fs = get_family_set(i)
                    d = HeadwordData(i, fc, fi, fs)
                    summary_html += templates \
                        .get_template("dpd_summary.html") \
                        .render(d=d)
                    dpd_html += templates \
                        .get_template("dpd_headword.html") \
                        .render(d=d)
            
            # roots
            if lookup_result.roots:
                roots_list = lookup_result.roots_unpack
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
                    dpd_html += templates \
                        .get_template("root.html") \
                        .render(d=d)

            # deconstructor
            if lookup_result.deconstructor:
                d = DeconstructorData(lookup_result)
                dpd_html += templates \
                    .get_template("deconstructor.html") \
                    .render(d=d)

            # variant
            if lookup_result.variant:
                d = VariantData(lookup_result)
                dpd_html += templates \
                    .get_template("variant.html") \
                    .render(d=d)

            # spelling mistake
            if lookup_result.spelling:
                d = SpellingData(lookup_result)
                dpd_html += templates \
                    .get_template("spelling.html") \
                    .render(d=d)

            if lookup_result.grammar:
                d = GrammarData(lookup_result)
                dpd_html += templates \
                    .get_template("grammar.html") \
                    .render(d=d)

            # help          
            if lookup_result.help:
                d = HelpData(lookup_result)
                dpd_html += templates \
                    .get_template("help.html") \
                    .render(d=d)

            # abbreviations
            if lookup_result.abbrev:
                d = AbbreviationsData(lookup_result)
                dpd_html += templates \
                    .get_template("abbreviations.html") \
                    .render(d=d)

            # epd 
            if lookup_result.epd:
                d = EpdData(lookup_result)
                dpd_html += templates \
                    .get_template("epd.html") \
                    .render(d=d)

    # the two cases below search directly in the DpdHeadwords table

    elif search.isnumeric(): # eg 78654
        search_term = int(search)
        headword_result = db_session\
            .query(DpdHeadwords)\
            .filter(DpdHeadwords.id == search_term)\
            .first()
        if headword_result:
            fc = get_family_compounds(headword_result)
            fi = get_family_idioms(headword_result)
            fs = get_family_set(headword_result)
            d = HeadwordData(headword_result, fc, fi, fs)
            dpd_html += templates \
                .get_template("dpd_headword.html") \
                .render(d=d)

        # return closest matches
        else:
            dpd_html = find_closest_matches(search)

    elif re.search(r"\s\d", search): # eg "kata 5"
        headword_result = db_session \
            .query(DpdHeadwords) \
            .filter(DpdHeadwords.lemma_1 == search) \
            .first()
        if headword_result:
            fc = get_family_compounds(headword_result)
            fi = get_family_idioms(headword_result)
            fs = get_family_set(headword_result)
            d = HeadwordData(headword_result, fc, fi, fs)
            dpd_html += templates \
                .get_template("dpd_headword.html") \
                .render(d=d)

        # return closest matches
        else:
            dpd_html = find_closest_matches(search)

    # or finally return closest matches
    
    else:
        dpd_html = find_closest_matches(search)

    db_session.close()
    return dpd_html, summary_html

    

def find_closest_matches(search) -> str:

    ascii_matches = ascii_to_unicode_dict[search]
    closest_headword_matches =  \
        difflib.get_close_matches(
            search, headwords_clean_set,
            n=10,
            cutoff=0.7)
    
    combined_list = []
    combined_list.extend(ascii_matches)
    combined_list.extend([
        item 
        for item in closest_headword_matches
        if item not in ascii_matches
    ])

    string = "<h3>No results found. "
    if combined_list:
        string += "The closest matches are:</h3><br>"
        string += "<p>"
        string += ", ".join(combined_list)
        string += "</p>"
    else:
        string += "</h3>"

    return string

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        # host="127.1.1.1",
        port=8080,
        reload=True,
        reload_dirs="exporter/dpd_fastapi")

# run in terminal: 
# uvicorn exporter.dpd_fastapi.main:app --host 127.1.1.1 --port 8080 --reload --reload-dir exporter/dpd_fastapi
# uvicorn exporter.dpd_fastapi.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir exporter/dpd_fastapi


# TODO make help popup tooltips and a toggle to turn them off
# TODO dropdown menu when searching
# TODO summary of roots
# TODO history forward and backwards buttons
# TODO include mw, cpd, dppn, cone, etc.
