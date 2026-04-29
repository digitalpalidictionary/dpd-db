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
from dataclasses import dataclass
from typing import Sequence

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

ACTIVE_DETECTORS: dict[str, bool] = {
    "same_construction": True,
    "by_rules": True,
    "base_e_aya": True,
    "base_ya_iya_iiya": True,
}

PHONETIC_RULES: list[tuple[str, str, bool]] = [
    # vowels
    ("a", "ā", True),
    ("a", "u", True),
    ("i", "ī", True),
    ("i", "u", True),
    ("ī", "e", True),
    ("u", "ū", True),
    ("e", "aya", True),
    ("o", "ava", True),
    # consonants
    ("t", "ṭ", True),
    ("d", "ḍ", True),
    ("n", "ṇ", True),
    ("n", "ṅ", True),
    ("n", "ñ", True),
    ("r", "t", True),
    ("r", "d", True),
    ("l", "ḷ", True),
    ("v", "b", True),
    # nasals
    ("ṃ", "ṅ", True),
    ("ṃ", "n", True),
    ("ṃ", "ṇ", True),
    ("ṃ", "m", True),
    ("ṃ", "ñ", True),
    # doubles
    ("iya", "eyya", True),
    ("īya", "eyya", True),
    ("ūl", "ull", True),
    ("ūḷ", "ull", True),
    ("ika", "aka", True),
    ("ika", "iya", True),
    ("ikā", "iyā", True),
    ("kk", "k", True),
    ("kk", "g", True),
    ("gg", "g", True),
    ("jj", "j", True),
    ("cc", "c", True),
    ("ṭṭ", "ṭ", True),
    ("ṭ", "ḍ", True),
    ("ṭ", "t", True),
    ("ḍḍ", "ḍ", True),
    ("t", "d", True),
    ("tt", "t", True),
    ("dd", "d", True),
    ("nh", "h", True),
    ("ny", "ññ", True),
    ("dy", "jj", True),
    ("ty", "cc", True),
    ("ṃy", "ññ", True),
    ("nah", "nh", True),
    ("nāh", "nh", True),
    ("vi", "vy", True),
    ("ll", "l", True),
    ("ss", "s", True),
    # delete
    ("h", "", True),
    ("y", "", True),
    ("v", "", True),
]


@dataclass
class Pair:
    rule: str
    source: DpdHeadword
    target: DpdHeadword


def _exception_key(hw_a: DpdHeadword, hw_b: DpdHeadword) -> str:
    pairs = sorted(
        [
            f"{_headword_identity(hw_a)}:{hw_a.pos}",
            f"{_headword_identity(hw_b)}:{hw_b.pos}",
        ]
    )
    return f"{pairs[0]}|{pairs[1]}"


def _split_field(value: str) -> set[str]:
    return {t.strip() for t in value.split(",") if t.strip()}


def _already_related(a: DpdHeadword, b: DpdHeadword) -> bool:
    a_clean = a.lemma_clean
    b_clean = b.lemma_clean
    a_phon = _split_field(a.var_phonetic)
    b_phon = _split_field(b.var_phonetic)
    return b_clean in a_phon and a_clean in b_phon


def _already_recorded_single(hw: DpdHeadword, other_clean: str) -> bool:
    return other_clean in _split_field(hw.var_phonetic)


_FREQ_KEYS = ("CstFreq", "BjtFreq", "SyaFreq", "ScFreq")


def _has_textual_occurrence(hw: DpdHeadword) -> bool:
    if hw.meaning_1:
        return True
    freq = hw.freq_data_unpack
    return any(
        v > 0
        for key in _FREQ_KEYS
        if isinstance(val := freq.get(key), list)
        for v in val
    )


def _same_family_if_present(value_a: str, value_b: str) -> bool:
    if not value_a and not value_b:
        return True
    return bool(value_a and value_b and value_a == value_b)


def _same_families_if_present(a: DpdHeadword, b: DpdHeadword) -> bool:
    return (
        _same_family_if_present(a.root_key, b.root_key)
        and _same_family_if_present(a.family_root, b.family_root)
        and _same_family_if_present(a.family_word, b.family_word)
    )


def _headword_identity(hw: DpdHeadword) -> str:
    hw_id = getattr(hw, "id", None)
    if hw_id is not None:
        return str(hw_id)
    return hw.lemma_1


