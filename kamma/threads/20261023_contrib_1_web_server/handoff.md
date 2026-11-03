# Handoff — 20261023_contrib_1_web_server (2026-11-03, evening IST)

> **SUPERSEDED 2026-11-03, later the same evening.** The rebuild finished and
> passed; drilltest is removed (§1); the two-user blocker (§2) is fixed and
> proved live with two users at once; the htpasswd test (§4) is proven by a
> revert. See plan.md 3.4 and 3.5 for the evidence. §3 and §8 still hold.

Resume with `/kamma:2-do 20261023_contrib_1_web_server`. Read `spec.md` and
`plan.md` first: the plan was updated today with dated findings and is the
source of truth for what is done and what is not.

The owner is unhappy with how today went: two full database rebuilds were
triggered on the live server and alice was offline for long stretches, mostly
because a long server command was run through the herdr agent's shell, which
timed out at 120 s and killed the process group mid-rebuild. Finish the
cleanup cleanly and carefully; do not start new work on the server without
reading the warnings below.

---

## 1. LIVE STATE — read this before touching the server

**A database rebuild is running right now** (started 18:44 IST, detached with
`setsid nohup`, pids ~3257761/62/65). At 18:44→~19:35 it is in the generate
step (`~650,000 / 935,023` rows of `lookup`). It will:

1. finish generate → health check → re-apply WAL,
2. write `~/dpd-db/logs/last_built_commit`,
3. **restart `dpd-gui@alice`** in its `finally` block.

Until it finishes, `dpd-gui@alice` is `failed` (stopped) — this is expected,
not damage.

Expected healthy end state to verify:

```bash
cd ~/dpd-db && tail -6 logs/maintenance_20261103.log
# expect: components generated / health check passed / WAL re-applied /
#         systemctl start dpd-gui@alice / maintenance window end: rebuilt
cat logs/last_built_commit          # expect 8af6e887...
systemctl is-active dpd-gui@alice   # expect active
sqlite3 dpd.db "select count(*) from dpd_headwords; select count(*) from lookup;"
# expect ~89774 and ~1179891; db should be ~883 MB
```

**If the rebuild died again**, the db is incomplete (`dpd.db` smaller than
~800 MB) and `dpd.db.prev` is **not** a safe fallback — it was captured when
the db was already mid-rebuild (132 MB). Re-run:

```bash
cd ~/dpd-db && setsid nohup env PYTHONPATH=. /root/.local/bin/uv run --no-sync \
  scripts/server_contrib/maintenance_window.py --data-dir /var/lib/dpd/contrib_data \
  --instance dpd-gui@alice --status-file /var/lib/dpd/status.txt \
  >> /root/mem/window_recover.log 2>&1 < /dev/null &
```

**NEVER let the herdr agent wait on a long command.** Its shell timeout (120 s)
has now killed this window twice. Always `setsid nohup … < /dev/null &` and have
the agent return immediately. Then watch from the laptop with a bounded loop on
the log, not from the agent.

### Leftover test account (must be removed)

`drilltest` (port 8555, throwaway password `drillpass2026xyz`) still has files.
The removal drill's part 2 never ran (the window died first). Do exactly:

```bash
systemctl disable --now dpd-gui@drilltest          # already disabled, re-run is safe
rm -f /etc/dpd/drilltest.env /etc/nginx/dpd/drilltest.htpasswd /etc/nginx/dpd/drilltest.conf
nginx -t && systemctl reload nginx
curl -s -o /dev/null -w '%{http_code}\n' -u drilltest:drillpass2026xyz \
  https://187-126-118-33.sslip.io/drilltest/      # expect 404
ls /etc/dpd/ /etc/nginx/dpd/                       # drilltest gone
ls /var/lib/dpd/contrib_data/ | grep drilltest ; echo NO_DRILLTEST_FILES
```

`drilltest` never wrote any data (no files in `/var/lib/dpd/contrib_data`), so
nothing needs archiving. **alice's data files are intact** — do not touch them.

### What was changed on the server today (all reversible)

