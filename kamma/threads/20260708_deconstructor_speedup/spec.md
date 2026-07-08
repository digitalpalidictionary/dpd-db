# Spec: Deconstructor Speedup — lock contention + allocation/conversion churn

## Context

Two independent benchmark passes (thread `20260708_deconstructor_benchmark_design`,
`findings_agent2.md` is the trustworthy one) agree on where `go_modules/deconstructor/`
spends its time on the ~1M-word production run:

1. **`MakeMatch`'s global `muMatched` write-lock caps parallelism.** ~72% of all
   blocked worker-time. Worker scaling is only 1.27× for 4× workers (11→44),
   plateauing at 2×CPU. Verified: golden (word,split) output is byte-identical
   across 1- and 44-worker runs (`md5 500e8d09…`), so the matching logic itself
   is already deterministic and order-independent.
2. **`RunesPlus` + `[]rune→string` conversion dominate CPU/alloc.** `RunesPlus`
   = 67.6% of allocations (24GB, 621M calls). `runtime.slicerunetostring` (the
   implicit `string([]rune)` in `IsInInflections`) = ~16% flat CPU, 81% of it
   from `IsInInflections`. Together they drive 19% of CPU into GC. Both costs
   concentrate almost entirely in **Split3 (61.9%) and Split2 (37.5%)** — the
   two hot loops.

This thread implements two changes, each behind a **measured before/after gate**,
and folds in one confirmed latent bug fix.

## Correctness gate (applies to every change)

The sorted set of `(word, split)` pairs must stay **byte-identical** to baseline.
- Tier A golden: 20k deterministic sorted sample, `md5 = 500e8d090bb7497d554a2d20a83358c2`.
- Tier B golden: full corpus — capture once before any change (see plan 0.4).
- The `rules`, `route`, `time` output columns are NOT part of the gate (route/time
  vary legitimately; `rules` changes intentionally in Change C). Compare only the
  `(word, split)` projection.

If a change alters the `(word, split)` set, it is wrong — stop and diagnose, do
not re-freeze the golden.

## Measured-benefit gate (the point of this thread)

"Benefit" = **full-corpus (Tier B) wall-clock, median of 3 fresh processes,
before vs after**, measured on a quiet machine (`uptime` checked; report
median + spread). A change is kept only if the measured median improves beyond
the run-to-run noise band. Each change is also confirmed by the specific profile
metric it targets (below). No change is accepted on a single run or on a
micro-benchmark alone. State each result as a fraction of the standalone
deconstructor command (and note the deconstructor is itself one stage of
`makedict`).

---

## Change A — per-worker MatchData (remove global lock contention)

### Design
Each word is dispatched to exactly one worker (`jobs` channel), and all recursion
for that word runs synchronously inside that worker's `deconstruct(w)` call. The
four global mutexes exist only because the accumulator maps/slices are shared
containers — per-key access is already single-threaded. Therefore:

- Give each worker its **own** `MatchData` (local `MatchedMap`, `TriedMap`,
  `ProcessCount`, `WordStats`, `MatchedItems`, and a local set of matched words).
  No locks in the hot path.
- Add a collecting worker-pool variant, e.g.
  `RunCollect[S, T any](n int, newState func() S, jobs <-chan T, fn func(S, T)) []S`,
  returning each worker's state. Keep the existing `Run` for other callers.
- After compute, **merge**: keys are disjoint across workers (one word → one
  worker), so merging `MatchedMap`/`ProcessCount` is conflict-free; concat
  `MatchedItems`/`WordStats`; apply matched-word deletions to the global
  `Unmatched`. `BlockedTries`/`MaxedOut` stay as global atomics.
- `Summary()`/`Save*()` run on the merged `MatchData` unchanged; the existing
  final sort keeps output order deterministic.

### Constraints / hazards
- Every splitter reaches `data.M` as a package global. Threading per-worker state
  through `SplitRecursive` → sub-splitters requires either passing the accumulator
  down the call chain or binding it per job. Prefer passing it explicitly
  (a `*MatchData` param) over a new global; if that balloons the diff, an
  acceptable fallback is a per-job accumulator captured in the `fn` closure and
  reached via the `WordData` — decide by which keeps the splitter signatures
  cleanest, and record the choice in plan notes.
- Preserve `NotTriedYet` dedup semantics exactly (now per-worker, which is safe
  since a word is owned by one worker).
- Must not change `SaveToDb`, output formats, or limits.

### Accept if
- Tier B wall-clock median improves beyond noise (primary).
- Block profile: `muMatched` share of block time drops from ~72% to a small
  fraction; worker sweep {11,22,44} scales better than the baseline 1.27×.
