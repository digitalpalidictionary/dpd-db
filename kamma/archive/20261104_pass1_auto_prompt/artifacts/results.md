# Pass1 Auto prompt test — results

## 1.1 Target model ids (checked 2026-11-04)

Script: `artifacts/eval/check_models.py`, `artifacts/eval/check_deepseek_ids.py`.

- DeepSeek API `/models` lists only `deepseek-flash` and `deepseek-v4-pro`. There is no `4.1` id on the direct API.
- `deepseek-v4-flash` (the id in `tools/ai_models.json`) is still accepted; the API answers with `"model": "deepseek-flash"`. So it is an alias of the current flash model.
- `deepseek-v4.1-flash` is rejected: `HTTP 400: The supported API model names are deepseek-flash, deepseek-v4-pro, but you passed deepseek-v4.1-flash.`
- `tools/ai_models.json` not changed: no 4.1 id exists, and the current id works.
- **Test id used: `deepseek` / `deepseek-v4-flash`** (same id the gui2 dropdown sends).

Test request results:

- `deepseek/deepseek-v4-flash` → `'ok'` — `SUCCESS in 0.93s. deepseek/deepseek-v4-flash`
- `zai/glm-5.3-flash` → **failed** — `HTTP 429: [1310] Weekly/Monthly Limit Exhausted. Your limit will reset at 2026-11-05 10:05:01`
- Z.ai `/models` does list `glm-5.3-flash`. **Dropped from the test** (owner, 2026-11-04: "We don't need a test with GLM. Deepseek is enough.").

## 1.4 Coverage of the target books (2026-11-04)

Scripts: `artifacts/eval/coverage.py`, `coverage_short.py`, `coverage_stem.py`. Missing words use the controller's `is_missing()` rules (`artifacts/eval/common.py::MissingChecker`).

| book | missing words | ≥1 SC sentence (old) | ≥1 ePitaka sentence | ≥1 sentence (new) | ≥1 PEU entry |
|---|---|---|---|---|---|
| Vv | 1012 | 0% | 98% | 98% | 54% |
| Pv | 720 | 0% | 96% | 96% | 56% |
| Ap-i | 5045 | 0% | 100% | 100% | 51% |
| Ap-ii | 3758 | 0% | 100% | 100% | 53% |
| Bv | 898 | 0% | 100% | 100% | 60% |
| Cp | 0 | - | - | - | - |

- Cp shows 0 because every one of its 528 missing words already has an answer in `pass1_auto_cp.json` (so `is_missing()` skips it). With that file ignored: 528 missing, 521 (99%) with ≥1 ePitaka sentence. Set K takes its Cp words from these 528.
- PEU cut used (all target books): exact 624, cut 1: 3722, cut 2: 484, cut 3: 1257.

### 20 random PEU matches (right/wrong)

18 right, 1 near, 1 doubtful:

- right: guṇadhāraṇo→guṇadhāraṇa, vinābhūtā→vinābhūta, tiṇṇoghehi→tiṇṇogha, upaṭṭhahitvāna→upaṭṭhahitvā, mānaggi (exact), suddhamānaso→suddhamānasa, panthapaṭipanne→panthapaṭipanna, pupphavasso→pupphavassa, antojālikatā→antojālikata, samudayadukkhaniccataṃ→samudayadukkhaniccatā, ratanamaṇḍapaṃ→ratanamaṇḍapa, micchādiṭṭhigatāsayo→micchādiṭṭhigatāsaya, asamappaṭipuggalo→asamappaṭipuggala, sotamanoharaṃ→sotamanohara, sakiyā→sakiya, vanakoraṇḍiyo→vanakoraṇḍiya, sabbītiparivajjito→sabbītiparivajjita, vātadhutā→vātadhuta
- near: sabbaphalado→sabbaphala (a component, not the word)
- doubtful: sakāsayā→sakāsa

### Stem length check

PEU hits by stem length after the cut (all target books, 11,433 missing words): 1–3 letters: 44, 4: 106, 5: 232, 6: 323, 7: 456, 8+: 4302. Hand-read samples of 10: stem 4 ≈2 right, 5 ≈3, 6 ≈3, 7 ≈7, 8+ 10/10.

**Decision: no minimum stem length.** Short stems are often wrong, but they are only 12% of PEU hits (705 of ~5,900); most missing words in these books are long compounds (owner, 2026-11-04: "Don't invent problems"). The prompt already tells the model PEU is only a guide.

