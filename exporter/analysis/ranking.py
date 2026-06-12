"""Option ranking and fallback meaning helpers for Pāḷi translation."""

from typing import Any

from ._base import (
    _clean_meaning,
    _is_deconstruction_key,
    _is_numeric_score,
    _strip_grammar_annotations,
)
from .ai_response import _is_deconstructed_placeholder, _is_missing_key
from .prompts import _PARENT_MEANING_STOPWORDS, _PARENT_MEANING_TOKEN_RE


def _component_contextual_meaning(component: dict[str, Any]) -> str:
    for field in ("meaning_combo", "meaning_1"):
        meaning = component.get(field)
        if isinstance(meaning, str) and meaning.strip():
            return _strip_grammar_annotations(meaning)
    return ""


def _direct_key_rank(option: dict[str, Any]) -> int:
    key = str(option.get("key", ""))
    if not key or _is_deconstruction_key(key) or _is_missing_key(key):
        return 0
    if key.endswith(("_default", "_inflection")):
        return 0
    return 1 if "_" in key else 0


def _db_example_rank(option: dict[str, Any]) -> int:
    match_type = option.get("db_example_match_type", "")
    if match_type == "source_text_overlap":
        return 2
    if match_type == "text_overlap":
        return 1
    return 0


def _dictionary_quality_rank(option: dict[str, Any]) -> int:
    if not option.get("meaning_1"):
        return 0
    if option.get("example_1") or option.get("example_2"):
        return 2
    return 1


def _grammar_case_rank(option: dict[str, Any]) -> int:
    grammar = option.get("grammar")
    if not isinstance(grammar, str):
        return 0

    tokens = {token.lower() for token in grammar.split()}
    if "gen" in tokens:
        return 2
    if "dat" in tokens:
        return 1
    return 0


def _meaning_tokens(text: str) -> set[str]:
    return {
        token
        for token in _PARENT_MEANING_TOKEN_RE.findall(text.lower())
        if token not in _PARENT_MEANING_STOPWORDS
    }


def _parent_meaning_overlap_rank(
    option: dict[str, Any],
    parent_meaning: str,
) -> int:
    parent_tokens = _meaning_tokens(parent_meaning)
    if not parent_tokens:
        return 0
    option_tokens: set[str] = set()
    for field in ("meaning_combo", "meaning_1"):
        meaning = option.get(field)
        if isinstance(meaning, str):
            option_tokens.update(_meaning_tokens(meaning))
    return 1 if parent_tokens & option_tokens else 0


def _option_rank(
    option: dict[str, Any],
    is_component: bool = False,
    parent_meaning: str = "",
) -> tuple:
    ai_score = option.get("ai_score")
    numeric_score_rank = 1 if _is_numeric_score(ai_score) else 0
    score = ai_score if _is_numeric_score(ai_score) else -1
    component_pos_rank = 1 if is_component and option.get("pos") == "ind" else 0
    option_id = option.get("id")
    stable_id_rank = -option_id if isinstance(option_id, int) else 0
    return (
        numeric_score_rank,
        score,
        _db_example_rank(option),
        _direct_key_rank(option),
        _parent_meaning_overlap_rank(option, parent_meaning),
        component_pos_rank,
        _dictionary_quality_rank(option),
        _grammar_case_rank(option),
        option.get("score", 0),
        stable_id_rank,
    )


def _select_best_option(
    options: list[dict[str, Any]],
    is_component: bool = False,
    parent_meaning: str = "",
) -> dict[str, Any] | None:
    return max(
        options,
        key=lambda option: _option_rank(
            option,
            is_component=is_component,
            parent_meaning=parent_meaning,
        ),
        default=None,
    )


def _first_meaning_sense(option: dict[str, Any]) -> str:
    for field in ("meaning_combo", "meaning_1"):
        meaning = option.get(field)
        if not isinstance(meaning, str):
            continue
        first_sense = meaning.split(";", maxsplit=1)[0]
        cleaned = _clean_meaning(_strip_grammar_annotations(first_sense))
        if cleaned and not _is_deconstructed_placeholder(cleaned):
            return cleaned
    return ""


def _component_join_fallback_meaning(option: dict[str, Any]) -> str:
    components = option.get("components")
    if not isinstance(components, list):
        return ""
    parent_meaning = option.get("meaning_combo", "")
    if not isinstance(parent_meaning, str):
        parent_meaning = ""

    meanings: list[str] = []
    for component_group in components:
        if not isinstance(component_group, list):
            continue
        best_part = _select_best_option(
            component_group,
            is_component=True,
            parent_meaning=parent_meaning,
        )
        if best_part is None:
            continue
        meaning = _first_meaning_sense(best_part)
        if meaning:
            meanings.append(meaning)
    return " + ".join(meanings)


def _deconstruction_fallback_meaning(option: dict[str, Any]) -> str:
    meaning = _component_join_fallback_meaning(option)
    if meaning:
        return meaning
    return "*(AI analysis of deconstruction)*"
