# Spec: Add s.4nt.org to sutta links

## Request
Add `s.4nt.org` to the list of SuttaCentral-based website links shown in the
sutta / vagga / etc. tab of the GoldenDict and webapp exporters. **One sutta
code must land on that individual sutta** — not on a container page the
user then has to scroll through by hand (e.g. SN12.5 must not dump the user
on the 300-sutta SN12 saṃyutta page).

## History (five attempts — corrected each time by testing against the
## real site, twice by explicit user rejection of a container-only link)
1. **First attempt** assumed one uniform pattern
   (`/<book>/<sc_code>/index.html`) from a single developer-given MN example,
   never actually fetched. Wrong for everything except DN/MN — caught only
   after the user manually 404'd every link.
2. **Second attempt** curl-probed the live site and found real per-piṭaka
   container pages (DN/MN per-sutta, SN per-saṃyutta, AN per-nipāta, KN
   per-book), but user pointed out this loses per-vagga/per-sutta precision
   within container pages.
3. **Third attempt** added `#tr-<sc_code>:0.1` segment fragments, over-
   engineered against a fragment scheme (`tr-`) that doesn't apply to
   sutta-level anchors at all (that prefix is for translation-row deep
   links, not sutta group headers).
4. **Fourth attempt** ("final" at the time): dropped fragments entirely on
   the belief the user didn't want them, landing on the bare container page
   for SN/AN/KN. **This shipped in commit 9ab17694 and was wrong** — the
   user tested it live on SN12.5 (`sn/sn12/index.html`, ~300 entries) and
   rejected it outright: a sutta code must resolve to *that* sutta, full
   stop. The "no fragment needed" note in the prior spec version was a
   misreading of the user's earlier "no segment-level fragments" comment
   (which was about *sub-sutta* translation-row anchors, not about landing
   on the right sutta at all).
