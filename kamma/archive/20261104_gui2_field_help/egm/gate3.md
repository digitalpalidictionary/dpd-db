# Gate 3 — implementation-readiness audit

Backend: native subagent (Plan type, read-only). One Goldfish. Given the plan path, the spec path and the repo. It did not read `egm/`.

## Raw findings (condensed)

No Blockers. Five Majors, four Nits. The reviewer confirmed: the Phase 1 snippet matches `dpd_fields.py:458-467`; `ft.Tooltip`, `size_constraints` and `wait_duration` int are valid in Flet 1.0.1; `DpdTextField(name=...)` builds outside a page (`test_dpd_fields_classes.py:21,29`); 50 `FieldConfig("...")` calls with string first arguments sit in `__init__`.

1. Major: "change nothing else" contradicts "fix pre-existing lint errors"; line-count check is weak.
2. Major: pyright form differs between tasks (`--project /dev/null` versus plain).
3. Major: the untracked-files check needs git, which the executor rules forbid.
4. Major: browser sequence leaves port, pid file, start under `timeout`, navigation, connect method and selection check to the implementer.
5. Major: Phase 4 does not say which of the nine fields Pass 1 hides; 18 hovers impossible.
6. Nit: cache helper unnamed; cache clearing in tests unspecified.
7. Nit: verify lines lack expected strings; `just typecheck` is pyrefly; no place for the fail count and screenshot paths.
8. Nit: Phase 3 source list has no file name or layout.
9. Nit: `ast` visitor must read `args[0]`.

## Dispositions

| # | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | Edit rule vs lint rule | Major | Accept | plan task 3 of Phase 1 | plan: backup copy, plain `diff`, list lint fixes, formatter-drift fallback |
| 2 | Pyright form | Major | Accept | `CLAUDE.md` says plain pyright analyses nothing under `gui2/` | plan: `--project /dev/null` everywhere |
| 3 | Git in a check | Major | Accept | executor rule forbids git | plan: `find -newer` against the pid file |
| 4 | Browser sequence | Major | Accept | `CLAUDE.md:67` documents `attach --extension=chrome`; `main.py:254` has `_TAB_JUMP_KEYS` (E = Pass2Add) | plan: "Live check recipe" section |
| 5 | Pass 1 field list | Major | Accept | `PASS1_FIELDS` (`dpd_fields_lists.py:324`) shows `lemma_1`, `pos`, `example_1`, `comment` of the nine | plan Phase 4: 13 hovers |
| 6 | Helper name and cache clearing | Nit | Accept | none named before | plan: `_cached_help`, fixture with `cache_clear()` |
| 7 | Expected strings, where to write | Nit | Accept | `justfile:144` `typecheck` runs `pyrefly check` | plan verify lines |
| 8 | Source list layout | Nit | Accept | none named before | plan: `$SCRATCH/help_sources.md`, `name \| source \| ticked` |
| 9 | `ast` `args[0]` | Nit | Accept | reviewer confirmed 50 string-constant first arguments | plan Phase 1 test task |

Counts: 9 raw findings, 9 rows. 9 accepted, 0 rejected, 0 escalated.
