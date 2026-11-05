BRIEF: daily pull of contributor words from the server (EGM Gate 1 input)

## Request (owner, 2026-11-04)
The contributor web server (one gui2 instance per contributor, behind nginx) keeps
each contributor's words in per-contributor files. The owner wants those words
merged into the local data on the owner's laptop automatically, once a day, with
no GitHub pull request and no git merge. "I want the words that users have added
merged locally, that's it." Many contributors in future, not only alice. The laptop
is normally on at 08:00 and the desktop editor (gui2) is closed then.

## Anchored hypothesis
Every morning at 08:00 the laptop copies the contributors' files from the server over
the existing ssh login into a scratch folder. It drops every word the maintainer has
already processed. It copies the rest into the local data folder and runs the
existing merge script for the flag files. It skips the run if the editor is open.
The processed-word filter is the key part: when the maintainer processes a word, the
editor REMOVES it from the contributor's local file, so a plain copy from the server
would bring it back.

## Facts read from the repo (claims to re-check, not facts)
1. Server folder: /var/lib/dpd/contrib_data holds additions_<user>.json, checked_<user>.csv,
   manual_corrections_<user>.tsv, db_test_exceptions_<user>.tsv, daily_log_<user>.json,
   history_<user>.json. It is set by scripts/server_contrib/add_contributor.sh.
2. tools/contrib_entry.py DELIVERED_KINDS lists which per-contributor file patterns are
   delivered (additions, corrections, user_dictionary, checked, manual_corrections,
   variant_readings, spelling_mistakes, db_test_exceptions). History, daily log, presets,
   stash are never delivered. `*_added*` files are review logs and excluded.
3. gui2/additions_manager.py: the maintainer's editor (primary user) reads every
   additions_*.json in gui2/data once at start. save_processed_addition() appends
   (_source_key, _source_hash) to additions_added.json and REMOVES the key from the
   contributor's file (_remove_key_from_file). reject() does the same.
4. scripts/server_contrib/contrib_reconcile.py: reconcile_entries() drops entries whose
   (key, entry_hash) is in the processed log; reconcile_lines() drops flag lines that
   are in contrib_lines_merged.json. The server runs this nightly after pulling main,
   so the server only learns what was processed when the maintainer pushes main.
5. scripts/server_contrib/merge_contrib_files.py: `merge_all(data_dir, shared, log_path)`
   folds flag files (user dictionary, checked, manual corrections, variants, spelling,
   test exceptions) into the shared files and logs each handled line in
   gui2/data/contrib_lines_merged.json. main() default data_dir is gui2/data.
   It does NOT touch additions or corrections JSON.
6. config.ini already has `[epitaka_server] ssh` (a 19-character user@host). No Python
   code reads it. Do not open config.ini (secrets). tools/configger.py reads it with
   config_read(section, option, default).
7. The old git route: `just contrib-merge` = git fetch + git merge origin/contributions
   + merge_contrib_files.py. The server still pushes the contributions branch nightly.
   gui2/data/additions_alice.json, checked_alice.csv, manual_corrections_alice.tsv are
   tracked in git.
8. Laptop: systemd --user works (`systemctl --user is-system-running` = running).
   The editor starts with `uv run python gui2/main.py` (justfile recipe `gui`).
9. Server window: at 01:00 IST the server stops contributor instances, pulls main,
   reconciles, pushes, maybe rebuilds the db (30–55 min), restarts instances.
   Contributor instances write their JSON with write-then-swap (atomic) in
   additions_manager.py; flag files were not checked.

## Constraints
- Never edit .env or .ini files. Never run git commands in the product code path.
- No GitHub, no pull requests, no git merge.
- Keep it simple. The owner calls over-engineering a defect.
