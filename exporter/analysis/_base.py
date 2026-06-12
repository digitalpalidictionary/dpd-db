"""Pure constants and functions with no project-level imports.

Every module in this package may import from here without creating a cycle.
"""

import re
from typing import Any

_GRAMMAR_ANNOTATION_KEYWORDS = (
    "nominative",
    "accusative",
    "genitive",
    "dative",
    "instrumental",
    "locative",
    "ablative",
    "vocative",
    "singular",
    "plural",
    "masculine",
    "feminine",
    "neuter",
    "enclitic",
    "particle",
    "indeclinable",
    "optative",
    "aorist",
    "participle",
    "component of",
    "grammatical",
    "interrogative",
)

_GRAMMAR_ABBREVIATION_RE = re.compile(
    r"\b(?:masc|fem|nt|nom|acc|gen|dat|abl|instr|loc|voc|sg|pl)\."
)


def _is_deconstruction_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.startswith("decon_") or "_decon_" in key


def _is_numeric_score(score: Any) -> bool:
    return isinstance(score, int | float) and not isinstance(score, bool)


def _has_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _retry_prompt_groups(
    missing_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "word": group.get("word", ""),
            "context": group.get("context", ""),
            "missing_keys": group.get("missing_keys", []),
            "options": group.get("options", []),
        }
        for group in missing_groups
    ]


def _clean_meaning(meaning: str) -> str:
    """Strip trailing grammar parentheticals that duplicate the Grammar column."""
    return re.sub(r"\s*\([^)]*'[^']+'\)\s*$", "", meaning).strip()


def _strip_grammar_annotations(text: str) -> str:
    """Remove AI-added grammar parentheticals while preserving meaning notes."""

    def replace_annotation(match: re.Match[str]) -> str:
        content = match.group(1).lower()
        if any(
            keyword in content for keyword in _GRAMMAR_ANNOTATION_KEYWORDS
        ) or _GRAMMAR_ABBREVIATION_RE.search(content):
            return ""
        return match.group(0)

    cleaned = re.sub(r"\s*\(([^()]*)\)", replace_annotation, text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s*[-,;:]\s*$", "", cleaned)
    return cleaned.strip()