## 1.5 Word sets (2026-11-04)

Script: `artifacts/eval/pick_words.py` (seed 20261104). Output: `artifacts/eval/words.json`.

- Gold pool: 5,217 words in `dpd.db` with a saved `_prompt` and a valid-JSON `_response`. Only 217 of them are in the six verse books I checked.
- Set G: 50 words. By book: ja 33, cp 17. No `th`, `thi`, `dhp` or `snp` words were picked from the verse pool: none made the first 50 after the shuffle. 25 words had no sentence in their saved prompt, 25 had at least one.
- Set K: 50 words. Vv 8, Pv 8, Ap-i 8, Ap-ii 8, Bv 9, Cp 9. Cp words come from the 528 with old answers (all of Cp), so the old answer exists for them too.

## 2.1 Old prompt builder (2026-11-04)

Script: `artifacts/eval/check_old_prompt.py` (parser: `artifacts/eval/saved_prompt.py`).

- `gui2/pass1_context.py::build_old_prompt` holds the old `compile_prompt` text, copied by script so every space is kept.
- Fed the sentences and related entries parsed from each saved `_prompt` file, it rebuilds **all 50 G-word prompts byte for byte** (50 of 50 identical; the plan asked for 3).

## 2.2 New prompt (2026-11-04)

Module: `gui2/pass1_context.py` (`build_new_prompt`, `SYSTEM_PROMPT`, `choose_sentences`, `related_headwords`, `related_entry_dict`, `load_allowed_values`). Tests: `tests/gui2/test_pass1_context.py`, 10 passed. Breaking the sentence order fails 2 of them; breaking the duplicate check fails 1. Samples: `artifacts/eval/sample_prompts.md` (script `sample_prompts.py`, context builder `context.py`).

What the new prompt does, in order:

1. Fixed part (the same for every word, so the provider prompt caches can reuse it): task, the 14 exact JSON keys, one worked example (DPD entry 55988 `lokanāyaka`, word in text `lokanāyakaṃ`), field rules, then the real dictionary values for `pos` (30, with descriptions), `pattern` (153, most common first), `root_sign` (66), `root_key` (753, with meanings). Owner, 2026-11-04: "in case of doubt, you can always include the list of real dictionary values for any field, pick one."
2. Word part: book name and text type, the word, up to 3 sentence pairs (SC first, then ePitaka) or "No sentences found.", PEU entries with their caveat and the gender codes, related entries as JSON objects in the answer's shape.

Rule changes against the old prompt, each checked against `dpd.db` (recent entries, id > 80000, where practice changed):

- Nouns and adjectives use the stem (`pamādī`, `punesanā`), not the vocative. The old "vocative singular" rule is wrong for ī-stems.
- Present, imperative, optative and future forms go under the present 3rd singular. The `ati pr` inflection template covers pr, imp, opt and fut (checked in `inflection_templates`). Aorists get their own headword.
- An enclitic or quotation `ti` at the end is dropped (gold: `suvihīnaṃva` → `suvihīna`, `pāpamupalimpatīti` → `pāpamupalimpati`).
- Compound verbs (`pāpaṃ + akāsi`) are "comp vb", not sandhi.
- `family_compound`: verbs and participles list themselves (recent verbs: 1347 of 2147 self, 458 empty); derived nouns list their base word (recent: 1099 of 1281 filled). Sandhi: empty (1461 of 1483).
- Root fields also for nouns made from a root word (recent "from X" nouns: 964 of 1281 have a root). `root_base` only for verbs.
- Pattern word order fixed (old answers wrote `masc a`; DPD writes `a masc`), with the stem rule shown on six real entries.
- Typos fixed ("nominitve", "absolutes adverbs", "left example as they are").

Leak checks:

- Related entries: the G word's gold ids are removed (`exclude_ids`). None of the 3 G samples shows its gold `lemma_1` in the related block.
- **Fixed part:** a first draft took its rule examples from the gold words' own rows (`pamādino → pamādī`, `jaggato → jagganta`, and about 20 more). That would hand the model the answer for those gold words. Every example was replaced with entries outside both word sets. `sample_prompts.py` now scans the rules and example for every G and K word, every gold `lemma_1`, and the gold `construction`, `family_compound`, `family_root` and `root_base`: **no leaks**. Planting three gold values made the scan report all three.

Prompt length (characters; tokens ≈ chars / 4):

