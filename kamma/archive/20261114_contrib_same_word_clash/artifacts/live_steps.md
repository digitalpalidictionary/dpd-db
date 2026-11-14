# Putting the book split live

`<repo root>` is the dpd-db folder on the laptop. Do the steps in this order.

1. Close gui2 on the laptop. The daily pull skips while gui2 is open.
2. Pull the contributors' finished words now, so the old draft files lose them
   before the split:

   `cd <repo root> && just contrib-pull`

   Check that `logs/contrib_pull_status.txt` says `pulled`. If a contributor
   already pulled today, move `logs/contrib_pull_status.txt` aside first.
3. Dry run. It prints counts and writes nothing:

   `cd <repo root> && uv run kamma/threads/20261114_contrib_same_word_clash/artifacts/split_drafts.py`

   Expected (dry run of 2026-11-14): `ap` gives `tha-ap` 341 and `thi-ap` 17;
   `nidd1&2` gives `mnd` 158 and `cnd` 89, with 478 bold tag fragments dropped; `ja` gives `ja-1` 153, `ja-2` 154,
   `ja-3` 124, `ja-4` 89, `ja-5` 137, with one unplaced word (`mavoca`, it goes
   to `ja-5`). No other word is left without a home.
   The numbers shift if the pull removed words in step 2.
4. Write the new files and delete the three old ones:

   `cd <repo root> && uv run kamma/threads/20261114_contrib_same_word_clash/artifacts/split_drafts.py --write`
5. Run the tests, then commit and push to `main` after review:

   `cd <repo root> && uv run pytest tests/gui2 tests/tools tests/scripts -q`
6. The server pulls from GitHub in its nightly window. Until it does, a contributor
   who has `ap`, `nidd1&2` or `ja` open keeps working on the old book.
   Finished-word entries under the old keys (`ap`, `nidd1&2`, `ja`) are NOT carried
   over to the new part files. On 2026-11-14 only two test users had any (18 words
   under `ap`, none left in the new files), so nothing was lost. A word finished
   under an old key after the split would be offered again. Before the push, check
   the server's finished lists for those three keys.
7. When a contributor starts a book after the pull, the dropdown shows `tha-ap`,
   `thi-ap`, `mnd`, `cnd` and `ja-1` to `ja-5`.
