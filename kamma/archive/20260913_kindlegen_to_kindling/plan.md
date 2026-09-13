# Plan: trial replacement of kindlegen with kindling

Spec: `spec.md`. Research: `research.md`.
Status markers: `[ ]` todo · `[~]` in progress · `[x]` done.

---

## Phase 0 — baseline

- [x] **0.1 Record the pre-existing test state.**
  `uv run pytest tests/exporter/kindle/ -q` and note failures that exist
  *before* any edit. These are not this thread's to fix.
  → verify: failure list written into Results below, or "clean".
- [x] **0.2 Create the branch.** `git checkout -b kindling-trial` from a clean
  `main`. No commits — the user commits at the end.
  → verify: `git branch --show-current` = `kindling-trial`; `git status`
  shows only this thread's untracked files.
- [x] **0.3 Stage the pinned binary.** Copy the already-downloaded
  `kindling-cli-linux` v0.45.1 to `exporter/kindle/kindling-cli`, `chmod +x`,
  add to `.gitignore`.
  → verify: `./exporter/kindle/kindling-cli --version` prints `kindling 0.45.1`;
  `git check-ignore -v exporter/kindle/kindling-cli` matches.

## Phase 1 — templates: make the OPF a valid EPUB3 dictionary

- [x] **1.1 `ebook_content_opf.jinja`** — add `<dc:type>dictionary</dc:type>`
  to metadata and a `<guide>` with `<reference type="index" ...>` at the first
  Pāḷi letter file (`Text/0_a.xhtml`).
- [x] **1.2 `ebook_letter.jinja`** — `epub:type="dictionary"` on `<body>`.
  The `epub` namespace is already declared on `<html>`; confirm before editing.
- [x] **1.3 Verify the two validator errors are gone.** Re-render (Phase 2)
  then `kindling-cli validate` on the fresh OPF.
  → verify: `R15.e1 / OPF_078` and `R15.e2 / OPF_079` absent; **0 errors**.
  Remaining warnings listed in Results, not silenced.

## Phase 2 — render once, build twice

- [x] **2.1 Render harness.** Scratchpad script calling
  `render_dpd_xhtml` → `render_epd_xhtml` → `save_abbreviations_xhtml_page` →
  `save_title_page_xhtml` → `zip_epub` directly, bypassing the
  `make_ebook = no` gate without touching `config.ini`.
  → verify: `Text/` repopulated with a fresh mtime; `content.opf` and
  `dpd-kindle.epub` regenerated; entry count printed.
- [x] **2.2 Build the OLD artefact** — `exporter/kindle/kindlegen` on the fresh
  `dpd-kindle.epub`, output renamed to `dpd-kindle-kindlegen.mobi`.
  → verify: file exists, ~75 MB, wall time recorded.
  Note: kindlegen exits 1 on warnings — that is its normal state here, not a
  failure. If it regresses on the Phase-1 template change, rebuild from the
  pre-change template and say so (spec assumption).
- [x] **2.3 Build the NEW artefact** — `kindling-cli build` on the fresh
  `content.opf`, **validation on**, no `--fold-accents`, output
  `dpd-kindle-kindling.mobi`.
  → verify: exit 0, "0 P0 errors" on readback, ~40 MB, wall time recorded.
- [x] **2.4 Record the comparison** — size, wall time, orth-index term count
  for both, into Results.

## Phase 3 — the code change

- [x] **3.1 `tools/paths.py`** — add `kindling_path`. Leave `kindlegen_path`
  in place (spec: the old artefact must stay buildable).
- [x] **3.2 `make_mobi()`** — one code path: `kindling-cli build <opf> -o
  <dpd_mobi_path>`. Delete the `platform.system()` branch, the `Darwin` /
  Calibre arm, and the silent red no-op. Stream output through `pr.white()`.
  **Honour the exit code** — non-zero must raise/`pr.red` and stop, not pass
  silently as today.
  → verify: the function is exercised by 3.3 and by a real run in 2.3.
- [x] **3.3 Tests** — `tests/exporter/kindle/test_kindle_exporter.py` covering
  the new `make_mobi()`: correct argv shape (OPF in, `-o` out, no
  `--fold-accents`, no `--no-validate`), missing-binary path, and non-zero exit
  surfacing as an error. Fake the subprocess; no real build in the suite.
  → verify: `uv run pytest tests/exporter/kindle/ -q` green.
- [x] **3.4 Lookup regression check** — a fixed list of inflected Pāḷi forms
  driven through `kindling-cli lookup` against the built MOBI. Include at least
  one form from the ambiguous set (88,775 forms) and one from the duplicate
  headwords (10,046), so the homograph behaviour is on record.
  → verify: every listed word resolves; ambiguous-form results recorded as
  data, not asserted as correct.

## Phase 3b — binary acquisition on a real GitHub runner (the central question)

Measured on `ubuntu-latest`, not extrapolated from a 22-core workstation.
Proven on a throwaway branch whose CI run stays citable after the branch is
deleted.

- [x] **3b.1 Benchmark workflow** on a throwaway branch containing *only* the
  workflow file — no kindle changes — so the measurement is not entangled with
  the trial. Triggered `on: push` to that branch (a `workflow_dispatch` would
  only be offered on the default branch).
  Jobs, each timed independently:
  - **A — committed binary:** measure the checkout cost of a 17 MB tracked blob.
  - **B — download release asset:** `curl` the pinned v0.45.1 linux asset,
    verify its SHA-256, `chmod +x`.
  - **C — `cargo install kindling-mobi --version 0.45.1`**, cold, no cache.
  - **C-cached — same with a Rust cache restored**, to show the steady state.
  Each job then builds a small synthetic OPF dictionary so the binary is proven
  to *run* on the runner, not merely to exist.
  → verify: all jobs green; per-job wall clock recorded from the run's own
  timings, not from a log line we print ourselves.
- [x] **3b.2 Record the numbers and pick an option** with the user. Criterion is
  release-job wall clock and failure modes.
- [x] **3b.3 Wire the chosen option into `draft_release.yml`** and re-run to
  prove the real release path works end to end.

### Phase 3b results — measured on `ubuntu-latest`, run 34754250894

