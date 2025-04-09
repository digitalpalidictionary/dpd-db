from contextlib import contextmanager
import re
import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI app first
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=500)

# Then import other dependencies
from db.db_helpers import get_db_session
from db.models import BoldDefinition
from exporter.webapp.preloads import (
    make_ascii_to_unicode_dict,
    make_headwords_clean_set,
    make_roots_count_dict,
)
from exporter.webapp.tools import fuzzy_replace, make_dpd_html
from tools.paths import ProjectPaths
from tools.translit import auto_translit_to_roman

# Rest of your existing code...

# Add new proxy endpoints after all other route definitions
@app.get("/gd/{path:path}")
async def proxy_gd_request(request: Request, path: str):
    """Proxy requests to dpdict.net/gd/"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://dpdict.net/gd/{path}")
            response.raise_for_status()
            return HTMLResponse(content=response.text)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Word not found")

@app.get("/ru/gd/{path:path}")
async def proxy_gd_request_ru(request: Request, path: str):
    """Proxy Russian requests to dpdict.net/ru/gd/"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://dpdict.net/ru/gd/{path}")
            response.raise_for_status()
            return HTMLResponse(content=response.text)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Word not found")

# Modify existing endpoints to use proxy (add these after the original versions)
@app.get("/search_html", response_class=HTMLResponse)
async def proxied_db_search_html(request: Request, q: str):
    """Modified to use proxy for gd content"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://dpdict.net/gd/{q}")
            response.raise_for_status()
            
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "q": q,
                    "dpd_results": response.text,
                }
            )
    except httpx.HTTPStatusError:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "q": q,
                "dpd_results": "<div class='error'>Word not found</div>",
            }
        )

# Keep all your existing code below...
