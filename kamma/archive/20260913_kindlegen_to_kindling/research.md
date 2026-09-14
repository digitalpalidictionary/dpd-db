# Research: replacing kindlegen with kindling

Status: **research only** — no decision taken, no spec, no plan.
Date: 2026-09-13.

> **Snapshot warning.** Every count in this document was measured against the
> render of 2026-07-28. The thread re-rendered on 2026-09-13; the current
> figures are in `plan.md` and supersede these. Sizes are MB (10^6 bytes).

> **§4 was wrong and is corrected below.** The original text claimed
> `--fold-accents` loses real headwords. It does not. See the correction.
Upstream: https://github.com/ciscoriordan/kindling (MIT, Rust, v0.45.1, released 2026-09-12).

---

## 1. What we do today

`exporter/kindle/kindle_exporter.py` renders the EPUB skeleton in
`exporter/kindle/epub/` from the db, zips it to
`exporter/share/dpd-kindle.epub`, then `make_mobi()` shells out:

| Platform | Tool | Result |
|---|---|---|
| Linux | `pth.kindlegen_path` = `exporter/kindle/kindlegen` | real Kindle dictionary `.mobi` |
| macOS | `ebook-convert` (Calibre) | plain `.mobi` book — **no orthographic index, no lookup** |
| macOS w/o Calibre | nothing | `pr.red("No compatible MOBI converter found")`, silent no-op |

The committed `kindlegen` binary is:

```
ELF 32-bit LSB executable, Intel 80386, statically linked, stripped
28,673,912 bytes, Amazon kindlegen(Linux) V2.9 build 1028-0897292 (2014)
```

Amazon discontinued kindlegen in 2022. It is a 28 MB **i386** blob committed
into the repo; GitHub's Ubuntu runners still execute it only because of
lingering multiarch support in the image.

The markup we feed it is a genuine Kindle dictionary:
`ebook_entry.jinja` and `ebook_deconstructor_entry.jinja` emit
`<idx:entry name="Pali" scriptable="yes" spell="yes">` →
`<idx:short>` → `<idx:orth value="…">` → `<idx:infl>/<idx:iform exact="yes">`,
with `<DictionaryInLanguage>pi</DictionaryInLanguage>` in the OPF `<x-metadata>`.

### Measured scale of the current input (read from the rendered epub on disk)

| Quantity | Count |
|---|---|
| `<idx:entry>` (headword + deconstructor + EPD + abbrev) | 188,971 |
| `<idx:orth>` occurrences / unique | 188,971 / 173,886 |
| `<idx:iform>` occurrences / unique | 491,151 / 314,874 |
| unique orth ∪ unique iform | **422,191** |
| headword labels claimed by >1 entry | 10,020 |
| inflected forms claimed by >1 entry | **88,500** |
| inflected forms that are also a headword | 66,569 |

---

## 2. Measured head-to-head (this machine, real DPD data, one run each)

Input: the rendered `exporter/kindle/epub/OEBPS/content.opf` (188,971 entries).
Baseline `.epub` for kindlegen: `exporter/share/dpd-kindle.epub` copied to scratch.

| | kindlegen V2.9 | kindling 0.45.1 (default) | kindling `--fold-accents` |
|---|---|---|---|
| Wall clock | **281.1 s** | **12.1 s** (8.6 s warm) | 8.6 s |
| Peak RSS | 738 MB | 957 MB | — |
| Output size | **74,796,940 B** (74.8 MB) | **39,895,905 B** (39.9 MB) | 45.1 MB |
| Exit status | 1 (warnings) | 0 | 0 |
| Orth index terms | 188,971 (headwords only; inflections in a separate INFL index) | 422,191 (headwords **and** inflections, flat) | 422,191 |
| Self-check | n/a | 18 P0 checks passed, 0 P1 warnings | same |

**≈23× faster, ≈47% smaller output.** n=1 per variant on a loaded interactive
machine; the ratio is the deliverable, not the absolute seconds. Both figures
are far from the "7,000×" headline — DPD is not the pathological case kindlegen
chokes on.

kindlegen's own warnings on our input, for the record:

```
W14024: Unrecognized language code in dc:Language metadata field.
W15008: language not supported. Using default phonetics for spellchecker: english.
W26001: Index not supported for enhanced mobi.
I12001: Enhanced mobi generation suppressed.
```

i.e. kindlegen already refuses to build the KF8 half for us, and its
spellchecker index is built with *English* phonetics against Pāḷi.

---

## 3. Two blockers found by actually running it

### 3a. KDP validation aborts on our OPF (2 errors)

```
[error R15.e1] OPF_078: An EPUB 3 dictionary must contain at least one content
               document with epub:type="dictionary".
[error R15.e2] OPF_079: idx:entry present but the OPF does not declare
               <dc:type>dictionary</dc:type>.
```

