# Server rebuild config — what runs, what no-ops, what must be skipped

The nightly maintenance window rebuilds the server's scratch db by running
`scripts/build/db_rebuild_from_tsv.py` then the **lean** rebuild
`scripts/server/generate_components_server.py` (invoked by
`maintenance_window.py`) under the config in `config_server.template`.

The lean script runs only the steps that populate tables/columns the
interactive gui2 app actually reads during data entry — a strict, reordered
subset of `scripts/bash/generate_components.py`. Everything that exists solely
for exporters, release artifacts, or db columns gui2 never queries is dropped,
cutting the rebuild substantially (local baseline: full ≈ 11 min; the dropped
transliterate/grammar/epd/sutta/frequency steps are ≈ 220s of that, and the
lean db also skips the assets that made the full pytest gate fail).

Prerequisites on the server: the **Go toolchain** (the deconstructor `go run`
step) and the `resources/sc-data` + `resources/dpd_submodules` submodules. No
audio hardware, no Anki, no GPU, no outbound network beyond `git fetch/pull`.

## Lean rebuild — kept vs dropped (verified against gui2 source, 2026-07-19)

gui2 reads only: `dpd_headwords`/`dpd_roots` (core), `lookup.{lookup_key,
headwords, deconstructor, spelling}`, `inflection_templates.pattern` +
`dpd_headwords.inflections/inflections_html`, and the `family_root/word/compound`
name columns. `spelling` feeds pass2pre filtering (kept despite gui2 not reading
the column directly).

**KEPT** (in `generate_components_server.py`): logo, version,
create_inflection_templates, generate_inflection_tables, root_has_verb,
sanskrit_root_families, family_root/word/compound/set/idiom, deconstructor
`go run` + deconstructor_output_add_to_db, api_ca_eva_iti_iva_hi,
inflections_to_headwords, lookup/see, lookup/spelling_mistakes.

**DROPPED** (maintainer-confirmed unused by gui2 data entry, or exporter-only):
`uv run pytest tests/` (see below), config_uposatha_day, families_to_json,
anki ×2, variants, transliterate_inflections, transliterate_lookup_table,
suttas_update, suttas_to_lookup, grammar_to_lookup, help_abbrev_add_to_lookup,
epd_to_lookup, ebt_counter, frequency `go run`, generate_search_index, audio ×3,
dealbreakers.

The table below documents the FULL `generate_components.py` for reference (what
each command does and why it is or isn't in the lean set).

## Full generate_components.py per-command reference

| # | Command | Gate | On the server |
|---|---------|------|---------------|
| 1 | `uv run pytest tests/` | none (always) | ~34s locally, but **hard-fails on a headless server** — see below |
| 2 | tools/logo.py | always | runs (trivial) |
| 3 | tools/version.py | always | runs |
| 4 | scripts/build/config_uposatha_day.py | always | runs (may flip `[exporter] upload_audio_db` — harmless, audio is off) |
| 5 | db/inflections/create_inflection_templates.py | always | runs |
| 6 | db/inflections/generate_inflection_tables.py | `[regenerate] db_rebuild` | full regen (db_rebuild = yes) |
| 7 | scripts/build/root_has_verb_updater.py | always | runs |
| 8 | scripts/build/sanskrit_root_families_updater.py | always | runs |
| 9–13 | db/families/family_*.py | `[regenerate] db_rebuild` OR exporter make_* | run (db_rebuild = yes) |
| 14 | scripts/build/families_to_json.py | always | runs |
| 15 | exporter/anki/anki_updater.py | `[anki] update` | **no-op** (update = no) |
| 16 | exporter/anki/anki_apkg_exporter.py | `[anki] update` | **no-op** (update = no) |
| 17 | db/variants/main.py | `[exporter] make_variants` | no-op (make_variants = no) |
| 18 | `go run go_modules/deconstructor/main.go` | none (Go) | runs — **requires Go** |
| 19 | scripts/build/deconstructor_output_add_to_db.py | `[generate] deconstructor` | runs (deconstructor = yes; consumes #18 output) |
| 20 | scripts/build/api_ca_eva_iti_iva_hi.py | always | runs |
| 21 | db/inflections/transliterate_inflections.py | `[regenerate] db_rebuild` | full (db_rebuild = yes) |
| 22 | db/inflections/inflections_to_headwords.py | `[generate] inflections_to_headwords` | runs (= yes) |
| 23 | db/suttas/suttas_update.py | `[generate] suttas` | runs (= yes) |
| 24 | db/suttas/suttas_to_lookup.py | `[generate] suttas` | runs (= yes) |
| 25 | db/grammar/grammar_to_lookup.py | `[generate] grammar` | runs (= yes) |
| 26 | db/lookup/see.py | always | runs |
| 27 | db/lookup/spelling_mistakes.py | always | runs |
| 28 | db/lookup/transliterate_lookup_table.py | `[regenerate] db_rebuild` | full (db_rebuild = yes) |
| 29 | db/lookup/help_abbrev_add_to_lookup.py | always | runs |
| 30 | scripts/build/ebt_counter.py | always | runs |
| 31 | `go run go_modules/frequency/main.go` | none (Go) | runs — **requires Go** |
| 32 | db/epd/epd_to_lookup.py | `[generate] epd` | runs (= yes) |
| 33 | exporter/webapp/generate_search_index.py | `[generate] search_index` | no-op (= no; no webapp on this server) |
| 34 | audio/bhashini/generate_dpd.py | `[exporter] make_audio_db` | **no-op** (make_audio_db = no; would need network + Bhashini key) |
| 35 | audio/db_create.py | `[exporter] make_audio_db` | **no-op** (make_audio_db = no; would need local audio files) |
| 36 | audio/db_release_upload.py | `[exporter] upload_audio_db` | **no-op** (upload_audio_db = no; would need GitHub token + network) |
| 37 | scripts/build/dealbreakers.py | always | runs |

Hard blockers if their flags were left on: #34/#36 (network + secrets), #15/#16
(Anki + local collection). The template disables all of them. #18/#31 need Go —
install it on the server (spec point 7).

## No pytest in the server rebuild (resolved 2026-07-19)

The lean server rebuild does **not** run `uv run pytest tests/`, for two reasons:

1. The lean db intentionally omits data (grammar/epd/sutta/frequency lookup
   rows) that parts of the suite assert on, so a full run would fail on the
   missing data.
2. Even the full suite hard-fails on a headless server: `tests/audio/
   test_audio_query.py` (and the two `tests/exporter/webapp/test_webapp_*`
   files) call `sys.exit(1)` at import when a generated asset is missing, and
   the 1.2 GB audio db is absent on the audio-disabled server — this crashes
   pytest collection and would abort the rebuild.

The pulled code is already CI-tested on main before it reaches the server, and
the post-rebuild gate is the maintenance window's **health check**
(`maintenance_window.py` → headword/lookup row-count bounds). No change to the
shared `scripts/bash/generate_components.py`; the lean list lives in its own
`scripts/server/generate_components_server.py`.