Throwaway branch `kindling-ci-bench`, workflow file only, 5 jobs, all green.
The branch is deleted; the run and its logs remain citable.

| Option | Acquire time | Extra cost |
|---|---|---|
| **B — download release asset + sha256 check** | **0.607 s** | none |
| C — `cargo install`, cold | 200.8 s | 180 MB cargo cache; needs a toolchain |
| C-cached — same with `actions/cache` wired | 209.1 s on a miss | cache infra for no gain |
| A — commit the binary | 0 s (in the checkout) | +17 MB tracked forever, linux-only |

Context for A: a full clone of this repo already takes **18.5 s** and is
**403 MB**, of which the tracked `kindlegen` blob is 28,673,912 B.

Runner toolchain was cargo/rustc 1.98.1. The source build produces a
17,031,152 B binary against the released 17,170,456 B; both report
`kindling 0.45.1`.

**Smoke job:** the downloaded binary built a synthetic dictionary on the runner
and resolved an inflected form through it — `Wrote smoke.mobi (10598 bytes)`,
`"dhammassa" resolves (exact headword/alias)`. The binary is proven to *run*
there, not merely to download.

**Decision: option B.** 330× faster than building, no toolchain, no cache, no
new blob in the repo. Wired into `.github/workflows/draft_release.yml` as an
"Install kindling" step immediately before "Export Kindle & ePub", pinned to
v0.45.1 and checksum-verified. `exporter/kindle/kindling-cli` stays gitignored.

**Not yet proven:** the full release workflow end to end. `draft_release.yml`
builds the whole database first, which is a multi-hour job, so the new step has
been proven in isolation on a runner rather than in situ. That is the remaining
CI risk, and it is small — the step is four lines and its failure mode is loud.

## Phase 3c — end-to-end local run and kindlegen retirement

- [x] **3c.1 Flip `[exporter] make_ebook` to `yes`** (user gave explicit
  permission; global rules otherwise forbid editing `.ini` files). Applied via
  `tools.configger.config_update` so the file is not reformatted — the diff is
  one line. Original backed up to the scratchpad.
- [x] **3c.2 Run the real entry point**, `just export-kindle`, with no harness,
  no bypass, and the output file deleted first so its creation is proved.
  → verify: exits 0, validation 0 errors, mobi written to `dpd_mobi_path`.
- [x] **3c.3 Retire kindlegen** — delete the binary and `kindlegen_path`, after
  verifying the archive copy is byte-identical and sweeping for live callers.
- [ ] **3c.4 Decide whether `make_ebook` stays `yes`** — user's call; the flag
  is currently left ON, see Results.

### Phase 3c results

**End-to-end, real entry point, no harness — PASSED.**

```
just export-kindle          →  67.7 s total
  validation                →  0 errors, 31 warnings, 1 info
  parsed                    →  189,505 dictionary entries
  lookup terms              →  423,001 unique
  sections                  →  3 (30 MB split)
  wrote                     →  exporter/share/dpd-kindle.mobi (40,093,355 B)
  self-check                →  18 P0 checks passed, 0 P1 warnings
  conversion stage          →  20.7 s
```

This is the gap the review flagged and it is now closed: the config gate,
render, EPD, abbreviations, titlepage, zip and conversion all ran as one
unassisted chain through `main()`. The two comparison artefacts were not
touched — the run writes `dpd-kindle.mobi`, they are
`dpd-kindle-kindlegen.mobi` and `dpd-kindle-kindling.mobi`.

Note the output is 40,093,355 B against the 40,094,196 B comparison copy — an
841-byte difference, entirely explained by the regenerated titlepage/OPF
timestamps. Not a discrepancy.

**kindlegen retired.** `exporter/kindle/kindlegen` (28,673,912 B, ELF 32-bit
i386, Amazon V2.9 build 2014) deleted along with `ProjectPaths.kindlegen_path`,
its only live reference. Verified safe three ways before deleting:

| Check | Result |
|---|---|
| User's archive copy | `2_Resources/Software/Linux/Kindlegen/kindlegen.tar.gz` |
| Tarball contents vs repo binary | **byte-identical**, sha256 `b8b0f0ab…461a69` |
| Recoverable from git | yes — `git checkout main -- exporter/kindle/kindlegen` |
| Comparison artefact still needed? | no — already built |
| Live callers | one (the path constant), removed |

The `kindlegen.s3.amazonaws.com` strings remaining in the two letter templates
are the `idx:`/`mbp:`/`cx:` XML namespace URIs the Kindle dictionary format
requires. They are **not** references to the binary and must stay.

Net repo change: −28.7 MB tracked, with nothing added (the kindling binary is
downloaded in CI and gitignored locally).

**`make_ebook` is currently left `yes`.** That is a change to the user's local
config, not to the repo default (`tools/configger.py` still ships `no` in the
default profile). It needs a decision: leave it on so `just makedict` builds
the Kindle dictionary, or set it back to `no`. Backup at
`<scratchpad>/config.ini.bak`.

## Phase 3d — DEVICE TEST FAILED: homograph collapse (blocker)

User tested both files on a real Kindle on 2026-09-13. Inflected lookup works.
**Homonyms do not.** Tapping `uttara` shows only `uttara 2.12`; `uttarā` shows
only `uttarā 5`. The user reports this was a known weakness before and is worse
now.

### Root cause — confirmed by minimal reproduction

kindling indexes **unique labels**. Where several entries declare the same
`<idx:orth value="...">`, all but one are dropped from the index. Reduced to
three entries sharing the label `uttara`:

```
Parsed 3 dictionary entries
Encoding 1 unique lookup terms      <-- three entries, one term
"uttara" resolves at text position 168   (of 265 bytes of text = the LAST)
```

The source XHTML is correct — all 13 `uttara` entries are rendered, with the
right headwords. The loss is entirely in the index build, and the survivor is
the last entry in document order, exactly as the user saw.

Not upstream issue #12 (multi-leaf routing counts), which was closed
2026-06-21, months before v0.45.1. Nothing in the README or the open issues
covers duplicate headwords; the README only says "the entry body may be shaped
however you like".

### Blast radius — measured against the shipped build