| word | set | old | new | new word part only |
|---|---|---|---|---|
| vīraka | G | 6098 | 28178 | 3201 |
| jhāpaye | G | 4887 | 26924 | 1947 |
| dharaṇīruhaṃ | G | 5187 | 27199 | 2222 |
| revatīvimānaṃ | K | 5009 | 26936 | 1959 |
| jinapabhuttamaṃ | K | 7506 | 30220 | 5243 |
| kapirājacariyā | K | 6471 | 28577 | 3600 |

The new prompt is about 5× longer (about 7k tokens against 1.5k). About 25k characters of it is the fixed part, mostly the root list (about 16k). The cache-hit share was not measured: `AIManager` does not return the token usage.

NOTICED: the related entries are often noise. `vīraka` gets `tatha`, `anurūpa` and five `eva` entries, from an old deconstruction in `lookup`. The old prompt had the same entries, so the comparison stays fair.

## 2.3 Dry run (2026-11-04)

Script: `artifacts/eval/dry_run.py <provider> <model>`. Words: the first K word of Vv, Pv, Ap-i, Ap-ii and Bv (`revatīvimānaṃ`, `duṭṭhavāco`, `pañcapaññāsake`, `kusaṭṭhakadāyakattherassāpadānaṃ`, `dhammavimalamādāsaṃ`).

- `deepseek/deepseek-v4-flash`, first prompt: 5 of 5 valid JSON, exact keys in order, all strings. Answers kept in `raw/dry/v1/`. Content faults: both adjectives got a nominative `lemma_2` (`duṭṭhavāco`, `pañcapaññāsako`), against DPD practice (adjectives: `lemma_2` = `lemma_1` in 19,042 of 19,075). `family_compound` listed the suffix `ka`.
- Prompt fix: the `lemma_2` rule now names adjectives and participles with an example (`pasannacitta`, not `pasannacitto`). The `family_compound` rule now says suffixes are not parts. Leak scan rerun: none.
- `deepseek/deepseek-v4-flash`, fixed prompt: 5 of 5 valid. Both adjectives now have `lemma_2` = `lemma_1`; `ka` no longer in `family_compound`. The neuter title `kusaṭṭhakadāyakattherassāpadāna` now has `lemma_2` = `lemma_1` (should be `…apadānaṃ`), one word, left for the Phase 4 analysis. Answers in `raw/dry/deepseek-v4-flash/`.
- `zai/glm-5.3-flash`: not run. Dropped from the test (owner, 2026-11-04).

NOTICED: the Apadāna titles (`kusaṭṭhakadāyakattherassāpadānaṃ` = `…therassa apadānaṃ`) and `dhammavimalamādāsaṃ` (`…vimalaṃ ādāsaṃ`) are sandhi of two inflected words; the model treats them as one compound. A Phase 4 point if the K results show it often.

## Phase 3 — test run and scores (2026-11-04)

Run: `artifacts/eval/run.py`, DeepSeek `deepseek-v4-flash`, 200 calls (50 G + 50 K, old + new), 200 raw files, 0 failures.
Scored: `artifacts/eval/score.py` → `artifacts/eval/scores.csv`. Exact match after trimming; `lemma_1` against the gold lemma without homonym number; best-matching gold headword. n = 50 (25 + 25 in the splits), so one word is 2 points.
Hand check: `vīraka`, `jhāpaye`, `nillāleti` (new answers vs `dpd_headwords` rows): all 24 field marks agree with `scores.csv`.

Set G, all 50 words (% of words matching gold):

| version | json% | keys% | lemma_1 | pos | root_key | family_root | family_compound | construction | stem | pattern | total% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| old | 100 | 100 | 64 | 78 | 76 | 82 | 42 | 30 | 62 | 62 | 62.0 |
| new | 100 | 100 | 88 | 84 | 88 | 88 | 42 | 50 | 74 | 74 | 73.5 |
| hist (saved answers) | 100 | 96 | 46 | 62 | 68 | 70 | 28 | 30 | 48 | 40 | 49.0 |

Words with no sentence in the old prompt (25): old 62.5, new 73.0, hist 52.5.
Words with a sentence in the old prompt (25): old 61.5, new 74.0, hist 45.5.
Set K (50): JSON valid old 100%, new 100%; exact keys old 100%, new 98% (one new answer has different keys; read it in Phase 4).

Early read (the verdict is Phase 4): no field is lower for new; family_compound is equal (42 vs 42). `vīraka` new answer says "name of a bird", but the sentence addresses a person called Viraka. Meaning is not scored, so the owner judges it in the spot check.

