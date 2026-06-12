"""Deterministic scoring and AI score merge helpers for Pāḷi translation."""

import copy
from typing import Any

from ._base import _is_deconstruction_key
from .ai_response import _iter_options, _texts_overlap
from .prompts import (
    _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE,
    _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
    _FINITE_VERB_GRAMMAR_RE,
    _QUOTATIVE_TI_SELECTION_SOURCE,
    _TRAILING_PUNCTUATION,
)
from .ranking import _component_contextual_meaning


def _score_selection_source(score_data: Any) -> str:
    if not isinstance(score_data, dict):
        return ""
    selection_source = score_data.get("selection_source")
    if not isinstance(selection_source, str):
        return ""
    return selection_source


def _is_db_example_tied_score(score_data: Any) -> bool:
    return _score_selection_source(score_data) == _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE


def pre_match_db_examples(
    analysis: list[dict[str, Any]],
    verse_source: str,
    verse_text: str,
) -> None:
    """Mark options whose curated example text overlaps the analyzed passage.

    Mutates `analysis` in-place by setting ``ai_score`` and ``db_example_match``
    on matching options. Does not return a value.
    """
    for token_data in analysis:
        for option in _iter_options(token_data.get("data", [])):
            best_match_type = ""
            for index in (1, 2):
                example = option.get(f"example_{index}", "")
                source = option.get(f"source_{index}", "")
                if not _texts_overlap(example, verse_text):
                    continue
                match_type = (
                    "source_text_overlap"
                    if source and source == verse_source
                    else "text_overlap"
                )
                if match_type == "source_text_overlap":
                    best_match_type = match_type
                    break
                if not best_match_type:
                    best_match_type = match_type

            if best_match_type:
                option["ai_score"] = 10
                option["db_example_match"] = True
                option["db_example_match_type"] = best_match_type
                option["selection_source"] = f"db_example_{best_match_type}"


def _is_quotative_ti_token(word: Any) -> bool:
    if not isinstance(word, str):
        return False
    normalized = word.lower().replace("’", "'").rstrip(_TRAILING_PUNCTUATION)
    return normalized.endswith("'ti")


def _construction_parts(option: dict[str, Any]) -> list[str]:
    construction = option.get("construction")
    if not isinstance(construction, str):
        return []
    clean_construction = construction.replace("<b>", "").replace("</b>", "")
    return [
        part.strip().lower().replace("’", "'")
        for part in clean_construction.split("+")
        if part.strip()
    ]


def _is_iti_final_deconstruction(option: dict[str, Any]) -> bool:
    key = option.get("key")
    if not _is_deconstruction_key(key):
        return False
    parts = _construction_parts(option)
    return len(parts) >= 2 and parts[-1] == "iti"


def _finite_verb_first_component(option: dict[str, Any]) -> dict[str, Any] | None:
    components = option.get("components")
    if not isinstance(components, list) or not components:
        return None
    first_group = components[0]
    if not isinstance(first_group, list):
        return None
    for component in first_group:
        if not isinstance(component, dict):
            continue
        pos = component.get("pos")
        grammar = component.get("grammar")
        if (
            isinstance(pos, str)
            and pos.lower() == "verb"
            and isinstance(grammar, str)
            and _FINITE_VERB_GRAMMAR_RE.search(grammar.lower())
        ):
            return component
    return None


def _copy_score_context_fields(
    source_score: Any,
    target_score: dict[str, Any],
) -> None:
    if not isinstance(source_score, dict):
        return
    for field in ("contextual_meaning", "selected_pos"):
        value = source_score.get(field)
        if value:
            target_score[field] = value


def _numeric_score_value(score_data: Any) -> int | float | None:
    if isinstance(score_data, dict):
        score = score_data.get("score")
    else:
        score = score_data
    if isinstance(score, int | float) and not isinstance(score, bool):
        return score
    return None


def _positive_ai_score_value(score_data: Any) -> float | None:
    score = _numeric_score_value(score_data)
    if score is None or score <= 0:
        return None
    return float(score)


def _deterministic_score_value(option: dict[str, Any]) -> int | float | None:
    return _numeric_score_value(option.get("ai_score"))


def _db_example_group_key(option: dict[str, Any]) -> str:
    option_id = option.get("id")
    if isinstance(option_id, int | str) and not isinstance(option_id, bool):
        return str(option_id)
    key = option.get("key")
    if isinstance(key, str):
        return key.split("_", 1)[0]
    return ""


def _deterministic_selection_source(option: dict[str, Any]) -> str:
    selection_source = option.get("selection_source")
    if isinstance(selection_source, str) and selection_source:
        return selection_source
    return "deterministic"


