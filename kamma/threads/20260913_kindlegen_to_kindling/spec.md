# Spec: trial replacement of kindlegen with kindling

GitHub issue: none (reference #157 refactoring umbrella in any commit; do NOT close).
Branch: `kindling-trial` — a throwaway branch. The deliverable is two `.mobi`
files for on-device comparison plus the code that produced the new one. Merge
or discard is the user's call after testing on a real Kindle.

Prior research: `research.md` in this thread. Read it first — it carries the
measured numbers and the open questions this thread exists to answer.

## Overview

`exporter/kindle/kindle_exporter.py::make_mobi()` currently compiles the
rendered EPUB to a Kindle dictionary with a committed 2014 32-bit
`exporter/kindle/kindlegen` binary on Linux, and with Calibre's
`ebook-convert` on macOS — the latter producing a MOBI with **no orthographic
index at all**, i.e. not a dictionary.

This thread swaps that for `kindling-cli` (MIT, Rust, pinned v0.45.1) on every
platform, and produces both the old and the new artefact from **one identical
render** so the user can sideload both and compare lookup behaviour on real
hardware.

**There are two questions of equal weight, not one.** The device question
(§"the one question" below) decides whether kindling works at all. The CI
question decides whether it is usable: `.github/workflows/draft_release.yml` is
where the shipped dictionary is actually built, so *how the runner obtains the
binary* is the heart of this thread, not an implementation detail to settle
later. The old compiler was a git-tracked blob and therefore always present; the
new one is not a Python package, so `uv add` cannot supply it — verified, it is
published only to crates.io (`kindling-mobi`), with no PyPI release and no
Python packaging in the repo.

The one question that decides everything (research.md §8.1): does a real Kindle
resolve an inflected Pāḷi form from a kindling-built DPD, given kindling writes
no separate inflection INDX and instead puts all 423,001 forms in the flat orth
index? Nothing here can answer it; the build exists to let the user answer it.

## Verified facts this spec rests on

All read from the repo or measured by running the tools, not from memory.

- `make_mobi()` branches on `platform.system()`: `Darwin` → `ebook-convert` (or
  a red no-op if Calibre is absent), everything else → `pth.kindlegen_path`.
- `pth.kindlegen_path` = `exporter/kindle/kindlegen`, an
  `ELF 32-bit LSB executable, Intel 80386`, 28,673,912 bytes, git-**tracked**.
- kindlegen infers its output name from the input; kindling requires `-o`.
  `pth.dpd_mobi_path` = `exporter/share/dpd-kindle.mobi` already exists and is
  the name kindlegen happens to produce from `dpd-kindle.epub`.
- Feeding kindling the **`.epub`** embeds it as an 18.9 MB `SRCS` record and
  trips its own P0 readback check (>16 MB record → "Unable to Open Item" on
  device); it refuses to ship the file. Feeding it the **`content.opf`** skips
  source embedding entirely ("EPUB source embedding skipped for non-EPUB
  input"). **Feed the OPF.**
- kindling's KDP pre-flight aborts on our OPF with exactly two errors, both
  caused by `ebook_content_opf.jinja` declaring `<package version="3.0">` while
  carrying OPF-2 `<x-metadata>` dictionary tags:
  - `R15.e1 / OPF_078` — no content document carries `epub:type="dictionary"`.
  - `R15.e2 / OPF_079` — metadata lacks `<dc:type>dictionary</dc:type>`.
- `ebook_letter.jinja` already declares `xmlns:epub="http://www.idpf.org/2007/ops"`,
  so `epub:type` needs no new namespace.
- `--fold-accents` (the advertised kindlegen-parity flag) **breaks Pāḷi**:
  measured, `thāna` and `ṭhana` stop resolving. Case folding works without it.
  Do not pass it.
- Generated output is gitignored: `content.opf`, `Text/[0-9]*_*.xhtml`,
  `Text/abbreviations.xhtml`, `Text/epd_*.xhtml`, and all of `exporter/share/`.
  `Text/titlepage.xhtml` is **tracked yet regenerated on every run** (it embeds
  `datetime.now()`), so a render dirties one tracked file. Pre-existing
  behaviour, not introduced here.
- `config.ini` has `[exporter] make_ebook = no`, so `main()` short-circuits.
  Global rules forbid editing `.ini` files, so the test builds run through a
  scratchpad harness that calls the render functions directly — the same
  approach the archived `20260706_kindle_optimize` thread used.
- The three `--script deva/sinhala/thai` variants never call `make_mobi()`;
  they are untouched by this thread.

## What it should do

1. **One `make_mobi()`, one tool, every platform.** Delete the
   `platform.system()` branch and the Calibre fallback. Invoke
   `kindling-cli build <content.opf> -o <pth.dpd_mobi_path>`, stream its output
   through `pr.white()` as today, and fail loudly — not silently — when the
   binary is missing or the build returns non-zero. The current code ignores
   the return code entirely; the new tool uses exit status meaningfully
   (it exits 1 and refuses to write a corrupt file), so that signal must be
   honoured.
2. **Make the OPF a valid EPUB3 dictionary** so the 116-point pre-flight runs
   for real instead of being bypassed with `--no-validate`:
   - `<dc:type>dictionary</dc:type>` in `ebook_content_opf.jinja` metadata;
   - `epub:type="dictionary"` on the `<body>` in `ebook_letter.jinja` **and**
     `ebook_epd_letter.jinja` (drift, recorded 2026-09-13: the spec originally
     named only the first. `OPF_078` needs just one such document, so the EPD
     edit was not required — but both files carry real `<idx:entry>` content,
     so marking only one would have been the inconsistent choice. Kept, and
     recorded rather than reverted);
   - a `<guide><reference type="index" .../></guide>` pointing at the first
     Pāḷi letter file. This is warning `R15.7`, not an error, but the validator
     states older firmware uses it to locate the dictionary's entry section —
     which is exactly the behaviour under test, so it is in scope rather than
     deferred.
   Everything else the validator reports stays as-is: the missing logical TOC
   and the ~30 `properties="remote-resources"` warnings are pre-existing,
   advisory, and out of scope.
3. **Binary acquisition — the central question, decided by measurement on a
   real GitHub runner.** `pth.kindling_path` = `exporter/kindle/kindling-cli`.
   `tools/configger.py` sets `make_ebook = yes` in the `github_release` profile,
   so `draft_release.yml` runs this exporter on every release. If the runner
   cannot produce the binary, `make_mobi` raises and takes the whole exporter
   job down — Kobo, TXT, tarball and every upload step with it.

   Three candidates, to be measured on a real `ubuntu-latest` runner rather
   than argued about:

   | Option | What CI does | Repo cost |
   |---|---|---|
   | **A** commit the binary | nothing — it is in the checkout | +17 MB tracked, forever, one platform |
   | **B** download the release asset | one `curl` + checksum | 0 |
   | **C** `cargo install kindling-mobi` | compile from source | 0, but needs a Rust toolchain |

   Local reference figures (22 cores, load 2.25): C cold = **190.9 s**, 1.5 GB
   peak RSS, 160 MB of cargo cache; C warm = instant. A GitHub runner has ~4
   cores, so C will be materially slower there — which is exactly why this is
   measured on the runner and not extrapolated from this machine. The
   source-built binary is 17,031,152 B against the released 17,170,456 B; both
   report `kindling 0.45.1` and both build the dictionary.

   The decision criterion is release-job wall clock and failure modes, not
   elegance.

   **Measured and decided (run 34754250894): option B.** Download = 0.607 s,
   `cargo install` = 200.8 s, checkout of the whole repo = 18.5 s. B is wired
   into `draft_release.yml`; the binary stays gitignored. `exporter/kindle/kindlegen` is **not** deleted in this thread:
   the old artefact must stay buildable for as long as the comparison is live.
4. **Retire `exporter/kindle/kindlegen`.** Delete the 28,673,912 B tracked
   i386 binary and its now-unused `ProjectPaths.kindlegen_path`. Safe on three
   independent counts, each verified rather than assumed:
   - the user's own archive holds it at
     `2_Resources/Software/Linux/Kindlegen/kindlegen.tar.gz`, and the binary
     inside that tarball is **byte-identical** to the repo copy
     (sha256 `b8b0f0ab…461a69` both sides);
   - git history retains it regardless — `git checkout main --
     exporter/kindle/kindlegen` restores it at any time;
   - the comparison artefact `dpd-kindle-kindlegen.mobi` is **already built**,
     so the device test does not need the binary to still be present.

   The only live reference was the path constant; the `kindlegen.s3.amazonaws.com`
   strings in the jinja templates are the `idx:`/`mbp:` XML namespace URIs that
   the dictionary format requires and must **not** be touched.

5. **Build both artefacts from one render** and hand the user two clearly named
   files plus install instructions.
6. **A lookup regression check** over a fixed list of inflected Pāḷi forms,
   using `kindling-cli lookup`. Build-side only; it simulates the firmware's
   orth search and is explicitly "not a hardware oracle". It is the first
   automated correctness check this exporter has ever had, so it belongs in the
   thread even though it cannot settle the device question.

## Deliverables for the user to test

Both built from the same render, same data, same templates:

| File | Built by | Expected |
|---|---|---|
| `dpd-kindle-kindlegen.mobi` | `exporter/kindle/kindlegen` (today's tool) | ~75 MB |
| `dpd-kindle-kindling.mobi` | `kindling-cli` v0.45.1 | ~40 MB |

Sizes throughout this thread are MB (10^6 bytes).

Plus a short test protocol naming the exact words to tap.

## Assumptions & uncertainties

- The on-disk `exporter/kindle/epub/` render is from 2026-07-28; this thread
  re-renders so the template changes take effect. Data drift between then and
  now is irrelevant to a compiler comparison as long as **both** artefacts come
  from the same render — which is the whole point of building them together.
- Adding `epub:type="dictionary"` and `<dc:type>` changes bytes kindlegen also
  reads. kindlegen ignores unknown `epub:*` attributes, but this is an
  assumption about a black box, not a verified fact. If the kindlegen build
  regresses, the fallback is to build the old artefact from the pre-change
  template and say so.
- Whether the two errors are the *only* thing blocking validation is verified
  for the current data. A different data state could surface new findings; the
  build must not silently paper over them with `--no-validate`.
- Timings in research.md are n=1 on a loaded interactive machine. Ratios, not
  absolutes.
- kindling is v0.**45**.1, five months old, one maintainer. The version is
  pinned deliberately.

## Constraints

- No commits, no pushes, no GitHub writes. The user commits at the end.
- **Shared working tree.** Other kamma threads may be editing this repo right
  now. Never `git stash`, `git checkout -- <path>`, `git restore`, or
  `git reset --hard`. Stage nothing. Re-read files from disk immediately before
  editing.
- Do not edit `config.ini` (global rule). The render harness bypasses the
  `make_ebook` gate from outside.
- Harness lives in the session scratchpad, not in the repo.
- `ruff check --fix` → `ruff format` → `pyright` → related `pytest` on every
  touched file. `just typecheck` before handoff.
- Do not touch `exporter/kindle/kindlegen` or the `--script` code paths.

## How we'll know it's done

- Both `.mobi` files exist, are the expected order of magnitude, and were
  produced from one render.
- The kindling build completes **with validation on** (no `--no-validate`) and
  reports 0 P0 errors on its own readback check.
- The lookup check resolves every word in the fixed list.
- `make_mobi()` has no `platform` branch, no Calibre reference, and a non-zero
  exit from the compiler surfaces as an error rather than a green run.
- Full `tests/` suite run, with pre-existing failures identified as such
  (not fixed, not weakened) and named.
- A test protocol handed to the user in plain English.

## What's not included

- Purging `kindlegen` from git *history* (the working-tree deletion is in
  scope; rewriting history is not, and is unnecessary — see point 4).
- The StarDict / EPUB3 / AZW3 / `--headwords-only` capabilities from
  research.md §5 — all real, all separate follow-ups, none needed to answer the
  question this thread asks.
- The missing logical TOC and `remote-resources` validator warnings.
- The `--script` transliteration variants.
- Any change to `docs/install/kindle.md` — the user-facing install steps are
  identical either way.

---

# Part 2: the dictionary structure (v10)

Added 2026-09-13 after device testing. Part 1 (above) swaps the compiler; this
part fixes a correctness bug that predates kindling and would affect any Kindle
build. The two are separable but ship together on this branch.

## The bug

`ebook_entry.jinja` labels every entry `<idx:orth value="{{ lemma_clean }}">`.
**One index term reaches exactly one entry** — verified three ways, not assumed:
3 entries sharing an `<idx:iform>` resolve to the first only; one entry carrying
two different `<idx:orth>` labels indexes only the first; 13 entries labelled
`uttara` leave 12 unreachable. Measured on the shipped build: **15,124 of
189,505 entries (8.0%) cannot be reached**, worst on the commonest words —
`dhamma` 16 entries, `vaṇṇa` 15, `attha` 13, `ṭhāna` 11.

## What it should do

Restructure so the entry a form points at carries every sense that form has,
per `Lookup.headwords_unpack` — the database's own form→headword index, which is
the authoritative answer and is already used by `exporter/sutta_central`.

1. **One full entry per headword**, labelled `lemma_1` (unique by construction),
   carrying summary + grammar table + examples **once**. No duplication.
2. **One entry per ambiguous form**, listing exactly the headwords the lookup
   table names, each **linking** to its full entry.
3. **Unambiguous forms** stay plain `<idx:iform>` aliases on their owner's full
   entry, so they open the detail directly.
4. **Contested labels** — a form entry and a headword entry wanting the same
   string (4,913 cases, e.g. `acca`) — merge into one entry carrying both the
   list and that headword's detail, keeping its anchor.
5. **All three scripts recognised.** Devanāgarī, Sinhala and Thai spellings of
   each form attach to that form's entry as aliases, from `Lookup`'s own
   `devanagari` / `sinhala` / `thai` columns (populated on ~100% of rows). One
   dictionary recognises all four scripts.
6. **Retire the `--script` flag** and its per-script epubs. Point 5 makes one
   file recognise every script, so separate `dpd-kindle-deva/sinhala/thai.epub`
   builds are obsolete. Nothing references them — no justfile recipe, no CI
   step, no docs (swept).

## Measured on the accepted prototype

```
172,024 entries -> 172,024 distinct labels   LOST 0   (was 15,124)
1,380,565 unique lookup terms
63,914,130 bytes            (today's kindlegen build: 75.2 MB)
16 P0 checks passed, 0 P1 warnings; all cross-references resolved
22/22 lookups, all three scripts
```

Against the lookup table: `gacchati` → `gacchati 1` + `gacchati 2`
(ids 24043, 24044); `gacchanta` → `gacchanta 1` + `gacchanta 2`;
`uttaro` → 11 senses; `vitthāra` → 3.

## Accepted limitation

Device-tested by the user: the sense links are **not clickable inside the
lookup popup**, but **are clickable when the dictionary is opened as a book**.
Accepted as a useful compromise — the popup gives the correct complete list with
summaries; full detail is one step away. Do not attempt to work around this;
it is firmware behaviour.

## Constraints

- Reuse `KindleData` for entry bodies; render each headword's body **once**.
- `Lookup.headwords_unpack` is the only authority for which senses a form shows.
  Never re-derive it from inflection lists.
- Entry bodies must not duplicate detail per form — that reached 118 MB and was
  rejected.
- Same gates as Part 1: ruff, pyright, `just typecheck`, full pytest.

## What's not included

- Making popup links clickable (firmware, not ours).
- The EPD, abbreviations, titlepage, zip and `make_mobi` stages — unchanged.
- Frequency-targeted detail (v6) — superseded by v10 storing detail once.

---

# Part 3: a test build workflow for users

Added 2026-09-13. The user wants testers to get a Kindle dictionary without
building anything locally, before this branch is merged.

## What it should do

A workflow that skips the multi-hour database build entirely by **downloading
the published `dpd.db.tar.xz`** (169 MB, an asset on every release), then
running only the Kindle exporter.

1. Check out the branch under test, **with submodules** — the exporter needs the
   CST and SuttaCentral text sets from `resources/` to limit the word set.
2. `uv sync --all-groups` (bare `uv sync` strips groups).
3. Download `dpd.db.tar.xz` from the **latest release** via `gh release
   download`, extract to `dpd.db`.
4. Apply the existing `scripts/build/config_github_release.py` profile, which
   already sets `make_ebook = yes`. `config.ini` is untracked, so CI generates
   it — the same way `draft_release.yml` does.
5. Fetch the pinned `kindling-cli` release asset and verify its SHA-256, exactly
   as the Install kindling step in `draft_release.yml` does.
6. Run `exporter/kindle/kindle_exporter.py`.
7. Publish `dpd-kindle.mobi` and `dpd-kindle.epub` as a **prerelease** on a
   fixed tag, so testers can download them from a plain link without a GitHub
   login — a workflow artifact would require one.

## Triggers

`workflow_dispatch` for normal use, **plus** a `push` trigger scoped to the
branch. A `workflow_dispatch`-only workflow is not offered in the Actions UI
until it exists on the default branch, so without the push trigger this could
not be proven before merge. The push trigger is to be removed at merge; it is
marked in the file.

## Constraints

- Must not build the database, and must not run the other exporters.
- Must not touch the real release tags used by `draft_release.yml`; the
  prerelease uses its own fixed tag and is marked prerelease.
- Fail loudly: the exporter now raises on a missing or non-executable kindling
  binary and on a non-zero compile, so a broken build cannot publish silently.

## How we'll know it's done

The workflow runs green on a real runner, the prerelease carries a `.mobi` of
the expected order of magnitude, and the run log shows 0 validation errors.

## What's not included

- Any change to `draft_release.yml`'s own asset list or schedule.
- Building the db from source in this workflow.
- Notifying testers (the user handles that).
