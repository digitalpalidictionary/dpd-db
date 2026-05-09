"""Shared synonym & phonetic-variant detection logic.

Used by:
- db_tests/single/add_synonym_variant_multi.py
- db_tests/single/add_synonym_variant_single.py
- db_tests/single/add_phonetic_variants.py
- gui2 (via DatabaseManager.get_relationship_detector())

Owns all the rule definitions, exclusivity logic, and per-headword
candidate detectors. Callers do their own UX (CLI prompts, GUI fields).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter

# ---------------------------------------------------------------------------
# phonetic substitution rules (from add_phonetic_variants.py)
# ---------------------------------------------------------------------------

PHONETIC_RULES: list[tuple[str, str, bool]] = [
    # vowels
    ("a", "ā", True),
    ("a", "u", True),
    ("i", "ī", True),
    ("i", "u", True),
    ("ī", "e", True),
    ("u", "ū", True),
    ("u", "o", True),
    ("e", "aya", True),
    ("o", "ava", True),
    # consonants
    ("ṭ", "ḍ", True),
    ("t", "d", True),
    ("t", "ṭ", True),
    ("d", "ḍ", True),
    ("n", "ṇ", True),
    ("n", "ṅ", True),
    ("n", "ñ", True),
    ("p", "b", True),
    ("r", "t", True),
    ("r", "d", True),
    ("l", "ḷ", True),
    ("l", "y", True),
    ("v", "b", True),
    # nasals
    ("ṃ", "ṅ", True),
    ("ṃ", "n", True),
    ("ṃ", "ṇ", True),
    ("ṃ", "m", True),
    ("ṃ", "ñ", True),
    # doubles
    # iī
    ("ika", "aka", True),
    ("ika", "iya", True),
    ("ikā", "iyā", True),
    ("iya", "ya", True),
    ("iya", "eyya", True),
    ("īya", "ya", True),
    ("īya", "eyya", True),
    # uū
    ("ūl", "ull", True),
    ("ūḷ", "ull", True),
    # k kh g gh ṅ
    ("kk", "k", True),
    ("kk", "g", True),
    ("gg", "g", True),
    # c ch j jh ñ
    ("cc", "c", True),
    ("cch", "ñch", True),
    ("jj", "j", True),
    # ṭ ṭḥ ḍ ḍh ṇ
    ("ṭṭ", "ṭ", True),
    ("ṭhā", "ṭhaha", True),
    ("ḍḍ", "ḍ", True),
    ("ḍḍh", "ddh", True),
    ("ṇṭ", "nt", True),
    ("ṇṭ", "nd", True),
    # t th d dh n
    ("tt", "t", True),
    ("ty", "cc", True),
    ("dd", "d", True),
    ("dy", "jj", True),
    ("nah", "nh", True),
    ("nāh", "nh", True),
    ("ny", "ññ", True),
    ("nh", "h", True),
    # p ph b bh m
    ("pp", "p", True),
    ("bb", "b", True),
    # y r l s v h ṃ
    ("ṃy", "ññ", True),
    ("vi", "vy", True),
    ("ll", "l", True),
    ("ss", "s", True),
    # delete
    ("h", "", True),
    ("y", "", True),
    ("v", "", True),
]

_SUFFIX_NORM: dict[str, str] = {
    "itvā": "tvā",
    "itvāna": "tvāna",
}

# ---------------------------------------------------------------------------
# meaning + grammar normalisation
# ---------------------------------------------------------------------------

_CASE_PERSON = re.compile(r"\b(nom|acc|instr|dat|abl|gen|loc|voc|1st|2nd|3rd)\b")
_GENDER = re.compile(r"\b(masc|fem|nt)\b")


def clean_meaning(text: str) -> str:
    """Strip `(comm)…$` tail and bracketed content from a meaning string."""
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


NOUN_GENDERS: frozenset[str] = frozenset({"masc", "fem", "nt"})
TILINGA_POS: frozenset[str] = frozenset({"adj", "pp", "ptp", "prp"})
_PHONETIC_MASC_NT: frozenset[str] = frozenset({"masc", "nt"})


def phonetic_pos_class(pos: str) -> str:
    """Group pos values for phonetic-variant matching.

    masc and nt are treated as equivalent — the same word often appears in
    both genders with identical meaning and spelling variants.
    fem stays distinct (different stem endings, genuinely different words).
    All other pos values stay exact.
    """
    if pos in _PHONETIC_MASC_NT:
        return "noun_mn"
    return pos


def pos_class(pos: str) -> str:
    """Group pos values that the classical grammars treat as one class.

    - {masc, fem, nt} → "noun": Pāḷi derives semantically identical abstract
      nouns across genders (-tā fem, -tta nt, -bhāva masc).
    - {adj, pp, ptp, prp} → "tiliṅga": all are declinable in three genders
      (tiliṅga in classical grammar) and can overlap in meaning across
      formations (e.g. pp `mata` ↔ adj `kālakata`).

    All other pos values (aor, ind, pron, sandhi, ...) stay distinct.
    Phonetic-variant matching deliberately does NOT use this — variants
    are spellings of the same word and should preserve pos.
    """
    if pos in NOUN_GENDERS:
        return "noun"
    if pos in TILINGA_POS:
        return "tiliṅga"
    return pos


def split_field(value: str | None) -> set[str]:
    """CSV string → set of stripped non-empty tokens."""
    if not value:
        return set()
    return {t.strip() for t in value.split(",") if t.strip()}


# ---------------------------------------------------------------------------
# exclusivity logic for syn/var/var_phonetic/var_text
# ---------------------------------------------------------------------------


def assign_relationship(hw: DpdHeadword, other: str, target: str) -> None:
    """Assign `other` to `target` field on `hw`, enforcing exclusivity rules:
    - synonym, var_phonetic, var_text are mutually exclusive — a word can
      belong to at most one of the three
    - assigning to any of the three also drops the word from `variant`
    """
    syn = split_field(hw.synonym)
    var = split_field(hw.variant)
    var_phon = split_field(hw.var_phonetic)
    var_text = split_field(hw.var_text)

    if target == "synonym":
        syn.add(other)
        var_phon.discard(other)
        var_text.discard(other)
        var.discard(other)

    elif target == "var_phonetic":
        var_phon.add(other)
        syn.discard(other)
        var_text.discard(other)
        var.discard(other)

    elif target == "var_text":
        var_text.add(other)
        syn.discard(other)
        var_phon.discard(other)
        var.discard(other)

    elif target == "delete":
        syn.discard(other)
        var.discard(other)
        var_phon.discard(other)
        var_text.discard(other)

    else:
        raise ValueError(f"unknown target: {target!r}")

    hw.synonym = ", ".join(pali_list_sorter(syn))
    hw.variant = ", ".join(pali_list_sorter(var))
    hw.var_phonetic = ", ".join(pali_list_sorter(var_phon))
    hw.var_text = ", ".join(pali_list_sorter(var_text))


def assign_relationship_dict(
    fields: dict[str, str], other: str, target: str
) -> dict[str, str]:
    """Same exclusivity rules but operating on a dict of string fields.
    Returns a new dict with updated synonym/variant/var_phonetic/var_text.
    Used by the GUI where we don't have an ORM row in hand.
    """
    syn = split_field(fields.get("synonym"))
    var = split_field(fields.get("variant"))
    var_phon = split_field(fields.get("var_phonetic"))
    var_text = split_field(fields.get("var_text"))

    if target == "synonym":
        syn.add(other)
        var_phon.discard(other)
        var_text.discard(other)
        var.discard(other)

    elif target == "var_phonetic":
        var_phon.add(other)
        syn.discard(other)
        var_text.discard(other)
        var.discard(other)

    elif target == "var_text":
        var_text.add(other)
        syn.discard(other)
        var_phon.discard(other)
        var.discard(other)

    elif target == "delete":
        syn.discard(other)
        var.discard(other)
        var_phon.discard(other)
        var_text.discard(other)

    else:
        raise ValueError(f"unknown target: {target!r}")

    return {
        "synonym": ", ".join(pali_list_sorter(syn)),
        "variant": ", ".join(pali_list_sorter(var)),
        "var_phonetic": ", ".join(pali_list_sorter(var_phon)),
        "var_text": ", ".join(pali_list_sorter(var_text)),
    }


# ---------------------------------------------------------------------------
# already-related checks
# ---------------------------------------------------------------------------


def pair_consistently_related(a: DpdHeadword, b: DpdHeadword) -> bool:
    """A pair counts as 'already done' only when both rows reference each
    other via the SAME field (synonym, var_phonetic, or var_text). Mixed
    states — e.g. a says syn, b says phon — are inconsistent and should
    surface so the user can pick the right field.
    """
    a_clean = a.lemma_clean
    b_clean = b.lemma_clean
    if b_clean in split_field(a.synonym) and a_clean in split_field(b.synonym):
        return True
    if b_clean in split_field(a.var_phonetic) and a_clean in split_field(
        b.var_phonetic
    ):
        return True
    if b_clean in split_field(a.var_text) and a_clean in split_field(b.var_text):
        return True
    return False


def pair_consistently_related_sets(
    a: DpdHeadword,
    b: DpdHeadword,
    syn_sets: dict[int, set[str]],
    phon_sets: dict[int, set[str]],
    text_sets: dict[int, set[str]],
) -> bool:
    """Same as `pair_consistently_related`, using pre-split sets keyed by id."""
    a_clean = a.lemma_clean
    b_clean = b.lemma_clean
    if b_clean in syn_sets[a.id] and a_clean in syn_sets[b.id]:
        return True
    if b_clean in phon_sets[a.id] and a_clean in phon_sets[b.id]:
        return True
    if b_clean in text_sets[a.id] and a_clean in text_sets[b.id]:
        return True
    return False


def construction_without_base(hw: DpdHeadword) -> str | None:
    """Strip the base form from construction_clean, leaving prefixes + suffixes.

    Returns None if construction_clean or root_base_clean is missing.
    Normalises equivalent suffix pairs (itvā→tvā, itvāna→tvāna).
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