| Bucket | Entries | Distinct labels | Unreachable |
|---|---|---|---|
| Pāḷi (headwords + deconstructor) | 109,763 | 94,678 | **15,085** |
| EPD (English→Pāḷi) | 79,518 | 79,518 | 0 |
| Abbreviations | 224 | 224 | 0 |
| Cross-bucket collisions | — | — | 39 |
| **Total** | **189,505** | **174,381** | **15,124 (8.0%)** |

It hits the most-consulted words first: `dhamma` 16 entries, `vaṇṇa` 15,
`paṭhamavagga` 14, `attha` 13, `uttara` 13, `mahāvagga` 13, `pada` 12,
`pariyāya` 12, `ṭhāna` 11.

**99.7% of the loss is Pāḷi homonyms sharing a `lemma_clean`** — a single,
well-defined cause with a fix entirely inside our exporter.

### Proposed fix (NOT implemented — awaiting the user's go-ahead)

Emit **one `<idx:entry>` per distinct label**, with every homonym's content
inside its body, instead of one entry per `DpdHeadword`. `uttara` becomes one
entry whose body carries `uttara 1.1` … `uttara 2.12` in sequence. Nothing is
dropped because nothing collides.

This is the conventional dictionary shape — one headword, many numbered senses
— and it is compiler-independent: it would have improved the old kindlegen
behaviour too, which is consistent with the user calling this a pre-existing
weakness. It needs no upstream change and no new dependency.

Open design points to settle before building:
- grouping key: `lemma_clean` for headwords, but deconstructor rows share the
  same letter files and the same label space — group by the rendered label, not
  by the ORM class;
- entry ordering inside a merged body (current `pali_sort_key` order);
- whether the 39 cross-bucket collisions (Pāḷi/EPD/abbreviation) are merged too
  or deliberately left, since merging an English and a Pāḷi entry is odd;
- `id` numbering, currently one per entry.

### Options tested (real builds, real lookups, `--no-compress` so offsets are readable)

The user's reading of the cause is correct and the tests confirm it: the Kindle
dictionary format assumes **one entry per word with several subheadings inside
it**, while DPD is structured as **several entries per word**. The index is
keyed on the entry's headword label, so the format simply has nowhere to put
DPD's shape.

| # | Structure | Entries → index terms | Result |
|---|---|---|---|
| 1 | **One entry, one `<idx:orth>`, all senses in the body** | 1 → 1 | **Works.** Resolves to the top of the merged entry; all senses present, reachable by scrolling the popup |
| 2 | One entry, repeated `<idx:orth>` with the *same* label | 1 → 1 | Works, but identical to 1 — the extra orth adds nothing |
| 3 | Separate entries with *unique* labels (`uttara 1.1`, …) plus a shared `<idx:iform value="uttara">` alias | 3 → 4 | **Lossy.** The bare word resolves to the **first** entry only; nobody taps `uttara 2.01` in a text |
| 4 | One entry with **two different** `<idx:orth>` labels | 1 → 1 | **Only the first label is indexed.** `uttarapada` does not resolve. One entry = one headword, no exceptions |
| 5 | **Merged entry + every homonym's inflections pooled into one `<idx:infl>`** | 1 → 3 | **Works, and is the complete shape.** `uttara`, `uttaraṃ`, `uttarassa` all resolve to the merged entry |

Option 4 is the important negative result: it rules out any design that tries to
keep several headword labels on one entry. Option 3 is the tempting one and it
fails where it matters.

**Option 5 is the answer.** One `<idx:entry>` per distinct label; the body
carries every homonym's content in `pali_sort_key` order; the `<idx:infl>` block
is the union of all their inflections. Nothing collides, so nothing is dropped.

This is compiler-independent — it is the shape the format was designed for, so
it would have improved the old kindlegen output too, which fits the user's
recollection of this being a long-standing weakness.

### Correction: merging by lemma is WRONG (user, 2026-09-13)

Option 5 above is rejected. The homonyms under one spelling have **different
paradigms** — `uttara` masc and `uttara` nt do not inflect alike — so pooling
their inflections would make `uttaro` surface senses that cannot produce that
form. Lexicographically wrong, not merely noisy. The grouping key cannot be the
lemma.

### What the measurements say

Merging every entry that shares a form (transitive closure) does not explode —
72,907 components, 57,850 of them singletons — but the largest swallows 1,528
entries (`attha`, `acca`, …). A 1,528-sense popup is not a dictionary entry.

Keying entries on the **form** instead of the lemma:

| | count | note |
|---|---|---|
| distinct forms | 343,345 | |
| unambiguous (one headword) | 246,605 | **72%** — already correct today |
| ambiguous (>1 headword) | 96,740 | 28%; worst form claimed by **27** headwords |
| (form, headword) pairs | 535,342 | 4.9× duplication if each form carried full content |

Naive form-keyed with full content is **impossible**: 4.9× duplication is ~0.5 GB
of text, which at the observed ~4 KB/record is ~122,000 PalmDB records against
the format's hard ceiling of 65,535.

### Design that fits (proposed, NOT built)

One entry per distinct **form**, with the content depending on ownership:

- **Unambiguous form (72%)** — no new entry needed at all. It stays an
  `<idx:iform>` alias on its single owning headword's full entry. Zero
  duplication. This is what already works today.
- **Ambiguous form (28%)** — one compact entry that **lists the headwords that
  actually generate that form**, each with its pos, grammar and meaning. Tapping
  `uttaro` lists only the masculines; `uttarā` lists only what can be `uttarā`.

Estimated cost: current ~74 MB of text plus ~35 MB of disambiguation lists, so
roughly 27,000 records — comfortably inside the ceiling.

This also subsumes the original homonym bug: a lemma is just another form, so
`uttara` claimed by 13 headwords becomes a 13-way disambiguation entry rather
than silently keeping the last.

**Open question for the user:** should an ambiguous form show a compact list of
candidates (keeps the file buildable), or the full content of every candidate
(blows the record ceiling)? The list is the only option that fits, but the
reader then needs one extra tap to reach a full entry.

### The answer: a reverse dictionary keyed on inflections

The user pointed at `exporter/sutta_central/`, which already solves exactly this
and has been shipping for years. Its shape:

