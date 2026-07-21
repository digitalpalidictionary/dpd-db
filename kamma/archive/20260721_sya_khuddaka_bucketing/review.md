# Review — SYA Khuddaka bucketing

Verdict: **PASS.** Two independent review passes, run in parallel; no code defects.

## Reviews run
1. **CodeRabbit** (`coderabbit review --agent --base main --type uncommitted`) — **zero findings
   on the three changed code files** (`4SYA.go`, `sya_file_map.json`, `ebt_counter.py`). It
   raised one doc-hygiene nit on this thread's `spec.md` (stale "Research checklist" section) —
   fixed. Its other three findings were on the unrelated, already-archived `budsir_thai_texts`
   thread's docs — out of scope, not touched (concurrent-threads rule).
2. **Independent from-scratch subagent audit** — verified all four risk areas against the
   actual code and regenerated data; **no defects**:
   - Positional consumption safe: SYA still 30 sections, template indices ≤26 in range.
   - Split marker unique (line 6427); byte-slice preserves the exact word multiset; no
     multi-char construct (`<…>`, `(pts …)`, quotes) straddles the cut; `CleanMachine`
     (`\n`→space, `addHyphenatedWords=false`) never joins lines. Error path sound.
   - Synthetic keys character-exact between `4SYA.go`, `sya_file_map.json`, and the live JSON —
     no section silently drops a text.
   - `_sya_is_ebt` classifies exactly files 01–02, 09–25 and `::th-thi` (20 keys); `::vv-pv`
     and all Non-Canonical/commentary keys excluded. Consistent with CST `ebts` (`s0508`/`s0509`
     EBT, `s0506`/`s0507` not).

## Verification recap
- Slice sum == pre-split file-26 freq word-for-word (46434 = 23110 + 23324).
- `sya_freq.json` byte-identical (pure reassignment, no gain/loss).
- Bucket movement proven: `theragāthāya` kn2→kn1; `pabhāsatīti` (Vv/Pv) stays kn2.
- `go vet` clean; `go test ./go_modules/...` ok; ruff + pyright clean; full suite 1687 passed.

## Tracked changes (blast radius as specced)
- `go_modules/frequency/setup/4SYA.go`
- `go_modules/frequency/file_maps/sya_file_map.json`
- `scripts/build/ebt_counter.py`
(`shared_data/frequency/*.json` are gitignored artifacts; live `dpd.db` freq columns + `ebt_count`
regenerate in the normal `/db` build.)
