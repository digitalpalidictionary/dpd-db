# Final review of the changed code — 2026-11-07

Written for an executor that needs exact instructions. Do each edit exactly as
written. Do not change anything that is not listed. Do not commit or push.

**Reviewer limits:** the reviewer ran no test, no linter and no type check,
never started the service, and did not read the two new test files or the full
runbook diff. Part C below makes the executor do those.

## Part A — edits to make (all required)

### A1. One store for the whole process (real bug)

Why: `store()` builds a new `PasswordStore` on every call. The per-user lock
lives inside the store. So every request has its own lock and two requests at
once never wait for each other.

File: `scripts/server_contrib/password_service.py`

1. In the import block at the top, add the line `import functools` directly
   ABOVE the line `import grp`. Then run `uv run ruff check --fix` on the file.
2. Replace exactly these two lines:

```python
def store() -> PasswordStore:
    return PasswordStore(Path(os.environ.get("DPD_HTPASSWD_DIR", DEFAULT_HTPASSWD_DIR)))
```

with exactly these three lines:

```python
@functools.cache
def store() -> PasswordStore:
    return PasswordStore(Path(os.environ.get("DPD_HTPASSWD_DIR", DEFAULT_HTPASSWD_DIR)))
```

3. Add this test at the END of `tests/scripts/server_contrib/test_password_change.py`.
   Add `from scripts.server_contrib import password_service` to the imports of
   that file if it is not there:

```python
def test_service_store_is_one_shared_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DPD_HTPASSWD_DIR", str(tmp_path))
    password_service.store.cache_clear()
    try:
        assert password_service.store() is password_service.store()
    finally:
        password_service.store.cache_clear()
```

4. Prove the test guards the fix: remove the `@functools.cache` line, run
   `uv run pytest tests/scripts/server_contrib/test_password_change.py -k shared_instance`,
   confirm it FAILS, then put the line back and confirm it passes. Report both
   results.

### A2. Trailing newline in the user name

File: `scripts/server_contrib/password_change.py`, function `valid_username`.
Replace exactly:

```python
    return bool(USERNAME_RE.match(user)) and "added" not in user
```

with exactly:

```python
    return bool(USERNAME_RE.fullmatch(user)) and "added" not in user
```

Add a case to the existing user-name test: `valid_username("alice\n")` must be
`False`.

### A3. Reject control characters in the new password

Why: a hand-made POST can send a line break inside the password. `htpasswd -i`
reads only the first line, so the stored password would be shorter than the one
sent.

File `scripts/server_contrib/password_change.py`, function `change_password`.
Directly AFTER these two lines:

```python
        if len(password_bytes) > MAX_LENGTH_BYTES:
            raise ChangeError("too_long")
```

add these two lines (same indent as the `if` above):

```python
        if any(ord(c) < 32 or ord(c) == 127 for c in new_password):
            raise ChangeError("bad_characters")
```

File `scripts/server_contrib/password_service.py`, function `change`. Directly
AFTER the whole `if not MIN_LENGTH_BYTES <= len(...) <= MAX_LENGTH_BYTES:`
block (the one that ends with `)` on its own line, just before `try:`), add:

```python
    if any(ord(c) < 32 or ord(c) == 127 for c in new_password):
        journal(request, user, "rejected:characters")
        return HTMLResponse(
            form_page(user, "Do not use line breaks or control characters.")
        )
```

Add a test: `change_password("alice", "abcdefghij\nklm")` raises `ChangeError`
and the htpasswd file is byte-for-byte unchanged and the marker still exists.

### A4. The page says "characters" but the limit counts bytes

File `scripts/server_contrib/password_service.py`.

1. In `form_page`, replace exactly:

```
<p style="color: #555;">Between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} characters.
Letters, numbers and punctuation are all fine.</p>
```

with exactly:

```
<p style="color: #555;">Between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} bytes
(a plain letter, digit or punctuation mark is one byte).</p>
```

2. In `change`, replace exactly:

```python
                f"Use between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} characters.",
```

with exactly:

```python
                f"Use between {MIN_LENGTH_BYTES} and {MAX_LENGTH_BYTES} bytes.",
```

### A5. Fix the thread text (no code)

File `kamma/threads/20261105_contrib_password_change/plan.md`:

1. Phase 2, the smoke-run task. Replace
   `uv run python\n  scripts/server_contrib/password_service.py` (two lines in
   the file) with `uv run python -m\n  scripts.server_contrib.password_service`.
   Why: running the file by path breaks its import line.
2. Phase 3, the `add_contributor.sh` task. Replace `chmod 644` with `chmod 600`.
3. Phase 4, the unit task. Replace `(`[Unit]` Description/After,` with
   `(`[Unit]` Description,`.