```python
for word in sc_word_set:                       # key = the INFLECTED FORM
    for headword_id in lookup_entry.headwords_unpack:   # form -> headword ids
        sc_dict[word].append(f"{lemma_1}: {pos}. {meaning} [{construction}]")
```

One entry per form; its body lists **only the headwords that actually generate
that form**, taken from the `Lookup` table's existing form→headword index. No
`<idx:infl>` at all — the inflections *are* the entries. That is why it is a
reverse dictionary.

### Prototype built and tested on the reported case

19 headwords of the `uttara` / `uttarā` / `uttāra` families → 68 distinct forms
→ a real MOBI:

```
Parsed 68 dictionary entries
Encoding 68 unique lookup terms      <-- 1:1, zero collapse
MOBI check: 16 P0 checks passed, 0 P1 warnings
```

Every form resolves to its own distinct position, and the ownership is
linguistically correct:

| tapped form | headwords listed |
|---|---|
| `uttaro` | 9 — **`uttara 1.1`, `2.01`–`2.12` only. No feminines.** |
| `uttarā` | 18 — the `uttarā 1`–`5` feminine lemmas **and** the `uttara` masc/nt forms that are genuinely `uttarā` |
| `uttāro` | its own entry, unrelated |

This is precisely the requirement: `uttaro` never shows `uttarā`, because
`uttaro` is not a form of `uttarā`.

### Full-scale sizing (measured against the live db, current kindle word set)

| | value |
|---|---|
| form-keyed entries | 286,658 |
| total text | **71.5 MB** (today's build: 74.6 MB) |
| average entry | 249 bytes |
| PalmDB records | **17,460** against the 65,535 ceiling |
| forms with 1 headword | 203,818 (71%) |
| worst form | 26 headwords |

It is **not bigger than what we ship today** — the duplicated full entries and
the separate inflection lists both disappear. There is roughly 3.7× headroom
before the record ceiling, so richer entry content can be added back later.

### The trade-off to decide

The SuttaCentral-style entry is compact — `lemma: pos. meaning [construction]`
per headword. Today's Kindle entry carries a summary, a grammar table and
examples (~944 bytes of body). Keying on forms means that content would be
repeated under every inflected form, which is what blows the record ceiling at
full richness. The headroom allows *some* of it back; how much is a judgement
call about what is useful in a popup.

### Full-scale build — measured, not estimated

Built the complete reverse dictionary against the live db, limited to the same
text sets the kindle exporter uses (CST + SuttaCentral EBT books + words inside
deconstructed compounds), exactly as `exporter/sutta_central` does.

```
text sets            266,953 forms   (cst 89,568 | sc 85,504 | + deconstructions)
lookup rows matched  258,708
entries rendered     264,504         (25.3 s)
Parsed               264,504 dictionary entries
Encoding             264,504 unique lookup terms     <-- 1:1, ZERO collapse
Compressed text into 12,643 records (51,784,475 bytes uncompressed)
Wrote                20,030,985 bytes
MOBI check           16 P0 checks passed, 0 P1 warnings
```

| | current build | reverse dictionary |
|---|---|---|
| entries | 189,505 | 264,504 |
| unique index terms | 174,381 (**15,124 lost**) | 264,504 (**0 lost**) |
| file size | 40,094,196 B | **20,030,985 B** |
| PalmDB records | 18,210 | **12,643** of 65,535 |

**Half the size and nothing is dropped.** The duplicated homonym bodies and the
separate `<idx:infl>` blocks both disappear, which more than pays for having an
entry per form.

### Lookup battery — 20/20 resolve

`uttaro uttarā uttaraṃ uttarassa dhammo dhammassa dhammā buddhaṃ buddho
ariyasaccaṃ bhikkhussa bhikkhu gacchati gacchāmi ṭhānaṃ okārassa bhikkhūti
evaṃvipāko idheva dhammānudhammappaṭipanno` — every one resolves, none fail.

### Content correctness — the reported case, from the built file

```
uttaro  -> 11 headwords: uttara 1.1 adj, 2.01 adj, 2.02 adj, 2.04 masc,
           2.06/2.07/2.10/2.11/2.12 masc, uttari 2.1 aor, uttari 2.2 aor
uttarā  -> 21 headwords: the above PLUS uttara 2.03/2.05/2.08/2.09 nt,
           uttarā 1-5 fem, uttaranta 1.1 prp
uttāro  -> 1 headword:  uttāra masc
```

`uttaro` carries **no neuters and no feminines**; `uttarā` carries both, because
it genuinely is a form of all of them. The paradigm distinction the user
insisted on is preserved exactly.

### Artefact for device testing

`exporter/share/dpd-kindle-reverse.mobi` (20.0 MB).

### Remaining trade-off

Entry content is the SuttaCentral-compact shape — `lemma: pos. meaning
[construction]` per headword. No grammar table, no examples. There is **5.2×
headroom** on the record ceiling (12,643 of 65,535), so content can be added
back; how much is a judgement call, and it multiplies per form.

### Full content, no reduction — built and tested

The user rejected the compact entry. Rebuilt with the **complete kindle entry
content** (summary + grammar table + examples) for every owning headword, each
headword's body rendered once and reused across its forms.

**My earlier estimate that this would breach the record ceiling was wrong.**
I predicted ~116,686 records from 477.9 MB of assembled source. The real build
uses **38,585**. kindling normalises the markup before packing, so the packed
text is 316 MB, not 478 MB. The lesson is the one in CLAUDE.md — measure the
mechanism, do not extrapolate it.

```
Parsed               264,504 dictionary entries
Kindle limits        split into 10 sections
Compressed text into 38,585 records (316,084,014 bytes uncompressed)
Encoding             264,504 unique lookup terms      <-- still 1:1, zero collapse
Wrote                112,654,591 bytes
MOBI check           16 P0 checks passed, 0 P1 warnings
Build                15.2 s (render 41.3 s)
```

`uttaro` entry: 11,523 bytes, **11 headwords, 11 grammar tables, examples
present** — the full DPD entry for each, not a summary line.

Lookup battery: 18/18 resolve.

### The four artefacts

| File | Size | Content | Entries lost |
|---|---|---|---|
| `dpd-kindle-kindlegen.mobi` | 75.2 MB | full | **15,124** |
| `dpd-kindle-kindling.mobi` | 40.1 MB | full | **15,124** |
| `dpd-kindle-reverse.mobi` | 20.0 MB | compact | 0 |
| `dpd-kindle-reverse-full.mobi` | **112.7 MB** | **full** | **0** |

The full reverse dictionary is 1.5× the current kindlegen file and 2.8× the
current kindling file, and it is the only one that is both complete and correct.
Record headroom: 38,585 of 65,535, so it fits with ~40% to spare.

### v3 — bug fixed, structure corrected by the user

User tested the full build and reported `vitthāra` showing "two entries, both
vitthāra 1". The source data was fine (3 distinct headwords, ids 67927-67929,
`vitthāra 1/2/3`) and the rendered entry held all three. The fault was mine:

**Bug — empty `<idx:orth>`.** In the rich build I moved the `<h4>` headword
*outside* the orth element, leaving `<idx:orth value="vitthāra"></idx:orth>` with
no text content. **207,669 of 264,504 entries** were affected. The compact build
had it right (`<idx:orth value="x"><h4>x</h4></idx:orth>`); the rich one did not.
Fixed — the v3 build has **0** empty-orth entries.

**Two corrections from the user, both right:**

1. *"If you're using this method, then you don't need homonyms — the entry
   itself is the only one."* DPD's homonym numbers exist to disambiguate
   identical lemmas in a **lemma-keyed** dictionary. In a form-keyed one the
   form is the entry, so the numbers carry no information. Display now uses
   `lemma_clean`, with a local 1./2./3. index within the entry.
2. *"Each entry needs a summary up top, the same compact info as sutta
   central."* Each entry now opens with the compact SuttaCentral-style line for
   every sense, then gives the full detail below.

Resulting shape for `vitthāra`:

```
<idx:orth value="vitthāra"><h4>vitthāra</h4></idx:orth>
  1. vitthāra adj.  extensive; detailed; broad; full; lit. spread out [vi + √thar + *a]
  2. vitthāra masc. breadth; lit. spread out [vi + √thar + *a]
  3. vitthāra masc. detailed description; extended explanation [vi + √thar + *a]
  <h5>1. vitthāra</h5> ...grammar table + examples...
  <h5>2. vitthāra</h5> ...
  <h5>3. vitthāra</h5> ...
```

```
Parsed      264,504 entries -> 264,504 unique lookup terms   (1:1, zero collapse)
Compressed  40,210 records (329,392,371 bytes)   of the 65,535 ceiling
Wrote       117,973,775 bytes
MOBI check  16 P0 checks passed, 0 P1 warnings
```

Lookup battery 20/20, `vitthāra` and `vitthāraṃ` included.

Artefact: `exporter/share/dpd-kindle-reverse-v3.mobi` (118.0 MB). Supersedes
`dpd-kindle-reverse-full.mobi`, which carries the empty-orth bug and should not
be tested further.

### v4 — summary only, plus Devanagari / Sinhala / Thai aliases

User: the detail blows the size out; summary alone is enough for reading. Plus:
can the three scripts point at the same inflected form?

**Yes.** `Lookup` already carries per-form transliterations
(`devanagari`/`sinhala`/`thai` columns, populated on ~100% of its 1,284,663
rows), so each Roman form's own script spellings attach to that form's entry as
`<idx:iform>` aliases — no new transliteration, no guessing.

```
script aliases       1,091,912
Parsed               264,504 dictionary entries
Encoding             1,356,032 unique lookup terms
Compressed text into 14,612 records (59,850,267 bytes)   of the 65,535 ceiling
Wrote                43,483,129 bytes
MOBI check           16 P0 checks passed, 0 P1 warnings
```

All four scripts resolve to the **identical text position**, i.e. the same entry:

| query | position |
|---|---|
| `dhammo` / `धम्मो` / `ธมฺโม` / `ධම්මො` | all → 28,563,869 |
| `uttaro` / `उत्तरो` / `อุตฺตโร` | all → 13,310,414 |
| `vitthāra` / `वित्थार` | both → 49,053,074 |

### Where all the builds stand

| File | Size | Content | Scripts | Entries lost |
|---|---|---|---|---|
| `dpd-kindle-kindlegen.mobi` | 75.2 MB | full | roman | 15,124 |
| `dpd-kindle-kindling.mobi` | 40.1 MB | full | roman | 15,124 |
| `dpd-kindle-reverse.mobi` | 20.0 MB | compact | roman | 0 |
| `dpd-kindle-reverse-full.mobi` | 112.7 MB | full | roman | 0 (empty-orth bug) |
| `dpd-kindle-reverse-v3.mobi` | 118.0 MB | summary + detail | roman | 0 |
| **`dpd-kindle-reverse-v4.mobi`** | **43.5 MB** | **summary** | **4 scripts** | **0** |

v4 is 3.4 MB larger than what ships today, loses nothing, and adds three
scripts.

### Test documents

- `exporter/share/dpd-kindle-test.azw3` (13.8 KB) — **use this one.** Reflowable,
  so long-press dictionary lookup works normally. 24 words in all four scripts,
  listed per script and side by side.
- `exporter/share/dpd-kindle-test.pdf` (87 KB) — same content, rendered with
  typst in Noto Devanagari / Sinhala / Looped Thai, verified legible. Kindle's
  PDF reader supports long-press lookup poorly and inconsistently, so this is a
  fallback for reading, not a reliable lookup test.

Both built from real `Lookup` transliterations, not hand-typed.

### It does NOT have to be either/or — v6, frequency-targeted detail

Two further arrangements were tested against the "detail vs function" trade-off.

**v5 — full detail for sole-owner forms, lists for ambiguous ones.** Builds at
60.3 MB, 16/16 lookups. Looks good by word type (73% get full detail) and
**fails on real reading**: weighted by occurrences in the canon only **28%** of
tokens reach full detail, because the commonest words are precisely the
ambiguous ones — `ca` (167,174 occurrences, 5 owners), `na` (150,827, 4),
`vā` (116,860, 5), `hoti` (72,544, 3), `te` (38,089, 14). Only `pana` and `kho`
in the top fifteen have a single owner. Rejected: 17 MB spent on rare words.

