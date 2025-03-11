from contextlib import contextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from exporter.webapp.preloads import (
    make_ascii_to_unicode_dict,
    make_headwords_clean_set,
    make_roots_count_dict,
)
from exporter.webapp.tools import fuzzy_replace, make_dpd_html
from tools.paths import ProjectPaths

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory="exporter/webapp/static"), name="static")

pth: ProjectPaths = ProjectPaths()

# Create session factory for database connections
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=get_db_session(pth.dpd_db_path).bind
)


@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Preload data that is shared across languages
with get_db() as db_session:
    roots_count_dict = make_roots_count_dict(db_session)
    headwords_clean_set = make_headwords_clean_set(db_session)
    headwords_clean_set_ru = make_headwords_clean_set(db_session, "ru")
    ascii_to_unicode_dict = make_ascii_to_unicode_dict(db_session)
    bd_count = db_session.query(BoldDefinition).count()

# Set up templates
templates = Jinja2Templates(directory="exporter/webapp/templates")
templates_ru = Jinja2Templates(directory="exporter/webapp/ru_templates")

with open("exporter/webapp/static/dpd.css") as f:
    dpd_css = f.read()

with open("exporter/webapp/static/dpd.js") as f:
    dpd_js = f.read()

with open("exporter/webapp/static/home_simple.css") as f:
    home_simple_css = f.read()

# FIXME
history_list: list[tuple[str, str, str]] = []


@app.get("/")
def home_page(request: Request, response_class=HTMLResponse):
    """Home page."""

    return templates.TemplateResponse(
        "home.html", {"request": request, "dpd_results": "", "bd_count": bd_count}
    )


@app.get("/bd")
def bold_definitions_page(request: Request, response_class=HTMLResponse):
    """Bold definitions landing page"""

    return templates.TemplateResponse(
        "home.html", {"request": request, "dpd_results": "", "bd_count": bd_count}
    )


@app.get("/ru")
def home_page_ru(request: Request, response_class=HTMLResponse):
    """Russian home page"""

    return templates_ru.TemplateResponse(
        "home.html", {"request": request, "dpd_results": ""}
    )


@app.get("/search_html", response_class=HTMLResponse)
def db_search_html(request: Request, q: str):
    """Returns a JSON with HTML."""

    dpd_html, summary_html = make_dpd_html(
        q, pth, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict
    )
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "q": q,
            "dpd_results": dpd_html,
        },
    )


@app.get("/ru/search_html", response_class=HTMLResponse)
def db_search_html_ru(request: Request, q: str):
    """Returns a JSON with Russian HTML."""

    dpd_html, summary_html = make_dpd_html(
        q,
        pth,
        templates_ru,
        roots_count_dict,
        headwords_clean_set_ru,
        ascii_to_unicode_dict,
        "ru",
    )
    return templates_ru.TemplateResponse(
        "home.html",
        {
            "request": request,
            "q": q,
            "dpd_results": dpd_html,
        },
    )


@app.get("/search_json", response_class=JSONResponse)
def db_search_json(request: Request, q: str):
    """Main search route for website."""

    dpd_html, summary_html = make_dpd_html(
        q, pth, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict
    )
    response_data = {"summary_html": summary_html, "dpd_html": dpd_html}
    headers = {"Accept-Encoding": "gzip"}
    return JSONResponse(content=response_data, headers=headers)


@app.get("/ru/search_json", response_class=JSONResponse)
def db_search_json_ru(request: Request, q: str):
    """Main Russian search route for website."""

    dpd_html, summary_html = make_dpd_html(
        q,
        pth,
        templates_ru,
        roots_count_dict,
        headwords_clean_set_ru,
        ascii_to_unicode_dict,
        "ru",
    )
    response_data = {"summary_html": summary_html, "dpd_html": dpd_html}
    headers = {"Accept-Encoding": "gzip"}
    return JSONResponse(content=response_data, headers=headers)