Both fire only because `ebook_content_opf.jinja` declares
`<package version="3.0">` while carrying OPF-2 style `<x-metadata>` dictionary
tags. Three ways out, cheapest first:

1. pass `--no-validate` (throws away 116 useful pre-flight checks);
2. add `<dc:type>dictionary</dc:type>` + `epub:type="dictionary"` to the
   template (two-line change, also makes the Send-to-Kindle `.epub` a
   standards-correct EPUB3 dictionary);
3. drop the package version to 2.0.

Option 2 is the right one. Everything else in the report is a warning, and the
warnings are real and actionable: no logical TOC, no `<reference type="index">`
in `<guide>` (older firmware uses it to find the dictionary section), and
`properties="remote-resources"` missing on ~30 manifest items.

### 3b. Feeding it the `.epub` instead of the `.opf` produces a broken file

```
kindling-cli build --no-validate dpd-kindle.epub -o out.mobi
→ [P0] PalmDB record 18260 is 18,915,332 bytes (18 MB), over the 16 MB sanity
  limit; this trips the Kindle reader's "Unable to Open Item" path. Magic: SRCS
→ Error: MOBI readback check failed. Built MOBI may be corrupted, not shipping.
```

kindling embeds the source EPUB as an `SRCS` record by default, and our 18.9 MB
epub blows the record limit. It *caught its own bug and refused to ship the
file* — which is exactly the behaviour kindlegen lacks. Fix: feed the OPF (what
we already have on disk) or pass `--no-embed-source`.

---

## 4. Accent folding: the default is right, the kindlegen-parity flag is wrong

kindling defaults Latin dictionaries to exact accent matching. `--fold-accents`
exists for "byte-for-byte kindlegen parity". Measured on our data:

| query | exact (default) | `--fold-accents` |
|---|---|---|
| `thana` | resolves | resolves |
| `thāna` | resolves | **fails** |
| `ṭhana` | resolves | **fails** |
| `anicca` / `aniccā` / `amata` | resolves | resolves |
| `Buddha` / `DHAMMA` (case) | resolves | resolves |
| `ariyasaccam` (for `ariyasaccaṃ`) | fails | fails |

**Correction (2026-09-13, after review).** The reasoning above is wrong and the
table is misleading. `thāna` and `ṭhana` are **not in the dictionary at all** —
verified against the rendered index: zero occurrences as either a headword or an
inflected form. What the "exact" column recorded was a fuzzy fallback onto
`thana` (a different word — breast, not place), counted as a success.

Re-measured against the 2026-09-13 build, with a `--fold-accents` variant built
from the same render: every real Pāḷi word resolves at the **identical text
position** in both modes — `ṭhāna`, `dhammā`, `dhammassa`, `buddhaṃ`,
`ariyasaccaṃ`, `okārassa`, `okkamati`, `bhikkhūti`, `evaṃvipāko`, `suffering`,
`thana`. `--fold-accents` loses **no** real headword.

The recommendation stands, for different reasons: the default is more forgiving
on a misspelled query and produces a smaller file (40.1 MB vs 45.3 MB). But do
not repeat the "it loses headwords" claim — it is false.

Note also that `ṃ` → `m` is not an accent fold in either mode — we already
handle that ourselves via `add_niggahitas`, which emits the `ṃ`/`ṁ` pair
explicitly.

---

## 5. New functionality unlocked

1. **macOS parity.** Native Apple Silicon and Intel binaries. The Calibre
   fallback in `make_mobi()` — which silently produces a MOBI with **no
   dictionary index at all** — can be deleted. Today a Mac build of DPD-kindle
   is not a working dictionary.
2. **CI without an i386 blob.** A 17 MB x86_64 static binary, downloadable per
   release, replaces a 28 MB 2014 i386 binary committed to git history. Removes
   a real bus-factor risk as runners drop 32-bit support.
3. **A build-side lookup regression test.** `kindling-cli lookup <mobi> <word>`
   simulates the firmware's orth search. This is testable in CI — we could
   assert that a fixed list of inflected Pāḷi forms resolves in every release.
   Nothing equivalent exists today; correctness is currently only ever checked
   by a human with a Kindle.
4. **116-point KDP pre-flight validation + MOBI readback self-check.** Section
   3b is the proof this works.
5. **AZW3 / KF8 output** for books (dictionaries stay MOBI7 because the popup
   requires it — `--legacy-mobi` is a documented no-op on dictionary builds).
6. **StarDict export** (`.ifo/.idx/.dict/.syn`) from the same OPF — inflections
   become `.syn` redirects. Overlaps with our existing GoldenDict and Kobo
   exporters, so this is redundancy, not a new capability; possibly useful as a
   cross-check.
