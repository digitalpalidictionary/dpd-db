# Spec: ati- prefix words → compounds, not root derivations

**Thread:** 20260823_ati_prefix_to_compound
**Created:** 2026-08-23
**All counts below verified against the live `dpd.db` on 2026-08-23.**

## Problem

`ati` is a prefix that attaches to an already-existing word to intensify it
(`ati` + `bahu` → `atibahu` "too much"). In DPD such a word is recorded as a
**compound** — `compound_type = kammadhāraya`, `family_compound = ati <base>`,
`construction = ati + <base>` — with the root fields left empty, even when the
base word is itself root-derived.

That is the settled convention. `atijiṇṇa`, `atibhutta`, `atidhāta`,
`atidosa`, `atidāruṇa`, `atigambhīra`, `atijighacchā`, `atibahu`, `atichatta`,
`atitaruṇa` and ~200 more all follow it, and their bases (`jiṇṇa`, `bhutta`,
`dhāta`) are past participles with root families of their own.

A minority of `ati-` words were instead entered as **root derivations**, with
the prefix folded into the root family (`ati √gar`, `ati √lubh`,
`ati ni √puṇ`). This is inconsistent with the convention and creates root
families that contain one or two words and nothing else.

The clinching evidence: **`atisīta` is already correctly converted** (no root
family, `family_compound = ati sīta`, `kammadhāraya`) while its sibling
`nātisīta` was left behind carrying `ati √sid`. The root family `ati √sid`
exists only because the job was half finished.

## Scope

### Selection rule

A headword is a candidate when:

1. its `family_root` begins with `ati ` (79 such families exist), **and**
2. **no** member of that root family is a verb form — i.e. no member has
   `pos` in `pr, aor, fut, imperf, opt, imp, perf, cond, ger, abs, inf, caus`.

Rule 2 is what separates a compound from a genuine prefixed verb. A prefixed
verb (`atidhāvati`, `atināmeti`, `ativassati`) *is* a root derivation and must
keep its root family; so must its participles and gerunds. Excluding the whole
family, rather than each verb form individually, keeps a verb and its
participles together.

**This yields exactly 90 headwords across 53 root families.**

Note this is wider than a naive "root families with only one word" filter,
which finds 31. That filter misses 68 words in 22 further families that are the
same phenomenon but escaped because a negated or abstract sibling was also
entered (`atimahanta`/`nātimahanta`, `atikisa`/`nātikisa`/`nātikisatā`,
`atidūra 1`/`atidūra 2`/`atidūre`/`nātidūra`/`nātidūre`). It also correctly
drops the 7 singletons that are verb forms (`aticchati`, `atimodati`,
`atisallekhati`, `atibyādippati`, `accādhāya`, `atikassa`, `atibandhitvā`).

Part-of-speech breakdown of the 90: adj 36, ind 16, masc 14, pp 11, fem 7,
nt 5, ptp 1.

### Out of scope

- Any `ati` root family containing a verb form — 26 families, left untouched.
- `ati-` words that already have no root family — already correct.
- Creating missing base headwords (`nivāsa`, `atihīna` do not exist).
- Rebuilding `dpd.db`; this edits the live database in place.

## The transformation

Fields that change, for the plain compound shape:

| field | new value |
|---|---|
| `grammar` | existing string with `comp` inserted as the last qualifier, before `from`/`of` |
| `derived_from` | the base word |
| `root_key`, `root_sign`, `root_base`, `family_root` | cleared |
| `family_compound` | `ati ` + the base's compound-family token (see below) |
| `construction` | `ati + <base>` |
| `derivative`, `suffix` | cleared |
| `phonetic` | cleared, except at an `acc-` junction (see below) |
| `compound_type` | `kammadhāraya` |
| `compound_construction` | `ati + <base>` |

Unchanged: `pos`, `stem`, `pattern`, `meaning_1`, `meaning_lit`, `plus_case`,
`trans`, `verb`, and every field not listed above.

### The four regular shapes

**1. plain** — `ati` + base.
Model: `atitaruṇa`. `grammar = adj, comp, from taruṇa`,
`construction = ati + taruṇa`, `compound_construction = ati + taruṇa`,
`compound_type = kammadhāraya`.

**2. neg** — lemma begins `nāti`/`nācc`, `neg = neg`.
Model: `nātiucca`, `nātibahu`, `nātidīgha`, `nātirassa`, `nātithoka` — all
already correct in the db. `grammar = adj, comp, from na ucca`,
`derived_from = ucca` (the bare base, not `atiucca`),
`construction = na + ati + ucca`, `compound_construction = na + atiucca`,
`compound_type = kammadhāraya`.

**3. case** — an indeclinable that is a frozen case form.
Model: `aticiraṃ`. `grammar = ind, adv, comp, acc sg of aticira`,
`derived_from = aticira`, `construction = ati + cira + aṃ` newline
`aticira + aṃ`, `compound_construction = ati + ciraṃ`,
`compound_type = abyayībhāva` (9 of the 11 existing `ati-` indeclinable
compounds use the bare form; `kammadhāraya > abyayībhāva` and `kammadhāraya`
appear once each).

**4. abstr** — an abstract noun in `-tā`/`-tta`.
Model: `atijotitā`, `atijaccatā`, `atisītatā`. `grammar = fem, abstr, comp,
from joti`, `construction = ati + joti + tā` newline `atijoti + tā`,
`derivative = taddhita`, `suffix = tā` (both **retained**, unlike the other
shapes), `compound_construction = ati + jotitā`,
`compound_type = kammadhāraya`.

