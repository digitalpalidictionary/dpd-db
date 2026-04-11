"""Phonetic variant substitution rules for issue #144 (part 1).

Each rule is a tuple ``(x, y)`` and is applied bidirectionally by the
detector: for every headword's ``lemma_clean`` the detector replaces every
occurrence of ``x`` with ``y`` and separately every occurrence of ``y`` with
``x``, then checks whether the result exists as another headword's
``lemma_clean``. The rule list is intentionally noisy — downstream human
review of the generated TSV is the filter.

Notes on individual rules:

- ``(e, aya)`` / ``(o, ava)`` cover sandhi contractions.
- Long↔short vowel pairs cover metrical variants.
- ``(ṃ, ṅ)`` covers niggahīta vs. the velar nasal.
- Retroflex↔dental pairs (``t``/``ṭ`` etc.) cover scribal alternations.
- ``(h, "")`` and ``(y, "")``/``(v, "")`` cover glide/aspirate insertion and
  deletion.
"""

PHONETIC_RULES: list[tuple[str, str]] = [
    ("e", "aya"),
    ("o", "ava"),
    ("ā", "a"),
    ("ī", "i"),
    ("ū", "u"),
    ("ṃ", "ṅ"),
    ("t", "ṭ"),
    ("d", "ḍ"),
    ("n", "ṇ"),
    ("l", "ḷ"),
    ("h", ""),
    ("nh", "h"),
    ("y", ""),
    ("v", ""),
]

SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD: int = 2