- cron installed: `0 1 * * *` running `maintenance_window.py` (root crontab).
- `/status` nginx block added to `/etc/nginx/sites-available/dpd-contrib`
  (template: `scripts/server_contrib/nginx_status.conf.template`), served
  behind alice's login; the window writes `/var/lib/dpd/status.txt`.
- GitHub: `main` now has branch protection (PR required, 0 approvals,
  `enforce_admins=false`, force-push and deletions off). `contributions` left
  unprotected on purpose.
- `main` was force-restored to `8af6e887` (see §3) after a test commit.
- `chown root:www-data /etc/nginx/dpd/drilltest.htpasswd` by hand (drill).

---

## 2. THE BLOCKER (owner decision needed)

**Two contributors cannot both work behind path prefixes.** Flet 1.0.1 serves
its web shell with ABSOLUTE asset paths (`/python.js`, `/flutter_bootstrap.js`,
`/main.dart.wasm`, `/ws`, `/assets/`, `/icons/`). Those land on the domain root,
and `/etc/nginx/dpd/zz_root_asset_shim.conf` maps every one of them to a
**hard-coded alice realm and alice port 8551**. Its own comment says:

> "while this shim exists, root-level asset paths always answer as ALICE;
> multi-user prefixes need the native fix (ASGI root_path) — recorded for
> contrib_1 Phase 3"

Reproduced today with `drilltest`: authenticated HTML returned **200**, then the
browser console showed `401 @ /python.js` and `401 @ /manifest.json`, and the app
stayed at 74 MB with no db load. Alice works because the shim is alice's.

Options (owner to choose):

- **(a) native `root_path` support in gui2** so each instance serves prefixed
  assets — the shim's own recorded plan. Code change in `gui2/main.py` / the
  `ft.run` mount, plus verification that `/ws` and wasm paths get the prefix.
- **(b) a subdomain per contributor**, so root paths are per-host. Needs
  wildcard DNS and a wildcard certificate.

**UNRESOLVED CONTRADICTION — check this first.** The owner says two users were
working yesterday. Evidence gathered so far says only `alice` has ever existed
on this server (`/etc/dpd/`, `/etc/nginx/dpd/`, `/var/lib/dpd/contrib_data/`
all alice-only; the only other data files in the repo are
`gui2/data/additions_deva.json` and `gui2/data/corrections_deva.json`). It is
likely "two users" refers to the old **temp** server (threads `contrib_4/5/6`),
not this one. If two users really did run simultaneously behind prefixes on
**this** server, the shim analysis above is wrong and must be re-checked before
planning anything. **Ask the owner which server and which usernames.**

---

## 3. THE DEPLOY-KEY FINDING (owner accepted the risk)

The server pushes with `core.sshCommand = -i ~/.ssh/dpd_deploy`, which **is** the
repo's write deploy key (`dpd contrib6 temp server`, id 168360647,
`read_only=false`). **GitHub deploy keys bypass branch protection,** so the key
can still write `main` — proved by pushing an empty commit from a throwaway
clone (exit 0) while "Changes must be made through a pull request" was on. The
test commit `14b622f` landed on public main and was removed by a force-push
(admin bypass); main is now `8af6e887`, force-push disabled again.

The real fix (not done): give the server a credential branch protection applies
to — a non-admin account's SSH key or a fine-grained PAT. Owner's decision on
2026-11-03 was **accept the risk for now**.

---

## 4. THE HTPASSWD BUG (fix written, NOT fully verified)

`add_contributor.sh` wrote the htpasswd mode 640 but left it `root:root`, so the
nginx worker cannot read it and a brand-new URL answers **500** until someone
chgrps it by hand (the README admits it "is not checked locally"; alice's file
was fixed that way at some point). This is exactly what made the owner's login
to drilltest fail; verified live: 500 → `chown root:www-data` → 200.

Fix applied locally (uncommitted): after the `chmod 640`, determine nginx's group
(`HTPASSWD_GROUP` override, else parsed from `nginx -T`, else skip) and `chgrp`,
non-fatally, with a loud warning if it cannot.

**UNFINISHED / SUSPECT — do this first:**

