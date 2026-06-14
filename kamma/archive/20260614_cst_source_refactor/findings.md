# Findings — latent oddities (NOTED, NOT FIXED)

Strict behaviour preservation: anything below is preserved as-is in the refactor.
A fix would make new != old and break parity. These are follow-up candidates for
a *separate* thread.

## 1. `make_cst_soup` signature vs call
`GlobalData.make_cst_soup(self, unwrap_notes=True)` is called in `__init__` as
`self.make_cst_soup(self.filenames)`. The list `self.filenames` is passed into
the `unwrap_notes` parameter (a non-empty list is truthy, so notes are still
unwrapped) and the method ignores the argument entirely, reading `self.filenames`
internally. Functionally harmless today, but the parameter is misleading dead
weight. Preserve behaviour: notes always unwrapped.

## 2. Typo'd attribute names on `GlobalData`
`self.subtitlecoutner_alt` (line ~211) — "coutner". Also `self.vagga_alt_counter`
vs `self.subtitlecoutner_alt` naming is inconsistent. Renaming risks missing a
reader; keep names verbatim when porting to parser instance attrs.

## 3. `init_sutta_counter` / `init_samyutta_counter` match blocks
These seed per-book counters. In the OO design they are replaced by per-subclass
`__init__` seeds. Verify each seed value lands on the right parser class (dn2=13,
dn3=23, mn2=50, mn3=100, kn11=422; sn2=11, sn3=21, sn4=34, sn5=44).
→ DONE: seeded in DighaParser/MajjhimaParser/SamyuttaParser/Kn10Kn11Parser `__init__`;
all seed-variant books pass parity.

## 4. `kn17_patisambhidamagga` dead branch references unbound locals (LATENT BUG)
In `Kn17Parser.update` (and the original handler), the final branch
`elif self.vagga and self.section and not sutta_name:` does
`self.sutta = f"{vagga}, {section}".lower()` — but `vagga`/`section` are function
locals only assigned in the `chapter`/`title` branches, never in a `subhead` call.
If this branch ever fired it would raise `UnboundLocalError`. It evidently never
fires (parity is byte-identical), so it is dead code. **Preserved verbatim** — a
fix (e.g. `self.vagga`/`self.section`) would change behaviour if it ever fires.

## 5. `make_cst_soup` is now module-level (was a `GlobalData` method)
`loader.make_cst_soup(pth, books, unwrap_notes=True)` matches the signature the
already-broken `scripts/archive/*` imports expect. This is a *new* working public
symbol; those archive scripts were importing a name that did not exist at module
level before. Not a behaviour change to any live path.

## 6. `apt` uses prefix "AP", not "APt" — dead assignment (LATENT BUG)
*(surfaced by CodeRabbit in 2nd review)* `AptParser.update` (old
`apt_abhidhanapadipikatika`, lines 2764/2767) opens with `book = "APt"` immediately
overwritten by `book = "AP"`. So every `apt` source code is emitted with prefix
**"AP"**, and the apparently-intended "APt" prefix is dead. No collision (`ap` uses
"APP"), but the source codes are almost certainly wrong. **Preserved verbatim.**

## 7. `abh2` emits literal "xxxxxxx" placeholder in sutta text (LATENT BUG)
*(surfaced by CodeRabbit in 2nd review)* `Abh2Parser.update` (old `abh2_vibhanga`,
line 1458): when `not self.vagga`, `self.sutta = f"xxxxxxx, {sutta}".lower()`. A
debug placeholder leaks into real output for vagga-less `abh2` subheads. Parity
confirms the old module emits it identically. **Preserved verbatim** — a real data
artifact worth fixing in the follow-up.

## 8. `x["n"]` (str) assigned to int-typed `sutta_counter` (type smell, benign)
*(surfaced by CodeRabbit in 2nd review)* AnguttaraParser / ANa / ANt set
`self.sutta_counter = x["n"]` (a str). It is only ever interpolated into f-strings
afterwards, never used in arithmetic on that path, so no `TypeError`. Verbatim from
old (lines 804/1954/1983). Not a bug; noted for the typing follow-up.