### Compound-family token

The user's rule is `ati ` + the base's compound family. Verified against the
data: **almost every simple base has an empty `family_compound`**, so a literal
copy yields nothing. The working rule is:

> `family_compound` = `ati ` + (the base's own `family_compound` if it is
> non-empty, otherwise the base's `lemma_clean`, with the homonym digit
> attached and no space when the base has homonyms)

Only three of the 21 clean candidates have a base with its own value:
`tula` → `tulā`, `vepullatā` → `vipula`, `nijjhāyita` → `nijjhāyita`. So
`atitula` → `ati tulā`, `ativepullatā` → `ati vipula`, and everything else →
`ati garu`, `ati lobha`, `ati ṭhāna`, `ati udaka`.

Homonym-digit convention taken from existing rows: `ati dhāta2`, `ati dosa1`,
`ati khippa1`, `ati asana1`, `ati deva patta3` — digit appended, no space.

### Phonetic

Root-formation phonetics (`u > o` in `√lubh > lobh`, `ht > ḍh > ḷh`,
`dk > kk`, `st > ṭṭh`) belong to the old analysis and are cleared.

The `acc-` forms are the exception: `ati` + a vowel-initial base genuinely
produces `ati > aty > acc`, so `phonetic = ti > ty > cc` is kept. Where the
base's own initial vowel also shifts (`accodaka` = `acc` + `udaka`, needing
`u > o` as well) the generator cannot reliably infer the extra line — those
rows are marked for review.

## Approach: generate a TSV, edit it, apply it

~90 rows with real per-word lexicographic judgement in perhaps fifteen of them.
A row-by-row y/n prompt in the terminal would be 90 keystrokes with no way to
*correct* a wrong proposal — only to reject it and fix it by hand later. A TSV
lets the user change a value in place, which is exactly what the irregular rows
need.

One script, two modes:

- **generate** — reads the db, writes `scripts/fix/ati_prefix_to_compound.tsv`
  with a `do` column, a `base` column, and an `old_`/`new_` pair for every
  changed field, so old and new sit side by side.
- **apply** — reads the TSV back, writes every row marked `do = y` to the db,
  prints a summary.

Both re-runnable. Generate preserves the user's `do` and `base` edits from an
existing TSV and recomputes the `new_` columns from the edited `base` — so
correcting one cell fixes the whole row. Generate also skips headwords that no
longer match the selection rule, so a second pass after an apply shows only
what is left.

### Base derivation

Priority order, with the result recorded in the editable `base` column:

1. `derived_from`, if non-empty and it is not a root family (contains no `√`)
   and not a verb (does not end in `ti`). For the `neg` shape, strip a leading
   `na `. This already carries the right answer for most rows — `kisa`,
   `thūla`, `tanu`, `uṇha`, `dūra`, `mahanta`, `deva`, `bhāra`, `garu`,
   `lobha`, `nipuṇa`, `vikāla`, `sappāya`, `sambādha`, `saṅkhepa`, `tikhiṇa`,
   `ṭhāna`, `udaka`, `tulā`, `vepulla`, `nijjhāyita`, `odāta`, `āsanna`,
   `yācaka`, `yācana`.
2. Otherwise strip the prefix (`ati`/`acc`/`nāti`/`nācc`) from `lemma_clean`
   and look for a headword, undoing consonant gemination
   (`atiṭṭhāna` → `ṭhāna`) and `acc` + vowel coalescence
   (`accodaka` → `udaka`, `accukkaṭṭha` → `ukkaṭṭha`).
3. Otherwise leave blank for the user to fill.

A `base_ok` column records whether the derived base exists as a headword.

### Rows that will need the user's eye

Known from the data survey — the generator marks them rather than guessing:

- **`atidāyī`** "flying through" strips to `dāyī`, but that headword means
  "giver" and belongs to `√dā`. The current root family `ati √ḍi` looks right;
  this row should probably be set to `do = n`.
- **`atinivāsa`** — base `nivāsa` is not a headword.
- **`nātihīnaṃ`** — built on `atihīna`, which is not a headword.
- **`atibharita`** — `derived_from` reads `aribharati`, a typo for
  `atibharati`.
- **`atibhārita`** — a causative past participle, `ati + bhāre + ita`.
- **`atuṇha`**, **`sātisaya`** — irregular prefixes (`at-`, `sa + ati`).
- **`atimuttaka 1/2`**, **`atimuttā`** — a plant name, `ati + √muc + tā + ka`.
- **`atikhīṇa 1/2`**, **`atikkhaya`**, **`atinipāta`**, **`atigāḷha`**,
  **`accogāḷha`**, **`accokaṭṭha`**, **`accokkaṭṭha`** — no `derived_from`;
  base must be confirmed by hand.
- Every `acc-` row, for the extra phonetic line.

## Safety

- `gui2` writes to the same database and must be closed before applying.
- `--dry-run` on apply prints the changes without committing.
- The script only writes the fields listed above, only to rows the user marked
  `do = y`, and never touches a row it did not select.
- After applying, `just backup` writes the changes out to `db/backup_tsv/`.

## Success criteria

1. The generator produces a TSV with 90 rows and a correct proposal for the
   regular shapes.
2. After the user's edits and an apply, every approved word has an empty
   `family_root` and `root_key`, a `family_compound` beginning `ati `, and a
   `compound_type`.
3. Re-running the generator afterwards lists only the rows deliberately left
   as `do = n`.
4. `uv run ruff check`, `ruff format`, `pyright`, and `just typecheck` clean.
5. `db_tests` shows no new failures attributable to the change.
