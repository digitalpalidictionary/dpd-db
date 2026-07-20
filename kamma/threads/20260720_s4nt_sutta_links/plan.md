# Plan: Add s.4nt.org to sutta links

- [x] 1. Curl-probe s.4nt.org live to determine the real per-piṭaka URL
      shape (superseded the original single-pattern assumption).
- [x] 2. Design segment-fragment approach for vagga/sutta precision within
      container pages (superseded per user - head of page is sufficient).
- [x] 3. Find and clone the site's source repo
      (https://github.com/frankksutta/s.4nt) to
      `~/MyFiles/2_Resources/Code/s.4nt/` for ground-truth verification
      and future reference.
- [x] 4. Finalize `s_4nt_link` `@cached_property` on `SuttaInfo`
      (`db/models.py`): DN/MN direct sutta page, SN/AN saṃyutta/nipāta
      container, KN book container (18 books incl. `tha-ap`/`thi-ap`),
      else `None`.
- [x] 5. Template rows in goldendict + webapp headword templates
      (unchanged since first attempt - only the underlying property
      changed).
- [x] 6. Rewrite unit tests in `tests/db/test_sutta_info.py` - one per
      branch (DN, MN, SN, AN, bare-nipāta, range-code, 8 KN books,
      unknown-book None, no-sc_code None). 10 tests, all passing.
- [x] 7. Lint gate (ruff check, ruff format, pyright) - clean.
- [x] 8. Cross-check the final logic against **every** real `sc_code` row
      (5,114) in `dpd.db` against the site's actual committed file tree -
      0 mismatches. Live-spot-checked 15 random + several targeted
      examples via HTTP - all 200 OK.
