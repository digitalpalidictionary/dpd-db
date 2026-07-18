# Review: SC variants in freq maps

## Summary

Implementation matches the spec's stated design: mūla (left of `→`) is
skipped, witness parens are stripped, no-arrow continuation clauses are
treated as whole-clause variant text, and variant words are merged into the
same per-file freq key as the root file via filename substring replacement.
Path additions, loop wiring, and orphan handling (no variant twin → no
panic, `os.Stat` guard) are correct and match sibling exporters' style
(`1CST.go`, `3BJT.go`). `gofmt -l`, `go vet ./go_modules/...`, and
`go test ./go_modules/frequency/setup/...` are all clean.

Hand-verification against the live corpus (4,423 variant files / 19,434
entries — spec's counts are accurate) found one real correctness gap: the
witness-stripping regex silently fails on entries with unbalanced
parentheses, and there are 30 such entries in the real corpus, not the "1
junk token" the spec's investigation reported — see Finding 1.

## Findings

### 1. (Medium) Unbalanced-paren entries leak witness codes and citation text into the SC freq map as if they were Pali words

`extractVariantWords` (`go_modules/frequency/setup/2SC.go:108`) strips
witnesses with `witnessRe = regexp.MustCompile(`\([^)]*\)`)`, which only
matches a *closed* `(...)` group. I grepped the real corpus
(`resources/sc-data/sc_bilara_data/variant/pli/ms/**`) for entries where
`strings.Count(v, "(") != strings.Count(v, ")")` and found **30** such
entries (not the "1 junk token" the spec's investigation section claims),
concentrated in `thag*`, `ja*`, `thig*`, `mn95`, `sn20.6` variant files.

For most of them the unmatched `(` opens a witness list that continues
straight into an embedded cross-reference citation (sutta id, brackets,
title) with no closing paren before the entry ends, e.g.:

```
'Kassa → yassa (ud4.4:1 [Yakkhapahārasutta]; ne6:227 [Sāsanapaṭṭhāna]; '
'Lūkhenapi vā → lūkhenapi ca (bj, sya1ed, sya2ed, pts1ed, pts2ed mi7.5.6:1 '
'sugandhakaṁ → sagandhakaṁ (bj, sya1ed, sya2ed, pts1ed, pts2ed dhp44-59:50.2 [44. '
```

Running the actual extraction logic on these (simulated 1:1 in Python,
verified against the Go source) produces:

```
"yassa ud4.4:1 [Yakkhapahārasutta]; ne6:227 [Sāsanapaṭṭhāna];"
"lūkhenapi ca bj, sya1ed, sya2ed, pts1ed, pts2ed mi7.5.6:1"
"sagandhakaṁ bj, sya1ed, sya2ed, pts1ed, pts2ed dhp44-59:50.2 [44."
```

After `tools.CleanMachine` (digit strip, `[`/`]`/`,`/`.`/`;`/`:` strip) this
leaves standalone tokens like `bj`, `sya`, `ed`, `pts`, `mi`, `dhp`, and
sutta-title words (`yakkhapahārasutta`, `sāsanapaṭṭhāna`) counted as if they
were genuine Pali variant readings. Critically, `characterTest` in
`cleanMachine.go` does **not** flag any of this — `bj`, `ed`, `sya`, `pts`,
`dhp` are all composed of characters already in `allowedCharacters`, so
these get silently absorbed into the freq map with no error printed,
inflating counts for short abbreviation-shaped strings and injecting a
handful of sutta-title words that don't belong in a word-frequency map at
all.

Impact is small in absolute terms (30/19,434 entries ≈ 0.15% of variant
entries, and each only contributes a few spurious tokens against a
multi-hundred-thousand-word corpus), so this is not a build-breaker. But
the spec's own investigation undercounted the affected population by 30x,
and the fix (bail out / treat as whole-clause fallback, matching how the
no-arrow case is already handled) would be a small, low-risk addition to
`extractVariantWords`. Recommend either fixing before merge or explicitly
accepting the known gap in the spec/plan with the corrected count.

### 2. (Nit) `witnessRe` comment doesn't mention the unbalanced-paren failure mode

Minor documentation gap following from Finding 1 — the doc comment on
`extractVariantWords` (`2SC.go:97-101`) describes the no-arrow fallback but
says nothing about what happens when a witness paren never closes. Worth a
one-line note either way this gets resolved.

## Verification performed

- `gofmt -l go_modules/tools/pth.go go_modules/frequency/setup/2SC.go go_modules/frequency/setup/2SC_test.go` → clean
- `go vet ./go_modules/...` → clean
- `go test ./go_modules/frequency/setup/...` → `ok`, 6/6 `TestExtractVariantWords` subtests pass
- Confirmed real corpus counts match spec: 4,423 variant files, 19,434 entries, 0 variant files without a matching root file (2,866 root files have no variant twin, which the `os.Stat` guard handles without panic)
- Confirmed `tools.CleanMachine`'s `sc` branch + common section does strip stray `;`, `…`, `(`, `)`, `[`, `]`, `,`, `.`, `:` — so the semicolon-as-token and trailing-comma cases the test suite exercises are correctly cleaned downstream, no action needed there
- Simulated `extractVariantWords` in Python against the full real variant corpus (not committed — scratchpad only) to check for leaked punctuation/reference tokens; found the unbalanced-paren leak in Finding 1
- Style check against `1CST.go`/`3BJT.go`: loop structure, `PCounter`, `fileFreqMap` keying, and `saveFileFreqMap`/`makeFreqMap` reuse are consistent; package-level `regexp.MustCompile` matches existing precedent in `cleanMachine.go`

## Verdict

**Needs changes** — not for build/test correctness (all green), but Finding
1 is a real, verified data-quality leak that contradicts the spec's own
investigation numbers (1 vs 30 entries) and should either be fixed with a
small fallback (treat text after an unclosed paren as non-variant/discard,
consistent with how the no-arrow case already falls back to whole-clause
handling) or the spec should be corrected to acknowledge the true scope and
an explicit decision made to accept it.

## Fixes applied (2026-07-18)

- Finding 1: `extractVariantWords` now truncates each clause at the first
  `(` remaining after witness-stripping — an unclosed paren starts junk
  (witness codes, citations), and in every observed corpus case the genuine
  variant words precede it. Two regression tests added from real corpus
  entries (`thag16.6:14.3`, `thag1.22:1.3`). Spec investigation numbers
  corrected.
- Finding 2 (nit): comment added above the truncation explaining the
  unclosed-paren failure mode.
- Parallel CodeRabbit review finding: `scVariantText` no longer swallows
  non-ENOENT `os.Stat` errors — only `os.IsNotExist` means "no variant
  twin"; anything else fails loud via `tools.HardCheck`.
- Re-verified: `gofmt -l` clean, `go vet ./go_modules/...` clean,
  `go test ./go_modules/frequency/setup/` 8/8 subtests pass.

## Post-finalize round 2 (2026-07-18)

The user's real `go run ./go_modules/frequency/setup sc` surfaced
`characterTest` errors ("/" then "'") and a variant-only word probe exposed
three more junk classes the review round missed:

- editorial-note clauses (witness codes *outside* parens, e.g.
  "idaṁ padaṁ cck, pts-vp-pli1 potthakesu…") → clause skipped via `noteRe`
- citation references ("dn33:194 [Saṅgītisutta/5. Pañcaka]") → tokens
  containing digits/colons/brackets dropped via `citeCharRe`; "/" → space
  (also a genuine verse-line separator); letterless tokens dropped
- sandhi-elision apostrophes ("daharāsa'pāpikā") → "'" deleted joining the
  parts, matching CleanMachine's cst branch

Verified: full `setup sc` run completes with zero characterTest errors
(169,420 words); witness codes/citation ids absent from regenerated
`sc_freq.json`; variant-only words present (daharāsapāpikā 2, mutiṅgasaddo 1,
lapilakaṁ 2, petassudissatha 1 — all 0 hits in root texts). 13/13 unit tests,
gofmt/vet clean.

## Final verdict

**PASSED**
