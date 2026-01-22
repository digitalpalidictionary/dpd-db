# -*- coding: utf-8 -*-
from contextlib import contextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker
import re

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from audio.db.db_helpers import get_audio_record
from exporter.webapp.preloads import (
    make_ascii_to_unicode_dict,
    make_headwords_clean_set,
    make_roots_count_dict,
)
from exporter.webapp.toolkit import make_dpd_html
from tools.css_manager import CSSManager
from tools.paths import ProjectPaths
from tools.pali_text_files import cst_texts
from tools.tipitaka_db import search_all_cst_texts, search_book
from tools.translit import auto_translit_to_roman
from prometheus_fastapi_instrumentator import Instrumentator

pth: ProjectPaths = ProjectPaths()
app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory=str(pth.webapp_static_dir)), name="static")

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
    ascii_to_unicode_dict = make_ascii_to_unicode_dict(db_session)
    bd_count = db_session.query(BoldDefinition).count()

# Set up templates
templates = Jinja2Templates(directory=str(pth.webapp_templates_dir))

# Update CSS
css_manager = CSSManager()
css_manager.update_webapp_css()

# Global CSS and JS
with open(pth.webapp_css_path) as f:
    dpd_css = f.read()

with open(pth.webapp_js_path) as f:
    dpd_js = f.read()

with open(pth.webapp_home_simple_css_path) as f:
    home_simple_css = f.read()


# FIXME
history_list: list[tuple[str, str, str]] = []


@app.get("/")
def home_page(request: Request, response_class=HTMLResponse):
    """Home page."""

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "dpd_results": "",
            "bd_count": bd_count,
            "book_options": list(cst_texts.keys()),
        },
    )


@app.get("/bd")
def bold_definitions_page(request: Request, response_class=HTMLResponse):
    """Bold definitions landing page"""

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "dpd_results": "",
            "bd_count": bd_count,
            "book_options": list(cst_texts.keys()),
        },
    )


@app.get("/search_html", response_class=HTMLResponse)
def db_search_html(request: Request, q: str):
    """Returns a JSON with HTML."""

    q_roman = auto_translit_to_roman(q)

    dpd_html, summary_html = make_dpd_html(
        q_roman,
        pth,
        templates,
        roots_count_dict,
        headwords_clean_set,
        ascii_to_unicode_dict,
    )
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "q": q,
            "dpd_results": dpd_html,
            "book_options": list(cst_texts.keys()),
        },
    )


@app.get("/search_json", response_class=JSONResponse)
def db_search_json(request: Request, q: str):
    """Main search route for website."""

    q_roman = auto_translit_to_roman(q)

    dpd_html, summary_html = make_dpd_html(
        q_roman,
        pth,
        templates,
        roots_count_dict,
        headwords_clean_set,
        ascii_to_unicode_dict,
    )
    response_data = {"summary_html": summary_html, "dpd_html": dpd_html}
    headers = {"Accept-Encoding": "gzip"}
    return JSONResponse(content=response_data, headers=headers)