## Phase 4.1 — rule check (2026-11-04)

| rule | old | new | result |
|---|---|---|---|
| Set G total field-match higher | 62.0% | 73.5% | PASS |
| no field drops more than 5 points | — | no field drops; lowest change is family_compound 42 → 42 | PASS |
| valid-JSON rate not lower (G and K) | 100% / 100% | 100% / 100% | PASS |
| owner prefers new answers in the spot check | — | — | pending (4.3) |

No field dropped overall, but some words lost a field the old prompt had right. Per field, words lost / won (old right → new wrong, and the reverse): lemma_1 1/13, pos 1/4, root_key 1/7, family_root 2/5, family_compound 3/3, construction 1/11, stem 1/7, pattern 3/9.

Causes of the losses (each answer read):
- `pāpamupalimpatīti`: new kept the quotation "ti" in lemma_1 and left family_compound empty, though the prompt has a rule to drop -ti. The model ignored the rule once.
- `dinnadānassa`: new called it adj (pos and pattern "a adj"); gold is nt. A real judgement call: "dinnadāna" works as both.
- `jaggato` (gold jagganta 3): new chose √jāgar 1, old √jagg. Both roots are in the allowed list; DPD files this word under √jagg.
- `pamādino`: new left family_root empty (gold "pa √mad").
- `maṭṭhakuṇḍalī`: family_compound "maṭṭha kuṇḍalī" vs gold "maṭṭha kuṇḍala": the last part not put in dictionary form.
- `sirasaṃ`: family_compound empty vs gold "siras".
- `janayitvāna`: construction "jana + ya + tvāna" vs gold "janaya + itvāna".
- `jhāpaye`: stem "jhāpaya" vs gold "jhāpay" (the stem rule says lemma_1 minus the pattern's ending; "ati pr" gives "jhāpay").
- `candasūriyā`: pattern "a masc pl" vs gold "a masc" (the word is plural in the text; both patterns exist).
- `pāpamakāsi`: pattern empty vs gold "āsi aor" (treated the phrase as an idiom).
No single cause repeats more than twice. None is a fault in the new context; most are model slips the editor will catch.

Set K exact-keys 98% (new): `jhānaparāyanā` added an extra empty "comment_2" key; all 14 expected keys present. Pass1 Add fills only fields it has (`DpdFields.update_add_fields` uses `fields.get(...)`), so the extra key is ignored.

## Phase 4.2 — spot-check page (2026-11-04)

`artifacts/spot_check.html`, built by `artifacts/eval/spot_check.py` (fixed seed 20261104). 20 words: G 5 with and 5 without an old sentence; K Vv 2, Pv 2, Ap-i 2, Ap-ii 2, Bv 1, Cp 1. Structure check: 20 cards; every G table has 4 columns × 14 rows, every K table 3 × 14. 14 "no sentence" boxes, all on the old side (5 G words without a sentence + 9 K words from books with no SC text); every new prompt had at least one sentence.

## Phase 4.3 — owner verdict (2026-11-04)

**Verdict: new prompt is better — ship it (Phase 5).** Owner: "yeah in general looks cool, not perfect, but defintely better." Also: "this whole thing is just a support for the human so it doesn't have to be perfect."
All four "genuinely better" rules pass.

## Task 5.3a — old Pass1 Auto files retired (2026-11-04)

Moved all 18 `gui2/data/pass1_auto_*.json` into `gui2/data/pass1_auto_retired/20261104/`. `sha256sum -c` on the moved copies: 18 OK, 0 failed. No code under `gui2/` reads the folder.

Answer counts before the move: dhpa 9588, nidd1&2 3983, jaa 3400, ja 1493, vin5 667, cp 646, dhp 236, th 36, thi 17, an 9, text 9, iti 5, snp 5, and 0 in dn, mn, sn, ud, vin3&4 (total 20,104).

## Task 5.3 — kept K-set answers saved (2026-11-04)

`artifacts/eval/save_k.py` saved the 50 new-prompt DeepSeek answers into fresh files, with the `[deepseek: deepseek-v4-flash]` comment prefix, `example_*`/`translation_*` from the chosen sentences, and keys outside the answer list dropped. Old keys were compared before and after (all files were empty before, so none changed).

| book | keys before | keys after |
|---|---|---|
| vv | 0 | 8 |
| pv | 0 | 8 |
| ap | 0 | 16 |
| bv | 0 | 9 |
| cp | 0 | 9 |
