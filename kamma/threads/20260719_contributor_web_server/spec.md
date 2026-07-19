# Spec: Contributor Web Server — zero-install onboarding for data-entry contributors

**Thread:** 20260719_contributor_web_server
**Date:** 2026-07-19
**GitHub issue:** [#215 — Contributor Onboarding: Easy GUI Setup & Data Submission](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Status:** Confirmed direction — provider choice and domain name deliberately left open

> **Self-contained:** this spec + plan.md capture the entire 2026-07-19 discussion.
> A fresh agent with zero conversational context can execute from these two files.

## Relationship to issue #215 and the existing onboarding code

Issue #215 is the standing goal: easy GUI setup and data submission for
non-technical contributors. The `scripts/onboarding/` machinery (contributor_setup,
contributor_update, data_submission, desktop_shortcut, launch_gui + the Submit
Data / Update buttons in `gui2/main.py`) was **round one** of #215 — a git-based
desktop flow. This thread is **round two of the same issue**: a hosted web
version of gui2 that supersedes the git-based flow for non-technical
contributors. Commits reference `#215`.

### Fate of the existing onboarding machinery (decided 2026-07-19)

- **KEEP AND BUILD ON — the username/data model.** This is not onboarding, it is
  the data architecture, and the web plan depends on it:
  `UsernameManager.is_not_primary()` (`gui2/user.py`), `Gui2Paths.for_user`
  (`gui2/paths.py`) routing work to `gui2/data/additions_{username}.json` /
  `corrections_{username}.json`, and the primary-side review queue
  (`gui2/additions_manager.py`: merges all `additions_*.json`, feeds a review
  queue, tags contributor into `additions_added.json`, removes processed keys
  from the contributor file). Unchanged except the uuid-key fix below.
- **KEEP BUT MARK LEGACY — the git-based desktop contributor flow**
  (`scripts/onboarding/*`, its README, the Submit Data / Update buttons).
  It remains available for a *technical* contributor on desktop. It is NOT
  fixed in this thread despite known defects (documented below so nobody
  re-discovers them). Its deletion is a follow-up decision after the web
  server has proven itself with real contributors. `scripts/onboarding/README.md`
  gets a banner: non-technical contributors use the web version.
- **The role mechanism must distinguish** desktop-contributor (old flow: keeps
  Submit/Update buttons) from server-contributor (web: buttons hidden, sync is
  automated). See plan task 1.4.

### Known defects of the legacy git flow (review of 2026-07-19 — recorded, NOT fixed here)

1. `data_submission.py` runs `git commit`/`git push` but setup never configures
   git user.name/user.email or GitHub auth → first submit fails on a fresh
   machine; commit result is not checked, so the error surfaces as a misleading
   "check your internet connection".
2. Contributors need write access to main; the pull-rebase retry can strand
   them mid-rebase.
3. `contributor_update.py` compares the release tag to `[version] version` in
   config.ini, which is never set on contributor machines → every Update click
   re-downloads the ~2 GB db and leaves a 2.2 GB `dpd.db.*.backup` behind.
4. Setup is ~10 manual steps (GitHub account, git install, uv install, API key,
   PowerShell, 3 commands, 2 typed answers) — not viable for the audience.

## Overview

Host gui2 as a web app on a rented VPS. Contributors are non-technical people
in their 70s–80s, located in **India and Singapore**, doing Pass1Auto/Pass1Add
work (Pass2 later). Target onboarding experience, in full:

> "Open this link in your browser. Type the password I gave you."

Nothing to install, no git, no GitHub account, no API keys, no terminal, ever.
The server runs an **in-progress** copy of dpd.db — completely separate from
dpdict.net, which serves the release db and is untouched by this thread.

## Feasibility — already proven

Verified 2026-07-19 on the maintainer's machine, **zero code changes**:

```
uv run flet run --web -p 8550 gui2/main.py
```

- Serves the full gui2 in a browser (Flutter web UI + websocket to Python).
- Measured RSS: **~330 MB idle** (server up, no session); **~2.5 GB with one
  connected session** after db load + all-15-tab warm-up settled.
- Sizing: 3 concurrent users ≈ 8 GB → **16 GB VPS** with headroom.
- One defect found: every instance calls `start_dpd_server()`
  (`tools/fast_api_utils.py`), hardcoded to 127.1.1.1:8080 — a second instance
  gets "address already in use". Needs a per-instance port (plan 1.3).

## Architecture (all decisions made in discussion 2026-07-19 — do not relitigate)

1. **Dedicated VPS**, separate from dpdict.net.
2. **One gui2 web instance per contributor** (2–3 users). No multi-user
   shared-memory refactor — explicitly out of scope until ~10 users.
   Instances: systemd services, Flet web ports 8551/8552/8553.
   **UPDATE (Phase 1, 2026-07-19):** in `contributor-server` mode
   `start_dpd_server()` no-ops (its only consumer, the in-GUI browser lookup, is
   disabled in a headless session), so **no per-instance FastAPI helper runs** —
   the old 8081/8082/8083 helper ports and any nginx helper proxying are NOT
   needed. `DPD_API_PORT` remains only as belt-and-suspenders for any non-server
   instance. nginx proxies only the Flet web port per contributor.
3. **nginx in front**: HTTPS (certbot), one path or subdomain per contributor,
   HTTP basic auth per contributor (browser remembers the password after the
   first visit — that's the entire login story). Websocket proxying required
   (`proxy_http_version 1.1`, Upgrade/Connection headers).
4. **One shared db, read-WRITE for contributors.** Contributors use the same
   code paths as the primary user — they write to the db, because the server db
   is a **scratch copy** periodically wiped and rebuilt from main's TSVs.
   WAL journal mode so 3 writer processes coexist.
5. **Per-user JSON work files are the authoritative record** of contributions;
   the db write is convenience. The JSON survives the wipe.
6. **Data flows up continuously**: a server job commits + pushes per-user JSONs
   to a `contributions` branch, maintaining a single long-running open PR.
   The maintainer merges on his own schedule and processes through the existing
   primary-side review queue, then commits the resulting data update to main
   (which also updates `db/backup_tsv/`).
7. **Nightly maintenance window (~01:00 IST / 03:30 SGT)**: stop instances,
   push JSONs, rebuild db from main **only when safe** (invariant below),
   reconcile JSONs, restart. Rebuild = `git pull` →
   `scripts/build/db_rebuild_from_tsv.py` →
   `scripts/server/generate_components_server.py` (a LEAN, gui2-only subset of
   `scripts/bash/generate_components.py`).
   **UPDATED (Phase 2, 2026-07-19):** the server runs the lean subset, not the
   full generate_components. It keeps only steps that populate tables/columns
   gui2 reads during data entry (inflection templates/tables, families,
   deconstructor go+add, api_ca_eva, inflections_to_headwords, see, spelling);
   it DROPS the transliterate, grammar/epd/sutta/help lookup, and frequency
   steps (maintainer-confirmed unused by gui2), plus all exporter/anki/audio/
   variants/search_index/dealbreakers steps. The premade-deconstructor download
   is DEPRECATED — the deconstructor `go run` regenerates locally on the server
   (Go required). No pytest on the server (the lean db omits data the suite
   asserts on; the maintenance-window health check is the gate). Kept/dropped
   rationale in `scripts/server/config_server.md`.
8. **THE INVARIANT: never wipe what has not been absorbed upstream.** Rebuild
   is allowed only if every `additions_*.json` / `corrections_*.json` **in
   origin/main** is empty — i.e. the maintainer has processed everything
   previously pushed. Otherwise the window skips the rebuild and keeps serving
   yesterday's db. **A skipped rebuild is a normal outcome, not an error.**
9. **Stable `{username}_{id}` keys for contribution JSONs** (UPDATED Phase 1,
   2026-07-19 — was "uuid4"). Original hazard: `add_additions` keyed by
   `str(word.id)`, and a wipe recycles db ids, so a later addition could
   silently overwrite an unprocessed JSON entry. Resolution shipped: keys are
   `"{username}_{id}"` with dedup-by-id (`_key_for_id` reuses an entry's key for
   the same db id → one live entry per word, latest wins; the db id stays inside
   the entry). Uniqueness across the merged contributor pool comes from the
   username prefix; per-word stability from the id. Backward compatible —
   `_key_for_id` also reuses any pre-existing uuid- or numeric-keyed entry. The
   id-recycling overwrite is prevented by THE INVARIANT (only wipe once all
   contributor JSONs in main are empty) + push-before-rebuild. Primary side
   tolerates "JSON key ≠ final db id" via `source_key` (added to corrections in
   Phase 1 too).
10. **Key-level reconcile instead of git merge** for contributor JSONs. Server
    adds keys; maintainer's processing removes keys; raw `git pull` would
    conflict. Snapshot-based set operation:
    `final_local = local − (last_pushed − main_version)`
    — drop exactly the keys that were pushed and have since been removed
    upstream; keep everything added locally since the push.
    **REFINEMENT (Phase 1):** because keys are now STABLE across edits (an edit
    reuses the same `{username}_{id}` key), the reconcile must NOT drop a key
    that was pushed and removed upstream IF the local entry has since CHANGED
    (a fresh edit). Rule: drop only when `local[key] == last_pushed[key]`
    (untouched since push); keep the local edit otherwise. Covered in plan 2.1.
11. **AI keys are the maintainer's** — DeepSeek and/or OpenRouter, both already
    wired into gui2 (`tools/ai_deepseek_manager.py`, `tools/ai_open_router.py`).
    Keys go into the server-generated config.ini (never committed).
    Contributors never see an API key.
12. **Privileges**: contributors see everything; gating is minimal and
    action-level. `role = contributor-server` hides Submit Data / Update
    buttons (replaced by automation) and disables desktop shell-outs
    (e.g. GoldenDict lookups) that cannot work in a server session.
13. **Per-instance identity**: ONE repo clone on the server, three instances.
    `config.ini` is a single root-level file holding `[gui2] username`, so
    username/role/ports must be overridable per instance via environment
    variables set in each systemd unit, with config.ini as fallback —
    desktop behavior unchanged when the env vars are unset.
14. **Repo access from the server**: deploy key (read-write). GitHub deploy
    keys cannot be branch-restricted, so `main` gets a branch-protection rule
    (require PR) — the server key can then only effectively land pushes on
    `contributions`. PR is opened once by the maintainer and stays open.

## Server shopping (decision deferred to provisioning day — keep all three open)

| Provider | Location | 16 GB price | Notes |
|---|---|---|---|
| Contabo Cloud VPS 20 | **Navi Mumbai** | ~$8–12/mo | Cheapest 16 GB anywhere; oversold CPU, 24–48 h support |
| Hostinger KVM | **India + Singapore** | ~$20+/mo tier | Well known in India; friendlier panel |
| Hetzner Cloud | Singapore | ~2–3× Contabo | Quality option |

Mumbai↔Singapore RTT ~50–90 ms is fine for Flet websockets, so one server
serves both countries. Budget ≈ **$120–250/year**.

## What it should do (end state)

1. Maintainer onboards a new contributor by running one server-side script
   (instance + password), then telling the person a URL + password.
2. Contributor opens the URL, enters the password once, and works in gui2
   exactly as it works on desktop (Pass1Auto, Pass1Add, later Pass2 tabs).
3. Their work writes to the shared scratch db AND their per-user JSONs.
4. JSONs appear in the `contributions` PR automatically every night.
5. Maintainer merges the PR, processes the review queue in his own desktop
   gui2, commits the data update to main as usual.
6. Next safe night the server rebuilds from main and reconciles JSONs.
   Processed words are now "real" in the server db; nothing was ever lost.
7. A failed rebuild rolls back to the previous db and keeps serving;
   a status page tells the maintainer.

## Assumptions & uncertainties (ALL known unknowns — nothing lives outside this file)

- **Rebuild time on a budget VPS is unknown** (estimate: local time × 2–3).
  Measured in plan 3.3 before the window schedule is fixed. Fallback if > ~3 h:
  maintainer-pushed prebuilt db (`just contrib-push-db`, rsync ~600 MB
  compressed), server rebuild as a later upgrade.
- **Flet web session behavior** under disconnect / reconnect / overnight idle /
  laptop sleep is untested. Worst acceptable case is "reload the page", but it
  must be observed and documented (plan 4.2) before real users.
- **`gui2/corrections_manager.py` has not been read** — audit for the id-keying
  hazard and its primary/contributor merge behavior (plan 1.1).
- **Per-user state beyond additions/corrections** (daily log counts, history
  files, pass1/pass2 queue state in `gui2/data/`) not yet audited — everything
  a contributor session writes must be per-user-keyed or safely shared
  (plan 1.1).
- **Which gui2 features break in web mode** (clipboard, file dialogs,
  shell-outs, fonts) — needs a systematic browser click-through of the Pass1
  tabs (plan 1.5).
- **Concurrent SQLite writers**: WAL + short transactions should suffice for 3
  users; must verify gui2 save paths hold no long write transactions (plan 1.6).
- **`generate_components.py` on the server**: its COMMANDS list includes
  `uv run pytest tests/` and export steps; which entries run vs no-op under the
  server config must be established step by step (plan 2.5). Recommendation
  (needs user confirmation): replace pytest with targeted db health checks in
  the server run.
- **Submodules needed on the server**: `resources/sc-data`,
  `resources/dpd_submodules` (~2 GB) — same as
  `scripts/onboarding/contributor_setup.py::REQUIRED_SUBMODULES`. Assumed
  sufficient for gui2 + rebuild; verified implicitly by 3.3.
- **Domain/subdomain** for the server — maintainer decision at provisioning.
- **Provider** — maintainer decision at provisioning (table above).
- **Pass2 in web mode** — contributors "maybe later"; only Pass1 tabs must be
  fully verified in this thread; Pass2Add gets the same click-through but
  breakages there are recorded, not necessarily fixed.

## Constraints

- No changes to the release pipeline or dpdict.net.
- gui2 changes must not disturb the primary desktop experience — every
  contributor-mode behavior is gated by role/env config, defaulting to
  current behavior when unset.
- Never commit secrets (API keys, passwords, htpasswd). Server config.ini is
  generated on the server, not tracked.
- Project rules apply: pre-commit gate (ruff check, ruff format, pyright,
  pytest) on every touched file; modern type hints; pathlib; no ORM
  side-effect mutations; commits only when the user asks, format
  `#215 area: change1, change2` (≤72 chars).

## How we'll know it's done

1. Two real contributors (one India, one Singapore) doing daily Pass1 work
   with zero terminal contact and no maintainer intervention for ≥ 2 weeks.
2. Contributions arrive in the `contributions` PR nightly; at least one full
   cycle (contribute → merge → process → rebuild → word visible as processed
   in server db) completed with zero data loss.
3. A rebuild-skip night (unprocessed contributions in main) verifiably serves
   yesterday's db and touches nothing.
4. A simulated rebuild failure rolls back and the old db serves.
5. Onboarding contributor #3 takes the maintainer < 10 minutes server-side.

## What's not included

- Multi-user shared-memory refactor of gui2 (only at ~10+ users).
- Packaged desktop app (`flet build`) — considered and rejected fallback.
- Fixing or deleting the legacy git-based flow in `scripts/onboarding/`
  (README banner only; deletion is a follow-up thread after the web server
  is proven).
- Public signup, user-management UI, or more than ~3 contributors.
- Changes to the maintainer's own review/import workflow beyond uuid-key
  compatibility.
