# Gate 1 — idea stress-test

Backend: native subagents (Plan type, read-only). No smoke probe fail, no switch. Three Goldfish, lenses paired (small thread: code change under 100 lines).
- G1 = Contrarian/YAGNI + UX (given request and hypothesis only)
- G2 = Cost + Migration (given brief.md)
- G3 = Observability + Tech debt (given brief.md)

## Raw findings (condensed, severity as reported)

G1
1. Major — a hover tooltip on the label fails keyboard users. The label is a non-focusable `ft.Text`. Tooltips fire on hover or long-press. Fix: attach help to the focused field (helper text, or one help strip fed from `track_focus`).
2. Major — the label is not a good target. Rows with tall composites put the label mid-block, far from the cursor.
3. Major — Flet already has `helper_text`/`hint_text`; check collisions with validation messages.
4. Major — help text already exists in the two docs files; a new file forks it.
5. Major — no rule for a missing or misspelled help key; silent no-help.
6. Nit — default `wait_duration` is 100 ms; long text flashes.
7. Nit — no visual cue that a label has help.

G2
1. Major — cost: tooltip as a string property adds 0 controls. Load the help data once at module level, not per row, because the form is rebuilt on every clear.
2. Major — web payload: about 10 KB per rebuild at 200 characters each. Cap text length. (G2 also said desktop is the default client from `ft.run(main)`.)
3. Major — `selectable=True` label may not pass tooltip through or may block hover. Unverified. Spike on one field. Fallback: wrap label in a Container.
4. Major — help file can drift from the field list. Add a test: keys equal `FieldConfig` names, non-empty, under a length cap.
5. Nit — style guide has 39 headings, not 41; three are combined; one has a typo (`example_1 and example_1`).
6. Info — no test calls `_create_field_row`; loader must tolerate a missing file. `helper` must not carry static help because code overwrites it. Rollback is one revert.

G3
1. Major — no check ties help data to field list; all failures are silent. Add pytest, a runtime log warning, and decide that keys are base names only (not `_add`).
2. Major — help is a third copy beside the style guide and the table doc. Either name the data file as owner and cross-link, or generate from docs (fails for 9 fields).
3. Major — owner/format/location undecided. `gui2/data/` holds runtime state, so hand-written reference data does not belong there. A `.py` dict next to the code gives typo errors; JSON/TOML needs a loader and a failure policy.
4. Major — selectable label and tooltip width, same as G2-3. Cap text near 200 characters. Consider a help icon.
5. Nit — brief's style-guide count shaky.
6. Scope — leave dropdown option lists out; put any option explanation in the field-level text.

## Dispositions

| # | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G1-1 | Hover on label does not serve keyboard users | Major | Escalate (mechanism fork) | `gui2/dpd_fields.py:461` label is `ft.Text`; flet `tooltip.py` says hover (desktop) or long-press. Whether Flutter shows a tooltip on keyboard focus: not verified | spec decision 1 |
| G1-2 | Label far from tall composites | Major | Accept | row uses `vertical_alignment=CENTER` at `dpd_fields.py:517`; composites are tall | spec, mechanism options |
| G1-3 | Use `helper_text` | Major | Reject for static help | `helper_text` written at `dpd_fields.py:614` (cleared), `1125`, `1425` | spec constraints |
| G1-4 / G3-2 | Second source of truth | Major | Escalate (storage fork) | docs files read; 40 of 50 names have a heading, 9 have none | spec decision 2 |
| G1-5 / G2-4 / G3-1 | Silent drift | Major | Accept | no test covers it today | spec done criteria, plan |
| G1-6 | `wait_duration` 100 ms | Nit | Accept | `tooltip.py` default confirmed | spec |
| G1-7 | No cue help exists | Nit | Accept as open risk | label looks like plain text today | spec, mechanism |
| G2-1 | Cost / load once | Major | Accept (module-level cache); cost worry rejected | `_create_field_row` runs 50 times per rebuild; tooltip is a string property | spec |
| G2-2 | Web payload | Major | Accept cap; reject "desktop is default" | project CLAUDE.md: contributors use the web server (`FLET_FORCE_WEB_SERVER`) | spec length cap |
| G2-3 / G3-4 | Selectable label vs tooltip | Major | Accept: spike first | `selectable=True` at `dpd_fields.py:466`; behaviour not runnable from source | plan phase 1 |
| G2-5 / G3-5 | Style-guide count | Nit | Accept | recounted: 39 headings; 40 of 50 names appear; missing: id, family_idioms, translation_1, example_2, translation_2, var_phonetic, var_text, link, origin, comment. My brief said 41/9 | spec facts |
| G2-6 | Tolerant loader | Info | Accept in part: app warns and goes on; test fails hard | no test calls the row builder | spec |
| G3-3 | Do not store in `gui2/data/` | Major | Accept | listing shows per-user state files | spec decision 2 |
| G3-6 | Skip dropdown options | Scope | Accept | option lists come from `tools.pos` and the db | spec scope |

Counts: 19 raw findings (G1 7, G2 6, G3 6) merged into 13 table rows. Of the 13 rows: 10 accepted (G2-2 accepted in part), 1 rejected (G1-3), 2 escalated (G1-1, G1-4/G3-2).
