# Spec: Swap find.dhamma.gift → f.dhamma.gift

## Overview
The DPD webapp, GoldenDict export, and Flutter app generate "Dhamma.gift" and
"TBW Legacy" links using the host `find.dhamma.gift`. The webadmin requested
removing "find" so the links use a host without Cloudflare captcha (opens
quicker, works without VPN). Chosen host: `f.dhamma.gift` (user-confirmed).

## What it should do
Replace the host `find.dhamma.gift` with `f.dhamma.gift` in every link DPD
generates, keeping the path structure identical:
- `https://find.dhamma.gift/read/?q=<sc>` → `https://f.dhamma.gift/read/?q=<sc>`
- `https://find.dhamma.gift/bw/<book>/<sc>.html` → `https://f.dhamma.gift/bw/<book>/<sc>.html`

Three places:
1. **dpd-db webapp** — `db/models.py` `dhamma_gift` + `tbw_legacy` properties
   (also feeds webapp templates; goldendict shares the same properties)
2. **GoldenDict exporter** — same `db/models.py` properties, rendered by
   `exporter/goldendict/templates/dpd_headword.jinja` (no template edit needed)
3. **Flutter app** (neighbouring repo `../dpd-flutter-app`) —
   `lib/database/sutta_info_extensions.dart` `dhammaGift` + `tbwLegacy` getters

## Assumptions & uncertainties
- `f.dhamma.gift` serves identical content at the same paths — VERIFIED via curl:
  both `/read/?q=sn1.1` and `/bw/sn/sn1.1.html` return 200.
- Only the host changes; URL path structure stays identical.
- `thebuddhaswords.net` links (`tbw`) are NOT part of this request — leave them.

## Constraints
- Modern type hints; `pathlib.Path`; follow repo conventions.
- Flutter side must keep Dart style (`flutter analyze` clean).

## How we'll know it's done
- `rg "find\.dhamma\.gift"` finds zero matches in `db/models.py`,
  `tests/exporter/webapp/test_dpd_headword.py`,
  `tests/exporter/goldendict/test_dpd_headword.py`,
  `../dpd-flutter-app/lib/database/sutta_info_extensions.dart`,
  `../dpd-flutter-app/test/database/sutta_info_extensions_test.dart`.
- Python tests for webapp + goldendict pass; flutter tests pass.

## What's not included
- `db/suttas/dv_catalogue_suttas.tsv` — downloaded from the webadmin's own
  external repo (dhamma-vinaya-connections), not ours to edit.
- Static docs/README/newsletter files containing the old URL (README.md:39,
  docs/newsletters.md, scripts/build/newsletter_processed.json) — historical
  content, out of the three scoped places; flagged to user.