**v6 — detail where readers actually land.** Reading is extremely concentrated,
so the detail budget can be aimed by corpus frequency
(`shared_data/frequency/cst_freq.json`, real token counts):

| detail on | share of tokens | added source |
|---|---|---|
| top 1,000 forms | 53.1% | +3.3 MB |
| top 5,000 forms | 72.0% | +12.8 MB |
| **top 20,000 forms** | **87.0%** | +39.8 MB |
| top 50,000 forms | 94.9% | +82.3 MB |

Built at `DETAIL_TOP_N = 20000`:

```
Compressed text into 24,566 records (100,621,419 bytes)   of the 65,535 ceiling
Encoding 1,356,032 unique lookup terms
Wrote 62,622,158 bytes
MOBI check: 16 P0 checks passed, 0 P1 warnings
```

Verified targeting — frequent forms carry grammar tables, rare ones do not:

```
taṃ     7,100 B   7 senses   7 tables   DETAIL
dhammo 24,666 B  15 senses  15 tables   DETAIL
hoti    4,980 B   3 senses   3 tables   DETAIL
nillehitabba 628 B  1 sense  0 tables   summary only
```

10/10 lookups including all three scripts.

**Known wrinkle:** ranking is by the frequency of the *individual form*, so a
lemma like `vitthāra` falls outside the top 20,000 and gets summary only even
though its inflected forms are common. Ranking by the headword's whole paradigm
instead would fix that; not attempted yet.

`DETAIL_TOP_N` is a single constant — the trade-off is a dial, not a fork.

### The three candidates

| File | Size | Detail coverage (by tokens read) |
|---|---|---|
| `dpd-kindle-reverse-v4.mobi` | 43.3 MB | none — summary only |
| **`dpd-kindle-reverse-v6.mobi`** | **62.6 MB** | **87%** |
| `dpd-kindle-reverse-v3.mobi` | 118.0 MB | 100% (roman only, no scripts) |

All three: every form, every sense, correct every time.

### Issue #217

`Request to add transliterations as synonyms for kindle mobi dict` — already
CLOSED; the comment the user linked is where kindling was suggested. v4/v6
deliver what it asked for. **Not touched** (repo rule: never write to issues
unless asked).

### The root cause, found late: `lemma_clean` as the headword label

The original exporter labelled every entry `<idx:orth value="{lemma_clean}">`.
All 13 `uttara` homonyms therefore claimed the label `uttara`, and **one index
term reaches exactly one entry** — so 12 were silently dropped. That single
line, not kindling, caused the 15,124 lost entries.

The constraint itself was verified three ways, never assumed:

| test | result |
|---|---|
| 3 entries sharing one `<idx:iform>` | form resolves to **one** (the first) |
| 1 entry carrying two different `<idx:orth>` labels | **only the first is indexed** |
| 13 entries sharing a `lemma_clean` label | **12 unreachable** |

### v7 / v8 — GoldenDict index model

One entry per headword, labelled `lemma_1` (unique), full detail once, every
inflection and script spelling as an alias. 53.3 MB, **0 entries lost**, full
detail throughout, homonyms adjacent in the text.

**Rejected by the user on device evidence:** a shared form still lands on the
*first* homonym only. `gacchati` showed `gacchati 1` but not `gacchati 2`.
Adjacency does not rescue it — the popup renders one entry. The authoritative
answer for any form is `Lookup.headwords_unpack`, and only a form-keyed entry
can honour it.

### v10 — the accepted design

Since one term reaches one entry, the entry a form points at must itself carry
every sense that form has:

- **every headword** → one full entry, labelled `lemma_1`, detail stored **once**;
- **every ambiguous form** → an entry listing exactly the headwords
  `Lookup.headwords_unpack` names, each **linking** to its full entry;
- **unambiguous forms** → plain aliases on their owner's full entry;
- **contested labels** (4,913 cases where a form entry and a headword entry
  claim the same string, e.g. `acca`) → folded into a single entry carrying both
  the list and that headword's full detail.

```
Parsed      172,024 entries -> 172,024 distinct labels   LOST 0
Encoding    1,380,565 unique lookup terms
Wrote       63,914,130 bytes
MOBI check  16 P0 checks passed, 0 P1 warnings
cross-refs  all resolved
lookups     22/22 including all three scripts
```

Verified against the lookup table: `gacchati` → `gacchati 1` + `gacchati 2`
(ids 24043, 24044); `gacchanta` → `gacchanta 1` + `gacchanta 2` (24045, 88088);
`uttaro` → 11 senses; `vitthāra` → 3.

### Device verdict (user, 2026-09-13)

Links are **not clickable inside the popup**, but **are clickable when the
dictionary is opened as a book**. Accepted as "a very useful compromise":
the popup gives the correct, complete list of senses with summaries; the full
grammar and examples are one step away when wanted.

### Where this leaves the thread

Two separable outcomes:

1. **kindlegen → kindling**: yes. 10x faster, half the size, cross-platform,
   validating, CI-ready (binary downloaded in 0.6 s, wired into
   `draft_release.yml`). Implemented on the branch; end-to-end run passes.
2. **The dictionary structure**: v10 replaces the lemma-keyed model. **Still a
   scratchpad prototype** (`rev_v10.py`) — not yet in `exporter/kindle/`.

### Status

**v10 accepted. Implementation of v10 into the exporter is the remaining work.** The migration and this restructure are
separable: the reverse dictionary fixes a long-standing correctness bug that
predates kindling and would improve any Kindle build. Not "kindling is worse" — the same collapse rule
would apply to any compiler that indexes unique labels — but the current build
loses 8% of the dictionary, so it must not ship as-is.

## Phase 4 — gates and handoff

- [x] **4.1 Lint each touched file**, in order:
  `uv run ruff check --fix <file>` → `uv run ruff format <file>` →
  `uv run pyright <file>`.
  Touched-file set so far: `exporter/kindle/kindle_exporter.py`,
  `tools/paths.py`, `tests/exporter/kindle/test_kindle_exporter.py`.
  **TOUCH A FILE = OWN ITS LINT**, pre-existing errors included.
