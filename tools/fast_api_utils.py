# -*- coding: utf-8 -*-

"""Start the local DPD webapp server and open search requests in the browser.
Used by gui2 to look up words and bold definitions."""

import os
import subprocess
import urllib.parse
import webbrowser

from tools.server_mode import is_headless_server


def _api_port() -> str:
    """Per-instance helper API port. Defaults to 8080 (desktop). Overridable
    via DPD_API_PORT so multiple gui2 web instances on one host don't collide
    on 127.1.1.1:8080."""
    return os.environ.get("DPD_API_PORT", "8080")


def start_dpd_server() -> None:
    "uvicorn exporter.webapp.main:app --host 127.1.1.1 --port <DPD_API_PORT>"
    # The webapp helper only feeds request_dpd_server's browser pop-up, which is
    # disabled in a server session — so don't spin up a dead uvicorn per instance.
    if is_headless_server():
        return
    command = [
        "uvicorn",
        "exporter.webapp.main:app",
        "--host",
        "127.1.1.1",
        "--port",
        _api_port(),
    ]
    subprocess.Popen(command)


def request_dpd_server(q: str | int):
    # Opens a browser tab on the host running this process — useless (and
    # pointing at a dead port) in a headless server session.
    if is_headless_server():
        return
    base_url = f"http://127.1.1.1:{_api_port()}/"
    search_params = {"tab": "dpd", "q": q}
    url = f"{base_url}?{urllib.parse.urlencode(search_params)}"
    webbrowser.open(url)


if __name__ == "__main__":
    start_dpd_server()
    # request_dpd_server("katakicca")