5. **Fifth, corrected attempt (this version)**: re-read the site's own
   client-side router (`jumpToHash`/`jumpToRef` in the page's embedded JS)
   to find the real deep-link scheme, instead of guessing again. Confirmed:
   every container page (SN saṃyutta, AN nipāta, KN book) embeds a TOC with
   one JS object `id` per sutta/verse/poem (e.g. `"id": "sn12.5"`), and the
   page's own hash-router treats `#<id>` as a "sutta group header" anchor
   (see code comment: `an3.65) → a sutta group header`). So
   `https://s.4nt.org/sn/sn12/index.html#sn12.5` is a real, working,
   supported deep link — no scrolling required.

## Ground truth
The site (https://s.4nt.org, source: https://github.com/frankksutta/s.4nt,
a GitHub Pages static export) was cloned to
`~/MyFiles/2_Resources/Code/s.4nt/` for future reference. The committed
file tree is the **complete, authoritative list of every valid URL** - no
client-side routing, no hidden paths for the page-level scheme. The page's
embedded JS *is* the deep-link scheme for anchors within a page - read
directly from its source, not guessed.

### Fragment scheme
Each container page embeds a TOC JSON with objects like
`{"id": "sn12.5", "label": "SN 12.5 · Sikhī", ...}`. The page's own
`jumpToRef`/`jumpToHash` functions resolve a bare `#<id>` (matching an
object in the page's `SO` lookup) to that sutta's header, auto-expanding
any collapsed ancestor group and scrolling to it. `id` values are always
`<sc_book_code>.lower() + <numeric-address>` — i.e. exactly
`sc_code.lower()` for the overwhelming majority of real DPD rows.

**Verified exhaustively, not sampled**: extracted every `"id": "..."`
string from every SN/AN/KN container page's embedded TOC JSON in the
cloned repo, and cross-checked against **all 4,492 non-DN/MN `sc_code`
rows** in `dpd.db`'s `sutta_info` table:
- **4,447 direct matches** — `#<sc_code.lower()>` is a real id verbatim.
- **19 peyyala-range matches** — the site groups some abbreviated
  ("...pe...") sutta runs under one combined id (e.g. site's
  `sn23.23-33` covers DPD's individually-coded `SN23.23`..`SN23.33`).
  Resolved by numeric-range containment against every combined id found
  on that book's page.
- **26 DHP vagga-range codes** (DPD codes a whole vagga as one row, e.g.
  `DHP1-20`) — the site has no combined anchor for these; resolved to the
  first verse in the range (`#dhp1`), which lands the user at the top of
  that vagga instead of the top of the 423-verse DHP page.
- **0 unresolved** — every single one of the 4,492 rows now has a fragment
  that actually exists in the site's real page. The 45 non-direct cases are
  captured in a static override table (`_S4NT_ANCHOR_OVERRIDES`) rather than
  derived algorithmically, because the site's peyyala-compression boundaries
  aren't recoverable from DPD's own data — they're a static-site build
  artifact, verified once against the actual page content and pinned.

### Real page structure (confirmed from the repo tree, not guessed)
| Piṭaka | Page = one per... | Path pattern |
|---|---|---|
| DN | sutta | `/dn/<sc_code>/index.html` (no fragment needed - own page) |
| MN | sutta | `/mn/<sc_code>/index.html` (no fragment needed - own page) |
| SN | saṃyutta | `/sn/sn<N>/index.html#<sc_code.lower()>` |
| AN | nipāta | `/an/an<N>/index.html#<sc_code.lower()>` |
| KN (any book) | book | `/kn/<book>/index.html#<sc_code.lower()>` |

Bare nipāta-only codes (`AN1`..`AN11`, no sutta number - a handful of DPD
rows describing the nipāta itself) get no fragment - the container page's
own top *is* the correct target for those.

KN book slugs confirmed from the repo tree: `bv cnd cp dhp iti ja kp mil
mnd ne pe ps pv snp tha-ap thag thi-ap thig ud vv`. DPD's `sc_book_code`
(lowercased) matches these 1:1 for every book already populated in
`sutta_info` (`tha-ap`/`thi-ap` have no DPD rows yet but are included for
correctness/future-proofing - this was CodeRabbit's one valid finding,
initially wrongly dismissed as a hallucination before the repo was found).

### Vagga headings (round 6, reverted in round 7)
SN/AN vagga rows (`is_vagga` True) share `sc_code` with their first
individual sutta. Round 6 built a 411-entry allow-list of real
vagga-header anchor ids (`_S4NT_VAGGA_IDS`, extracted from every SN/AN
container page) plus a Pāḷi-name slugify, to anchor a vagga row to its own
heading instead of its first sutta (496/529 matched directly; the other 33
- mostly AN1's later peyyala sections - don't correspond to any real site
vagga division at all).

**Round 7 reverted this.** Landing on the vagga's first sutta - which is
exactly what the plain sc_code-based fragment already does with zero
extra code, since a vagga row's `sc_code` *is* its first sutta's code - is
functionally equivalent for the reader (that sutta sits right at the top
of the vagga) and doesn't depend on a 411-entry table that only 3.4% of
DPD's vagga names actually needed. Simpler, same verified correctness.

## Scope (minimal)
1. `s_4nt_link` `@cached_property` on `SuttaInfo` (`db/models.py`):
   - `dn`/`mn` → direct per-sutta page, no fragment
   - `sn`/`an` → saṃyutta/nipāta container page + `#<sc_code.lower()>`
     fragment (via `_S4NT_ANCHOR_OVERRIDES` for the 19 peyyala-range
     exceptions); bare nipāta-only code → container page, no fragment
   - any KN book (fixed set, incl. `tha-ap`/`thi-ap`) →
     `/kn/<book>/index.html` + `#<sc_code.lower()>` fragment (via
     `_S4NT_ANCHOR_OVERRIDES` for the 26 DHP vagga-range exceptions)
   - anything else (e.g. Vinaya) → `None`
2. `_S4NT_ANCHOR_OVERRIDES: dict[str, str]` constant (`db/models.py`) - the
   45 `sc_code → real site anchor id` exceptions, derived once from the
   cloned repo's embedded TOC data (see Ground truth above), not guessed.
3. Template row (unchanged from the previous commit - only the property's
   output changes): `s.4nt.org` under "Websites using Sutta Central" in
   both `exporter/goldendict/templates/dpd_headword.jinja` and
   `exporter/webapp/templates/dpd_headword.html`.
4. Unit tests in `tests/db/test_sutta_info.py` updated to assert the
   fragment on every branch, plus new cases for the peyyala-range and
   DHP vagga-range overrides.

## Range-code regression (carried over, still applies)
`sc_book_code`'s regex leaves a trailing hyphen on range codes like
`SN39.1-15` → `"SN-"`. `s_4nt_link` strips it (`sc_book_code.rstrip("-")`)
before use. The underlying `sc_book_code` bug itself (also affecting `tbw`/
`tbw_legacy`) is pre-existing and out of scope for this thread.

## Out of scope
- Sub-sutta / translation-row segment fragments (`#tr-...`) - only
  sutta-level precision was requested; the site's `tr-` scheme is a
  separate, finer-grained mechanism not needed here.
- Settings toggle, home-page ordering, commentary/vism links the developer
  mentioned in the original conversation - never requested here.

## Side task
Cloned https://github.com/frankksutta/s.4nt to
`~/MyFiles/2_Resources/Code/s.4nt/` per user request, for future reference
on this site's real URL/page structure (avoids re-deriving it by
trial-and-error again).

## Confidence: 10/10
Every branch verified against the actual static file tree of the site's
own source repo AND the real anchor ids embedded in every SN/AN/KN
container page - all 4,492 non-DN/MN `sc_code` rows resolve to a fragment
that provably exists in the real page (4,447 direct + 45 pinned overrides),
not inference - the strongest possible verification short of asking the
developer.