- [x] **4.2 `just typecheck`** (pyrefly, whole repo).
- [x] **4.3 Full suite** — `uv run pytest tests/`. Pre-existing failures named,
  not fixed, not weakened.
- [x] **4.4 Test protocol** — plain English, naming the two files, where to
  copy them, and the exact words to tap. Word list must include inflected
  forms, a homograph, and a deconstructed compound.
- [x] **4.5 Changed-file list** — verify each change is still present on disk
  (shared tree; a concurrent session can revert). `plan.md` is not proof.

---

## Phase 5 — implement v10 in the exporter (Part 2 of the spec)

Prototype: `rev_v10.py` in the session scratchpad. This phase moves it into
`exporter/kindle/` properly; the prototype is then deleted.

- [x] **5.1 Templates.** Replace `ebook_entry.jinja` (currently labels entries
  `lemma_clean` — the bug) with two templates: a **headword entry**
  (`lemma_1` label, aliases, summary + grammar + examples, anchor id) and a
  **form entry** (form label, script aliases, one linked line per sense).
  Keep `ebook_grammar.jinja` / `ebook_example.jinja` untouched.
  → verify: rendered sample matches the prototype's output shape.
- [x] **5.2 `kindle_exporter.py` render path.** Rewrite `render_dpd_xhtml` to:
  fetch `Lookup` rows for the text-set forms (headwords, deconstructor, and the
  three script columns in one pass); render each headword body **once** via
  `KindleData`; route forms — sole-owner → alias, ambiguous → linked form entry;
  merge contested labels. Leave `render_epd_xhtml`,
  `save_abbreviations_xhtml_page`, `save_title_page_xhtml`, `zip_epub` and
  `make_mobi` alone.
  → verify: entry count and distinct-label count equal; **0 lost**.
- [x] **5.3 Retire `--script`.** Remove `SCRATCH_CONFIG`/`--script`, the
  `script_attr`/`lookup_script_attr` parameters and the per-script epub paths.
  Sweep for references first (`rg --hidden`), including `tools/paths.py`.
  → verify: no references remain; `--help` no longer offers it.
- [x] **5.4 Tests.** Extend `tests/exporter/kindle/`: a form with several owners
  renders one entry listing exactly `Lookup.headwords_unpack`; a sole-owner form
  becomes an alias, not an entry; a contested label yields one entry carrying
  both list and detail; script spellings attach as aliases. Fixtures only, no db.
  → verify: `uv run pytest tests/exporter/kindle/ -q` green.
- [x] **5.5 Real run end to end.** `just export-kindle` with no harness.
  → verify: 0 validation errors, 0 lost labels, mobi written, spot-check
  `gacchati` → `gacchati 1` + `gacchati 2` against the db.
- [x] **5.6 Gates.** ruff check/format, pyright on every touched file;
  `just typecheck`; full `uv run pytest tests/`.
- [x] **5.7 Clean up.** Delete the scratchpad prototypes and the superseded
  artefacts in `exporter/share/` (keep the one the testers will use). Update
  `exporter/kindle/README.md` to describe the form-keyed structure.

### Phase 5 results — v10 implemented in the exporter

Real run, `just export-kindle`, no harness, 1:58 total:

```
Encoding    1,480,604 unique lookup terms
Compressed  26,933 records (110,315,678 bytes)   of the 65,535 ceiling
Wrote       exporter/share/dpd-kindle.mobi (71,568,669 bytes)
MOBI check  18 P0 checks passed, 0 P1 warnings
```

Larger than the 63.9 MB prototype because the real build also carries the EPD
(79,518 entries) and the abbreviations page, which the prototype omitted.

**Correctness, read back out of the shipped build:**

```
gacchati -> gacchati 1  10_g.xhtml#hw24043
         -> gacchati 2  10_g.xhtml#hw24044
```

matching `Lookup.headwords_unpack` exactly. 12/12 lookups resolve, all three
scripts included.

| | before | after |
|---|---|---|
| entries | 189,505 | 251,766 |
| distinct labels | 174,381 | 251,696 |
| **unreachable entries** | **15,124 (8.0%)** | **70 (0.03%)** |

**The remaining 70** are cross-bucket label collisions, not homonyms: 55 where
an English EPD headword spells the same as a Pāḷi form (`acc`, `base`, `agent`),
13 involving the abbreviations page, 1 three-way. They are a pre-existing class
(39 of them in the old build) and are **not fixed here** — merging them needs
the Pāḷi, EPD and abbreviation renderers to share one label space, which is a
restructure of three more functions. Logged as a follow-up; a 99.5% reduction
is the result of this phase.

**Changes:** `ebook_entry.jinja` rewritten (labels `lemma_1`, carries aliases
and an anchor); new `ebook_form_entry.jinja`; `ebook_deconstructor_entry.jinja`
deleted (deconstructions now render inline); `render_dpd_xhtml` rewritten around
`_load_lookup` / `_headword_aliases` / `render_form_entry`; `--script` and
`SCRIPT_CONFIG` removed (one file now recognises every script; swept for
references, none outside this thread).

**Gates:** ruff + pyright clean on every touched file; `just typecheck` 0 errors;
`uv run pytest tests/` **1862 passed, 12 deselected, 0 failed** (was 1856 —
6 new tests in `tests/exporter/kindle/test_form_entries.py`, one of which caught
a real digraph bug in my own fixture).

**Artefacts left for testers:** `exporter/share/dpd-kindle.mobi` (71.6 MB),
`dpd-kindle.epub`, plus `dpd-kindle-test.azw3` / `.pdf`. All the intermediate
prototype builds were deleted.

## Phase 6 — test build workflow (Part 3 of the spec)

- [ ] **6.1 Write `.github/workflows/kindle_test_build.yml`** — checkout with
  submodules, uv sync --all-groups, `gh release download` the latest
  `dpd.db.tar.xz`, extract, apply the github_release config profile, fetch and
  checksum kindling, run the kindle exporter only, publish a prerelease.
  → verify: `yaml.safe_load` parses it; no db build step present.
- [ ] **6.2 Prove it on a real runner** via the branch push trigger.
  → verify: run green; log shows `0 errors` from validation and a written mobi;
  prerelease carries the assets.
- [ ] **6.3 Record the run id and the tester download link.**

