# -*- coding: utf-8 -*-

"""Start the local DPD webapp server and open search requests in the browser.
Used by gui2 to look up words and bold definitions."""

import subprocess
import urllib.parse
import webbrowser


def start_dpd_server() -> None:
    "uvicorn exporter.webapp.main:app --host 127.1.1.1 --port 8080"
    command = [
        "uvicorn",
        "exporter.webapp.main:app",
        "--host",
        "127.1.1.1",
        "--port",
        "8080",
    ]
    subprocess.Popen(command)


def request_dpd_server(q: str | int):
    base_url = "http://127.1.1.1:8080/"
    search_params = {"tab": "dpd", "q": q}
    url = f"{base_url}?{urllib.parse.urlencode(search_params)}"
    webbrowser.open(url)


if __name__ == "__main__":
    start_dpd_server()
    # request_dpd_server("katakicca")