def _apply_quotative_ti_deconstruction_score(
    token_data: dict[str, Any],
    scores_map: dict[str, Any],
) -> None:
    if not _is_quotative_ti_token(token_data.get("word")):
        return

    deconstruction_options = [
        option
        for option in token_data.get("data", [])
        if isinstance(option, dict) and _is_iti_final_deconstruction(option)
    ]
    finite_matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for option in deconstruction_options:
        finite_component = _finite_verb_first_component(option)
        if finite_component:
            finite_matches.append((option, finite_component))

    if len(finite_matches) != 1:
        return

    winning_option, finite_component = finite_matches[0]
    winning_key = winning_option.get("key")
    if not isinstance(winning_key, str):
        return

    winning_score: dict[str, Any] = {
        "score": 10,
        "selection_source": _QUOTATIVE_TI_SELECTION_SOURCE,
    }
    _copy_score_context_fields(scores_map.get(winning_key), winning_score)
    if "contextual_meaning" not in winning_score:
        contextual_meaning = _component_contextual_meaning(finite_component)
        if contextual_meaning:
            winning_score["contextual_meaning"] = contextual_meaning
    scores_map[winning_key] = winning_score

    for option in deconstruction_options:
        key = option.get("key")
        if not isinstance(key, str) or key == winning_key:
            continue
        demoted_score: dict[str, Any] = {
            "score": 0,
            "selection_source": _QUOTATIVE_TI_SELECTION_SOURCE,
        }
        _copy_score_context_fields(scores_map.get(key), demoted_score)
        scores_map[key] = demoted_score


def _apply_deterministic_scores_to_map(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> None:
    for token_data in analysis:
        _apply_quotative_ti_deconstruction_score(token_data, scores_map)
        preexisting_scores = dict(scores_map)
        db_example_groups: dict[str, list[dict[str, Any]]] = {}
        handled_db_keys: set[str] = set()
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if not isinstance(key, str):
                continue
            score = _deterministic_score_value(option)
            if option.get("db_example_match") and score is not None:
                group_key = _db_example_group_key(option)
                if group_key:
                    db_example_groups.setdefault(group_key, []).append(option)
                    handled_db_keys.add(key)

        for group_options in db_example_groups.values():
            positive_scores: dict[str, float] = {}
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                positive_score = _positive_ai_score_value(preexisting_scores.get(key))
                if positive_score is not None:
                    positive_scores[key] = positive_score

            if positive_scores:
                top_score = max(positive_scores.values())
                winner_keys = {
                    key for key, score in positive_scores.items() if score == top_score
                }
                for option in group_options:
                    key = option.get("key")
                    if not isinstance(key, str):
                        continue
                    if key in winner_keys:
                        deterministic_score: dict[str, Any] = {
                            "score": 10,
                            "selection_source": _deterministic_selection_source(option),
                        }
                        _copy_score_context_fields(
                            preexisting_scores.get(key),
                            deterministic_score,
                        )
                        scores_map[key] = deterministic_score
                    elif key not in preexisting_scores:
                        scores_map[key] = {
                            "score": 0,
                            "selection_source": _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
                        }
                continue

            for option in group_options:
                key = option.get("key")
                score = _deterministic_score_value(option)
                if not isinstance(key, str) or score is None:
                    continue
                selection_source = _deterministic_selection_source(option)
                if len(group_options) > 1:
                    selection_source = _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE
                deterministic_score = {
                    "score": score,
                    "selection_source": selection_source,
                }
                _copy_score_context_fields(
                    preexisting_scores.get(key),
                    deterministic_score,
                )
                scores_map[key] = deterministic_score

        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            score = _deterministic_score_value(option)
            if (
                isinstance(key, str)
                and key not in handled_db_keys
                and key not in scores_map
                and score is not None
            ):
                scores_map[key] = {
                    "score": score,
                    "selection_source": _deterministic_selection_source(option),
                }


def merge_ai_selections(
    analysis_data: list[dict[str, Any]], ai_response: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge AI scores and meanings into the analysis data structure.
    Returns a new object containing translation and the enriched analysis.
    """
    # Create a deep copy to avoid mutating the original input
    enriched_analysis = copy.deepcopy(analysis_data)
    scores_map = ai_response.get("scores", {})

    # Helper to traverse and update
    def update_entries(data_list):
        for item in data_list:
            key = item.get("key")
            if key in scores_map:
                update = scores_map[key]
                if not isinstance(update, dict):
                    # AI returned a bare scalar instead of a score object
                    item["ai_score"] = (
                        int(update) if isinstance(update, (int, float)) else 0
                    )
                else:
                    item["ai_score"] = update.get("score", 0)
                    if "selection_source" in update:
                        item["selection_source"] = update["selection_source"]

                    # Apply contextual info if score is positive (implying relevance)
                    if update.get("score", 0) > 0:
                        contextual_meaning = update.get("contextual_meaning")
                        if (
                            isinstance(contextual_meaning, str)
                            and contextual_meaning.strip()
                        ):
                            item["meaning_combo"] = contextual_meaning
                        selected_pos = update.get("selected_pos")
                        if isinstance(selected_pos, str) and selected_pos.strip():
                            item["selected_pos"] = selected_pos
            else:
                item["ai_score"] = item.get("ai_score")

            # Recursively update components
            if "components" in item:
                for comp_list in item["components"]:
                    if isinstance(comp_list, list):
                        update_entries(comp_list)

    for word_obj in enriched_analysis:
        update_entries(word_obj["data"])

    return {
        "translation": ai_response.get("translation", ""),
        "literal_translation": ai_response.get("literal_translation", ""),
        "analysis": enriched_analysis,
    }