## Open questions carried forward

1. Does a real Kindle resolve inflected forms from the kindling build?
   **Only the user's device answers this.**
2. Ambiguous inflections on-device: old vs new.
3. Which Kindle generations are in scope?

Binary acquisition is no longer an open question carried forward — it is
Phase 3b, measured on a real runner.

## Results

### Phase 0 — baseline
- `uv run pytest tests/exporter/kindle/ -q` → **9 passed**, clean. No
  pre-existing failures in this area.
- Branch `kindling-trial` cut from a clean `main` (only this thread's untracked
  folder present).
- `exporter/kindle/kindling-cli` = pinned v0.45.1 linux x86_64, 17,170,456 B,
  gitignored at `.gitignore:68`.

### Phase 1 — validation
`kindling-cli validate` on the freshly rendered OPF:

```
0 errors, 31 warnings, 1 info
```

Both blocking errors are gone (`R15.e1 / OPF_078`, `R15.e2 / OPF_079`), and so
is the `R15.7` guide/index warning. **The build runs with validation on — no
`--no-validate` anywhere.** Remaining warnings, all pre-existing and advisory:

- `R5.2.1` / `R5.1` — no NCX or nav-based logical TOC (~42,872 pages).
- `R8.6` × ~29 — manifest items referencing remote resources without
  `properties="remote-resources"`.
- `R4.1.1` (info) — marketing cover can only be checked at KDP upload.

### Phase 2 — one render, two builds
Render: 58.97 s → 109,763 Pāḷi entries + 79,518 EPD + 224 abbreviations =
**189,505 entries**; 423,001 unique lookup terms (174,381 unique headword
labels ∪ 315,297 unique inflected forms).

| | kindlegen V2.9 | kindling 0.45.1 |
|---|---|---|
| Wall clock | **223.1 s** | **22.6 s** (incl. validation + `uv run` startup) |
| Output | **75,171,850 B** (75.2 MB) | **40,094,196 B** (40.1 MB) |
| Exit status | 1 (its normal state here) | 0 |
| Orth index | 174,381 distinct headword labels (189,505 entries); inflections in a separate INDX | 423,001 terms, flat |
| Self-check | none | 18 P0 checks passed, 0 P1 warnings |
| Text sections | 1 | 3 (30 MB split) |

**≈9.9× faster, 46.7% smaller.** The ratio is lower than research.md's 23×
because validation is now on and the timing includes interpreter startup; the
bare compile was 12.1 s.

kindlegen still builds cleanly on the Phase-1 template change — the spec's
`epub:type` / `<dc:type>` assumption held, so both artefacts come from the
same render as intended. Its warnings are unchanged and worth restating:

```
W14024: Unrecognized language code in dc:Language metadata field.
W15008: language not supported. Using default phonetics for spellchecker: english.
W26001: Index not supported for enhanced mobi.
```

Both builds report the same 7 unresolvable dictionary cross-references.

### Phase 3 — code + checks
`make_mobi()` is now one path on every platform: `kindling-cli build <opf> -o
<mobi>`, output streamed through `pr.white()`, missing binary → `FileNotFoundError`,
non-zero exit → `RuntimeError`. The `platform.system()` branch, the Calibre
`ebook-convert` arm and the silent red no-op are gone, as are the now-unused
`platform` and `shutil` imports. The new artefact was built **through this
function**, not by hand.

4 new tests in `tests/exporter/kindle/test_kindle_exporter.py`: argv shape (OPF
in, never a `.epub`), validation on / `--fold-accents` off, missing binary,
non-zero exit. Subprocess faked; no real build in the suite.

Lookup check against the built MOBI — 17 of 18 words resolve:

```
dhamma dhammā dhammassa buddhaṃ bhikkhussa gacchati ariyasaccaṃ
ṭhāna thāna(→"thana") okārassa okkamati bhikkhūti idheva
dhammānudhammappaṭipanno evaṃvipāko suffering compassion   → resolve
dhammānudhammamācara                                        → does not resolve
```

The one miss is **not a defect**: that string was copied from `pr.counter`'s
20-char truncated console output. The real key is
`dhammānudhammamācarantīti`, which is present in the rendered xhtml. Every
category is covered — plain inflections, niggahita endings, sandhi forms
resolved through the deconstructor, an inflection claimed by multiple entries
(`okārassa`), a duplicated headword (`okkamati`), and the English→Pāḷi side.

Note `thāna` resolves **via `thana`**, i.e. exact mode still carries a folded
alias. `--fold-accents` was not passed and must not be (research.md §4).

Wiring this check into CI is deferred with the binary-acquisition decision
(open question 3) — a permanent test needs the binary present in CI.

### Phase 4 — gates
- `ruff check --fix` / `ruff format` / `pyright` clean on all four touched
  Python/test files.
- `just typecheck` (pyrefly, whole repo): **0 errors**.
- `uv run pytest tests/`: **1853 passed, 12 deselected**, 0 failures. No
  pre-existing failures to report.

### Changed files (verified present on disk after the full run)

```
 M .gitignore                                        (+1, ignore kindling-cli)
 M exporter/kindle/kindle_exporter.py                (make_mobi rewritten)
 M exporter/kindle/templates/ebook_content_opf.jinja (+dc:type, +guide/index)
 M exporter/kindle/templates/ebook_epd_letter.jinja  (epub:type on body)
 M exporter/kindle/templates/ebook_letter.jinja      (epub:type on body)
 M tools/paths.py                                    (+kindling_path)
 M exporter/kindle/epub/OEBPS/Text/titlepage.xhtml   (regenerated; tracked-but-
                                                      generated, pre-existing)
?? tests/exporter/kindle/test_kindle_exporter.py
?? kamma/threads/20260913_kindlegen_to_kindling/
```

`exporter/kindle/kindlegen` deliberately untouched — the old artefact must stay
buildable while the comparison is live.

Nothing is committed. The user commits or discards after device testing.

### Deliverables
- `exporter/share/dpd-kindle-kindlegen.mobi` — 75.2 MB, old tool
- `exporter/share/dpd-kindle-kindling.mobi` — 40.1 MB, new tool
- `test_protocol.md` in this thread — the words to tap and what to report
