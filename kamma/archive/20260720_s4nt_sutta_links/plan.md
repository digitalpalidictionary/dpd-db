# Plan: Add s.4nt.org to sutta links

## Round 1 (commit 9ab17694 - shipped, then rejected on live test)
- [x] 1. Curl-probe s.4nt.org live to determine the real per-piṭaka URL
      shape (superseded the original single-pattern assumption).
- [x] 2. Design segment-fragment approach for vagga/sutta precision within
      container pages (superseded per user - head of page is sufficient).
      **← this call was wrong, see round 2.**
- [x] 3. Find and clone the site's source repo
      (https://github.com/frankksutta/s.4nt) to
      `~/MyFiles/2_Resources/Code/s.4nt/` for ground-truth verification
      and future reference.
- [x] 4. Finalize `s_4nt_link` `@cached_property` on `SuttaInfo`
      (`db/models.py`): DN/MN direct sutta page, SN/AN saṃyutta/nipāta
      container, KN book container (18 books incl. `tha-ap`/`thi-ap`),
      else `None`.
- [x] 5. Template rows in goldendict + webapp headword templates.
- [x] 6. Unit tests in `tests/db/test_sutta_info.py` - 10 tests, all
      passing (asserted container-page-only, no fragment).
- [x] 7. Lint gate (ruff check, ruff format, pyright) - clean.
- [x] 8. Cross-check page-level paths against the site's file tree - 0
      mismatches. **But never verified sutta-level precision within a
      container page - that gap is what the user caught live on SN12.5.**

## Round 2 (this correction - sutta-level precision)
- [x] 9. Read the site's own embedded JS router (`jumpToRef`/`jumpToHash`)
      in a real container page to find the actual supported deep-link
      scheme, instead of re-guessing.
- [x] 10. Confirm the scheme: bare `#<id>` where `id` is a TOC entry in
      the page's embedded JSON, format `<sc_book_code>.lower() + <num>`.
- [x] 11. Extract every real anchor `id` from every SN/AN/KN container
      page in the cloned repo; cross-check against all 4,492 non-DN/MN
      `sc_code` rows in `dpd.db`. Result: 4,447 direct matches, 45
      exceptions (19 SN/AN peyyala-range, 26 DHP vagga-range).
- [x] 12. Add `_S4NT_ANCHOR_OVERRIDES` constant (`db/models.py`) pinning
      the 45 exceptions to their real site anchor.
- [x] 13. Update `s_4nt_link` to append `#<fragment>` for SN/AN/KN
      (DN/MN unchanged - already per-sutta pages); bare nipāta-only codes
      (`AN1`..`AN11`) keep no fragment.
- [x] 14. Update `tests/db/test_sutta_info.py` - fragments on every
      SN/AN/KN case, plus new cases for both override categories.
- [x] 15. Lint gate (ruff check, ruff format, pyright) - clean.
- [x] 16. Re-run the exhaustive cross-check against all 4,492 rows via the
      actual `s_4nt_link` property (not the throwaway script) - 0
      unresolved fragments.

## Round 3 (vagga headings were still wrong)
- [x] 17. User reported vaggas link to "just the first sutta number of the
      range" after live-testing round 2. Root cause: a vagga row
      (`is_vagga` True, `dpd_code` has a "-" range) shares its `sc_code`
      with its own first individual sutta, so round 2's default fragment
      logic anchored to that sutta instead of the vagga heading.
- [x] 18. Confirmed the site has a real vagga-header anchor per top-level
      TOC section (id = `<book><nipāta>-<slug of the vagga's Pāḷi name>`,
      same diacritic-stripping slugify already used by `sc_vagga_link`).
- [x] 19. Extracted every real vagga-like id from every SN/AN container
      page in the cloned repo (411 total) into an allow-list
      `_S4NT_VAGGA_IDS` - used to gate the computed slug, since ~6% of
      DPD's own `sc_vagga` names don't line up with the site's actual
      vagga divisions (mostly AN1's later peyyala sections).
- [x] 20. Updated `s_4nt_link`: for `is_vagga` rows with `sc_vagga` set,
      compute the vagga slug and use it if (and only if) it's a real id in
      `_S4NT_VAGGA_IDS`; else fall back to the round-2 sutta-level
      fragment (never worse than round 2, often exact).
- [x] 21. Added 2 tests: a vagga that resolves to its heading, and one
      that falls back correctly when the slug isn't a real site anchor.
- [x] 22. Fixed a fixture gap exposed by this change: `SuttaInfo()` test
      instances that only set `sc_code` left `dpd_code` as `None` (real DB
      rows default to `""`), which crashed `is_vagga`'s `"-" in
      self.dpd_code`. Set `dpd_code` explicitly on the affected fixtures -
      not a model bug, just an unrealistic bare-instance test setup.
- [x] 23. Lint gate (ruff check, ruff format, pyright) - clean.
- [x] 24. Re-ran the exhaustive cross-check against all 5,114 real rows -
      0 mismatches, 482 rows now resolve through the vagga-heading path.

## Round 4 (reverted round 3 - over-engineered)
User pushed back after seeing the size of round 3's diff: a vagga row's
`sc_code` already equals its own first sutta's code, so the plain round-2
sutta-fragment logic *already* lands a vagga link on the first sutta of
that vagga - with zero extra code. Landing one sutta below the exact
heading is functionally the same result for a reader, and round 3's
"exact heading" upgrade wasn't reliable anyway (33/529 DPD vagga names
didn't match the site's real divisions).
- [x] 25. Deleted `_S4NT_VAGGA_IDS` (411-entry allow-list) and the
      `is_vagga`/`sc_vagga` branch in `s_4nt_link` entirely.
- [x] 26. Replaced the two round-3 vagga tests with one test asserting the
      simple behavior: a vagga row's `s_4nt_link` resolves to its first
      sutta's fragment (e.g. `SN12-21` vagga → `#sn12.1`).
- [x] 27. Lint gate (ruff check, ruff format, pyright) - clean.
- [x] 28. Re-ran the exhaustive cross-check against all 5,114 real rows -
      0 mismatches (same correctness as round 3, ~140 fewer lines).
