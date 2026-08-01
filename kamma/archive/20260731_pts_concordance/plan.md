# Plan: PTS references from the PTS↔CST concordance into sutta_info

Thread: `20260731_pts_concordance`

## Architecture Decisions
- Reuse the existing `dv_pts` column (minimal change); the concordance becomes the
  sole PTS source. The `dv_` prefix is now a legacy misnomer (noted in spec.md);
  rename is a follow-up, not this thread.
- Mirror the DV-catalogue enrichment pattern: a new
  `update_pts_concordance_in_db()` in `db/suttas/pts_concordance.py`, called from
  `suttas_update.py::main()` immediately after `update_dv_fields_in_db()`.
- Vendor the concordance as a converted TSV (`db/suttas/pts_concordance.tsv`),
  deterministically sorted by join key so regeneration produces no reorder diff.
  A converter script (`db/suttas/convert_pts_concordance.py`) reads the source XLSX
  on demand; the build reads only the TSV (offline, deterministic).
- **Join key (already measured — see spec.md "Measured facts"):**
  `(romn/{stem}.mul.xml, first paragraph number in the CST reference)`. 4,467 keys
  are written, 3,990 hit, 4,476 `sutta_info` rows populated vs 1,706 today
  (4,384 on exact keys, +92 via the range fallback added at review).
  No `dpd_code` fallback — measured worse (3,095 / 3,737 on the four nikāyas).
- **No disambiguation of multi-row keys.** 338 keys hit >1 row (vagga + first
  sutta); the PTS ref is written to all of them, matching today's DV behaviour, and
  the templates suppress PTS on vagga/saṃyutta rows anyway.
- **The 712 chapter-relative (`cN`) KN entries are skipped** and reported, not
  guessed at. Resolving them needs CST XML chapter structure — follow-up.
- **No skip guard** (revised at review): the step runs unconditionally. Guarding on
  `table_rebuilt` would have made the feature a no-op on every incremental run and
  left the old DV-format references in place — see spec.md.
- **Range `cst_paranum` fallback** (added at review): 121 rows store a paragraph
  range, so an exact-key miss retries on the start of the range (+92 rows).
- PTS keeps the concordance string verbatim, including the line number
  (`D i 1,7`), so every existing PTS ref changes appearance.
- The PTS template row moves out of the DV block into its own heading — required,
  because dropping `dv_pts` from `dv_exists` would otherwise leave 2,119 rows
  rendering a headingless PTS row at the tail of the BJT section.
- No live-DB mutation during the thread: verification uses synthetic test data and
  a `/tmp` copy of dpd.db. The user's real build applies the population later.

## Phase 1 — Converter + vendored TSV
Investigation is DONE — findings recorded in spec.md ("Measured facts"). No further
XLSX exploration or key selection is needed; go straight to the converter.

> Order deviation (2026-07-31): task **2.1** (`tools/paths.py`) was executed FIRST,
> before 1.1, because the converter writes to `pth.pts_concordance_tsv_path` and
> pyright fails on an attribute that does not exist yet.

> Duplicate-key rule (2026-07-31, found while writing the converter): 4,520 numeric
> keys collapse to **4,467 distinct keys** — 39 keys carry more than one collated
> entry, either `.item` sub-units sharing a paragraph (SN 12.82–12.93 all inside
> `s0302m:73`) or a single-para entry alongside a range starting at the same para
> (`s0401m:1` AN1.1 vs `s0401m:1-5` AN1.1-5). Tie-break by CST-ref form —
> `n` beats `a-b` beats `n.item` — then by sheet order. Rationale: a `sutta_info`
> row that starts at paragraph N is best described by the entry whose locus IS
> paragraph N, not by a sub-item inside it.

- [x] 1.1 Write `db/suttas/convert_pts_concordance.py`: download the XLSX from
      `https://github.com/jorgecaa/pts-vri-concordance/raw/main/PTS-CST_Concordance_of_the_Pali_Canon.xlsx`
      (or read a local path), read the `Concordance` sheet via pandas + openpyxl,
      filter to `Status == "Collated"`, parse `CST reference` into
      `(romn/{stem}.mul.xml, start-para)`, SKIP the `cN` chapter-relative forms, and
      write `db/suttas/pts_concordance.tsv` sorted by (file, int(start-para)).
      Columns: `cst_file`, `cst_paranum`, `pts_ref` (plus `nikaya`, `work`,
      `number`, `title` for human review of the vendored file).
  → verify: `uv run db/suttas/convert_pts_concordance.py` writes the TSV; report
    prints entries read 6,098 / collated 5,232 / chapter-form skipped 712 /
    join keys written 4,467 — and re-running produces a byte-identical file.
    DONE: all four counts as stated; md5 identical across three runs and across
    both input branches (downloaded XLSX and a local path passed as a bare
    positional argument).

- [x] 1.2 Coverage report against the live db (read-only): count how many join keys
      hit a `sutta_info` row, and classify misses as chapter-form / granularity
      (concordance itemizes what `sutta_info` groups) / no-such-file.
  → verify: matched `sutta_info` rows well above 1,706; miss classification totals
    reconcile with spec.md.
    DONE: 4,467 keys → **3,990 hit → 4,384 `sutta_info` rows** (2.6× today's
    1,706). 338 keys are multi-row. Misses 477 = 461 granularity + 16 no-such-file
    (all `romn/s0515m.mul.xml`, Nidd I — the only absent file whose entries are not
    already chapter-form). Full accounting: 6,098 read → 5,232 collated → 712
    chapter-form skipped → 4,520 numeric → 4,467 keys after the 53-entry
    duplicate-key collapse.