- Golden `(word,split)` MD5 unchanged (Tier A 500e8d09 + Tier B golden).

### Reject / revert if
- Tier B median is within noise of baseline, or golden changes.

---

## Change B — kill `RunesPlus` + `[]rune→string` churn in Split2/Split3 only

### Design (confined, NOT a global type swap)
Do **not** change `WordData.Word`/`Middle` from `[]rune` to `string` globally —
~20 splitters slice by rune index (`word[:len(word)-3]`, `len(w.Middle) <= 3`),
and a byte-index string swap silently corrupts multi-byte Pāḷi (`ā`, `ṃ`, …).

Instead, inside **Split2 and Split3 only** (99.4% of the cost):
- Convert the middle to a string **once per call**, and build a rune→byte offset
  table once: `s := string(word); off := runeOffsets(s)` (`off[i]` = byte index
  of rune `i`; `len(off)-1` = rune count).
- In the split loops, form candidate sub-words as **substrings**
  `s[off[i]:off[j]]` — O(1), zero allocation, and directly usable as a map key.
- Add `IsInInflectionsStr(s string) bool` (direct map lookup, no conversion);
  use it in these loops instead of `IsInInflections([]rune)` + `string()`.
- For sandhi rule application, replace `RunesPlus` with string concatenation of
  the substring prefix/suffix + `string(sr.Ch1/Ch2)` (small, only on rule match).
- Materialize `[]rune` again **only when a match is found** (rare relative to
  attempts), to feed the existing `ToFront`/`ToBack`/`MakeCopy` bookkeeping that
  the rest of `WordData` still expects. This keeps the change local — no
  `WordData` struct change, no other splitter touched.

### Constraints / hazards
- **Multi-byte safety is the whole risk.** Never index the string by a rune
  count as if it were a byte offset. All slicing goes through the offset table.
  `len()` on the string is byte length — use `len(off)-1` for rune count.
- Keep the `[]rune` `IsInInflections` for all other splitters — do not remove it.
- Behaviour must be identical: same candidates tested, same matches produced.
  The golden `(word,split)` gate is the proof.

### Accept if
- Tier B wall-clock median improves beyond noise, on top of Change A (primary).
- Alloc profile: `RunesPlus` alloc share collapses toward ~0; total alloc_space
  drops sharply; `slicerunetostring`/`encoderune` CPU collapses; `gcBgMarkWorker`
  CPU drops from ~19%.
- Golden `(word,split)` MD5 unchanged.

### Reject / revert if
- Tier B median within noise, or golden changes, or any multi-byte regression.

---

## Change C — fix `MakeCopy` RuleBack (confirmed latent bug, cheap)

`data/worddata.go:MakeCopy()` clones `RuleFront` twice and never clones
`RuleBack`, so copies start with `nil` RuleBack and silently drop back-rule
history in the output `rules` column for multi-step splits.

- Fix: clone `RuleFront` once, clone `RuleBack` once.
- This changes the `rules` output column (now complete) but **not** the
  `(word,split)` set — `RuleBack` feeds only `ruleString()` output, never a split
  decision. Verify that claim holds (golden `(word,split)` unchanged).
- Land it with whichever change touches `worddata.go` least disruptively; it is a
  ~2-line fix.

---

## Committable tests (correctness, permanent)

Add Go unit tests (these ship; the wall-clock benchmarks are scratchpad-only):
1. `data/worddata_test.go` — `MakeCopy` deep-copies both `RuleFront` and
   `RuleBack` (mutating the copy must not affect the original, and vice-versa).
2. `runeOffsets` / substring helper test — round-trips a multi-byte Pāḷi word
   (e.g. `bhikkhūnaṃ`, `ñāṇadassana`) and proves `s[off[i]:off[j]]` equals the
   `string(runes[i:j])` it replaces, for all i≤j.
3. `IsInInflectionsStr` returns the same result as `IsInInflections([]rune(s))`
   on a small fixture map.

## Out of scope
- `map[string]struct{}` for the inflection maps (H7): ~95MB memory, negligible
  speed per both benchmark passes — deferred; not worth the call-site churn now.
- The Split3 commented-out early-exit pre-check: only worth it after A+B; separate
  follow-up.
- Any change to `SaveToDb`, output schema, limits defaults, or `exporter/`.

## Risks
- Change B multi-byte correctness (mitigated: confined to 2 files, offset table,
  golden gate, unit test).
- Change A merge correctness / diff size if state threading is awkward (mitigated:
  disjoint keys, explicit param, golden gate).
- Measurement noise on a shared machine (mitigated: 3 fresh runs, median+spread,
  `uptime` check, profile confirmation of the targeted mechanism).
