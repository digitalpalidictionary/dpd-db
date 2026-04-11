"""Phonetic variant detection engine for issue #144 (part 1).

``PhoneticVariantDetector`` ingests a list of ``DpdHeadword``-like objects
and produces ``PhoneticVariantCandidate`` pairs using three techniques:

1. **Same construction** — headwords sharing ``construction_clean`` + ``pos``
   but differing in ``lemma_clean``. Ported from
   ``db_tests/single/add_phonetic_variants.py``.
2. **Handwritten rules** — the bidirectional substitution list in
   ``scripts/variants/phonetic_rules.py``.
3. **Levenshtein proximity** — pairs inside the same
   ``family_word``/``family_root`` whose ``lemma_clean`` values differ by
   a Levenshtein distance of at most
   ``SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD`` and share a first character.

The detector is intentionally decoupled from SQLAlchemy: any object exposing
the attribute set used below (``lemma_1``, ``lemma_clean``, ``pos``,
``construction_clean``, ``family_word``, ``family_root``, ``root_key``,
``meaning_combo``, ``var_phonetic``, ``var_text``, ``variant``) can be
passed in. Tests use
``types.SimpleNamespace`` fakes for this reason.
"""

from dataclasses import dataclass
from typing import Protocol, Sequence

import Levenshtein

from scripts.variants.phonetic_rules import (
    PHONETIC_RULES,
    SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD,
)


class HeadwordLike(Protocol):
    @property
    def lemma_1(self) -> str: ...

    @property
    def lemma_clean(self) -> str: ...

    @property
    def pos(self) -> str: ...

    @property
    def construction_clean(self) -> str: ...

    @property
    def family_word(self) -> str: ...

    @property
    def family_root(self) -> str: ...

    @property
    def root_key(self) -> str: ...

    @property
    def meaning_combo(self) -> str: ...

    @property
    def var_phonetic(self) -> str: ...

    @property
    def var_text(self) -> str: ...

    @property
    def variant(self) -> str: ...


@dataclass
class PhoneticVariantPair:
    """A canonicalized phonetic variant pair.

    Each unordered pair of ``lemma_clean`` values appears at most once per
    rule. ``source`` is the specific headword whose ``lemma_1`` is canonical;
    ``targets`` is every headword sharing the other ``lemma_clean`` (homonyms).
    """

    rule: str
    source: "HeadwordLike"
    targets: list["HeadwordLike"]


@dataclass
class PhoneticVariantCandidate:
    lemma_1: str
    candidate_lemma_clean: str
    rule: str
    construction_clean: str
    pos: str
    meaning_combo: str
    family_root: str
    var_phonetic: str
    var_text: str
    variant: str


def _candidate_from(
    headword: HeadwordLike, other_lemma_clean: str, rule: str
) -> PhoneticVariantCandidate:
    return PhoneticVariantCandidate(
        lemma_1=headword.lemma_1,
        candidate_lemma_clean=other_lemma_clean,
        rule=rule,
        construction_clean=headword.construction_clean,
        pos=headword.pos,
        meaning_combo=headword.meaning_combo,
        family_root=headword.family_root,
        var_phonetic=headword.var_phonetic,
        var_text=headword.var_text,
        variant=headword.variant,
    )


def _already_recorded(headword: HeadwordLike, candidate_lemma_clean: str) -> bool:
    """True if the candidate is already present in the headword's var_phonetic.

    ``var_phonetic`` is a ``", "``-separated string of existing phonetic
    variants. If the editor has already recorded this candidate on the
    source headword, there is nothing for the reviewer to do.
    """
    if not headword.var_phonetic:
        return False
    existing = {token.strip() for token in headword.var_phonetic.split(",")}
    return candidate_lemma_clean in existing


def _same_family_context(source: HeadwordLike, target: HeadwordLike) -> bool:
    if source.family_root or target.family_root:
        if not all(
            [source.family_root, target.family_root, source.root_key, target.root_key]
        ):
            return False
        if source.family_root != target.family_root:
            return False
        if source.root_key != target.root_key:
            return False

    if source.family_word or target.family_word:
        if not (source.family_word and target.family_word):
            return False
        if source.family_word != target.family_word:
            return False

    return True


