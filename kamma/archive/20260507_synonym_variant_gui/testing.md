# Testing instructions

Work through these as real headwords come up. Note results / issues
inline as you go (or move into review.md when done).

## Setup
- Start gui2 normally. Detector now builds at startup (end of
  `DatabaseManager.initialize_db`), so the first synonym/phonetic
  suggestion in a session is instant — but startup itself is a few
  seconds slower than before.
- After saving a headword (add/update/delete), the detector rebuilds
  in a **background thread** — saves return immediately. The previous
  detector keeps serving suggestions until the new one is ready, then
  atomically swaps in. Caveat: a relationship that was *just* saved
  may not be visible to the detector for a few seconds. By the time
  you reach the next headword this is no longer a concern.

## 1. Synonym suggestion — multi-meaning
- Pick a headword with `pos`, `lemma_1`, and `meaning_1` containing
  `; ` (multiple meanings).
- Edit `meaning_1`, then **tab/click away** to blur it.
- Expect:
  - `synonym` field populates with comma-separated lemmas.
  - `synonym_add` (right side, red) shows the same value.
  - Status bar: "N synonyms suggested" or "No synonyms found".

## 2. Synonym suggestion — single-meaning (new path)
- Pick a headword with a **single** `meaning_1` (no `; `) and a known
  sibling sharing the same cleaned meaning + same case/person grammar
  signature.
- Trigger: blur `meaning_1`.
- Expect candidates in both `synonym` and `synonym_add`.

## 3. Synonym fallback on focus
- Open a fresh headword, fill `pos` + `lemma_1` + `meaning_1`, then
  tab straight to `synonym` without first blurring `meaning_1` from a
  click elsewhere.
- Expect: focusing `synonym` triggers the same compute (since the
  blur-side flag wasn't set).

## 4. Phonetic-variant suggestion
- Pick a headword that should have a phonetic sibling — one of:
  - same `construction_clean` + same `pos`
  - one phonetic-rule edit away (e.g. `kk↔k`, `iya↔ya`, etc.)
  - `*e` ↔ `*aya` or `ya/iya/īya` root_sign sibling at same root_family
- Click into `var_phonetic`.
- Expect:
  - Candidates in `var_phonetic` and `var_phonetic_add`.
  - `var_phonetic` helper text reads `lemma: rule_label` per candidate
    (e.g. `kicca: same_construction; kīta: rule:i<->ī`).
  - Status bar: "N phonetic variants suggested" or "No phonetic
    variants found".

## 5. Already-recorded suppression
- On a headword that already has lemma X stored in
  `synonym`/`var_phonetic`/`var_text`, lemma X must not appear in any
  fresh suggestion.

## 6. Accept-time exclusivity (← button)
- Set up: a lemma `Y` sitting in `synonym`. Imagine the system suggests
  `Y` as `var_phonetic`, so `var_phonetic_add` shows `Y`.
- Click the ← button on `var_phonetic_add`.
- Expect: `Y` moves out of `synonym` into `var_phonetic`, and `variant`
  also gains `Y` (legacy mirror). Vice versa for accepting into
  `synonym` — the lemma should leave `var_phonetic`.

## 7. Re-trigger on meaning_1 edit
- After a synonym suggestion has populated, edit `meaning_1` again and
  blur. Expect a fresh recompute that overwrites the previous
  suggestion (the wipe-and-tell-user behaviour from the old code is
  gone).

## 8. Detector freshness after save
- Add or edit a headword that creates a new synonym/phonetic
  relationship, save it. Open the partner headword. The new
  relationship should now be visible to the detector (no stale
  suggestions; the partner won't be re-suggested if the relationship
  was just stored).

## Known limitations
- GUI updates only the **current** headword. Bidirectional partner
  cleanup is still the offline scripts' job (`add_synonym_variant_*`
  and `add_phonetic_variants` in `db_tests/single/`).
- The detector skips suggesting back any lemma already present in the
  current headword's `synonym`/`var_phonetic`/`var_text`. The
  `variant` legacy field is not used for suppression — it should
  always be a subset of the other three on a clean db.
