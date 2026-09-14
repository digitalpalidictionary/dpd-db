# Spec: Dhamma.gift short links

## Overview
The Dhamma.gift webadmin (Pavel K, email 2026-09-14) reports that the rebuilt
site resolves a sutta straight from the path — `https://dhamma.gift/mn1` — and a
word search the same way — `https://dhamma.gift/kacchapa`. He asked that DPD's
sutta-table links be switched to that form.

DPD currently emits the previous reader form, `https://f.dhamma.gift/read/?q=<SC>`,
set by thread `20260731_dhamma_gift_domain`. That thread is the reference for
scope: it names **three** surfaces that must change together, and this spec keeps
the same three.

## What it should do
Replace the reader link form everywhere DPD generates it:

- `https://f.dhamma.gift/read/?q=<SC_CODE>` → `https://dhamma.gift/<sc_code lowercased>`

Three surfaces (same list as `20260731_dhamma_gift_domain`):

1. **dpd-db webapp** — `db/models.py`, `SuttaInfo.dhamma_gift` cached_property.
   Rendered by `exporter/webapp/templates/dpd_headword.html` via `d.su.dhamma_gift`;
   no template edit needed.
2. **dpd-db GoldenDict exporter** — the *same* `db/models.py` property, rendered by
   `exporter/goldendict/templates/dpd_headword.jinja` via `d.su.dhamma_gift`;
   no template edit needed. It currently has **no test** asserting the link it
   renders — the fixture passes `dhamma_gift=None`.
3. **Flutter app** (sibling repo `../dpd-flutter-app`) —
   `lib/database/sutta_info_extensions.dart:69`, the `dhammaGift` getter, plus its
   test at `test/database/sutta_info_extensions_test.dart:22-26`.

## Verified facts
Established by reading the real sources, not assumed:

- **The new form serves real content.** `dhamma.gift` is a client-side SPA: every
  path returns HTTP 200 with byte-identical HTML, so status codes prove nothing.
  The page resolves the path against its own endpoint, `/api/text/<id>`, which
  returns the sutta's JSON (title + segments) or a 404 with
  `{"error":"Unknown sutta id: …"}`. All verification below went through that
  endpoint.
- **Titles match.** 70 `sc_code` values sampled across all 14 books were fetched
  from `/api/text/`; 64 returned a title matching the `sc_sutta` DPD stores, 4 were
  Dhammapada rows where DPD stores no name to compare against, 2 were the failures
  listed below. A nonsense id returns 404, so the matches are meaningful.
- **Range codes return the right sutta, not merely *a* sutta.** All 190 distinct
  hyphenated `sc_code` values were fetched and their titles compared the same way:
  109 matched the `sc_sutta` DPD stores, 79 are rows where DPD stores no name to
  compare against, **0 returned a different sutta**, and 2 were 404s — the same two
  named below (`DHP90-00`, `SN12.93-103`). No range code silently resolves to the
  wrong text.
- **`sc_code` is clean.** `sutta_info` holds 5115 rows: 5114 with a non-null,
  non-empty, uppercase `sc_code` carrying no whitespace or unusual characters, plus
  **1 row with an empty-string `sc_code`**, which both the Python `if self.sc_code:`
  and the Dart `_notEmpty` guards already send down the null branch. `.lower()` is
  sufficient; no quoting needed.
- **Three `sc_code` shapes have no text on the site**, covering 13 rows in all
  (pre-existing DPD data, not caused by this change; the site falls back to a
  search rather than an empty reader). Two of them, `DHP90-00` and `SN12.93-103`,
  are the two 404s in the range sweep above; `AN1` is the second failure in the
  70-code sample, whose other failure was `DHP90-00` again:
  - `DHP90-00` — a typo in DPD data; `dhp90-99` (Jīvakapañhavatthu) works. This
    also breaks that row's SuttaCentral and Buddha's Words links. Report only.
  - `AN1`–`AN11` (11 rows) — bare nipāta headings (`ekakanipātapāḷi`), not suttas.
  - `SN12.93-103` — a peyyāla block the site does not group that way.

## Assumptions & uncertainties
- The lowercase form is used because that is what the webadmin's own examples show
  (`/mn1`, `/kacchapa`); uppercase also resolves, so this is cosmetic consistency
  with DPD's other generated links.
- The webadmin asked about "the suttatable". His word-search form
  (`/kacchapa`) is noted but DPD generates no Dhamma.gift word-search link
  anywhere — swept, zero carriers — so nothing to change for it.

## Constraints
- Python: modern type hints, `pathlib.Path`, repo conventions.
- Dart: `flutter analyze` clean, existing style.
- Shared working tree: stage by explicit file list, never a directory or wildcard.

## How we'll know it's done
- `rg --hidden "f\.dhamma\.gift/read"` returns zero matches in `db/models.py`,
  `tests/`, and `../dpd-flutter-app/lib/` + `../dpd-flutter-app/test/`.
- A property-level test asserts the new form for plain, range and Khuddaka code
  shapes plus the `None` branch.
- A GoldenDict render test asserts the link row renders. Note honestly what this
  does and does not prove: that test feeds the template a stub URL, so it guards
  the template plumbing, **not** the link form. The form itself is guarded by the
  property-level test and by the webapp render test, which builds a real
  `SuttaInfo` and would fail on a revert.
- `uv run pytest tests/` passes; `flutter test` passes in the sibling repo.

## What's NOT included
Swept and deliberately excluded — each checked, not assumed:

- **`tbw_legacy`** (`db/models.py`, and the Dart `tbwLegacy` getter) — still on
  `f.dhamma.gift/bw/…`. That is the Buddha's Words mirror, a different service.
  User explicitly said "leave tbw" (2026-09-14).
- **`db/suttas/dv_catalogue_suttas.tsv`** — carries old-form URLs, but they are
  provably inert: the file is re-downloaded on every build from
  `dhamma-vinaya-connections/early-buddhist-connections` (see
  `db/suttas/dv_catalogue_suttas.py:19`, a different project from the webadmin's),
  and `get_dv_column_mapping()` imports only the `dv_*` columns, so the URL column
  never reaches the database or any renderer. Editing it would be overwritten and
  would change nothing. (The prior thread's weaker reason, "not ours to edit", was
  right by accident.)
- **`docs/newsletters.md:850`** — still on the *older* `find.dhamma.gift` host,
  but it is published newsletter history. Left as written.
- **`scripts/build/newsletter_processed.json`, `conductor/archive/**`,
  `kamma/archive/**`** — historical records of what was published or decided.
- **`resources/**`** (fdg_dpd, bw2, sc-data) — git submodules and vendored
  third-party content, confirmed in `.gitmodules`.

## Scope added mid-thread (2026-09-14)
The user decided that the forms in the webadmin's email are current and the docs
are simply stale, so two doc carriers moved from "report only" into scope:

- **`docs/integrations/dhamma_gift.md`** — the "Dhamma.Gift Read" bullet pointed at
  the legacy `read.php` reader; now points at a short-form sutta link.
- **`README.md:39`** — pointed at the older `find.dhamma.gift` host; now the bare
  domain.
