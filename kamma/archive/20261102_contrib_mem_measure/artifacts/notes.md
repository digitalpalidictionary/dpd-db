# Phase 0 notes (2026-11-02)

## get_db_session import sites
Original: `db/db_helpers.py:88`. Engines are cached by resolved path (`db/db_helpers.py:21-23`, `_get_cached_engine`).
Sites that bind the name at import (`from db.db_helpers import get_db_session`) and are reachable from the probe's points:
- `gui2/database_manager.py:14` (use at `:143` in `__init__`, and `:827` in the detector worker thread).
- `tools/bold_definitions_search.py:9` (use at `:18`).
- `tools/speech_marks.py:9` (use at `:78`). Not built by any point; patched anyway by the `sys.modules` walk.
- Lazy import inside a function: `gui2/dpd_fields.py:1040` (use `:1044`). Binds at call time from `db.db_helpers`, so patching `db.db_helpers.get_db_session` covers it.
- UI-only importers (not built by the probe, but imported by `gui2.main`): `gui2/spelling_find_replace_view.py:6`, `gui2/sandhi_find_replace_view.py:6`. The `sys.modules` walk patches them too.
- Other `gui2/` importers not reachable from `gui2.main` top-level: `gui2/utilities/*`, `gui2/pass2x/*`.
The probe walks `sys.modules` after the imports and replaces every module attribute `get_db_session` that `is` the original function, plus `db.db_helpers.get_db_session`.

## Import-time side effects
Method: AST scan of the top-level statements of `gui2/*.py`, `gui2/*/*.py`, `tools/*.py`, `db/*.py` for calls outside `def`/`class` (scratchpad script, nothing run from the repo).
Result: none that start a thread, write a file, call the network or start a server. Items found and judged harmless:
- `tools/configger.py:12-13` reads `config.ini` at import (read only; the probe never prints values).
- `tools/paths.py` `ProjectPaths()` is built at import in several modules (`tools/cst_sc_text_sets.py:20`, `tools/cache_load.py:14`, `tools/bjt.py:40`, `tools/exporter_functions.py:14`, `tools/cst_book_translator.py:27`). Path arithmetic only.
- `tools/cst_book_translator.py:77` runs `_load()` at import (reads a data file, builds dicts). Counted in the `imports` point.
- `gui2/books.py:78` builds `sutta_central_books` at import; each `SuttaCentralSource.__init__` lists its folders (`gui2/books.py:24-30` calling `make_file_list` at `:37`, `rglob`). Counted in `imports`. It does NOT load JSON (`segment_dict` is a `cached_property`, `gui2/books.py:42-43`; `word_dict` at `:68-69`).
- `gui2/main.py:670` `_session_lock = threading.Lock()`; `gui2/main.py:736` `ft.run(main)` is under `if __name__ == "__main__"`, so importing does not start the server.
- `db/db_helpers.py:23` `os.getpid()`.
- `tools/logo.py:4` prints a banner when imported, but its docstring says it is run directly by build scripts and `rg` finds no importer in `gui2/` or `tools/`.

## PYTHONPATH
Not needed on the laptop: `.venv/lib/python*/site-packages/_editable_impl_dpd_db.pth` lists the repo root, so `gui2`, `tools` and `db` import from any script path. `ProjectPaths` uses the cwd, so every command runs from the repo root. The plan keeps `PYTHONPATH=.` anyway (harmless); on the server it is kept because the venv there was not checked.

## AI providers (constructors, no config.ini opened)
`AIManager.__init__` is `tools/ai_manager.py:58`. It always builds `ClaudeManager` (`:70`) and `GptManager` (`:73`), builds each OpenAI-compatible provider only when `config_read("apis", name)` is set (`:77`), builds `GeminiManager` only when the gemini key is set (`:83`), and starts the `agy` probe thread only when `shutil.which("agy")` finds it (`:89`).
- ClaudeManager: `tools/ai_claude_manager.py:12` `shutil.which("claude")`. No network, no subprocess, no key.
- GptManager: `tools/ai_gpt_manager.py:13` `shutil.which("codex")`. No network, no subprocess, no key.
- OpenAiCompatManager: `tools/ai_openai_compat.py:180` reads a key with `config_read`; builds a header dict (`:187`). No network, no subprocess.
- GeminiManager: `tools/ai_gemini_manager.py:19` reads a key; `:27` `genai.Client(api_key=...)` builds a client object. No request is sent at construction (read of `__init__`; not proven by a run).
- Antigravity (`agy`): starts a thread that runs a subprocess auth check (`tools/ai_manager.py:89-96`, `_probe_antigravity_cli`). The probe removes `agy` from PATH so this thread never starts.

IMPORT_ONLY: (empty)

The probe sets no API keys itself. Which providers get built depends on the keys in the laptop `config.ini`; the row's `meta` records the provider names built (names only).

## Cap tool on the laptop
`systemd-run --user --scope -q -p MemoryMax=100M -p MemorySwapMax=0 true` -> `exit=0`.
`df -h /tmp | tail -1` -> `/dev/nvme0n1p2  938G  829G   61G  94% /` (61 GB free; the copy needs about 2.2 GB).
`dpd.db` is 2,301,067,264 bytes. `sqlite3` is at `/usr/bin/sqlite3`. `uv` is at `/home/bodhirasa/.local/bin/uv`.

## Phase check: points that cannot be built alone
none. Two facts to carry into the probe:
- `AIManager()` reads keys from `config.ini` through `config_read`; a laptop with keys builds more providers than the server. Recorded in `meta`.
- `CustomSpellChecker` is a singleton (`tools/spelling.py:28`): in the staircase, build it once, and give it an explicit temp dictionary path (`tools/spelling.py:35`).
