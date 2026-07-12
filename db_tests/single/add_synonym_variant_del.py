#!/usr/bin/env python3
"""Find and review synonym pairs that are likely wrong.

Before any homonym lookup, for pos == "pron" only: if syn_clean is
already one of the generated inflections for hw_a's pronoun family
(`family_word`), it's confirmed valid outright — some declined pronoun
forms (e.g. `ehi`, `amhā` as contracted spellings of `imehi`/`imasmā`)
were never given their own headword, so no same-lemma_clean homonym
exists to match against; the inflection table is the authoritative
source instead. Only the family's "primary" headword (e.g. `ima 1.1`,
`eta`) carries the full generated paradigm in its own `inflections`
field — every declined-form headword has a trivial self-only list — so
this unions `inflections_list` across the whole family_word rather than
checking hw_a alone. Restricted to pronouns because every other pos
always references a real headword — applying this bypass more broadly
would mask genuine self-referential mistakes elsewhere.

Otherwise gating uses a SOFT rule: same pos_class plus any of — shared
cleaned meaning, shared non-empty family_word (declension siblings), or
a reciprocal synonym link back to `hw_a` (`_has_reciprocal_synonym`).
Rationale: the synonym field stores lemma_clean only, so deleting
collaterally breaks links to plausibly-valid sibling homonyms. We
favour recall over precision here; the strict ≥2-shared rule from
single/multi is kept as `_is_valid_synonym` for easy revert.

Per-(hw_a, syn_clean):
- if there is exactly one candidate and its meaning overlaps hw_a's,
  it's confirmed valid regardless of pos — the pos_class restriction
  below exists to disambiguate between several candidates, which is
  meaningless with only one (e.g. `cicciṭa` masc ↔ `ciṭiciṭi` ind,
  identical meaning, unrelated pos)
- otherwise restrict candidates to same pos_class (cross-pos homonyms
  can't be the intended target when there's a choice to make)
- if any same-class candidate plausibly matches → skip whole syn_clean
- if none plausibly match → flag the same-class candidates
- if no same-class candidate exists at all → flag the cross-pos
  candidates (dangling reference, surface for cleanup)

All non-plausible candidates for one (hw_a, syn_clean) share the same
lemma_clean, so they're one underlying decision, not several — they are
grouped into a single review row rather than one row per homonym.
"""

import json

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.models import DpdHeadword
from db_tests.single.add_synonym_variant_multi import (
    GlobalVars as _BaseGlobalVars,
    _entry_label,
    _format_fields,
    _pair_key,
    _show_result,
)
from tools.db_search_string import db_search_string
from tools.printer import printer as pr
from tools.synonym_variant import (
    assign_relationship,
    clean_meaning,
    grammar_signature,
    pos_class,
    split_field,
)


