# Spec: Fix broken multi-link href in webapp & GoldenDict

## Overview
Headwords with two or more web links (stored newline-separated in the `link`
column) render as a single broken anchor whose href contains a URL-encoded
`<br>`, e.g.
`https://…/Tabernaemontana_divaricata%3Cbr%3Ehttps://…/Nerium`.

## Root cause
`db/models.py` exposes `link_list` (cached_property) which splits the raw
`link` string on `\n`. But before the template runs, the data-class
`convert_newlines` / `_convert_newlines` helpers mutate `obj.link` in place,
replacing every `\n` with `<br>`. By the time `link_list` is accessed there are
no `\n` left to split on, so it returns ONE item containing `<br>`, which the
template wraps in a single `<a href>`.

- `exporter/webapp/data_classes.py` — `"link"` in `string_columns`
- `exporter/goldendict/data_classes.py` — `"link"` in `attrs`
- Both templates render via `d.i.link_list` and use `d.i.link` only for an
  `{% if %}` truthiness check.

## What it should do
Each newline-separated link must render as its own separate `<a>` anchor with a
clean href.

## Assumptions & uncertainties
- The `link` field is rendered ONLY via `link_list` in both templates (verified
  — direct `d.i.link` use is truthiness-only), so `link` does not need `<br>`
  conversion at all.
- Other exporters (anki, tpr, kindle) handle links via their own code and are
  out of scope for this bug report.

## How we'll know it's done
A headword with two links shows two distinct working anchors in both the webapp
page and the GoldenDict export.

## What's not included
- Anki/TPR/Kindle exporters.
- Any DB data change — the stored `link` value is correct as-is.