@app.get("/gd", response_class=HTMLResponse)
def db_search_gd(request: Request, search: str):
    """Returns pure HTML for GoldenDict and MDict."""

    dpd_html, summary_html = make_dpd_html(
        search,
        pth,
        templates,
        roots_count_dict,
        headwords_clean_set,
        ascii_to_unicode_dict,
    )
    global dpd_css, dpd_js, home_simple_css

    return templates.TemplateResponse(
        "home_simple.html",
        {
            "request": request,
            "search": search,
            "dpd_results": dpd_html,
            "summary": summary_html,
            "dpd_css": dpd_css,
            "dpd_js": dpd_js,
            "home_simple_css": home_simple_css,
        },
    )


@app.get("/ru/gd", response_class=HTMLResponse)
def db_search_gd_ru(request: Request, search: str):
    """Returns pure HTML in Russian for GoldenDict and MDict."""

    dpd_html, summary_html = make_dpd_html(
        search,
        pth,
        templates_ru,
        roots_count_dict,
        headwords_clean_set_ru,
        ascii_to_unicode_dict,
        "ru",
    )
    global dpd_css, dpd_js, home_simple_css

    return templates.TemplateResponse(
        "home_simple.html",
        {
            "request": request,
            "search": search,
            "dpd_results": dpd_html,
            "summary": summary_html,
            "dpd_css": dpd_css,
            "dpd_js": dpd_js,
            "home_simple_css": home_simple_css,
        },
    )


@app.get("/bd_search", response_class=HTMLResponse)
def db_search(
    request: Request,
    q1: str,
    q2: str,
    option: str,
):
    """Search route for bold defintions."""

    with get_db() as db_session:
        # no search
        if not q1 and not q2:
            results = []

        # starts_with search
        elif option == "starts_with":
            search_1_start = f"^{q1}"
            results = (
                db_session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(search_1_start))
                .filter(BoldDefinition.commentary.regexp_match(q2))
                .all()
            )

        # regex search
        elif option == "regex":
            results = (
                db_session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(q1))
                .filter(BoldDefinition.commentary.regexp_match(q2))
                .all()
            )
            message = f"{len(results)} results found"

        # fuzzy search
        elif option == "fuzzy":
            search_1_fuzzy = fuzzy_replace(q1)
            search_2_fuzzy = fuzzy_replace(q2)
            results = (
                db_session.query(BoldDefinition)
                .filter(BoldDefinition.bold.regexp_match(search_1_fuzzy))
                .filter(BoldDefinition.commentary.regexp_match(search_2_fuzzy))
                .all()
            )
            message = f"{len(results)} results found"

    if results:
        message = f"<b>{len(results)}</b> results found"
    else:
        message = "<b>0</b> results found - broaden your search or try the fuzzy option"

    # highlight search_2
    if q2:
        for result in results:
            result.commentary = result.commentary.replace(
                q2, f"<span class='hi'>{q2}</span>"
            )

    history_list = update_history(q1, q2, option)

    # trim to 100 results
    too_many_results = False
    if len(results) > 100:
        results = results[:100]
        too_many_results = True


    return templates.TemplateResponse(
        "bold_definitions.html",
        {
            "request": request,
            "results": results,
            "search_1": q1,
            "search_2": q2,
            "search_option": option,
            "message": message,
            "too_many_results": too_many_results,
            "history": history_list,
        },
    )


def update_history(
    search_1: str, search_2: str, option: str
) -> list[tuple[str, str, str]]:
    global history_list
    history_tuple = (search_1, search_2, option)
    if history_tuple in history_list:
        history_list.remove(history_tuple)
    history_list.insert(0, history_tuple)
    return history_list[:25]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        # host="0.0.0.0",
        host="127.1.1.1",
        port=8080,
        reload=True,
        reload_dirs="exporter/webapp/",
    )

# run in terminal:
# uvicorn exporter.webapp.main:app --host 127.1.1.1 --port 8080 --reload --reload-dir exporter/webapp
# uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir exporter/webapp


# TODO make help popup tooltips and a toggle to turn them off
# TODO dropdown menu when searching
# TODO summary of roots
# TODO history forward and backwards buttons
# TODO include mw, cpd, dppn, cone, etc.
# TODO add set names in lookup table
