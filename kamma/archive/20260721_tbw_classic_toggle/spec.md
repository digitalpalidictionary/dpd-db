# Spec: TBW Legacy links opt-in via config toggle

## Background

The "TBW Legacy" sutta links (`find.dhamma.gift/bw/...`, B. Bodhi translations)
must be **removed from public builds** but remain usable **privately**. Request
from the developer (Pavel Katorgin): exclude TBW Legacy from the sutta
dictionary link list; he keeps the `bw/` folder on his server for private use.

`tbw_legacy` is a computed `@cached_property` on `SuttaInfo` (`db/models.py:888`)
returning the `find.dhamma.gift/bw/...` URL. It is **not stored in the db** — it
is computed at render time and shown in exactly two templates:

- `exporter/goldendict/templates/dpd_headword.jinja:423` — `{% if d.su.tbw_legacy %}`
- `exporter/webapp/templates/dpd_headword.html:434` — `{% if d.su.tbw_legacy %}`

So the gate is a **render-layer** change, not a data change.

## Goal

Default behaviour **excludes** TBW Legacy. A config setting includes it:
`[dictionary] show_tbw = yes`.

## The four surfaces

| Surface | Runs via | Renders | Public/Private | Outcome |
|---|---|---|---|---|
| GitHub release | `.github/workflows/draft_release.yml:183` → `exporter/goldendict/main.py` | goldendict template | public | **excluded** |
| dpdict.net server | `scripts/server/update-dpd.sh` → `uvicorn exporter.webapp.main:app` | webapp template (live) | public | **excluded** |
| `just makedict` | `scripts/bash/makedict.py` → `goldendict/main.py` | goldendict template | private | included |
| `just webapp` / `just gui` | local uvicorn / gui2 | webapp template | private | included |

## Why a `config.ini` toggle (not a CLI flag or env var)

- `config.ini` is **regenerated fresh on every GitHub run** from the
  `github_release` profile (`scripts/build/config_github_release.py` →
  `config_apply_profile("github_release")`). That profile does **not** set
  `show_tbw`, so a fresh CI config falls back to the `DEFAULT_CONFIG` value
  `no` → public build excluded. No CI change required.
- The dpdict.net server has its own persistent `config.ini` that never enables
  it → public server excluded. No server change required.
- Locally, `config.ini` **persists** (it is `.gitignored`, only regenerated on
  CI). The user sets `show_tbw = yes` once and it survives every local
  `just makedict` / `just webapp` / `just gui` run.
- `config_test(..., "yes")` returns `False` when the option is absent, so the
  toggle is safe even in a config that predates this change.

A `--tbw-classic` CLI flag was rejected: it cannot reach a long-running uvicorn
server, and `just makedict` invokes goldendict indirectly through
`makedict.py`'s script list, so the flag would not propagate. The config toggle
covers all four surfaces uniformly and matches the existing render-layer flag
pattern (`[dictionary] show_id`).

## Mechanism

Inject a Jinja **environment global** `show_tbw` (bool), read once from
config, into both the goldendict and webapp Jinja environments. Both envs use
default (non-strict) `Undefined`, so where the global is unset it evaluates
falsy — the legacy link is hidden. An env global is used rather than a
per-`render()` kwarg because the webapp renders `dpd_headword` from **six** call
sites (`toolkit.py:109, 239, 260, 324, 434, 453`); one global covers them all
and any future site.

Template gate (both files):

```jinja
{% if d.su.tbw_legacy and show_tbw %}
```

## Out of scope

- The separate `exporter/tbw/tbw_exporter.py` (`make_tbw`) — a different exporter
  that builds the TBW dictionary itself; unrelated to the legacy link list.
- `d.su.tbw` (the live `thebuddhaswords.net` link) — stays as-is; only
  `tbw_legacy` is gated.
- The developer's own `force_local` mode on dhamma.gift — his site, not this repo.

## Acceptance criteria

1. With no `show_tbw` option (or `= no`), neither template renders the TBW
   Legacy row, even when `d.su.tbw_legacy` returns a URL.
2. With `[dictionary] show_tbw = yes`, both templates render the TBW Legacy
   row when `d.su.tbw_legacy` is set.
3. A fresh CI config (`github_release` profile) yields `show_tbw = no` →
   excluded, with no workflow edits.
4. Existing goldendict/webapp template tests still pass.
