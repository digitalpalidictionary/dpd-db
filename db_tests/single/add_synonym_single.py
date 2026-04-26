#!/usr/bin/env python3
"""Suggest synonyms for words that share the same single cleaned meaning."""

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
        self.groups: dict[str, list[DpdHeadword]] = {}

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
    """Remove commentary meaning and all bracketed content from a meaning string."""
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


def existing_synonyms(hw: DpdHeadword) -> set[str]:
    return set(hw.synonym_list)


def existing_phonetic_variants(hw: DpdHeadword) -> set[str]:
    return _split_field(hw.var_phonetic)


def find_single_meaning_groups(g: GlobalVars) -> None:
    """Build groups of headwords that share the same pos and single cleaned meaning."""
    pr.green_tmr("finding single meaning groups")

    raw: dict[str, list[DpdHeadword]] = {}

    for hw in g.dpd_db:
        if not hw.meaning_1:
            continue
        cleaned = clean_meaning(hw.meaning_1)
        if not cleaned or "; " in cleaned:
            continue
        sig = grammar_signature(hw.grammar)
        key = f"{hw.pos}:{cleaned}:{sig}"
        if key in g.exceptions:
            continue
        raw.setdefault(key, []).append(hw)

    g.groups = {k: v for k, v in raw.items() if len(v) >= 2}
    pr.yes(str(len(g.groups)))


def _format_fields(hw: DpdHeadword) -> str:
    syn = hw.synonym.split(", ") if hw.synonym else []
    var = hw.variant.split(", ") if hw.variant else []
    var_text = hw.var_text.split(", ") if hw.var_text else []
    phon = sorted(_split_field(hw.var_phonetic))
    return f"syn:{syn}  var:{var}  var_text:{var_text}  var_phon:{phon}"


def _show_result(hw: DpdHeadword, color: str) -> None:
    print(f"  [{color}]{hw.lemma_1}:  {_format_fields(hw)}")


def prompt_groups(g: GlobalVars) -> bool:
    """Walk through groups and prompt the user. Returns True if restart requested."""
    pr.green("adding synonyms to db")

    groups_list = list(g.groups.items())
    total = len(groups_list)

    for counter, (key, headwords) in enumerate(groups_list):
        lemma_cleans = [hw.lemma_clean for hw in headwords]
        all_lemma_cleans = set(lemma_cleans)

        syn_candidates: dict[int, set[str]] = {}
        variant_candidates: dict[int, set[str]] = {}
        phonetic_candidates: dict[int, set[str]] = {}
        for hw in headwords:
            others = all_lemma_cleans - {hw.lemma_clean}
            already_syn = existing_synonyms(hw)
            syn_candidates[hw.id] = (
                others
                - already_syn
                - existing_phonetic_variants(hw)
                - set(hw.variant_list)
            )
            all_variants = (
                set(hw.variant_list)
                | _split_field(hw.var_text)
                | _split_field(hw.var_phonetic)
            )
            variant_candidates[hw.id] = others - all_variants - already_syn
            phonetic_candidates[hw.id] = others - all_variants - already_syn

        has_syn = any(c for c in syn_candidates.values())
        has_var = any(c for c in variant_candidates.values()) or any(
            c for c in phonetic_candidates.values()
        )
        if not has_syn and not has_var:
            continue

        pos, meaning, sig = key.split(":", 2)
        sig_label = f"  [dim]{sig}" if sig else ""
        print(f"\n[white]{counter + 1} / {total}  [green]{meaning}{sig_label}")
        for hw in headwords:
            print(
                f"  [yellow]{hw.lemma_1:<22}[blue]{hw.pos:<10}"
                f"[green]{hw.meaning_1:<35}  "
                f"[cyan]{_format_fields(hw)}"
            )

        gui_string = db_search_string([hw.lemma_1 for hw in headwords], gui=True)
        pyperclip.copy(gui_string)
        print(f"  [white]{gui_string}")
        print(
            "[dim]  synonyms: different construction  |  phonetic variants: same construction"
        )
        choice = Prompt.ask(
            "[white](s)ynonym, (v)ariant, (e)xception, (p)ass, (r)estart, (q)uit"
        )

        if choice == "s":
            for hw in headwords:
                moving = syn_candidates[hw.id]
                new_syns = pali_list_sorter(set(hw.synonym_list) | moving)
                hw.synonym = ", ".join(new_syns)
                new_vars = pali_list_sorter(set(hw.variant_list) - moving)
                hw.variant = ", ".join(new_vars)
                new_phon = pali_list_sorter(_split_field(hw.var_phonetic) - moving)
                hw.var_phonetic = ", ".join(new_phon)
                _show_result(hw, "cyan")
            g.db_session.commit()

        elif choice == "v":
            for hw in headwords:
                moving = variant_candidates[hw.id] | phonetic_candidates[hw.id]
                new_syns = pali_list_sorter(set(hw.synonym_list) - moving)
                hw.synonym = ", ".join(new_syns)
                new_vars = pali_list_sorter(
                    set(hw.variant_list) | variant_candidates[hw.id]
                )
                hw.variant = ", ".join(new_vars)
                new_phon = pali_list_sorter(
                    _split_field(hw.var_phonetic) | phonetic_candidates[hw.id]
                )
                hw.var_phonetic = ", ".join(new_phon)
                _show_result(hw, "violet")
            g.db_session.commit()

        elif choice == "e":
            g.add_exception(key)
            print(f"  [red]exception added: {key!r}")

        elif choice == "p":
            continue

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
        find_single_meaning_groups(g)
        if not prompt_groups(g):
            break
    pr.toc()


if __name__ == "__main__":
    main()