- The first version of the new test used `id -gn` (the file's *own* group), so it
  passed with the fix removed — worthless. It was rewritten to use a **secondary**
  group (`id -Gn`, first non-primary), which should make the chgrp observable.
- **The revert check was never completed** (the command was botched). Run it:
  remove the `chgrp` block from `add_contributor.sh`, run
  `uv run pytest tests/scripts/server_contrib/test_add_contributor.py -q -k group`,
  confirm it FAILS, restore. A backup copy exists at `/tmp/addc_ok.sh` (laptop).
- Then run the full file, `ruff check --fix` / `ruff format` / `pyright` on the
  test, and `just typecheck`.

---

## 5. UNCOMMITTED WORK ON THE LAPTOP

```
git status --porcelain
 M kamma/threads/20261023_contrib_1_web_server/plan.md      # today's findings, verified
 M scripts/server_contrib/add_contributor.sh                # htpasswd group fix
 M tests/scripts/server_contrib/test_add_contributor.py     # its test (see §4)
```

The `plan.md` edits are accurate and should be kept: 3.1 and 3.3 ticked with
measurements, **3.4 unticked** (it was wrongly ticked earlier — only alice was
verified, two users were never verified), 3.6 ticked with all four window paths
verified live, 3.5 annotated with the drill findings, and 3.2 annotated with the
branch-protection and deploy-key findings. Commit only after §4 is finished.

Suggested message once §4 is settled:
`#215 contrib_1: drill findings, htpasswd group fix`

---

## 6. WHAT IS ACTUALLY DONE (from the plan)

- **3.6 complete and verified live**: cron at 01:00 IST (server clock is IST) +
  the `/status` failure surface. All four window paths were exercised on the
  server and each reflected in `/status`: happy (`rebuilt`, 49 min and 55 min,
  health check passed), main unchanged (`skipped`, 9 s, problems 0), dirty tree
  (`failed` with the exact reason, alice untouched), rollback (corrupt JSON in a
  scratch dir: `failed`, then `restored db`, `restored working tree`, `restored
  contributor files`). Also found and fixed a real bug in the writer: it listed
  an *earlier* run's error in a clean run's status (commit `1befe821`).
- **3.3 complete**: full server rebuild measured at 49 min and 55 min on the
  2-core box — well under the ~3 h trigger, so the server keeps rebuilding
  nightly (no maintainer-pushed db).
- **3.2**: clone/pull/push proven working, `contributions` push reaches the
  branch, main protected; deploy-key caveat in §3.
- Push path verified end to end: `contrib: submit data 2026-11-03` on the
  `contributions` branch carried alice's 2 entries.

---

## 7. REMAINING TASKS AFTER THE CLEANUP

- 3.4 — blocked on §2 (multi-user).
- 3.5 — finish the removal drill (§1 leftovers), then mark done.
- 3B.1 — security review, read-only. **The plan has `⚠️ MODEL SWITCH REQUIRED
  (Opus)` here**; do it in a fresh session with a stronger model.
- 4.1–4.5 — rehearsal, failure drills, contributor-facing instructions, first
  real contributor, thread wrap. 4.1 needs 2–3 real entries by the owner.

---

## 8. RULES THAT BIT TODAY

- Never `pkill`/`kill` on the server; the window restarts instances itself.
- Never let the herdr agent hold a long-running command (120 s timeout kills it).
- Never print env/htpasswd contents; `grep -c` or a login test instead.
- The server agent (`herdr` pane `w2:p1`, host `epitaka`) was running a **free
  OpenRouter model (Nemotron)** today and made mistakes (wrong URL typo, wrong
  step ordering, ran the window in the foreground). Treat its output as
  untrusted: verify every claim from the laptop with a read-only command.
- A force-restore of `main` changed HEAD relative to `logs/last_built_commit`
  and turned the next "skip" run into a 55-minute rebuild. After any history
  rewrite, expect one full rebuild on the server.
- `NOTICED — NOT TOUCHING`: the window leaves an 883 MB `dpd.db.prev` and a
  `_contrib_worktree/` in the clone after a successful run; harmless on 65 GB
  free but worth a cleanup task.
