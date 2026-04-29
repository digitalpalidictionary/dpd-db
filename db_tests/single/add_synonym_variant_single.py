#!/usr/bin/env python3
"""Find synonyms for words that share one cleaned meaning and same pos/grammar signature."""

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.models import DpdHeadword
from db_tests.single.add_synonym_variant_multi import (
    GlobalVars,
    _assign,
    _entry_label,
    _format_fields,
    _general_key,
    _show_result,
    _split_field,
    clean_meaning,
    grammar_signature,
)
from tools.db_search_string import db_search_string
from tools.printer import printer as pr


def _pair_key_single(
    pos: str, hw_a: DpdHeadword, hw_b: DpdHeadword, meaning: str, sig: str
) -> str:
    lemmas = sorted([hw_a.lemma_clean, hw_b.lemma_clean])
    return f"{pos}:{lemmas[0]}|{lemmas[1]}:{meaning}:{sig}"


def find_single_meaning_pairs(g: GlobalVars) -> None:
    """Find pairs of single-meaning headwords sharing the same cleaned meaning and pos/grammar sig."""
    pr.green_tmr("finding single-meaning pairs")

    buckets: dict[tuple[str, str, str], list[DpdHeadword]] = {}

    syn_sets: dict[int, set[str]] = {}
    phon_sets: dict[int, set[str]] = {}
    text_sets: dict[int, set[str]] = {}

    for hw in g.dpd_db:
        syn_sets[hw.id] = set(hw.synonym_list)
        phon_sets[hw.id] = _split_field(hw.var_phonetic)
        text_sets[hw.id] = _split_field(hw.var_text)
        if not hw.meaning_1 or "; " in hw.meaning_1:
            continue
        cleaned = clean_meaning(hw.meaning_1)
        if not cleaned:
            continue
        sig = grammar_signature(hw.grammar)
        buckets.setdefault((hw.pos, sig, cleaned), []).append(hw)

    pairs: list[tuple[DpdHeadword, DpdHeadword, str]] = []
    seen: set[frozenset[int]] = set()

    for (pos, sig, meaning), entries in buckets.items():
        if len(entries) < 2:
            continue
        for i, hw_a in enumerate(entries):
            for hw_b in entries[i + 1 :]:
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                seen.add(edge)
                if hw_a.lemma_clean == hw_b.lemma_clean:
                    continue
                key = _pair_key_single(pos, hw_a, hw_b, meaning, sig)
                gen_key = _general_key(pos, [meaning])
                if key in g.exceptions or gen_key in g.exceptions:
                    continue
                a_clean = hw_a.lemma_clean
                b_clean = hw_b.lemma_clean
                a_has_b = (
                    b_clean in syn_sets[hw_a.id]
                    or b_clean in phon_sets[hw_a.id]
                    or b_clean in text_sets[hw_a.id]
                )
                b_has_a = (
                    a_clean in syn_sets[hw_b.id]
                    or a_clean in phon_sets[hw_b.id]
                    or a_clean in text_sets[hw_b.id]
                )
                already_related = a_has_b and b_has_a
                if already_related:
                    continue
                pairs.append((hw_a, hw_b, meaning))

    g.pairs = [(a, b, [m]) for (a, b, m) in pairs]
    pr.yes(str(len(g.pairs)))


def prompt_pairs(g: GlobalVars) -> bool:
    """Walk through single-meaning pairs and prompt the user. Returns True if restart requested."""
    pr.green("adding synonyms to db")

    total = len(g.pairs)

    print(
        "[dim]synonym: different construction.  phonetic: same construction, different spelling.  textual: manuscript variant."
    )

    for counter, (hw_a, hw_b, shared) in enumerate(g.pairs):
        meaning = shared[0]
        pos = hw_a.pos
        gen_key = _general_key(pos, [meaning])
        if gen_key in g.exceptions:
            continue

        print(
            "\n----------------------------------------------------------------------\n"
        )
        print(f"[white]{counter + 1} / {total}  [green]{meaning}")
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        print(_entry_label(hw_b))
        print(f"[cyan]{_format_fields(hw_b)}")

        sig = grammar_signature(hw_a.grammar)
        key = _pair_key_single(pos, hw_a, hw_b, meaning, sig)

        gui_string = db_search_string([hw_a.lemma_1, hw_b.lemma_1], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")
        choice = Prompt.ask(
            "[white](s)ynonym, (p)honetic, (t)extual, (e)xception, (g)eneral, (pass), (r)estart, (q)uit"
        )

        if choice == "s":
            _assign(hw_a, hw_b.lemma_clean, "synonym")
            _assign(hw_b, hw_a.lemma_clean, "synonym")
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

        elif choice == "g":
            g.add_exception(gen_key)
            print(f"  [red]general exception added: {gen_key!r}")

        elif choice == "r":
            return True

        elif choice == "q":
            break

    return False


def main() -> None:
    pr.tic()
    print("[bright_yellow]synonym single — finding and adding single-meaning synonyms")
    while True:
        g = GlobalVars()
        find_single_meaning_pairs(g)
        if not prompt_pairs(g):
            break
    pr.toc()


if __name__ == "__main__":
    main()