class GlobalVars(_BaseGlobalVars):
    """Separate exceptions file: del-exceptions mean 'keep this synonym
    despite failing validity', which is the opposite of multi/single's
    'don't propose as a new synonym'. Distinct verdicts, distinct files.
    """

    def _load_exceptions(self) -> list[str]:
        try:
            with open(self.pth.syn_var_del_exceptions_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_exceptions(self) -> None:
        with open(self.pth.syn_var_del_exceptions_path, "w", encoding="utf-8") as f:
            json.dump(self.exceptions, f, ensure_ascii=False, indent=2)


def _plausibly_valid_synonym(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    """Soft gating check: same pos_class + (shared cleaned meaning OR shared
    non-empty family_word).

    Used only to decide whether a lemma_clean reference has a plausibly
    intended target among its homonyms — if yes, we don't flag any
    sibling homonym as wrong (deleting would collaterally break the
    valid link, since the synonym field stores lemma_clean only).
    Strict validity belongs to the add scripts; here we favour recall.

    family_word catches declension siblings whose meaning text differs
    (e.g. `imasmā` "from this" vs `asmā` "from this" both belong to
    family_word `ima` — but even where wording diverges, `family_word`
    is the DB's own authoritative grouping of one word's inflected/
    alternate forms, more reliable here than meaning-text overlap).
    """
    if pos_class(hw_a.pos) != pos_class(hw_b.pos):
        return False
    if hw_a.family_word and hw_a.family_word == hw_b.family_word:
        return True
    return _meaning_overlap(hw_a, hw_b)


def _meaning_overlap(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    """True if hw_a and hw_b share at least one cleaned meaning phrase."""
    if not hw_a.meaning_1 or not hw_b.meaning_1:
        return False
    meanings_a = {m for raw in hw_a.meaning_1.split("; ") if (m := clean_meaning(raw))}
    meanings_b = {m for raw in hw_b.meaning_1.split("; ") if (m := clean_meaning(raw))}
    return bool(meanings_a & meanings_b)


def _has_reciprocal_synonym(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    """True if `hw_b` already lists `hw_a`'s lemma_clean in its own synonym field.

    A reciprocal link is stronger evidence than meaning overlap that an
    ambiguous lemma_clean reference (shared by several homonyms) has already
    been resolved to this specific homonym, e.g. `assācariya` → `sārathi`
    resolves to `sārathi 2` because `sārathi 2` already lists `assācariya`
    back, even though its cleaned meaning doesn't textually overlap.
    """
    return hw_a.lemma_clean in split_field(hw_b.synonym)


def _is_valid_synonym(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    if pos_class(hw_a.pos) != pos_class(hw_b.pos):
        return False
    if grammar_signature(hw_a.grammar) != grammar_signature(hw_b.grammar):
        return False
    if not hw_a.meaning_1 or not hw_b.meaning_1:
        return False
    a_single = "; " not in hw_a.meaning_1
    b_single = "; " not in hw_b.meaning_1
    if a_single and b_single:
        return clean_meaning(hw_a.meaning_1) == clean_meaning(hw_b.meaning_1)
    meanings_a = frozenset(
        m for raw in hw_a.meaning_1.split("; ") if (m := clean_meaning(raw))
    )
    meanings_b = frozenset(
        m for raw in hw_b.meaning_1.split("; ") if (m := clean_meaning(raw))
    )
    return len(meanings_a & meanings_b) >= 2


def find_wrong_synonym_pairs(
    g: GlobalVars,
) -> list[tuple[DpdHeadword, list[DpdHeadword]]]:
    """Return one (hw_a, group) row per ambiguous synonym reference.

    `group` holds every non-plausible homonym of that syn_clean — usually
    just one, but an ambiguous lemma_clean can resolve to several dead-end
    homonyms (e.g. `amhā` → both a pr and a fem headword), which is a
    single underlying decision, not one per homonym.
    """
    pr.green_tmr("finding wrong synonym pairs")

    by_lemma_clean: dict[str, list[DpdHeadword]] = {}
    for hw in g.dpd_db:
        by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)

    # Only the "primary" headword of a pronoun family (e.g. `ima 1.1`, `eta`)
    # carries the fully generated declension paradigm in its own
    # `inflections` field — every declined-form headword in the same family
    # (`imehi`, `imasmā`, ...) has a trivial self-only inflections field, so
    # checking hw_a's own list alone misses contracted spellings like `ehi`.
    # Union across the whole family_word instead.
    family_inflections: dict[str, set[str]] = {}
    for hw in g.dpd_db:
        if hw.pos == "pron" and hw.family_word:
            family_inflections.setdefault(hw.family_word, set()).update(
                hw.inflections_list
            )

    wrong: list[tuple[DpdHeadword, list[DpdHeadword]]] = []
    seen: set[frozenset[int]] = set()

    for hw_a in g.dpd_db:
        if not hw_a.synonym or not hw_a.meaning_1:
            continue
        a_class = pos_class(hw_a.pos)
        for syn_clean in split_field(hw_a.synonym):
            # Only pronouns have declension spellings that never got their own
            # headword (e.g. `ehi`, `amhā` as contracted forms of
            # `imehi`/`imasmā`) — every other pos always references a real
            # headword, so this bypass would mask genuine self-referential
            # mistakes there. If syn_clean is one of hw_a's family's generated
            # inflections, it's confirmed valid; no homonym lookup needed.
            if hw_a.pos == "pron" and syn_clean in family_inflections.get(
                hw_a.family_word, set()
            ):
                continue
            candidates = [
                hw_b
                for hw_b in by_lemma_clean.get(syn_clean, [])
                if hw_b.id != hw_a.id and hw_b.meaning_1
            ]
            if not candidates:
                continue
            # pos_class restriction below exists to disambiguate when a
            # lemma_clean has several candidates of differing pos — it's
            # meaningless when there's only one candidate at all, so an
            # unambiguous cross-pos match (e.g. `cicciṭa` masc ↔ `ciṭiciṭi`
            # ind, identical meaning) shouldn't be gated on pos matching.
            if len(candidates) == 1 and _meaning_overlap(hw_a, candidates[0]):
                continue
            # The synonym field references lemma_clean. Cross-pos homonyms
            # can't have been the intended target, so restrict the validity
            # decision to same-pos candidates when any exist. If none do,
            # the reference is dangling — flag the cross-pos candidates so
            # the user can clean it up.
            same_class = [hw_b for hw_b in candidates if pos_class(hw_b.pos) == a_class]
            if same_class:
                if any(
                    _plausibly_valid_synonym(hw_a, hw_b)
                    or _has_reciprocal_synonym(hw_a, hw_b)
                    for hw_b in same_class
                ):
                    continue
                flag_candidates = same_class
            else:
                flag_candidates = candidates

            # Drop candidates whose undirected (hw_a, hw_b) edge was already
            # surfaced from the reverse direction (hw_b's own synonym field
            # also referencing hw_a).
            group = []
            for hw_b in flag_candidates:
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                seen.add(edge)
                group.append(hw_b)
            if not group:
                continue

            sig = grammar_signature(hw_a.grammar)
            key = _pair_key(a_class, hw_a, group[0], sig)
            if key in g.exceptions:
                continue
            wrong.append((hw_a, group))

    pr.yes(str(len(wrong)))
    return wrong


def _choose_target(group: list[DpdHeadword]) -> DpdHeadword:
    """Pick which homonym an (s)/(t) action applies to.

    Single-candidate groups (the common case) return it directly with no
    prompt. Ambiguous groups (several dead-end homonyms sharing one
    lemma_clean) ask which one is actually meant.
    """
    if len(group) == 1:
        return group[0]
    for i, hw_b in enumerate(group):
        print(f"  [white]{i + 1}. {hw_b.lemma_1} {hw_b.pos} {hw_b.meaning_1}")
    idx = Prompt.ask(
        "[white]which homonym?", choices=[str(i + 1) for i in range(len(group))]
    )
    return group[int(idx) - 1]


def prompt_wrong_pairs(
    g: GlobalVars, wrong: list[tuple[DpdHeadword, list[DpdHeadword]]]
) -> bool:
    if not wrong:
        return False
    pr.green("reviewing wrong synonyms")
    print("[dim]delete: not a true synonym (pos / grammar / meaning mismatch).")

    total = len(wrong)
    for counter, (hw_a, group) in enumerate(wrong):
        print("\n" + "-" * 70)
        print(f"[red]{counter + 1} / {total}  [white]wrong synonym")
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        for hw_b in group:
            print(_entry_label(hw_b))
            print(f"[cyan]{_format_fields(hw_b)}")

        sig = grammar_signature(hw_a.grammar)
        key = _pair_key(pos_class(hw_a.pos), hw_a, group[0], sig)

        gui_string = db_search_string(
            [hw_a.lemma_1, *(hw_b.lemma_1 for hw_b in group)], gui=True
        )
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](s)ynonym, (p)honetic, (t)extual, (d)elete, (e)xception, "
            "(pass), (r)estart, (q)uit"
        )

        if choice == "s":
            hw_b = _choose_target(group)
            assign_relationship(hw_a, hw_b.lemma_clean, "synonym")
            assign_relationship(hw_b, hw_a.lemma_clean, "synonym")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "p":
            hw_b = _choose_target(group)
            assign_relationship(hw_a, hw_b.lemma_clean, "var_phonetic")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_phonetic")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "t":
            hw_b = _choose_target(group)
            assign_relationship(hw_a, hw_b.lemma_clean, "var_text")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_text")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "d":
            for hw_b in group:
                assign_relationship(hw_a, hw_b.lemma_clean, "delete")
                assign_relationship(hw_b, hw_a.lemma_clean, "delete")
            _show_result(hw_a)
            for hw_b in group:
                _show_result(hw_b)
            g.db_session.commit()

        elif choice == "e":
            g.add_exception(key)
            print(f"  [red]exception added: {key!r}")

        elif choice == "r":
            return True

        elif choice == "q":
            break

    return False


def main() -> None:
    pr.tic()
    print("[bright_yellow]synonym del — finding and removing wrong synonyms")
    while True:
        g = GlobalVars()
        wrong = find_wrong_synonym_pairs(g)
        if not prompt_wrong_pairs(g, wrong):
            break
    pr.toc()


if __name__ == "__main__":
    main()
