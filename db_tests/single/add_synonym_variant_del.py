#!/usr/bin/env python3
"""Find and remove or re-assign synonym relationships that no longer meet validity criteria."""

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.models import DpdHeadword
from db_tests.single.add_synonym_variant_multi import (
    GlobalVars,
    _assign,
    _format_fields,
    _pair_key,
    _show_result,
    _split_field,
    clean_meaning,
    grammar_signature,
)
from tools.db_search_string import db_search_string
from tools.printer import printer as pr


def _is_valid_synonym(hw_a: DpdHeadword, hw_b: DpdHeadword) -> bool:
    """Return True if the synonym relationship between hw_a and hw_b is valid.

    Single meaning: strict 1:1 — same pos, same grammar sig, exact cleaned meaning match.
    Multi meaning: same pos, same grammar sig, ≥2 shared cleaned meanings.
    """
    if hw_a.pos != hw_b.pos:
        return False
    if grammar_signature(hw_a.grammar) != grammar_signature(hw_b.grammar):
        return False
    a_single = "; " not in (hw_a.meaning_1 or "")
    b_single = "; " not in (hw_b.meaning_1 or "")
    if a_single and b_single:
        return clean_meaning(hw_a.meaning_1) == clean_meaning(hw_b.meaning_1)
    meanings_a = frozenset(
        m for raw in (hw_a.meaning_1 or "").split("; ") if (m := clean_meaning(raw))
    )
    meanings_b = frozenset(
        m for raw in (hw_b.meaning_1 or "").split("; ") if (m := clean_meaning(raw))
    )
    return len(meanings_a & meanings_b) >= 2


def find_wrong_synonym_pairs(g: GlobalVars) -> list[tuple[DpdHeadword, DpdHeadword]]:
    """Find pairs listed as synonyms that do not meet the validity criterion."""
    pr.green_tmr("finding wrong synonym pairs")

    by_lemma_clean: dict[str, list[DpdHeadword]] = {}
    for hw in g.dpd_db:
        by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)

    wrong: list[tuple[DpdHeadword, DpdHeadword]] = []
    seen: set[frozenset[int]] = set()

    for hw_a in g.dpd_db:
        if not hw_a.synonym:
            continue
        for syn_clean in _split_field(hw_a.synonym):
            candidates = by_lemma_clean.get(syn_clean, [])
            if any(_is_valid_synonym(hw_a, hw_b) for hw_b in candidates):
                continue
            for hw_b in candidates:
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                seen.add(edge)
                wrong.append((hw_a, hw_b))

    pr.yes(str(len(wrong)))
    return wrong


def prompt_wrong_pairs(
    g: GlobalVars, wrong: list[tuple[DpdHeadword, DpdHeadword]]
) -> bool:
    """Review wrong synonym pairs. Returns True if restart requested."""
    if not wrong:
        return False
    pr.green("reviewing wrong synonyms")

    total = len(wrong)
    print(
        "[dim]synonym: different construction.  phonetic: same construction, different spelling.  textual: manuscript variant."
    )

    for counter, (hw_a, hw_b) in enumerate(wrong):
        print(f"\n[red]{counter + 1} / {total}  [white]wrong synonym")
        print(f"[yellow]{hw_a.lemma_1} [blue]{hw_a.pos} [green]{hw_a.meaning_1}")
        print(f"[cyan]{_format_fields(hw_a)}")
        print(f"[yellow]{hw_b.lemma_1} [blue]{hw_b.pos} [green]{hw_b.meaning_1}")
        print(f"[cyan]{_format_fields(hw_b)}")

        pos = hw_a.pos
        sig = grammar_signature(hw_a.grammar)
        key = _pair_key(pos, hw_a, hw_b, sig)
        gui_string = db_search_string([hw_a.lemma_1, hw_b.lemma_1], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](d)elete, (p)honetic, (t)extual, (e)xception, (pass), (r)estart, (q)uit"
        )

        if choice == "d":
            _assign(hw_a, hw_b.lemma_clean, "delete")
            _assign(hw_b, hw_a.lemma_clean, "delete")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "p":
            _assign(hw_a, hw_b.lemma_clean, "var_phonetic")
            _assign(hw_b, hw_a.lemma_clean, "var_phonetic")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "t":
            _assign(hw_a, hw_b.lemma_clean, "var_text")
            _assign(hw_b, hw_a.lemma_clean, "var_text")
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
