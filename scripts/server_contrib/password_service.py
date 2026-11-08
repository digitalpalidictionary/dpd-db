"""FastAPI change-password service for the contributor server.

Thin layer over ``password_change.py`` (see that module for the core
invariants and the spec pointer). Runs as root behind nginx only:

- listens on a unix socket (default /run/dpd-password.sock, chmod 0660
  and chgrp'd to nginx's group after the bind), never a TCP port — a
  local non-root process cannot even connect, so it cannot forge an
  Authorization header;
- /check is the auth_request subrequest endpoint: 403 only for a
  positively identified user whose .initial marker exists, 200
  otherwise, silent;
- GET / and POST / are the form; POST carries an Origin/Referer CSRF
  guard because browsers attach cached basic-auth credentials to
  cross-site form posts.

All routes stay off the event loop for blocking work: GET routes are
plain ``def`` (FastAPI's threadpool); POST is ``async`` only to read
the urlencoded body (stdlib parse_qs — ``Form`` would require the
python-multipart dependency, which the spec forbids) and runs the
blocking write via ``run_in_threadpool``; the per-user threading.Lock
in the core applies directly in the worker thread (herdr review N9).
"""

from __future__ import annotations

import functools
import grp
import logging
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

from scripts.server_contrib.password_change import (
    MAX_LENGTH_BYTES,
    MIN_LENGTH_BYTES,
    ChangeError,
    PasswordStore,
    origin_allowed,
)

DEFAULT_SOCK = "/run/dpd-password.sock"
DEFAULT_HTPASSWD_DIR = "/etc/nginx/dpd"

log = logging.getLogger("dpd_password")
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.INFO)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@functools.cache
def store() -> PasswordStore:
    return PasswordStore(Path(os.environ.get("DPD_HTPASSWD_DIR", DEFAULT_HTPASSWD_DIR)))


def sock_path() -> Path:
    return Path(os.environ.get("DPD_PASSWORD_SOCK", DEFAULT_SOCK))


# -- pages (plain strings; a two-field form needs no template engine) --------


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family: sans-serif; max-width: 34em; margin: 4em auto;">
<h1>{title}</h1>
{body}
</body></html>"""


def form_page(user: str, message: str = "") -> str:
    note = f'<p style="color: #b00;">{message}</p>' if message else ""
    return _page(
        f"Change the password for {user}",
        f"""{note}
<form method="post">
<p><label>New password<br><input type="password" name="new_password" required></label></p>
<p><label>Type it again<br><input type="password" name="repeat" required></label></p>
<p style="color: #555;">Between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} bytes
(a plain letter, digit or punctuation mark is one byte).</p>
<p><label><input type="checkbox" id="show"> Show passwords</label></p>
<p><button type="submit">Change password</button></p>
</form>
<script>
document.getElementById("show").addEventListener("change", function () {{
  var kind = this.checked ? "text" : "password";
  document.querySelectorAll("input[name=new_password], input[name=repeat]")
    .forEach(function (box) {{ box.type = kind; }});
}});
</script>""",
    )


SUCCESS_PAGE = _page(
    "Password changed",
    """<p>Your password has been changed.</p>
<ul>
<li>Close any other DPD tabs, then go back to your editor page and log in
with the NEW password.</li>
<li>The next login prompt expects the new password. If your browser fills
in the old one, delete it and type the new one.</li>
<li>An editor tab that was already open may keep working for up to an hour
on the old login. Closing that tab ends it.</li>
</ul>
<p><a href="../">Back to the editor</a></p>""",
)

CSRF_PAGE = _page(
    "Open this page directly",
    """<p>This password form only works when you open it from your own
