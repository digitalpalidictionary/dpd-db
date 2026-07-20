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
