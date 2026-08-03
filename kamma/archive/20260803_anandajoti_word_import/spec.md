# Spec — import Anandajoti's word list into pass2add via the X button

## Goal

Turn the research note `~/MyFiles/Obsidian/Vicaya/2026-08-02 - Anandajoti-DPD-words.md`
into a queue of raw DPD headword data, loaded one entry at a time into pass2add by
clicking the **X** button — so the words can be reviewed, edited and saved without
typing or copy-pasting from the note.

## Decisions (confirmed with the user, 2026-08-03)

1. **Scope:** all words the note recommends — Part I (the 6 flagged words), §7b (prosody
   metres), §8a (grammar terms).
2. **X button is fully repurposed.** The SQL `filter_query` path is removed; X becomes
   purely the JSON import queue. (The importlib live-reload hack in `_click_x_button`
   existed only to pick up edits to `filter_query`, so it goes too.)
3. **Existing words → `_add` review fields.** Base fields hold the current db values,
   the note's proposals land in the right-hand `_add` fields to accept per-field.
   **New words → base fields directly** (nothing to compare against; `id` left blank so
   `get_current_values()` assigns the next id at save time).

## Verified facts (queried against live `dpd.db`, 2026-08-03)

- **Part I is mostly already entered** (ids 89894–89899, `origin = pass2`):
  `pādayuga 1`, `pādayuga 2`, `dohanta`, `doha` (meaning_1 empty), `anuggata 2.1`,
  `dīpaka 1.2` (decoy). So Part I contributes mostly *updates*, not new words.
- **All 25 §7b metres and all 15 remaining §8a grammar terms are absent from the db.**
  Exceptions found: `muddhaja 2` (id 53006) already carries the (gram) retroflex sense
  and `hīyattanī` (id 71360) already covers §8a's `hiyattana` — both dropped from the
  queue as already done.
- **`VUTT<n>` is not a DPD source code.** The db cites grammar works as lowercase
  free-text in `source_1` — `kaccāyana` (526), `padarūpasiddhi` (11),
  `saddanīti padamālā` (9). The queue follows that convention (`vuttodaya`,
  `saddanīti`, …), not the note's invented codes.
- `Pass2XManager` is constructed in exactly one place (`pass2_add_view.py:70`) and has
  no tests.
- `gui2/data/pass2_eg_words.json` is gitignored; the new queue file gets the same
  treatment since it is drained as it is worked through.

## Queue file

`gui2/data/pass2_x_words.json` — dict keyed by lemma, mirroring `pass2_eg_words.json`:

```json
{
    "pathyā": {
        "lemma_1": "pathyā",
        "pos": "fem",
        "meaning_1": "the normal form of a metre",
        "source_1": "vuttodaya",
        "notes": "...",
        "comment": "new — §7b"
    },
    "uttama 1": {
        "id": "14631",
        "source_2": "SNP29",
        "...": "...",
        "comment": "update — add Snp 452 example (§4)"
    }
}
```

- `id` present → update mode (load that headword, proposals into `_add`).
- `id` absent → new word (values straight into the base fields).
- `comment` is popped before filling fields and shown in the message bar — it carries
  the note's caveats (unverified attestations, renumbering decisions the editor must make).

## The X button is a scratch slot (user, 2026-08-03)

The X button is deliberately throwaway — it exists for one-off data entry, and the batch
it serves changes every time. So:

- **No tests may pin down its behaviour.** The queue file is gitignored and swapped out
  per batch; the data never reaches the test suite. Adding a test for `Pass2XManager` or
  `_click_x_button` would just have to be rewritten with the next batch.
- The code stays generic: nothing about *this* batch (Anandajoti, prosody, grammar terms)
  appears in any `.py` file. Changing what X does means replacing
  `gui2/data/pass2_x_words.json`, exactly as it previously meant editing `filter_query`.
- Because the file is hand-authored and hand-swapped, cheap shape-validation on load is
  worth keeping — a malformed hand-edit should say so, not crash oddly later.

## Out of scope

- No parser for the note. The conversion is one-off; the JSON is authored directly.
- No lexicographic decisions taken automatically: where the note flags a renumbering
  (`anuggata` → `anuggata 1.1`, `doha` → `doha 1`) or an unverified attestation
  (`doha 2`'s DA.I,296, `aññātāvī 1.1`), the proposal is queued with the caveat in
  `comment` for the editor to accept or reject.
- The §7c/§7d/§8c terms the note rules out (Sanskrit-only, unverified metre names,
  transparent compounds) are not queued.