7. **EPUB3 dictionary export** with Search Key Map + `epub:type`, i.e. a
   Send-to-Kindle `.epub` that Amazon actually recognises as a dictionary.
8. **`dump`, `rewrite-metadata`, `thumbnail`, `repair`** — diagnostics and a
   real cover tile for sideloaded files.
9. **`--headwords-only`** — a much smaller build variant for low-memory devices,
   one flag away.
10. **38 MB instead of 71 MB** on-device, and a 23× faster release build.

---

## 6. Old functionality lost or at risk

Ranked by how much it should worry us.

1. **The separate inflection INDX is gone — HIGHEST RISK.** kindlegen writes a
   dedicated INFL index; kindling writes `0xFFFFFFFF` at MOBI header offset 28
   and puts all 422,191 forms directly in the orth index. The author states
   this resolves inflected lookups on compatible devices, but "compatible" is
   doing work in that sentence. **This cannot be settled from the desk — it
   needs a real Kindle.**
2. **Homograph collapse.** 88,500 of our inflected forms are claimed by more
   than one entry, and 10,020 headword labels are duplicated. In the flat orth
   model each label resolves to exactly one text position — verified:
   `onaṃ` → one position, `oka` → one position. Duplicate *headwords* are
   adjacent in the text (we sort by `lemma_1`), so scrolling the popup should
   still show the neighbours; an ambiguous *inflection* whose owners live far
   apart alphabetically has no such consolation. How kindlegen's INFL index
   behaved here is not documented either. **Needs device comparison on a
   known-ambiguous form.**
3. **Phonetic spell index.** We pass `spell="yes"`; kindlegen built a
   spellchecker index (with English phonetics — see its W15008 warning). No
   equivalent is documented in kindling. Probably no real loss for Pāḷi, but
   it is a behaviour we currently emit and would stop emitting meaningfully.
4. **Output byte-parity is impossible.** Different compressor, different index
   layout, 47% smaller. Any future "byte-identical" parity gate on the MOBI is
   off the table; verification has to move to `lookup`-based assertions.
5. **Maturity.** kindling is 5 months old (created 2026-04-06), v0.**45**.1,
   52 stars, 7 forks, 4 open issues, MIT, one maintainer, shipping fast. That
   is momentum and bus-factor in one sentence. Pinning an exact release and
   vendoring the checksum matters.
6. **Nothing else.** The `.epub` we ship for Send-to-Kindle is produced by our
   own Python zip step, not by kindlegen, so it is unaffected. The three
   transliteration variants (`--script deva/sinhala/thai`) never call
   `make_mobi()` at all.

---

## 7. What a migration would actually touch (if we decide to do it)

Small. Listed for sizing only — not a plan.

- `exporter/kindle/kindle_exporter.py::make_mobi()` — collapse the three-way
  platform branch to one invocation; pass the OPF, not the zipped epub; pass
  `-o pth.dpd_mobi_path` explicitly (kindling does not infer our output name).
- `tools/paths.py` — `kindlegen_path` → a kindling path.
- `exporter/kindle/templates/ebook_content_opf.jinja` — add
  `<dc:type>dictionary</dc:type>`, `epub:type="dictionary"`, and optionally
  the `<guide><reference type="index">` the validator asks for.
- Binary acquisition: vendor a pinned x86_64 release (like today's kindlegen),
  or download-on-demand in CI with a checksum. The former keeps local builds
  working offline; the latter keeps a 17 MB blob out of git.
- `exporter/kindle/kindlegen` — delete (28 MB stays in history regardless).
- `docs/install/kindle.md` — unchanged for users; the install steps are
  identical.
- `.github/workflows/draft_release.yml` — unchanged apart from binary setup.
- New: a `lookup`-based smoke test over a fixed list of inflected forms.

---

## 8. Open questions that block a decision

1. **Does a real Kindle resolve an inflected Pāḷi form from a kindling-built
   DPD?** Build both, sideload both, tap ten inflected words. Nothing else in
   this document matters if the answer is no.
2. **What happens on an ambiguous inflection on-device**, old vs new?
3. Which Kindle generations are we committing to? kindling ships 15+ device
   profiles; our users span very old hardware.
4. Vendor the binary, or fetch it in CI?
5. Do we want the StarDict/EPUB3 exports at all, given we already ship
   GoldenDict, MDict, Kobo and slob?

## 9. Recommendation

Worth doing, on evidence, **conditional on question 1**. The current state is
worse than it looks: a 2014 32-bit binary Amazon abandoned, producing a 71 MB
file in 4.7 minutes, with macOS silently producing a non-dictionary. The
replacement is 23× faster, 47% smaller, cross-platform, validating, and
testable. The cost is a genuine unknown in on-device inflection lookup that
only a Kindle can answer.

Proposed next step before any spec: build one `.mobi` each way, sideload both,
and test the same ten inflected words on a real device.
