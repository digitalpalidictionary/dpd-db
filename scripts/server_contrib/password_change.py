"""Core password-change logic for the contributor server.

Plain module on purpose: no fastapi imports, everything testable with
the real ``htpasswd`` binary against a temporary directory (the
``--root``-style injection the other server_contrib tests use).

Two modules exist (spec: kamma/threads/20261105_contrib_password_change):
this core owns the username rule, ``identify_user``, the write path,
verify, marker ops, ``check_gated`` and the Origin/Referer decision.
``password_service.py`` is the thin FastAPI layer over it.

Invariants (egm/gate1.md #1, herdr review M1):

- the rewritten htpasswd keeps the ORIGINAL file's mode and group
  (today ``640 root:www-data``); a bare temp + os.replace yields
  ``600 root:root`` and the user's URL answers 500 forever;
- passwords only ever touch the stdin of an ``htpasswd`` subprocess,
  never argv, never logs;
- the marker is deleted only after a REAL verification passed
  (``htpasswd -vi`` on the temp file, before the replace);
- bcrypt cost stays pinned at 5 to match add_contributor.sh; nginx
  verifies the hash on every request and a higher cost would multiply
  that cost per request.
"""

from __future__ import annotations

import base64
import binascii
import os
import re
import shutil
import stat
import subprocess
import threading
from pathlib import Path

# Same rule as scripts/server_contrib/add_contributor.sh, including the
# "added" refusal (it would clash with the *_added review-log sync skips).
USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")

# Length bounds in bytes. 10 minimum (owner choice, no composition
# rules); 72 maximum because bcrypt truncates beyond 72 bytes
# (verified empirically: an 80-byte password fails htpasswd -vi).
MIN_LENGTH_BYTES = 10
MAX_LENGTH_BYTES = 72

# Matches add_contributor.sh's `htpasswd -B` (no -C) baseline.
BCRYPT_COST = "5"


