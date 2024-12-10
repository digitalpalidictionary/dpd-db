import uvicorn

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from exporter.webapp.tools import make_headwords_clean_set
from exporter.webapp.tools import make_ascii_to_unicode_dict
from exporter.webapp.tools import make_dpd_html

from exporter.goldendict.helpers import make_roots_count_dict

from db.db_helpers import get_db_session
from tools.paths import ProjectPaths


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory="exporter/webapp/static"), name="static")

pth: ProjectPaths = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

# Preload data that is shared across languages
roots_count_dict = make_roots_count_dict(db_session)
headwords_clean_set = make_headwords_clean_set(db_session)
headwords_clean_set_ru = make_headwords_clean_set(db_session, 'ru')
ascii_to_unicode_dict = make_ascii_to_unicode_dict(db_session)
db_session.close()

# Set up templates
templates = Jinja2Templates(directory="exporter/webapp/templates")
templates_ru = Jinja2Templates(directory="exporter/webapp/ru_templates")

with open("exporter/webapp/static/dpd.css") as f:
    dpd_css = f.read()

with open("exporter/webapp/static/dpd.js") as f:
    dpd_js = f.read()

with open("exporter/webapp/static/home_simple.css") as f:
    home_simple_css = f.read()


@app.get("/")
def home_page(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse(
        "home.html", {
            "request": request,
            "dpd_results": ""
        }
    )

@app.get("/ru/")
def home_page_ru(request: Request, response_class=HTMLResponse):
    return templates_ru.TemplateResponse(
        "home.html", {
            "request": request,
            "dpd_results": ""
        }
    )


@app.get("/search_html", response_class=HTMLResponse)
def db_search_html(request: Request, q: str):
    dpd_html, summary_html = make_dpd_html(q, pth, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict)
    return templates.TemplateResponse(
        "home.html", {
            "request": request,
            "q": q,
            "dpd_results": dpd_html,
        }
    )


@app.get("/ru/search_html", response_class=HTMLResponse)
def db_search_html_ru(request: Request, q: str):
    dpd_html, summary_html = make_dpd_html(q, pth, templates_ru, roots_count_dict, headwords_clean_set_ru, ascii_to_unicode_dict, 'ru')
    return templates_ru.TemplateResponse(
        "home.html", {
            "request": request,
            "q": q,
            "dpd_results": dpd_html,
        }
    )


@app.get("/search_json", response_class=JSONResponse)
def db_search_json(request: Request, q: str):
    dpd_html, summary_html = make_dpd_html(q, pth, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict)
    response_data = {
        "summary_html": summary_html,
        "dpd_html": dpd_html
    }
    headers = {"Accept-Encoding": "gzip"}
    return JSONResponse(content=response_data, headers=headers)


@app.get("/ru/search_json", response_class=JSONResponse)
def db_search_json_ru(request: Request, q: str):
    dpd_html, summary_html = make_dpd_html(q, pth, templates_ru, roots_count_dict, headwords_clean_set_ru, ascii_to_unicode_dict, 'ru')
    response_data = {
        "summary_html": summary_html,
        "dpd_html": dpd_html
    }
    headers = {"Accept-Encoding": "gzip"}
    return JSONResponse(content=response_data, headers=headers)


@app.get("/gd", response_class=HTMLResponse)
def db_search_gd(request: Request, search: str):

    dpd_html, summary_html = make_dpd_html(search, pth, templates, roots_count_dict, headwords_clean_set, ascii_to_unicode_dict)
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
        }
    )


@app.get("/ru/gd", response_class=HTMLResponse)
def db_search_gd_ru(request: Request, search: str):

    dpd_html, summary_html = make_dpd_html(search, pth, templates_ru, roots_count_dict, headwords_clean_set_ru, ascii_to_unicode_dict, "ru")
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
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        # host="127.1.1.1",
        port=8080,
        reload=True,
        reload_dirs="exporter/webapp/"
    
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