class PhoneticVariantDetector:
    def __init__(self, headwords: Sequence[HeadwordLike]) -> None:
        self._headwords: list[HeadwordLike] = list(headwords)

        self._by_lemma_1: dict[str, HeadwordLike] = {}
        self._by_lemma_clean: dict[str, list[HeadwordLike]] = {}
        self._by_construction_pos: dict[tuple[str, str], list[HeadwordLike]] = {}
        self._by_family: dict[str, list[HeadwordLike]] = {}

        for hw in self._headwords:
            self._by_lemma_1[hw.lemma_1] = hw
            self._by_lemma_clean.setdefault(hw.lemma_clean, []).append(hw)

            key = (hw.construction_clean, hw.pos)
            self._by_construction_pos.setdefault(key, []).append(hw)

            family_key = hw.family_word or hw.family_root
            if family_key:
                self._by_family.setdefault(family_key, []).append(hw)

    def detect_same_construction(self) -> list[PhoneticVariantCandidate]:
        """Pairs that share construction_clean + pos but differ in lemma_clean.

        Ports ``db_tests/single/add_phonetic_variants.py`` lines 72–91.
        """
        candidates: list[PhoneticVariantCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()
        for (construction_clean, _pos), group in self._by_construction_pos.items():
            if not construction_clean:
                continue
            distinct_clean = {hw.lemma_clean for hw in group}
            if len(distinct_clean) < 2:
                continue
            for a in group:
                for b in group:
                    if a is b:
                        continue
                    if a.lemma_clean == b.lemma_clean:
                        continue
                    if _already_recorded(a, b.lemma_clean):
                        continue
                    pair_key = (a.lemma_1, b.lemma_clean)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    candidates.append(
                        _candidate_from(a, b.lemma_clean, "same_construction")
                    )
        return candidates

    def detect_by_rules(self) -> list[PhoneticVariantCandidate]:
        """Candidates produced by applying each bidirectional rule."""
        candidates: list[PhoneticVariantCandidate] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        for hw in self._headwords:
            if not hw.lemma_clean:
                continue
            for x, y in PHONETIC_RULES:
                rule_tag = f"rule:{x}<->{y}"
                for produced in self._apply_rule_both_ways(hw.lemma_clean, x, y):
                    if produced == hw.lemma_clean:
                        continue
                    if produced not in self._by_lemma_clean:
                        continue
                    if _already_recorded(hw, produced):
                        continue
                    pair_key = (hw.lemma_1, produced, rule_tag)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    candidates.append(_candidate_from(hw, produced, rule_tag))
        return candidates

    @staticmethod
    def _apply_rule_both_ways(lemma_clean: str, x: str, y: str) -> list[str]:
        produced: list[str] = []
        if x and x in lemma_clean:
            produced.append(lemma_clean.replace(x, y))
        if y and y in lemma_clean:
            produced.append(lemma_clean.replace(y, x))
        return produced

    def detect_by_levenshtein(self) -> list[PhoneticVariantCandidate]:
        """Pairs inside the same family within the Levenshtein threshold.

        Both headwords must share the same ``pos``. Without this constraint
        the detector is overwhelmed by unrelated words that happen to share a
        family and look similar (e.g. noun forms vs. verb forms); a full-db
        run without the pos filter produced ~200k false positives.
        """
        candidates: list[PhoneticVariantCandidate] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        for _family_key, group in self._by_family.items():
            if len(group) < 2:
                continue
            for a in group:
                if not a.lemma_clean:
                    continue
                for b in group:
                    if a is b or not b.lemma_clean:
                        continue
                    if a.pos != b.pos:
                        continue
                    if a.lemma_clean[0] != b.lemma_clean[0]:
                        continue
                    distance = Levenshtein.distance(a.lemma_clean, b.lemma_clean)
                    if distance == 0:
                        continue
                    if distance > SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD:
                        continue
                    if _already_recorded(a, b.lemma_clean):
                        continue
                    rule_tag = f"levenshtein:{distance}"
                    pair_key = (a.lemma_1, b.lemma_clean, rule_tag)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    candidates.append(_candidate_from(a, b.lemma_clean, rule_tag))
        return candidates

    def detect_all(self) -> list[PhoneticVariantCandidate]:
        """Run every detector in order and concatenate without cross-method dedup."""
        results: list[PhoneticVariantCandidate] = []
        results.extend(self.detect_same_construction())
        results.extend(self.detect_by_rules())
        # results.extend(self.detect_by_levenshtein())
        return results

    def detect_canonical_pairs(self) -> list[PhoneticVariantPair]:
        """Run all detectors, collapse symmetric duplicates, and filter recorded.

        For each unordered ``(lemma_clean_a, lemma_clean_b)`` pair a given
        rule only emits one ``PhoneticVariantPair``. The pair is dropped
        entirely if *either* side already records the other in
        ``var_phonetic``. Results are sorted by ``(rule, source.lemma_1)``.
        """
        candidates = self.detect_all()
        seen: set[tuple[str, str, str]] = set()
        pairs: list[PhoneticVariantPair] = []
        for c in candidates:
            source = self._by_lemma_1.get(c.lemma_1)
            if source is None:
                continue
            targets = [
                target
                for target in self._by_lemma_clean.get(c.candidate_lemma_clean, [])
                if _same_family_context(source, target)
            ]
            if not targets:
                continue
            a_clean = source.lemma_clean
            b_clean = c.candidate_lemma_clean
            key = (c.rule, min(a_clean, b_clean), max(a_clean, b_clean))
            if key in seen:
                continue
            if _already_recorded(source, b_clean):
                continue
            if any(_already_recorded(t, a_clean) for t in targets):
                continue
            seen.add(key)
            pairs.append(
                PhoneticVariantPair(rule=c.rule, source=source, targets=targets)
            )
        pairs.sort(key=lambda p: (p.rule, p.source.lemma_1))
        return pairs
