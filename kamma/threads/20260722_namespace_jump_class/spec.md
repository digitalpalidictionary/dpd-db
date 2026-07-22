# Spec: Namespace the `.jump` CSS class → `.dpd-jump` (finish #201)

**Thread:** 20260722_namespace_jump_class
**Date:** 2026-07-22
**Status:** PARKED — spec only, no plan. Not scheduled. Do not implement until picked up.
**Related:** #201 (namespace cleanup that renamed `.button`→`.dpd-button` etc. but
skipped `.jump`), #253 (s.4nt.org theme — exposed the collision).

## Problem

`.jump` is an un-namespaced, generic CSS class used by DPD for the compound /
idiom / set family "jump to:" anchor lists and their "back to the top ⤴" links
(`<a class="jump">`). When the browser extension injects its panel into a host
page that *also* defines `.jump`, the host's rule leaks in (the panel is not in a
shadow DOM). Observed on s.4nt.org, whose `.jump{display:flex}` forced every
jump-to item and the back-to-top link onto its own line inside the popup.

This is the last generic class left over from the #201 sweep, which namespaced the
other collision-prone classes but missed `.jump`.

## Immediate band-aid already applied (NOT this thread)

A minimal, self-contained CSS guard was shipped in the wxt extension bundle on
2026-07-22 (separate from this parked thread):
- `exporter/wxt_extension/assets/styles/dpd.css` — `#dict-panel-25445 a.jump { display: inline; }`
- `exporter/wxt_extension/assets/styles/chrome-extension.css` — `line-height: normal;`
  on `.button` and `a.dpd-button` (a related host `line-height` leak, not `.jump`).

The id-scoped selector out-specifies any host `.jump`, so the leak is contained
today. This namespacing thread is the durable follow-up. The band-aid's
`display:inline` / `line-height` guards are harmless hardening and may be kept or
dropped when the rename lands — decision deferred.

## Scope — rename `jump` → `dpd-jump` everywhere it is live

### Emitters (`class="jump"` → `class="dpd-jump"`)
- `exporter/webapp/templates/dpd_headword.html` (compound-family + set lists + back-to-top)
- `exporter/goldendict/javascript/family_compound_template.js`
- `exporter/goldendict/javascript/family_idiom_template.js`
- `exporter/goldendict/javascript/family_set_template.js`

### CSS (`a.jump` / `.jump` → `a.dpd-jump` / `.dpd-jump`)
- `identity/css/dpd.css`  ← **canonical source**
- `identity/css/dpd-css-and-fonts.css`
- `exporter/webapp/static/dpd.css`
- `exporter/wxt_extension/assets/styles/dpd.css`
- `exporter/chrome_extension/css/dpd.css` (old chrome extension)

### Explicitly EXCLUDED
- Everything under `archive/` (archived web_app_old + archived goldendict copies
  also contain `.jump` — leave them).

## Open questions to resolve when implementing (do NOT assume)

1. **CSS propagation is not uniform.** `identity/css/` is canonical.
   `exporter/chrome_extension/scripts/build-css.js` *generates* the old chrome
   extension's CSS from `identity/`. But the **wxt copy currently DIVERGES** from
   `identity/css/dpd.css` (verified `diff` differs, no sync script found) — so it
   is hand-maintained or stale. Rename at the source AND in each consumer, and
   confirm no regen step re-introduces the old `.jump`.
2. **Deploy ordering across the client/server boundary.** The extension renders
   HTML fetched live from the webapp (`/search_json` → `dpd_headword.html`). So the
   template rename (server, must be redeployed to dpdict.net) and the extension
   CSS rename (shipped in an extension update) must land together; otherwise an
   old extension styling `.jump` meets server HTML using `.dpd-jump` (or vice
   versa) and the anchors render unstyled. Keep the band-aid until the rename is
   fully rolled out on both.
3. **GoldenDict/MDict have their own bundled CSS** — confirm the goldendict export
   CSS that styles these anchors is included in the CSS list above (it consumes
   `identity/css`), so the JS-emitter rename and its CSS rename stay in sync.

## Verification (when implemented)

- Grep the repo (excluding `archive/`) for `class="jump"` and `\.jump\b` → zero live hits.
- Rebuild each affected export; confirm the family jump-to lists still render inline
  and styled (bold, coloured) in: webapp, wxt extension, goldendict.
- Re-check on s.4nt.org that the collision is gone even with the band-aid removed.