4. Tick (`[x]`) a task ONLY after you have checked that its work exists and its
   `→ verify:` line passes. Do not tick the smoke run until Part C step 4 is done.

File `kamma/threads/20261105_contrib_password_change/spec.md`:

1. Line 6. Replace `planned via kamma-1-plan-egm; Gates 1–2 done, Gate 3 pending`
   with `planned via kamma-1-plan-egm; Gates 1–3 and the herdr review done`.
2. In the "Review record" Gate 2 paragraph, the accepted list in "Assumptions"
   says `chmod 644`. Replace `marker `--root` +\n  chmod 644 + write-last` with
   `marker `--root` +\n  chmod 600 + write-last`.

## Part B — optional (do only if the owner says yes)

### B1. Restore without a half-written file

File `scripts/server_contrib/password_change.py`. Replace the whole function
`_restore` with:

```python
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
```

After it, the existing restore test must still pass.

## Part C — checks to run, in this order, and report the output

1. `uv run pytest tests/scripts/server_contrib/` — report passed and failed counts.
2. For every Python file changed or added in `scripts/server_contrib/`:
   `uv run ruff check --fix <file>`, `uv run ruff format <file>`,
   `uv run pyright <file>`. For files under `tests/`: use
   `uv run pyright --project /dev/null <file>`. Fix every error, including old
   ones. Do not add `# noqa`. If pyright complains about the
   `# type: ignore[override]` or the bare `list` in `password_service.py`, fix
   only what it reports.
3. `bash -n` on `add_contributor.sh`, `set_password.sh`, `server_setup.sh`.
   Then `just typecheck`.
4. Smoke run of the service, from the repo root, in the background, with a test
   user in a temp folder:
   `DPD_PASSWORD_SOCK=<scratchpad>/pw.sock DPD_HTPASSWD_DIR=<scratchpad>/pwht uv run python -m scripts.server_contrib.password_service`
   Then: `curl --unix-socket <scratchpad>/pw.sock http://localhost/health`
   prints `ok`; `/check` with no header gives 200; `stat -c %a <scratchpad>/pw.sock`
   prints `660`; a POST with `-H "Origin: https://localhost"` and a
   `Host: localhost` header changes the hash; a POST with no Origin is refused.
   Stop the server by its process number. Never use `pkill`.
5. Do not run anything against the real server in this part.

## Part D — ask the owner before you touch this

`scripts/server_contrib/contrib_pull.py` (line ~590 and ~592) and
`tests/scripts/server_contrib/test_contrib_pull.py` (line ~1047) now read the
config section `[dpd_contributor_server]` instead of `[epitaka_server]`. The
spec does not mention it. Runbook Step 10a still says `[epitaka_server]`. Today
`[dpd_contributor_server]` points at the NEW server, so the daily pull would go
there. Ask the owner which one they want:

- Keep it: change `[epitaka_server]` to `[dpd_contributor_server]` in the
  runbook Step 10a line, and name the rename on its own line in the commit
  message.
- Revert it: put `epitaka_server` back in those three places.

Do nothing about this until the owner answers.

## Notes for the owner (no action by the executor)

- uvicorn sets mode 0666 on a unix socket when it binds. The service sets 660
  only afterwards. For a moment any local process could connect. The server has
  no other users today. After the first start on the server, run `stat` on the
  socket and report the mode.
- `set_password.sh` rewrites the file in place with no lock. A reset at the same
  instant as a self-service change could clash. Rare. Accepted.
- A pull on the server changes nothing for the running site. The owner must run
  runbook Step 7e on the live server: install the unit, patch the site file,
  regenerate each user's conf, `nginx -t`, reload, then the CHECK list. Users
  that already exist are not armed.

## Checked and correct (by reading)

- Both socket `proxy_pass` lines carry the second colon (`.sock:/`, `.sock:/check`).
- The same socket path appears in the unit, both templates, the service and the runbook.
- `@pw_@USER@` becomes `@pw_<user>` under the `sed` in `add_contributor.sh`.
- `add_contributor.sh` writes the marker last, mode 600. Its site-file warning
  uses the runbook's path (`sites-available/dpd-contrib`).
- `server_setup.sh` skips the unit when it exists and fills `@CLONE@`.
- Runbook Step 7e exists and its site-file patch tests for `_dpd_pw_check` first.
- The write path keeps mode and group, verifies the temp file before the replace,
  and deletes the marker only after a real verify.
- `/check` returns 403 only for a known user with an armed marker, and 200 in
  every other case.