@app.get("/gd", response_class=HTMLResponse)
def db_search_gd(request: Request, search: str):
    """Returns pure HTML for GoldenDict and MDict."""

    search_roman = auto_translit_to_roman(search)

    dpd_html, summary_html = make_dpd_html(
        search_roman,
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


@app.get("/bd_search", response_class=HTMLResponse)
def db_search_bd(
    request: Request,
    q1: str,
    q2: str,
    option: str,
):
    """Search route for bold definitions."""

    from tools.bold_definitions_search import BoldDefinitionsSearchManager

    bd_searcher = BoldDefinitionsSearchManager()
    results = bd_searcher.search(q1, q2, option)

    if results:
        message = f"<b>{len(results)}</b> results found"
    else:
        message = "<b>0</b> results found - broaden your search or try the fuzzy option"

    # highlight search_2
    if q2:
        for result in results:
            result.commentary = re.sub(
                f"({q2}?)",  # Add ? to make quantifiers non-greedy
                r"<span class='hi'>\g<1></span>",
                result.commentary,
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


@app.get("/tt_search", response_class=JSONResponse)
def tt_search(request: Request, q: str, book: str, lang: str):
    """Search Tipiṭaka Translations."""

    # Limit results
    limit = 100

    # Determine search column
    search_column = "pali_text" if lang == "Pāḷi" else "english_translation"

    # Perform search
    if book == "all":
        results = search_all_cst_texts(q, search_column=search_column)
    else:
        results = search_book(book, q, search_column=search_column)

    total_count = len(results)
    results = results[:limit]

    # Generate JSON
    response_data = {"total": total_count, "results": []}

    if results:
        for i, (pali_text, eng_trans, table_name, book_name) in enumerate(results, 1):
            response_data["results"].append(
                {
                    "id": i,
                    "pali": pali_text,
                    "eng": eng_trans,
                    "book": book_name,
                    "table": table_name,
                }
            )

    return JSONResponse(content=response_data)


@app.get("/audio/{headword}", response_class=Response)
def get_audio(request: Request, headword: str, gender: str = "male"):
    """Serve audio file for a headword with byte-range support."""

    cleaned_headword = re.sub(r" \d.*$", "", headword)
    audio_data = get_audio_record(cleaned_headword, gender)

    if audio_data:
        file_size = len(audio_data)
        range_header = request.headers.get("range")

        headers = {
            "Accept-Ranges": "bytes",
        }

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1

                if start < file_size:
                    chunk = audio_data[start : end + 1]
                    headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
                    headers["Content-Length"] = str(len(chunk))
                    return Response(
                        content=chunk,
                        status_code=206,
                        headers=headers,
                        media_type="audio/mpeg",
                    )

        headers["Content-Length"] = str(file_size)
        return Response(
            content=audio_data,
            status_code=200,
            headers=headers,
            media_type="audio/mpeg",
        )

    return Response(status_code=404)


def update_history(
    search_1: str, search_2: str, option: str
) -> list[tuple[str, str, str]]:
    global history_list
    history_tuple = (search_1, search_2, option)
    if history_tuple in history_list:
        history_list.remove(history_tuple)
    history_list.insert(0, history_tuple)
    history_list = history_list[:250]
    return history_list


# Global metrics for /status
metrics = {
    "total_requests": 0,
    "active_requests": 0,
    "total_time": 0.0,
    "endpoints": {},  # route -> {"count": 0, "history": []}
}


@app.middleware("http")
async def track_performance(request: Request, call_next):
    # Ignore background noise
    path = request.url.path
    if (
        path.startswith("/static")
        or path == "/favicon.ico"
        or path == "/metrics"
        or path == "/status"
    ):
        return await call_next(request)

    import time
    from urllib.parse import unquote

    start_time = time.time()
    metrics["active_requests"] += 1
    metrics["total_requests"] += 1

    # Identify the route pattern (e.g. /audio/{headword})
    route = request.scope.get("route")
    route_path = route.path if route else path

    if route_path not in metrics["endpoints"]:
        metrics["endpoints"][route_path] = {"count": 0, "history": []}

    metrics["endpoints"][route_path]["count"] += 1

    # Capture decoded Unicode request string
    full_query = unquote(str(request.url.query))
    request_display = f"{path}?{full_query}" if full_query else path

    history = metrics["endpoints"][route_path]["history"]
    if request_display not in history:
        history.insert(0, request_display)
        metrics["endpoints"][route_path]["history"] = history[:10]

    try:
        response = await call_next(request)
        return response
    finally:
        process_time = time.time() - start_time
        metrics["total_time"] += process_time
        metrics["active_requests"] -= 1


@app.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    """Human-readable status dashboard."""
    import psutil
    import platform
    import os
    from datetime import datetime
    from tools.cache_load import _audio_dict_cache

    process = psutil.Process()
    mem_info = process.memory_info()
    sys_mem = psutil.virtual_memory()

    # Memory Calculation (App)
    app_used = mem_info.rss
    app_total = 4096 * 1024 * 1024  # 4GB Limit
    app_percent = (app_used / app_total) * 100

    # Memory Calculation (System)
    sys_used = sys_mem.used
    sys_total = sys_mem.total
    sys_percent = sys_mem.percent

    health_color = "green"
    if app_percent > 70:
        health_color = "orange"
    if app_percent > 90:
        health_color = "red"

    # Performance stats
    avg_time = 0
    if metrics["total_requests"] > 0:
        avg_time = metrics["total_time"] / metrics["total_requests"]

    stats = {
        "pid": os.getpid(),
        "python_version": platform.python_version(),
        "start_time": datetime.fromtimestamp(process.create_time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "uptime": str(
            datetime.now() - datetime.fromtimestamp(process.create_time())
        ).split(".")[0],
        # App Mem
        "app_mem_used": f"{app_used / 1024 / 1024:.2f} MB",
        "app_mem_total": f"{app_total / 1024 / 1024 / 1024:.2f} GB",
        "app_mem_percent": f"{app_percent:.1f}%",
        # Sys Mem
        "sys_mem_used": f"{sys_used / 1024 / 1024 / 1024:.2f} GB",
        "sys_mem_total": f"{sys_total / 1024 / 1024 / 1024:.2f} GB",
        "sys_mem_percent": f"{sys_percent:.1f}%",
        "health_color": health_color,
        "cpu_percent": f"{process.cpu_percent(interval=0.1)}%",
        "threads": process.num_threads(),
        # Performance
        "active_requests": metrics["active_requests"],
        "total_requests": metrics["total_requests"],
        "avg_response_time": f"{avg_time * 1000:.2f} ms",
        "history_count": len(history_list),
        "endpoints": metrics["endpoints"],
        "audio_cache_loaded": _audio_dict_cache is not None,
    }

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "stats": stats,
        },
    )


# Proactively monitor memory and performance
Instrumentator().instrument(app).expose(app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        # host="0.0.0.0",
        host="127.1.1.1",
        port=8080,
        reload=True,
        reload_dirs=str(pth.webapp_static_dir.parent),
    )

# Run on local machine with reload on changes
# uv run uvicorn exporter.webapp.main:app --host 127.1.1.1 --port 8080 --reload --reload-dir exporter/webapp

# Run on local network with reload on changes
# uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir exporter/webapp


# TODO make help popup tooltips and a toggle to turn them off
# TODO dropdown menu when searching
# TODO include mw, cpd, dppn, cone, etc.
# TODO add set names in lookup table