## Phase 2 — Population pipeline
- [x] 2.1 Add `self.pts_concordance_tsv_path = base_dir / "db/suttas/pts_concordance.tsv"`
      to `tools/paths.py` (alongside `dv_catalogue_suttas_tsv_path`, line ~67).
      Executed out of order, before 1.1 — see the note in Phase 1.
  → verify: `uv run ruff check tools/paths.py` and `uv run pyright tools/paths.py`
    clean.

- [x] 2.2 Create `db/suttas/pts_concordance.py::update_pts_concordance_in_db(pth,
      table_rebuilt=True) -> None`: return early unless `table_rebuilt`; load the
      TSV into `dict[tuple[str, str], str]`; query `SuttaInfo`, set `dv_pts` on
      every row whose `(cst_file, cst_paranum)` is present; commit; log
      matched/unmatched counts.
  → verify: `uv run ruff check` + `uv run pyright` on the new file clean.

- [x] 2.3 Stop DV supplying PTS: in `db/suttas/dv_catalogue_suttas.py::
      get_dv_column_mapping` delete `"pts": "dv_pts",` (line 142); in
      `db/models.py::SuttaInfo.dv_exists` remove the `self.dv_pts` term (line 1027).
  → verify: `uv run pytest tests/db/suttas/` passes (note: no existing test asserts
    the `pts` mapping, so this is a weak signal — rely on 3.1);
    `uv run ruff check` + `uv run pyright` on both files clean.

- [x] 2.4 Wire into `db/suttas/suttas_update.py::main`: call
      `update_pts_concordance_in_db(pth, table_rebuilt)` immediately after
      `update_dv_fields_in_db(pth, table_rebuilt)` (line 171). Update the import.
  → verify: `uv run pytest tests/db/suttas/test_suttas_update.py` passes;
    `uv run ruff check` + `uv run pyright` on the file clean.

- [x] 2.5 Move the PTS row in both templates
      (`exporter/webapp/templates/dpd_headword.html:733`,
      `exporter/goldendict/templates/dpd_headword.jinja:684`): relocate it above the
      `<!-- DV catalogue -->` block, keep it inside the
      `{% if not is_vagga and not is_samyutta %}` gate, and precede it with its own
      `{% if d.su.dv_pts %}` heading row ("Pali Text Society") following the
      existing heading pattern. Keep both templates in step.
  → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py` passes;
    render one headword with PTS + no other DV data and confirm the PTS row sits
    under its own heading, and one with full DV data to confirm the DV heading is
    unaffected.

## Phase 3 — Tests + repo-wide verification
- [x] 3.1 Add `tests/db/suttas/test_pts_concordance.py`: synthetic TSV + `SuttaInfo`
      rows on a temp DB; assert `dv_pts` set for matched rows, unmatched rows left
      untouched, the multi-row key case (vagga + first sutta BOTH written), and the
      `table_rebuilt=False` early return. Add a converter test that a `cN`
      chapter-form row is skipped and a `a-b` range row keys on its start para.
  → verify: `uv run pytest tests/db/suttas/test_pts_concordance.py` passes.

- [x] 3.2 Run the full sutta suite + linters/typecheckers on every touched file.
  → verify: `uv run pytest tests/db/suttas/` passes; `uv run ruff check <files>`;
    `uv run ruff format <files>`; `uv run pyright <files>`; `just typecheck` — all
    clean.

- [x] 3.3 End-to-end smoke on a THROWAWAY copy: `cp dpd.db /tmp/dpd_pts_test.db`,
      run `update_pts_concordance_in_db` against the copy, then sqlite3-check:
      DN1 = `D i 1,7`, DN2 = `D i 47,3`, populated-row count ≈ 4,384, and that only
      `AN3.48` / `AN3.63` lost a previously-held PTS. Do NOT touch the live dpd.db.
      DONE: DN1 `D i 1,7`, DN2 `D i 47,3`, MN1 `M i 1,3`, vagga DN1-13 `D i 1,7`;
      **4,384 rows populated** (from 1,706); lost exactly `AN3.48`, `AN3.63`; live
      `dpd.db` md5 unchanged. The copy was blanked of `dv_pts` first to emulate the
      real build, where sutta_info is dropped and recreated before enrichment.
  → verify: those checks pass on `/tmp/dpd_pts_test.db`; live dpd.db untouched.

## Finalize
- [x] Review (spawn independent subagent if available; re-read spec/plan, inspect
      diff, run tests, check dead code, report findings) and fix blocking/major.
      DONE: see review.md — 7 findings, 4 fixed (1 blocker: the skip guard made the
      feature a no-op on incremental runs), 3 accepted with written rationale.
- [x] Finalize: review.md written; `kamma/tech.md` Resources updated with the
      concordance source, the unguarded-step rationale and the chapter-form gap;
      `kamma/project.md` needed no change (generic). Thread archived. Commit message
      + files-changed list handed to the user. (No GitHub issue referenced.)
- [x] Follow-ups recorded in kamma/tech.md and spec.md: chapter-relative KN
      entries (712), the `dv_pts` → `pts_ref` rename, and a possible sweep of the
      blanket `except Exception` shared by both enrichment steps (review finding 2).