class ChangeError(Exception):
    """A password change failed; ``reason`` is a short machine-readable tag."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def valid_username(user: str) -> bool:
    """True when user passes the add_contributor.sh name rules."""
    return bool(USERNAME_RE.fullmatch(user)) and "added" not in user


def origin_allowed(origin: str | None, referer: str | None, host: str | None) -> bool:
    """CSRF guard for the POST (basic-auth credentials ride cross-site forms).

    Accept only requests whose Origin equals ``https://<host>`` or whose
    Referer starts with ``https://<host>/`` — same-site navigation to the
    password page. The trailing slash prevents ``host`` vs ``host.evil.com``
    confusion. No header → reject.
    """
    if host is None:
        return False
    expected = f"https://{host}"
    if origin is not None and origin == expected:
        return True
    if referer is not None and referer.startswith(f"{expected}/"):
        return True
    return False


# -- seams for tests (egm/gate3.md #5) --------------------------------------


def _run_htpasswd(args: list[str], input: str) -> subprocess.CompletedProcess[str]:
    """Run htpasswd with the password on stdin only."""
    return subprocess.run(
        ["htpasswd", *args], input=input, capture_output=True, text=True
    )


def _replace(src: Path, dst: Path) -> None:
    """Atomic swap; a seam so tests can induce a failure here."""
    os.replace(src, dst)


# -- the store ---------------------------------------------------------------


class PasswordStore:
    """All htpasswd and marker operations for one directory.

    The directory is injected, so tests run against tmp_path and never
    touch /etc/nginx/dpd.
    """

    def __init__(self, htpasswd_dir: Path) -> None:
        self.dir = htpasswd_dir
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    # paths

    def _file(self, user: str) -> Path:
        return self.dir / f"{user}.htpasswd"

    def marker(self, user: str) -> Path:
        return self.dir / f"{user}.initial"

    def _lock(self, user: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(user, threading.Lock())

    # identity

    def identify_user(self, auth_header: str | None) -> str | None:
        """User from a basic-auth header, or None when not positively known.

        None on: missing header, undecodable base64, no colon, a name the
        add script would refuse, or no existing htpasswd file. Callers
        treat None as "not identified" (the /check endpoint answers 200;
        nginx's auth_basic remains the real gate for such requests).
        """
        if not auth_header or not auth_header.startswith("Basic "):
            return None
        try:
            decoded = base64.b64decode(
                auth_header.removeprefix("Basic ").strip(), validate=True
            ).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None
        user, sep, _password = decoded.partition(":")
        if not sep or not valid_username(user):
            return None
        if not self._file(user).is_file():
            return None
        return user

    # marker (forced first change)

    def needs_change(self, user: str) -> bool:
        return self.marker(user).exists()

    def check_gated(self, user: str) -> bool:
        """True only for an existing valid user whose marker is armed.

        The /check endpoint maps this to 403; everything else is 200.
        """
        return (
            valid_username(user)
            and self._file(user).is_file()
            and self.needs_change(user)
        )

    def clear_marker(self, user: str) -> None:
        self.marker(user).unlink(missing_ok=True)

    # write path

    def change_password(self, user: str, new_password: str) -> None:
        """Rewrite user's hash safely; clear the marker on success.

        Raises ChangeError on every failure; the original file (and the
        marker) survive untouched in that case.
        """
        if not valid_username(user):
            raise ChangeError("bad_username")
        target = self._file(user)
        if not target.is_file():
            raise ChangeError("unknown_user")
        password_bytes = new_password.encode("utf-8")
        if len(password_bytes) < MIN_LENGTH_BYTES:
            raise ChangeError("too_short")
        if len(password_bytes) > MAX_LENGTH_BYTES:
            raise ChangeError("too_long")
        if any(ord(c) < 32 or ord(c) == 127 for c in new_password):
            raise ChangeError("bad_characters")

        with self._lock(user):
            self._change_locked(user, target, new_password)

    def _change_locked(self, user: str, target: Path, new_password: str) -> None:
        original = target.stat()
        bak = self.dir / f"{user}.htpasswd.bak"
        temp = self.dir / f".{user}.htpasswd.tmp"

        # .bak first (spec step 1): a later failure restores from it.
        shutil.copy2(target, bak)
        try:
            shutil.copy2(target, temp)
            written = _run_htpasswd(
                ["-B", "-C", BCRYPT_COST, "-i", str(temp), user],
                input=f"{new_password}\n",
            )
            if written.returncode != 0:
                raise ChangeError("write_failed")
            # Real verification of the TEMP file, before any replace:
            # the marker is never deleted without this passing.
            verified = _run_htpasswd(
                ["-v", "-i", str(temp), user], input=f"{new_password}\n"
            )
            if verified.returncode != 0:
                raise ChangeError("verify_failed")
            _apply_owner(temp, original)
            _replace(temp, target)
            _fsync_dir(self.dir)
            replaced = target.stat()
            if (
                stat.S_IMODE(replaced.st_mode) != stat.S_IMODE(original.st_mode)
                or replaced.st_gid != original.st_gid
            ):
                raise ChangeError("post_check_failed")
        except BaseException as exc:
            # Any failure after the .bak copy restores the original
            # bytes AND their mode/group (copy2 never preserves group —
            # herdr review M1), then re-raises: ChangeError and
            # system exits (KeyboardInterrupt &c.) unchanged, any other
            # exception wrapped so callers only ever see ChangeError.
            _restore(bak, target, original)
            _fsync_dir(self.dir)
            temp.unlink(missing_ok=True)
            if isinstance(exc, ChangeError) or not isinstance(exc, Exception):
                raise
            raise ChangeError("internal") from exc
        temp.unlink(missing_ok=True)
        self.clear_marker(user)


def _apply_owner(path: Path, original: os.stat_result) -> None:
    """Give path the original file's mode and group, EPERM-tolerant.

    Non-root callers (tests) cannot chown to another uid/gid; the
    same-user case needs no chown anyway.
    """
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fchmod(fd, stat.S_IMODE(original.st_mode))
        try:
            os.fchown(fd, original.st_uid, original.st_gid)
        except PermissionError:
            pass
    finally:
        os.close(fd)


def _restore(bak: Path, target: Path, original: os.stat_result) -> None:
    """Put bak back as target, with the original mode and group.

    Goes through a temp file and os.replace, so nginx never reads a
    half-written htpasswd file.
    """
    temp = target.with_name(f".{target.name}.restore")
    shutil.copy2(bak, temp)
    os.chmod(temp, stat.S_IMODE(original.st_mode))
    try:
        os.chown(temp, original.st_uid, original.st_gid)
    except PermissionError:
        pass
    os.replace(temp, target)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