_FREQ_KEYS = ("CstFreq", "BjtFreq", "SyaFreq", "ScFreq")


def has_textual_occurrence(hw: DpdHeadword) -> bool:
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


def same_families_if_present(a: DpdHeadword, b: DpdHeadword) -> bool:
    return (
        _same_family_if_present(a.root_key, b.root_key)
        and _same_family_if_present(a.family_root, b.family_root)
        and _same_family_if_present(a.family_word, b.family_word)
    )


def headword_identity(hw: DpdHeadword) -> str:
    hw_id = getattr(hw, "id", None)
    if hw_id is not None:
        return str(hw_id)
    return hw.lemma_1


def exception_key(hw_a: DpdHeadword, hw_b: DpdHeadword) -> str:
    pairs = sorted(
        [
            f"{headword_identity(hw_a)}:{hw_a.pos}",
            f"{headword_identity(hw_b)}:{hw_b.pos}",
        ]
    )
    return f"{pairs[0]}|{pairs[1]}"


# ---------------------------------------------------------------------------
# Phonetic variant detector (kept as in the offline script)
# ---------------------------------------------------------------------------


@dataclass
class Pair:
    rule: str
    source: DpdHeadword
    target: DpdHeadword


ACTIVE_DETECTORS: dict[str, bool] = {
    "same_construction": True,
    "by_rules": True,
    "base_e_aya": True,
    "base_ya_iya_iiya": True,
    "transitive": True,
}


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

    @property
    def by_lemma_clean(self) -> dict[str, list[DpdHeadword]]:
        return self._by_lemma_clean

    def detect_same_construction(self) -> list[tuple[DpdHeadword, str, str]]:
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
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "same_construction"))
        return results

    def detect_by_rules(self) -> list[tuple[DpdHeadword, str, str]]:
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
                    a_stripped = construction_without_base(a)
                    b_stripped = construction_without_base(b)
                    if a_stripped is None or a_stripped != b_stripped:
                        continue
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "base:e<->aya"))
        return results

    def detect_base_ya_iya_iiya(self) -> list[tuple[DpdHeadword, str, str]]:
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
                    a_stripped = construction_without_base(a)
                    b_stripped = construction_without_base(b)
                    if a_stripped is None or a_stripped != b_stripped:
                        continue
                    key = (a.lemma_1, b.lemma_clean)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((a, b.lemma_clean, "base:ya<->iya<->īya"))
        return results

    def detect_transitive(self) -> list[tuple[DpdHeadword, str, str]]:
        """Walk the existing bidirectional var_phon graph and propose
        transitive completions: when A↔B and B↔C are both bidirectional
        var_phon but A and C are not yet related, propose A↔C.

        Catches the multi-step substitution case (e.g. pāṇīya↔pāniya needs
        ṇ→n AND ī→i) that the per-rule detectors can't compose.
        """
        declared: dict[str, set[str]] = {}
        for hw in self._headwords:
            lc = hw.lemma_clean
            if not lc:
                continue
            phon_set = split_field(hw.var_phonetic)
            if phon_set:
                declared.setdefault(lc, set()).update(phon_set)

        bidir: dict[str, set[str]] = {}
        for lc, neighbors in declared.items():
            for n in neighbors:
                if lc in declared.get(n, set()):
                    bidir.setdefault(lc, set()).add(n)

        visited: set[str] = set()
        components: list[set[str]] = []
        for lc in bidir:
            if lc in visited:
                continue
            comp: set[str] = set()
            stack = [lc]
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                comp.add(cur)
                for n in bidir.get(cur, set()):
                    if n not in visited:
                        stack.append(n)
            if len(comp) >= 3:
                components.append(comp)

        results: list[tuple[DpdHeadword, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for comp in components:
            members = sorted(comp)
            for i, a_lc in enumerate(members):
                for b_lc in members[i + 1 :]:
                    if b_lc in bidir.get(a_lc, set()):
                        continue
                    for source_hw in self._by_lemma_clean.get(a_lc, []):
                        if not source_hw.meaning_1:
                            continue
                        key = (source_hw.lemma_1, b_lc)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append((source_hw, b_lc, "transitive"))
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
        if ACTIVE_DETECTORS["transitive"]:
            results.extend(self.detect_transitive())
        return results

    def detect_canonical_pairs(self, exceptions: list[str]) -> list[Pair]:
        raw = self.detect_all_raw()
        seen: set[tuple[str, str, str]] = set()
        pairs: list[Pair] = []

        for source_hw, candidate_clean, rule in raw:
            targets = self._by_lemma_clean.get(candidate_clean, [])
            if not targets:
                continue
            for target_hw in targets:
                if phonetic_pos_class(source_hw.pos) != phonetic_pos_class(
                    target_hw.pos
                ):
                    continue
                if not has_textual_occurrence(source_hw):
                    continue
                if not has_textual_occurrence(target_hw):
                    continue
                if not (source_hw.meaning_1 and target_hw.meaning_1):
                    continue
                if not same_families_if_present(source_hw, target_hw):
                    continue
                source_id = headword_identity(source_hw)
                target_id = headword_identity(target_hw)
                source_pair = f"{source_id}:{source_hw.pos}"
                target_pair = f"{target_id}:{target_hw.pos}"
                pair_key = (
                    rule,
                    min(source_pair, target_pair),
                    max(source_pair, target_pair),
                )
                if pair_key in seen:
                    continue
                exc_key = exception_key(source_hw, target_hw)
                if exc_key in exceptions:
                    continue
                if pair_consistently_related(source_hw, target_hw):
                    continue
                seen.add(pair_key)
                pairs.append(Pair(rule=rule, source=source_hw, target=target_hw))

        pairs.sort(key=_pair_sort_key)
        return pairs

    # --- per-headword query, used by gui2 ---

    def find_phonetic_variants_for(self, hw: DpdHeadword) -> list[tuple[str, str]]:
        """Return [(lemma_clean, rule_label), ...] phonetic candidates for `hw`,
        suppressing pairs that are already consistently related (same field
        both sides). Same-family check applied when families are present on
        both sides.
        """
        out: list[tuple[str, str]] = []
        seen_clean: set[str] = set()

        def _consider(candidate_clean: str, rule: str) -> None:
            if candidate_clean == hw.lemma_clean:
                return
            for target in self._by_lemma_clean.get(candidate_clean, []):
                if phonetic_pos_class(target.pos) != phonetic_pos_class(hw.pos):
                    continue
                if not has_textual_occurrence(target):
                    continue
                if not (hw.meaning_1 and target.meaning_1):
                    continue
                if not same_families_if_present(hw, target):
                    continue
                if pair_consistently_related(hw, target):
                    continue
                if candidate_clean in seen_clean:
                    return
                seen_clean.add(candidate_clean)
                out.append((candidate_clean, rule))
                return

        # rule 1: same construction_clean + pos
        if (
            ACTIVE_DETECTORS["same_construction"]
            and hw.construction_clean
            and hw.meaning_1
        ):
            group = self._by_construction_pos.get((hw.construction_clean, hw.pos), [])
            for other in group:
                if other.lemma_clean != hw.lemma_clean:
                    _consider(other.lemma_clean, "same_construction")

        # rule 2: phonetic substitution rules
        if ACTIVE_DETECTORS["by_rules"] and hw.lemma_clean:
            for x, y, enabled in PHONETIC_RULES:
                if not enabled:
                    continue
                rule_tag = f"rule:{x}<->{y}"
                for produced in self._apply_rule(hw.lemma_clean, x, y):
                    if produced and produced in self._by_lemma_clean:
                        _consider(produced, rule_tag)

        # rule 3 & 4: root_sign variants — only meaningful if hw has matching root_sign
        if hw.root_key and hw.family_root and hw.root_sign and hw.meaning_1:
            group = self._by_root_family_pos.get(
                (hw.root_key, hw.family_root, hw.pos), []
            )
            hw_stripped = construction_without_base(hw)
            if hw_stripped is not None:
                if ACTIVE_DETECTORS["base_e_aya"] and hw.root_sign in {"*e", "*aya"}:
                    for other in group:
                        if other.lemma_clean == hw.lemma_clean:
                            continue
                        if other.root_sign not in {"*e", "*aya"}:
                            continue
                        if other.root_sign == hw.root_sign:
                            continue
                        other_stripped = construction_without_base(other)
                        if other_stripped == hw_stripped:
                            _consider(other.lemma_clean, "base:e<->aya")

                if ACTIVE_DETECTORS["base_ya_iya_iiya"] and hw.root_sign in {
                    "ya",
                    "iya",
                    "īya",
                }:
                    for other in group:
                        if other.lemma_clean == hw.lemma_clean:
                            continue
                        if other.root_sign not in {"ya", "iya", "īya"}:
                            continue
                        if other.root_sign == hw.root_sign:
                            continue
                        other_stripped = construction_without_base(other)
                        if other_stripped == hw_stripped:
                            _consider(other.lemma_clean, "base:ya<->iya<->īya")

        return out


_RULE_PRIORITY: dict[str, int] = {
    "base:e<->aya": 0,
    "base:ya<->iya<->īya": 0,
}


def _pair_has_meaning_1(pair: Pair) -> bool:
    return bool(pair.source.meaning_1 or pair.target.meaning_1)


def _pair_sort_key(pair: Pair) -> tuple[int, int, str, str, str]:
    return (
        _RULE_PRIORITY.get(pair.rule, 1),
        0 if _pair_has_meaning_1(pair) else 1,
        pair.rule,
        pair.source.lemma_1,
        pair.target.lemma_1,
    )


# ---------------------------------------------------------------------------
# Synonym detection (multi + single)
# ---------------------------------------------------------------------------


@dataclass
class SynonymContext:
    """Index over the db needed to find synonym candidates fast.

    Built once and reused; rebuild on db commit.
    """

    by_pos_sig_meaning: dict[tuple[str, str, str], list[DpdHeadword]]
    by_pos_sig_meanings: dict[tuple[str, str], list[tuple[DpdHeadword, frozenset[str]]]]
    cleaned_meanings_for_id: dict[int, frozenset[str]]


def build_synonym_context(headwords: Sequence[DpdHeadword]) -> SynonymContext:
    by_single: dict[tuple[str, str, str], list[DpdHeadword]] = {}
    by_multi: dict[tuple[str, str], list[tuple[DpdHeadword, frozenset[str]]]] = {}
    cleaned_for_id: dict[int, frozenset[str]] = {}

    for hw in headwords:
        if not hw.meaning_1:
            continue
        sig = grammar_signature(hw.grammar)
        pcls = pos_class(hw.pos)
        if "; " in hw.meaning_1:
            cleaned = frozenset(
                m for raw in hw.meaning_1.split("; ") if (m := clean_meaning(raw))
            )
            if cleaned:
                by_multi.setdefault((pcls, sig), []).append((hw, cleaned))
                cleaned_for_id[hw.id] = cleaned
        else:
            cleaned_one = clean_meaning(hw.meaning_1)
            if cleaned_one:
                by_single.setdefault((pcls, sig, cleaned_one), []).append(hw)
                cleaned_for_id[hw.id] = frozenset({cleaned_one})

    return SynonymContext(
        by_pos_sig_meaning=by_single,
        by_pos_sig_meanings=by_multi,
        cleaned_meanings_for_id=cleaned_for_id,
    )


def find_synonyms_for(hw: DpdHeadword, ctx: SynonymContext) -> list[str]:
    """Return [lemma_clean, ...] synonym candidates for `hw`.

    Combines single-meaning and multi-meaning detectors. One-sided
    already-related suppression. Excludes hw itself.
    """
    if not hw.meaning_1:
        return []

    sig = grammar_signature(hw.grammar)
    pcls = pos_class(hw.pos)
    candidates: set[str] = set()

    if "; " in hw.meaning_1:
        meanings_a = frozenset(
            m for raw in hw.meaning_1.split("; ") if (m := clean_meaning(raw))
        )
        if not meanings_a:
            return []
        bucket = ctx.by_pos_sig_meanings.get((pcls, sig), [])
        for hw_b, meanings_b in bucket:
            if hw_b.id == hw.id:
                continue
            if hw_b.lemma_clean == hw.lemma_clean:
                continue
            shared = meanings_a & meanings_b
            if len(shared) < 2:
                continue
            candidates.add(hw_b.lemma_clean)
    else:
        cleaned = clean_meaning(hw.meaning_1)
        if not cleaned:
            return []
        bucket = ctx.by_pos_sig_meaning.get((pcls, sig, cleaned), [])
        for hw_b in bucket:
            if hw_b.id == hw.id:
                continue
            if hw_b.lemma_clean == hw.lemma_clean:
                continue
            candidates.add(hw_b.lemma_clean)

    candidates.discard(hw.lemma_clean)

    syn_set = split_field(hw.synonym)
    phon_set = split_field(hw.var_phonetic)
    text_set = split_field(hw.var_text)
    candidates -= syn_set
    candidates -= phon_set
    candidates -= text_set

    return pali_list_sorter(candidates)


# ---------------------------------------------------------------------------
# Combined relationship detector — what gui2 calls
# ---------------------------------------------------------------------------


class RelationshipDetector:
    """Single object that owns both detectors. Built once, reused."""

    def __init__(self, headwords: Sequence[DpdHeadword]) -> None:
        self._headwords = list(headwords)
        self._phonetic = PhoneticVariantDetector(self._headwords)
        self._synonym_ctx = build_synonym_context(self._headwords)

    @property
    def phonetic(self) -> PhoneticVariantDetector:
        return self._phonetic

    @property
    def synonym_ctx(self) -> SynonymContext:
        return self._synonym_ctx

    def find_synonyms(self, hw: DpdHeadword) -> list[str]:
        return find_synonyms_for(hw, self._synonym_ctx)

    def find_phonetic_variants(self, hw: DpdHeadword) -> list[tuple[str, str]]:
        return self._phonetic.find_phonetic_variants_for(hw)
