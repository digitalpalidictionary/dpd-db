#!/usr/bin/env python3
"""Find synonyms for words that share 2+ cleaned meanings and same pos/grammar signature."""

import json
import re

import pyperclip
from rich import print
from rich.prompt import Prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.exceptions: list[str] = self._load_exceptions()
        self.pairs: list[tuple[DpdHeadword, DpdHeadword, list[str]]] = []

    def _load_exceptions(self) -> list[str]:
        try:
            with open(self.pth.syn_var_exceptions_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_exceptions(self) -> None:
        with open(self.pth.syn_var_exceptions_path, "w") as f:
            json.dump(self.exceptions, f, ensure_ascii=False, indent=2)

    def add_exception(self, key: str) -> None:
        self.exceptions.append(key)
        self._save_exceptions()


_CASE_PERSON = re.compile(r"\b(nom|acc|instr|dat|abl|gen|loc|voc|1st|2nd|3rd)\b")
_GENDER = re.compile(r"\b(masc|fem|nt)\b")


def clean_meaning(text: str) -> str:
    """Remove commentary meaning and bracketed content from a meaning string."""
    text = re.sub(r"\(comm\).*$", "", text)
    text = re.sub(r" \(.*?\) | \(.*?\)|\(.*?\) ", "", text)
    return text.strip()


def grammar_signature(grammar: str) -> str:
    """Return case/person markers; add gender only when case is also present."""
    cases = set(_CASE_PERSON.findall(grammar))
    if not cases:
        return ""
    markers = sorted(cases | set(_GENDER.findall(grammar)))
    return ",".join(markers)


def _split_field(value: str) -> set[str]:
    return {t.strip() for t in value.split(",") if t.strip()}


def _pair_key(pos: str, hw_a: DpdHeadword, hw_b: DpdHeadword, sig: str) -> str:
    lemmas = sorted([hw_a.lemma_clean, hw_b.lemma_clean])
    return f"{pos}:{lemmas[0]}|{lemmas[1]}:{sig}"


def _general_key(pos: str, meanings: list[str]) -> str:
    return f"[{pos}] {'; '.join(sorted(meanings))}"


def find_multi_meaning_pairs(g: GlobalVars) -> None:
    """Find pairs of multi-meaning headwords sharing ≥2 cleaned meanings and same pos/grammar sig."""
    pr.green_tmr("finding multi-meaning pairs")

    # bucket: (pos, sig) -> list of (hw, frozenset of cleaned meanings)
    buckets: dict[tuple[str, str], list[tuple[DpdHeadword, frozenset[str]]]] = {}

    # precompute relationship sets once to avoid repeated splits in inner loop
    syn_sets: dict[int, set[str]] = {}
    phon_sets: dict[int, set[str]] = {}
    text_sets: dict[int, set[str]] = {}

    for hw in g.dpd_db:
        syn_sets[hw.id] = set(hw.synonym_list)
        phon_sets[hw.id] = _split_field(hw.var_phonetic)
        text_sets[hw.id] = _split_field(hw.var_text)
        if not hw.meaning_1 or "; " not in hw.meaning_1:
            continue
        cleaned: frozenset[str] = frozenset(
            m for raw in hw.meaning_1.split("; ") if (m := clean_meaning(raw))
        )
        if not cleaned:
            continue
        sig = grammar_signature(hw.grammar)
        bucket_key = (hw.pos, sig)
        buckets.setdefault(bucket_key, []).append((hw, cleaned))

    pairs: list[tuple[DpdHeadword, DpdHeadword, list[str]]] = []
    seen: set[frozenset[int]] = set()

    for (pos, sig), entries in buckets.items():
        # inverted index: meaning -> headwords in this bucket
        meaning_to_hws: dict[str, list[DpdHeadword]] = {}
        for hw, meanings in entries:
            for m in meanings:
                meaning_to_hws.setdefault(m, []).append(hw)

        for hw_a, meanings_a in entries:
            # candidates: headwords sharing at least one meaning with hw_a
            candidates: dict[int, DpdHeadword] = {}
            for m in meanings_a:
                for hw_b in meaning_to_hws[m]:
                    if hw_b.id != hw_a.id:
                        candidates[hw_b.id] = hw_b

            for hw_b in candidates.values():
                edge = frozenset({hw_a.id, hw_b.id})
                if edge in seen:
                    continue
                seen.add(edge)
                if hw_a.lemma_clean == hw_b.lemma_clean:
                    continue
                meanings_b = frozenset(
                    m for raw in hw_b.meaning_1.split("; ") if (m := clean_meaning(raw))
                )
                shared = meanings_a & meanings_b
                if len(shared) < 2:
                    continue
                key = _pair_key(pos, hw_a, hw_b, sig)
                gen_key = _general_key(pos, list(shared))
                if key in g.exceptions or gen_key in g.exceptions:
                    continue
                b_clean = hw_b.lemma_clean
                a_clean = hw_a.lemma_clean
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
                pairs.append((hw_a, hw_b, sorted(shared)))

    g.pairs = pairs
    pr.yes(str(len(g.pairs)))


def _entry_label(hw: DpdHeadword) -> str:
    family_root = f" [magenta]{hw.family_root}" if hw.family_root else ""
    family_word = f" [magenta]{hw.family_word}" if hw.family_word else ""
    return (
        f"[yellow]{hw.lemma_1} [blue]{hw.pos} "
        f"[green]{hw.meaning_1} [white]({hw.degree_of_completion})"
        f"{family_root}{family_word}"
    )


def _format_fields(hw: DpdHeadword) -> str:
    syn = hw.synonym.split(", ") if hw.synonym else []
    var = hw.variant.split(", ") if hw.variant else []
    var_text = hw.var_text.split(", ") if hw.var_text else []
    phon = sorted(_split_field(hw.var_phonetic))
    return f"  syn:{syn}\n  var:{var}\n  var_text:{var_text}\n  var_phon:{phon}"


def _show_result(hw: DpdHeadword) -> None:
    print()
    print(f"[green]{hw.lemma_1}:")
    print(f"[green]{_format_fields(hw)}")


def _assign(hw: DpdHeadword, other: str, target: str) -> None:
    """Add `other` to `target` field, enforcing exclusivity rules:
    - s and p are mutually exclusive
    - s and t can coexist
    - variant is a legacy catch-all: modified surgically, never recomputed wholesale
    """
    syn = _split_field(hw.synonym)
    var = _split_field(hw.variant)
    var_phon = _split_field(hw.var_phonetic)
    var_text = _split_field(hw.var_text)

    if target == "synonym":
        syn.add(other)
        var_phon.discard(other)
        # s and t can coexist — do not touch var_text
        # only remove from variant if other is no longer in either var_ field
        if other not in var_text and other not in var_phon:
            var.discard(other)

    elif target == "var_phonetic":
        var_phon.add(other)
        var.add(other)
        syn.discard(other)  # s and p are mutually exclusive
        # do not touch var_text

    elif target == "var_text":
        var_text.add(other)
        var.add(other)
        # s and t can coexist — do not touch synonym or var_phon

    elif target == "delete":
        syn.discard(other)
        # leave var, var_phon, var_text untouched

    hw.synonym = ", ".join(pali_list_sorter(syn))
    hw.variant = ", ".join(pali_list_sorter(var))
    hw.var_phonetic = ", ".join(pali_list_sorter(var_phon))
    hw.var_text = ", ".join(pali_list_sorter(var_text))


def prompt_pairs(g: GlobalVars) -> bool:
    """Walk through pairs and prompt the user. Returns True if restart requested."""
    pr.green("adding synonyms to db")

    total = len(g.pairs)

    for counter, (hw_a, hw_b, shared) in enumerate(g.pairs):
        pos = hw_a.pos
        gen_key = _general_key(pos, shared)
        if gen_key in g.exceptions:
            continue

        print("\n" + "-" * 100)
        print("[white][dim]synonym: different construction.")
        print("[white][dim]phonetic: same construction, different spelling.")
        print("[white][dim]textual: manuscript variant.")
        print("-" * 100 + "\n")
        shared_label = " | ".join(shared)
        print(f"[white]{counter + 1} / {total}  [green]{shared_label}")
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        print(_entry_label(hw_b))
        print(f"[cyan]{_format_fields(hw_b)}")

        sig = grammar_signature(hw_a.grammar)
        key = _pair_key(pos, hw_a, hw_b, sig)

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
    print("[bright_yellow]synonym multi — finding and adding multi-meaning synonyms")
    while True:
        g = GlobalVars()
        find_multi_meaning_pairs(g)
        if not prompt_pairs(g):
            break
    pr.toc()


if __name__ == "__main__":
    main()