contributor address, like <code>https://…/&lt;your name&gt;/password/</code>.
Please open that address in your browser and try again.</p>""",
)


def error_page(message: str) -> str:
    return _page("Password not changed", f"<p>{message}</p>")


# -- journald line per GET/POST (never the password, never the header) -------


def journal(request: Request, user: str, outcome: str) -> None:
    ip = request.headers.get("x-real-ip", "-")
    log.info("%s %s %s %s", request.method, user or "-", ip, outcome)


# -- routes ------------------------------------------------------------------


@app.get("/health")
def health() -> Response:
    return Response("ok", media_type="text/plain")


@app.get("/check")
def check(request: Request) -> Response:
    # nginx auth_request subrequest; fires on every editor request, so it
    # logs nothing. auth_basic has already answered 401 for strangers by
    # the time we run; anything we cannot positively identify is 200.
    pw_store = store()
    user = pw_store.identify_user(request.headers.get("authorization"))
    if user is not None and pw_store.check_gated(user):
        return Response(status_code=403)
    return Response(status_code=200)


@app.get("/")
def form(request: Request) -> HTMLResponse:
    user = store().identify_user(request.headers.get("authorization"))
    if user is None:
        return HTMLResponse(error_page("No login found for this page."))
    journal(request, user, "ok")
    return HTMLResponse(form_page(user))


@app.post("/")
async def change(request: Request) -> HTMLResponse:
    fields = parse_qs(
        (await request.body()).decode("utf-8", "replace"), keep_blank_values=True
    )
    new_password = fields.get("new_password", [""])[0]
    repeat = fields.get("repeat", [""])[0]
    pw_store = store()
    user = pw_store.identify_user(request.headers.get("authorization"))
    if user is None:
        return HTMLResponse(error_page("No login found for this page."))
    if not origin_allowed(
        request.headers.get("origin"),
        request.headers.get("referer"),
        request.headers.get("host"),
    ):
        journal(request, user, "rejected:csrf")
        return HTMLResponse(CSRF_PAGE)
    if new_password != repeat:
        journal(request, user, "rejected:repeat")
        return HTMLResponse(form_page(user, "The two passwords do not match."))
    if not MIN_LENGTH_BYTES <= len(new_password.encode("utf-8")) <= MAX_LENGTH_BYTES:
        journal(request, user, "rejected:length")
        return HTMLResponse(
            form_page(
                user,
                f"Use between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} bytes.",
            )
        )
    if any(ord(c) < 32 or ord(c) == 127 for c in new_password):
        journal(request, user, "rejected:characters")
        return HTMLResponse(
            form_page(user, "Do not use line breaks or control characters.")
        )
    try:
        # The htpasswd subprocesses block; the threadpool keeps the event
        # loop free and the core's per-user lock applies in the worker.
        await run_in_threadpool(pw_store.change_password, user, new_password)
    except ChangeError as exc:
        log.error("change failed for %s: %s", user, exc.reason)
        journal(request, user, f"rejected:{exc.reason}")
        return HTMLResponse(
            error_page(
                "The server could not change your password. "
                "Tell the maintainer what you saw here."
            ),
            status_code=500,
        )
    journal(request, user, "ok")
    return HTMLResponse(SUCCESS_PAGE)


def nginx_group() -> str | None:
    """nginx's worker group, same detection as add_contributor.sh."""
    override = os.environ.get("HTPASSWD_GROUP")
    if override:
        return override
    try:
        out = subprocess.run(
            ["nginx", "-T"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in out.splitlines():
        if line.startswith("user") and len(line.split()) > 1:
            return line.split()[1].rstrip(";")
    return None


class PasswordServer(uvicorn.Server):
    """uvicorn.Server that fixes socket permissions after the bind.

    The chmod/chown happens in startup() AFTER super().startup() has
    bound the socket — a startup-hook chmod races the bind (egm/gate3.md
    #2). uvicorn re-applies the mode of a stale socket on restart but
    never the group (herdr review N4), so this runs on every start.
    """

    def __init__(self, config: uvicorn.Config) -> None:
        super().__init__(config)
        self._sock = sock_path()
        self._group = nginx_group()

    async def startup(self, sockets: list | None = None) -> None:  # type: ignore[override]
        await super().startup(sockets)
        os.chmod(self._sock, 0o660)
        group = self._group
        if group:
            try:
                os.chown(self._sock, -1, grp.getgrnam(group).gr_gid)
            except (KeyError, PermissionError, OSError):
                log.warning("could not chgrp %s to %s", self._sock, group)
        else:
            log.warning(
                "no nginx group found; run chgrp <nginx group> %s or the "
                "editor cannot reach the service",
                self._sock,
            )


def main() -> None:
    config = uvicorn.Config(
        app,
        uds=str(sock_path()),
        log_level="info",
        # The write path is a subprocess call per request; one worker is
        # the whole design (spec: per-user lock in one process).
        workers=1,
    )
    PasswordServer(config).run()


if __name__ == "__main__":
    main()