class PhoneticVariantDetector:
    def __init__(self, headwords: Sequence[DpdHeadword]) -> None:
        self._headwords: list[DpdHeadword] = list(headwords)
        self._by_lemma_1: dict[str, DpdHeadword] = {}
        self._by_lemma_clean: dict[str, list[DpdHeadword]] = {}
        self._by_construction_pos: dict[tuple[str, str], list[DpdHeadword]] = {}
        self._by_root_family_pos: dict[tuple[str, str, str], list[DpdHeadword]] = {}

        for hw in self._headwords:
            self._by_lemma_1[hw.lemma_1] = hw
            self._by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)
            key = (hw.construction_clean, hw.pos)
            self._by_construction_pos.setdefault(key, []).append(hw)
            if hw.root_key and hw.family_root:
                rkey = (hw.root_key, hw.family_root, hw.pos)
                self._by_root_family_pos.setdefault(rkey, []).append(hw)

    def detect_same_construction(self) -> list[tuple[DpdHeadword, str, str]]:
        """Same construction_clean + pos, different lemma_clean."""
        results: list[tuple[DpdHeadword, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for (construction_clean, _pos), group in self._by_construction_pos.items():
            if not construction_clean:
                continue
            if len({hw.lemma_clean for hw in group}) < 2:
                continue
            for a in group:
                if not a.meaning_1:
                    continue
                for b in group:
                    if a is b or a.lemma_clean == b.lemma_clean:
                        continue
                    if not b.meaning_1:
                        continue
                    if _already_recorded_single(a, b.lemma_clean):
                        continue
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "same_construction"))
        return results

    def detect_by_rules(self) -> list[tuple[DpdHeadword, str, str]]:
        """Bidirectional phonetic substitution rules on lemma_clean."""
        results: list[tuple[DpdHeadword, str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for hw in self._headwords:
            if not hw.lemma_clean:
                continue
            for x, y, enabled in PHONETIC_RULES:
                if not enabled:
                    continue
                rule_tag = f"rule:{x}<->{y}"
                for produced in self._apply_rule(hw.lemma_clean, x, y):
                    if produced == hw.lemma_clean:
                        continue
                    if produced not in self._by_lemma_clean:
                        continue
                    if _already_recorded_single(hw, produced):
                        continue
                    key = (hw.lemma_1, produced, rule_tag)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((hw, produced, rule_tag))
        return results

    @staticmethod
    def _apply_rule(lemma_clean: str, x: str, y: str) -> list[str]:
        produced: list[str] = []
        if x and x in lemma_clean:
            produced.append(lemma_clean.replace(x, y))
        if y and y in lemma_clean:
            produced.append(lemma_clean.replace(y, x))
        return produced

    def detect_base_e_aya(self) -> list[tuple[DpdHeadword, str, str]]:
        """Same root_key + family_root + pos; root_sign differs *e ↔ *aya; same suffixes."""
        results: list[tuple[DpdHeadword, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for group in self._by_root_family_pos.values():
            if len(group) < 2:
                continue
            for a in group:
                if a.root_sign not in {"*e", "*aya"}:
                    continue
                if not a.meaning_1:
                    continue
                for b in group:
                    if a is b or a.lemma_clean == b.lemma_clean:
                        continue
                    if b.root_sign not in {"*e", "*aya"}:
                        continue
                    if a.root_sign == b.root_sign:
                        continue
                    if not b.meaning_1:
                        continue
                    a_stripped = _construction_without_base(a)
                    b_stripped = _construction_without_base(b)
                    if a_stripped is None or a_stripped != b_stripped:
                        continue
                    if _already_recorded_single(a, b.lemma_clean):
                        continue
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "base:e<->aya"))
        return results

    def detect_base_ya_iya_iiya(self) -> list[tuple[DpdHeadword, str, str]]:
        """Same root_key + family_root + pos; root_sign differs ya ↔ iya ↔ īya; same suffixes."""
        results: list[tuple[DpdHeadword, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for group in self._by_root_family_pos.values():
            if len(group) < 2:
                continue
            for a in group:
                if a.root_sign not in {"ya", "iya", "īya"}:
                    continue
                if not a.meaning_1:
                    continue
                for b in group:
                    if a is b or a.lemma_clean == b.lemma_clean:
                        continue
                    if b.root_sign not in {"ya", "iya", "īya"}:
                        continue
                    if a.root_sign == b.root_sign:
                        continue
                    if not b.meaning_1:
                        continue
                    a_stripped = _construction_without_base(a)
                    b_stripped = _construction_without_base(b)
                    if a_stripped is None or a_stripped != b_stripped:
                        continue
                    if _already_recorded_single(a, b.lemma_clean):
                        continue
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "base:ya<->iya<->īya"))
        return results

    def detect_all_raw(self) -> list[tuple[DpdHeadword, str, str]]:
        results: list[tuple[DpdHeadword, str, str]] = []
        if ACTIVE_DETECTORS["same_construction"]:
            results.extend(self.detect_same_construction())
        if ACTIVE_DETECTORS["by_rules"]:
            results.extend(self.detect_by_rules())
        if ACTIVE_DETECTORS["base_e_aya"]:
            results.extend(self.detect_base_e_aya())
        if ACTIVE_DETECTORS["base_ya_iya_iiya"]:
            results.extend(self.detect_base_ya_iya_iiya())
        return results

    def detect_canonical_pairs(self, exceptions: list[str]) -> list[Pair]:
        """Collapse symmetric duplicates, filter already-related and excepted pairs."""
        raw = self.detect_all_raw()
        seen: set[tuple[str, str, str]] = set()
        pairs: list[Pair] = []

        for source_hw, candidate_clean, rule in raw:
            targets = self._by_lemma_clean.get(candidate_clean, [])
            if not targets:
                continue
            for target_hw in targets:
                if source_hw.pos != target_hw.pos:
                    continue
                if not _has_textual_occurrence(source_hw):
                    continue
                if not _has_textual_occurrence(target_hw):
                    continue
                if rule == "same_construction" and not (
                    source_hw.meaning_1 and target_hw.meaning_1
                ):
                    continue
                if not _same_families_if_present(source_hw, target_hw):
                    continue
                source_id = _headword_identity(source_hw)
                target_id = _headword_identity(target_hw)
                source_pair = f"{source_id}:{source_hw.pos}"
                target_pair = f"{target_id}:{target_hw.pos}"
                pair_key = (
                    rule,
                    min(source_pair, target_pair),
                    max(source_pair, target_pair),
                )
                if pair_key in seen:
                    continue
                exc_key = _exception_key(source_hw, target_hw)
                if exc_key in exceptions:
                    continue
                if _already_related(source_hw, target_hw):
                    continue
                seen.add(pair_key)
                pairs.append(Pair(rule=rule, source=source_hw, target=target_hw))

        pairs.sort(key=_pair_sort_key)
        return pairs


_SUFFIX_NORM: dict[str, str] = {
    "itvā": "tvā",
    "itvāna": "tvāna",
}


def _construction_without_base(hw: DpdHeadword) -> str | None:
    """Strip the base form from construction_clean, leaving prefixes + suffixes.

    Returns None if construction_clean or root_base_clean is missing.
    Normalises equivalent suffix pairs (itvā/tvāna→tvā, si→i).
    """
    if not hw.construction_clean or not hw.root_base_clean:
        return None
    rbc = hw.root_base_clean
    if ">" not in rbc:
        return None
    base = rbc.split(">")[1].strip().split()[0]
    parts = hw.construction_clean.split(" + ")
    if base in parts:
        parts.remove(base)
    parts = [_SUFFIX_NORM.get(p, p) for p in parts]
    return " + ".join(parts)


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
    phon = sorted(_split_field(hw.var_phonetic))
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


def _assign(hw: DpdHeadword, other: str, target: str) -> None:
    """Match add_synonym_variant_multi.py assignment semantics."""
    syn = _split_field(hw.synonym)
    var = _split_field(hw.variant)
    var_phon = _split_field(hw.var_phonetic)
    var_text = _split_field(hw.var_text)

    if target == "synonym":
        syn.add(other)
        var_phon.discard(other)
        if other not in var_text and other not in var_phon:
            var.discard(other)

    elif target == "var_phonetic":
        var_phon.add(other)
        var.add(other)
        syn.discard(other)

    elif target == "var_text":
        var_text.add(other)
        var.add(other)

    elif target == "delete":
        syn.discard(other)

    hw.synonym = ", ".join(pali_list_sorter(syn))
    hw.variant = ", ".join(pali_list_sorter(var))
    hw.var_phonetic = ", ".join(pali_list_sorter(var_phon))
    hw.var_text = ", ".join(pali_list_sorter(var_text))


def _pair_has_meaning_1(pair: Pair) -> bool:
    return bool(pair.source.meaning_1 or pair.target.meaning_1)


_RULE_PRIORITY: dict[str, int] = {
    "base:e<->aya": 0,
    "base:ya<->iya<->īya": 0,
}


def _pair_sort_key(pair: Pair) -> tuple[int, int, str, str, str]:
    return (
        _RULE_PRIORITY.get(pair.rule, 1),
        0 if _pair_has_meaning_1(pair) else 1,
        pair.rule,
        pair.source.lemma_1,
        pair.target.lemma_1,
    )


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
            exc_key = _exception_key(hw_a, hw_b)
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
