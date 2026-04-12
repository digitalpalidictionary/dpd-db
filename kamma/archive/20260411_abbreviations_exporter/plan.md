# Plan: Integrate abbreviations_other into exporter pipeline

Issue: #77
Read spec.md in this directory first.

## Phase 1 — Database model & paths

- [x] 1.1 Read `db/models.py` lines around `abbrev` column (~line 224) and
      `abbrev_pack` / `abbrev_unpack` methods (~line 353–364). Understand the
      pack/unpack pattern exactly before writing new methods.

- [x] 1.2 Add to `Lookup` class in `db/models.py`:
      ```python
      abbrev_other: Mapped[str] = mapped_column(default="")

      def abbrev_other_pack(self, data: list[dict[str, str]]) -> None:
          self.abbrev_other = json.dumps(data, ensure_ascii=False)

      @property
      def abbrev_other_unpack(self) -> list[dict[str, str]]:
          if self.abbrev_other:
              return json.loads(self.abbrev_other)
          return []
      ```
      Note: use `@property` not `@cached_property` — cached_property stores in `__dict__`
      which SQLAlchemy can interfere with on mapped objects, causing stale data.

- [x] 1.3 Add to `tools/paths.py` alongside `abbreviations_tsv_path`:
      ```python
      self.abbreviations_other_tsv_path = base_dir / "shared_data/help/abbreviations_other.tsv"
      ```
      Find the exact line by searching for `abbreviations_tsv_path`.

- [x] 1.4 No migrations — just update the DB directly. Added `ensure_abbrev_other_column(g)`
      to `db/lookup/help_abbrev_add_to_lookup.py`: checks if column exists via
      `sa_inspect`, runs `ALTER TABLE lookup ADD COLUMN abbrev_other TEXT DEFAULT ''`
      if not. Called at the top of `main()` so it runs idempotently on every script run.
      DB version bumped to `minor = 4` in `tools/version.py`.

- [x] 1.5 Verification: `uv run python -c "from db.models import Lookup; print(Lookup.abbrev_other)"` exits without error.

## Phase 2 — Lookup table population

- [x] 2.1 Read `db/lookup/help_abbrev_add_to_lookup.py` in full to understand
      `add_abbreviations()` exactly (remove-then-add pattern, `is_another_value` guard).

- [x] 2.2 Add `add_abbreviations_other(g: GlobalVars)` function to
      `db/lookup/help_abbrev_add_to_lookup.py`:
      - Read `g.pth.abbreviations_other_tsv_path` with `csv.DictReader(delimiter="\t")`.
      - Group rows by `abbreviation` key into
        `dict[str, list[dict[str, str]]]` — each value is a list of
        `{"source": ..., "meaning": ..., "notes": ...}` dicts.
      - Remove/clear old `abbrev_other` entries (mirror the `add_abbreviations` cleanup).
      - For each group, upsert into `Lookup` with `abbrev_other_pack(grouped_list)`.
      - `db_session.commit()` at end.

- [x] 2.3 Call `add_abbreviations_other(g)` from `main()` after `add_abbreviations(g)`.

- [x] 2.4 Verification: syntax check with `uv run python -m py_compile
      db/lookup/help_abbrev_add_to_lookup.py`.

- [x] 2.5 Ask user to run `uv run python db/lookup/help_abbrev_add_to_lookup.py`
      and confirm no errors.

## Phase 3 — GoldenDict export

- [x] 3.1 Read `exporter/goldendict/export_help.py` `add_abbrev_html()` and
      `exporter/goldendict/data_classes.py` `AbbreviationsData` class in full.

- [x] 3.2 Read `exporter/goldendict/templates/help_abbrev.jinja` to understand
      the header/body pattern.

- [x] 3.3 Create `exporter/goldendict/templates/help_abbrev_other.jinja`:
      - `<h3 class="dpd">{{ d.abbreviation }}</h3>` heading
      - `<h4 class="dpd">Other Abbreviations</h4>` subheading
      - Table rows: `source | meaning (notes)` — no redundant "Abbreviation" row

- [x] 3.4 Add `AbbrevOtherData` dataclass to `exporter/goldendict/data_classes.py`
      (or inline in `export_help.py` — match whichever pattern `AbbreviationsData` uses).
      Fields: `abbreviation: str`, `rows: list[dict[str, str]]`, `header: str`.

- [x] 3.5 Add `add_abbrev_other_html(pth, jinja_env) -> list[DictEntry]` to
      `exporter/goldendict/export_help.py`:
      - Read TSV, group by `abbreviation`.
      - For each unique abbreviation, render the template, build `DictEntry(word=abbrev, ...)`.
      - Return the list.

- [x] 3.6 Call `add_abbrev_other_html()` from `generate_help_html()` and extend
      `help_data_list`.

- [x] 3.7 Verification: syntax check both changed files.

## Phase 4 — Webapp export

- [x] 4.1 Read `exporter/webapp/toolkit.py` lines around `abbrev` rendering
      (~128–136, ~329–336). Read the `abbreviations.html` and
      `abbreviations_summary.html` templates to understand their structure.

- [x] 4.2 Decide (based on template structure) whether to reuse existing templates
      with an extra `rows` variable or create `abbreviations_other.html` /
      `abbreviations_other_summary.html`. Simpler is better.

- [x] 4.3 Add rendering of `lookup_result.abbrev_other` in both locations in `toolkit.py`.
      Placed at the very end of each rendering block (last in summary list).
      Templates: `abbreviations_other.html` / `abbreviations_other_summary.html`.
      - Summary: `ka other abbreviations. ►` — matches grammar/variant summary pattern
      - Detail heading: `other abbreviations: ka` — matches `grammar: ka` / `variants: ka`
      - Table: source | meaning (notes) rows only, no redundant heading inside div
      - Paths added to `tools/paths.py`: `template_abbreviations_other_summary` /
        `template_abbreviations_other`

- [x] 4.4 Verification: syntax check `exporter/webapp/toolkit.py`.

## Phase 5 — End-to-end test (user runs)

- [x] 5.1 Ask user to run the full export pipeline and look up:
      - `ka` — should show grouped table with pts, cone, dpd_db sources
      - `AAWG` — cone-only entry
      - `Be` — general-only entry
      - `SLTP` — general-only entry
      - `abl` — DPD-only entry; must be unaffected
- [x] 5.2 Fix rendering issues:
      - Webapp heading changed to `other abbreviations: ka` pattern (matches grammar/variant)
      - Summary changed to `ka other abbreviations. ►` (last in summary list)
      - GoldenDict template rewritten to match `help_abbrev.jinja` structure exactly
      - `abbrev_other` moved to last in both webapp rendering blocks and GoldenDict pipeline
      - `@cached_property` → `@property` to avoid SQLAlchemy `__dict__` interference
      - Webapp dot-search fix: query now matches both `q` and `q + "."` via `or_()`,
        so `jap` / `Jap` / `jap.` all resolve to `Jap.` in the lookup table

## Phase 6 — Cleanup

- [x] 6.1 `pos='abbrev'` entries deleted from DB manually by user.
      `scripts/extractor/compile_abbreviations_other.py` to be deleted — no more
      extraction. `abbreviations_other.tsv` is now the permanent master list.
- [x] 6.2 Updated `shared_data/help/abbreviations_other_README.md`: final counts
      (PTS 558, CPD 306, Cone 145, CST 57, General 23 = 1089 total), removed
      rebuild instructions, noted file is now edited directly.
- [x] 6.3 All tasks done.
