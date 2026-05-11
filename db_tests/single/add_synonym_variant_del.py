#!/usr/bin/env python3
"""Find and review synonym pairs that are likely wrong.

Gating uses a SOFT rule (`_plausibly_valid_synonym`): same pos_class
plus at least one shared cleaned meaning. Rationale: the synonym field
stores lemma_clean only, so deleting collaterally breaks links to
plausibly-valid sibling homonyms. We favour recall over precision here;
the strict ≥2-shared rule from single/multi is kept as
`_is_valid_synonym` for easy revert.

Per-(hw_a, syn_clean):
- restrict candidates to same pos_class (cross-pos homonyms can't be
  the intended target)
- if any same-class candidate plausibly matches → skip whole syn_clean
- if none plausibly match → flag the same-class candidates
- if no same-class candidate exists at all → flag the cross-pos
  candidates (dangling reference, surface for cleanup)
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
            with open(self.pth.syn_var_del_exceptions_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_exceptions(self) -> None:
        with open(self.pth.syn_var_del_exceptions_path, "w") as f:
            json.dump(self.exceptions, f, ensure_ascii=False, indent=2)


def _plausibly_valid_synonym(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    """Soft gating check: same pos_class + at least one shared cleaned meaning.

    Used only to decide whether a lemma_clean reference has a plausibly
    intended target among its homonyms — if yes, we don't flag any
    sibling homonym as wrong (deleting would collaterally break the
    valid link, since the synonym field stores lemma_clean only).
    Strict validity belongs to the add scripts; here we favour recall.
    """
    if pos_class(hw_a.pos) != pos_class(hw_b.pos):
        return False
    if not hw_a.meaning_1 or not hw_b.meaning_1:
        return False
    meanings_a = {m for raw in hw_a.meaning_1.split("; ") if (m := clean_meaning(raw))}
    meanings_b = {m for raw in hw_b.meaning_1.split("; ") if (m := clean_meaning(raw))}
    return bool(meanings_a & meanings_b)


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
) -> list[tuple[DpdHeadword, DpdHeadword]]:
    pr.green_tmr("finding wrong synonym pairs")

    by_lemma_clean: dict[str, list[DpdHeadword]] = {}
    for hw in g.dpd_db:
        by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)

    wrong: list[tuple[DpdHeadword, DpdHeadword]] = []
    seen: set[frozenset[int]] = set()

    for hw_a in g.dpd_db:
        if not hw_a.synonym:
            continue
        a_class = pos_class(hw_a.pos)
        for syn_clean in split_field(hw_a.synonym):
            candidates = [
                hw_b for hw_b in by_lemma_clean.get(syn_clean, []) if hw_b.id != hw_a.id
            ]
            if not candidates:
                continue
            # The synonym field references lemma_clean. Cross-pos homonyms
            # can't have been the intended target, so restrict the validity
            # decision to same-pos candidates when any exist. If none do,
            # the reference is dangling — flag the cross-pos candidates so
            # the user can clean it up.
            same_class = [hw_b for hw_b in candidates if pos_class(hw_b.pos) == a_class]
            if same_class:
                if any(_plausibly_valid_synonym(hw_a, hw_b) for hw_b in same_class):
                    continue
                flag_candidates = same_class
            else:
                flag_candidates = candidates
            for hw_b in flag_candidates:
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                sig = grammar_signature(hw_a.grammar)
                key = _pair_key(a_class, hw_a, hw_b, sig)
                if key in g.exceptions:
                    continue
                seen.add(edge)
                wrong.append((hw_a, hw_b))

    pr.yes(str(len(wrong)))
    return wrong


def prompt_wrong_pairs(
    g: GlobalVars, wrong: list[tuple[DpdHeadword, DpdHeadword]]
) -> bool:
    if not wrong:
        return False
    pr.green("reviewing wrong synonyms")
    print("[dim]delete: not a true synonym (pos / grammar / meaning mismatch).")

    total = len(wrong)
    for counter, (hw_a, hw_b) in enumerate(wrong):
        print("\n" + "-" * 70)
        print(f"[red]{counter + 1} / {total}  [white]wrong synonym")
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        print(_entry_label(hw_b))
        print(f"[cyan]{_format_fields(hw_b)}")

        sig = grammar_signature(hw_a.grammar)
        key = _pair_key(pos_class(hw_a.pos), hw_a, hw_b, sig)

        gui_string = db_search_string([hw_a.lemma_1, hw_b.lemma_1], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](s)ynonym, (t)extual, (d)elete, (e)xception, (pass), (r)estart, (q)uit"
        )

        if choice == "s":
            assign_relationship(hw_a, hw_b.lemma_clean, "synonym")
            assign_relationship(hw_b, hw_a.lemma_clean, "synonym")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "t":
            assign_relationship(hw_a, hw_b.lemma_clean, "var_text")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_text")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "d":
            assign_relationship(hw_a, hw_b.lemma_clean, "delete")
            assign_relationship(hw_b, hw_a.lemma_clean, "delete")
            _show_result(hw_a)
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
