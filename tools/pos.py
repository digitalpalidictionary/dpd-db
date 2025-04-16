"""Categorizing parts of speech (pos) into various lists."""

INDECLINABLES = [
    "abbrev",
    "abs",
    "ger",
    "ind",
    "inf",
    "prefix",
    "sandhi",
    "suffix",
    "idiom",
    "var",
]

CONJUGATIONS = ["aor", "cond", "fut", "imp", "imperf", "opt", "perf", "pr"]

DECLENSIONS = [
    "adj",
    "card",
    "cs",
    "fem",
    "letter",
    "masc",
    "nt",
    "ordin",
    "pp",
    "pron",
    "prp",
    "ptp",
    "root",
    "ve",
]

POS = [
    "abbrev",
    "abs",
    "adj",
    "aor",
    "card",
    "cond",
    "cs",
    "fem",
    "fut",
    "ger",
    "idiom",
    "imp",
    "imperf",
    "ind",
    "inf",
    "letter",
    "masc",
    "nt",
    "opt",
    "ordin",
    "perf",
    "pp",
    "pr",
    "prefix",
    "pron",
    "prp",
    "ptp",
    "root",
    "sandhi",
    "suffix",
    "ve",
]

VERBS = [
    "abs",
    "aor",
    "cond",
    "fut",
    "ger",
    "imp",
    "imperf",
    "inf",
    "opt",
    "perf",
    "pp",
    "pr",
    "prp",
    "ptp",
]

PARTICIPLES = [
    "pp",
    "prp",
    "ptp",
]

NOUNS = [
    "fem",
    "masc",
    "nt",
]

EXCLUDE_FROM_FREQ: set = {
    "abbrev",
    "cs",
    "idiom",
    "letter",
    "prefix",
    "root",
    "suffix",
    "ve",
}
