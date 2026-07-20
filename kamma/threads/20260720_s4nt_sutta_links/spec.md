# Spec: Add s.4nt.org to sutta links

## Request
Add `s.4nt.org` to the list of SuttaCentral-based website links shown in the
sutta / vagga / etc. tab of the GoldenDict and webapp exporters. Land on the
head/top of the relevant page — no segment-level fragment needed.

## History (three false starts, corrected each time by testing)
1. **First attempt** assumed one uniform pattern
   (`/<book>/<sc_code>/index.html`) from a single developer-given MN example,
   never actually fetched. Wrong for everything except DN/MN — caught only
   after the user manually 404'd every link.
2. **Second attempt** curl-probed the live site and found real per-piṭaka
   container pages (DN/MN per-sutta, SN per-saṃyutta, AN per-nipāta, KN
   per-book), but user pointed out this loses per-vagga/per-sutta precision
   within container pages.
3. **Third attempt** added `#tr-<sc_code>:0.1` segment fragments to pinpoint
   the exact sutta/vagga within a container page, with special-casing for
   DHP vagga ranges (no combined key - anchor on first verse), SN/AN
   peyyala ranges (full range code is itself a real key), and bare
   whole-nipāta codes (no fragment target exists).
4. **Final, adopted design**: the user clarified fragments aren't needed at
   all - landing on the head of the container page is sufficient. This
   also sidesteps every fragment edge case from attempt 3.

## Ground truth
The site (https://s.4nt.org, source: https://github.com/frankksutta/s.4nt,
a GitHub Pages static export) was cloned to
`~/MyFiles/2_Resources/Code/s.4nt/` for future reference. The committed
file tree is the **complete, authoritative list of every valid URL** - no
client-side routing, no hidden paths.

Cross-checked the final link-generation logic against **every one of the
5,114 real `sc_code` rows** in `dpd.db`'s `sutta_info` table: every
generated path exists in the real repo tree (0 mismatches). Also spot-
checked 15 random + several targeted examples live via HTTP - all 200 OK.

### Real page structure (confirmed from the repo tree, not guessed)
| Piṭaka | Page = one per... | Path pattern |
|---|---|---|
| DN | sutta | `/dn/<sc_code>/index.html` |
| MN | sutta | `/mn/<sc_code>/index.html` |
| SN | saṃyutta | `/sn/sn<N>/index.html` |
| AN | nipāta | `/an/an<N>/index.html` |
| KN (any book) | book | `/kn/<book>/index.html` |

KN book slugs confirmed from the repo tree: `bv cnd cp dhp iti ja kp mil
mnd ne pe ps pv snp tha-ap thag thi-ap thig ud vv`. DPD's `sc_book_code`
(lowercased) matches these 1:1 for every book already populated in
`sutta_info` (`tha-ap`/`thi-ap` have no DPD rows yet but are included for
correctness/future-proofing - this was CodeRabbit's one valid finding,
initially wrongly dismissed as a hallucination before the repo was found).

## Scope (minimal)
1. `s_4nt_link` `@cached_property` on `SuttaInfo` (`db/models.py`):
   - `dn`/`mn` → direct per-sutta page
   - `sn`/`an` → extract the leading number from `sc_code`, link to the
     saṃyutta/nipāta container page
   - any KN book (fixed set, incl. `tha-ap`/`thi-ap`) → `/kn/<book>/index.html`
   - anything else (e.g. Vinaya) → `None`
2. One row labelled `s.4nt.org` under "Websites using Sutta Central" in
   both `exporter/goldendict/templates/dpd_headword.jinja` and
   `exporter/webapp/templates/dpd_headword.html`.
3. Unit tests in `tests/db/test_sutta_info.py` covering each branch.

## Range-code regression (carried over, still applies)
`sc_book_code`'s regex leaves a trailing hyphen on range codes like
`SN39.1-15` → `"SN-"`. `s_4nt_link` strips it (`sc_book_code.rstrip("-")`)
before use. The underlying `sc_book_code` bug itself (also affecting `tbw`/
`tbw_legacy`) is pre-existing and out of scope for this thread.

## Out of scope
- Segment-level fragments (explicitly not wanted - head of page is enough).
- Settings toggle, home-page ordering, commentary/vism links the developer
  mentioned in the original conversation - never requested here.

## Side task
Cloned https://github.com/frankksutta/s.4nt to
`~/MyFiles/2_Resources/Code/s.4nt/` per user request, for future reference
on this site's real URL/page structure (avoids re-deriving it by
trial-and-error again).

## Confidence: 10/10
Every branch verified against the actual static file tree of the site's
own source repo, not inference - the strongest possible verification
short of asking the developer.
