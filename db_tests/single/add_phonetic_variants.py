#!/usr/bin/env python3
"""Find and add phonetic variant pairs to the DPD database.

Walk candidate pairs detected by four rules:
1. same construction_clean + pos, different lemma_clean
2. bidirectional phonetic substitution rules on lemma_clean
3. same construction_clean, base differs by e/aya (or *e/*aya) at one slot
4. same construction_clean, base differs by iya/īya at one slot

Prompt: (p)honetic, (e)xception, [enter] pass, (r)estart, (q)uit.
Exceptions are stored in add_phonetic_variants.json (same directory).
"""

import json

import pyperclip
from rich import print
from rich.prompt import Prompt
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.synonym_variant import (
    Pair,
    PhoneticVariantDetector,
    assign_relationship,
    exception_key,
    split_field,
)


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.exceptions: list[str] = self._load_exceptions()
        self.pairs: list[Pair] = []

    def _load_exceptions(self) -> list[str]:
        try:
            with open(self.pth.add_phonetic_variants_exceptions_path) as f:
                exceptions: list[str] = json.load(f)
                return list(dict.fromkeys(exceptions))
        except FileNotFoundError:
            return []

    def _save_exceptions(self) -> None:
        with open(self.pth.add_phonetic_variants_exceptions_path, "w") as f:
            json.dump(self.exceptions, f, ensure_ascii=False, indent=2)

    def add_exception(self, key: str) -> None:
        if key not in self.exceptions:
            self.exceptions.append(key)
            self._save_exceptions()


def find_pairs(g: GlobalVars) -> None:
    pr.green_tmr("finding phonetic variant pairs")
    detector = PhoneticVariantDetector(g.dpd_db)
    g.pairs = detector.detect_canonical_pairs(g.exceptions)
    pr.yes(str(len(g.pairs)))


def _format_fields(hw: DpdHeadword) -> str:
    syn = hw.synonym.split(", ") if hw.synonym else []
    var = hw.variant.split(", ") if hw.variant else []
    var_text = hw.var_text.split(", ") if hw.var_text else []
    phon = sorted(split_field(hw.var_phonetic))
    return f"  syn:{syn}\n  var:{var}\n  var_text:{var_text}\n  var_phon:{phon}"


def _show_result(hw: DpdHeadword) -> None:
    print()
    print(f"[green]{hw.lemma_1}:")
    print(f"[green]{_format_fields(hw)}")


def _entry_label(hw: DpdHeadword) -> str:
    family_root = f" [magenta]{hw.family_root}" if hw.family_root else ""
    root_meaning = (
        f" [magenta]{hw.rt.root_meaning}" if hw.rt and hw.rt.root_meaning else ""
    )
    return (
        f"[yellow]{hw.lemma_1} [blue]{hw.pos} "
        f"[green]{hw.meaning_combo} [white]({hw.degree_of_completion})"
        f"{family_root}"
        f"{root_meaning}"
    )


def _pair_has_meaning_1(pair: Pair) -> bool:
    return bool(pair.source.meaning_1 or pair.target.meaning_1)


def prompt_pairs(g: GlobalVars) -> bool:
    """Walk pairs and prompt the user. Returns True if restart requested."""
    pr.green("reviewing phonetic variant pairs")
    total_pairs = len(g.pairs)
    total_meaning_1_pairs = sum(1 for pair in g.pairs if _pair_has_meaning_1(pair))
    print(
        "[dim]synonym: different construction.  phonetic: same construction, different spelling.  textual: manuscript variant."
    )

    for counter, pair in enumerate(g.pairs):
        hw_a = pair.source
        hw_b = pair.target

        print("\n" + "-" * 70 + "\n")
        print(
            f"[white]{counter + 1} / {total_meaning_1_pairs} / {total_pairs}  [cyan]{pair.rule}"
        )
        print(_entry_label(hw_a))
        print(f"[cyan]{_format_fields(hw_a)}")
        print(_entry_label(hw_b))
        print(f"[cyan]{_format_fields(hw_b)}")

        gui_string = db_search_string([hw_a.lemma_1, hw_b.lemma_1], gui=True)
        pyperclip.copy(gui_string)
        print(f"\n[white]{gui_string}")

        choice = Prompt.ask(
            "[white](s)ynonym, (p)honetic, (t)extual, (e)xception, (pass), (r)estart, (q)uit",
            default="",
        )

        if choice == "s":
            assign_relationship(hw_a, hw_b.lemma_clean, "synonym")
            assign_relationship(hw_b, hw_a.lemma_clean, "synonym")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "p":
            assign_relationship(hw_a, hw_b.lemma_clean, "var_phonetic")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_phonetic")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "t":
            assign_relationship(hw_a, hw_b.lemma_clean, "var_text")
            assign_relationship(hw_b, hw_a.lemma_clean, "var_text")
            _show_result(hw_a)
            _show_result(hw_b)
            g.db_session.commit()

        elif choice == "e":
            exc_key = exception_key(hw_a, hw_b)
            g.add_exception(exc_key)
            print(f"  [red]exception added: {exc_key!r}")

        elif choice == "r":
            return True

        elif choice == "q":
            break

    return False


def main() -> None:
    pr.tic()
    print("[bright_yellow]add phonetic variants — find and add phonetic variant pairs")
    while True:
        g = GlobalVars()
        find_pairs(g)
        if not prompt_pairs(g):
            break
    pr.toc()


if __name__ == "__main__":
    main()
