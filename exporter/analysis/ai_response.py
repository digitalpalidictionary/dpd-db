"""AI response parsing and normalization helpers for Pāḷi translation."""

import json
import re
from collections.abc import Iterator
from typing import Any


def _normalize_ai_response(ai_data: dict[str, Any]) -> dict[str, Any]:
    """Fix malformed AI responses with nested 'scores' keys.

    Some AI models return scores in a nested structure like {"scores": {"scores": {...}}}.
    This function flattens that to the expected {"scores": {...}} format.
    """
    from .rendering import _strip_grammar_annotations

    scores = ai_data.get("scores", {})
    if (
        isinstance(scores, dict)
        and "scores" in scores
        and not any(
            k.startswith(("decon_", "digits")) or "_" in k
            for k in scores.keys()
            if isinstance(k, str)
        )
    ):
        # The outer "scores" key only contains another "scores" key → nested structure
        ai_data["scores"] = scores["scores"]
        scores = ai_data["scores"]
    if isinstance(scores, dict):
        for key, value in list(scores.items()):
            if isinstance(value, int | float) and not isinstance(value, bool):
                scores[key] = {"score": value}
                continue
            if not isinstance(value, dict):
                continue
            contextual_meaning = value.get("contextual_meaning")
            if isinstance(contextual_meaning, str) and contextual_meaning.strip():
                value["contextual_meaning"] = _strip_grammar_annotations(
                    contextual_meaning
                )
    return ai_data


def _coerce_flat_score_map(
    ai_data: dict[str, Any],
    expected_keys: set[str],
) -> dict[str, Any]:
    """Wrap a bare ``{key: {"score": N}}`` response in the ``scores`` contract."""
    if not ai_data or "scores" in ai_data:
        return ai_data

    matched: dict[str, Any] = {}
    for key, value in ai_data.items():
        if key not in expected_keys:
            continue
        if isinstance(value, dict):
            score = value.get("score")
            if isinstance(score, int | float) and not isinstance(score, bool):
                matched[key] = value
        elif isinstance(value, int | float) and not isinstance(value, bool):
            matched[key] = {"score": value}

    if not matched or len(matched) * 2 < len(ai_data):
        return ai_data
    return {"scores": matched}


def _normalize_example_text(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = text.replace("'", "")
    text = re.sub(r"[^\w]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _texts_overlap(first_text: str, second_text: str) -> bool:
    first = _normalize_example_text(first_text)
    second = _normalize_example_text(second_text)
    return bool(first and second and (first in second or second in first))


def _strip_occurrence_key_prefix(key: str) -> str:
    match = _OCCURRENCE_KEY_PREFIX_RE.match(key)
    if not match:
        return key
    return match.group(1)


def _is_deconstruction_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.startswith("decon_") or "_decon_" in key


def _is_missing_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.startswith("missing_") or "_missing_" in key


def _is_deconstructed_placeholder(meaning: Any) -> bool:
    return isinstance(meaning, str) and meaning.strip() == _DECONSTRUCTED_PLACEHOLDER


def _normalize_containment_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _append_unique_text_part(parts: list[str], text: Any) -> None:
    if not isinstance(text, str):
        return
    candidate = re.sub(r"\s+", " ", text).strip()
    if not candidate:
        return
    accumulated = _normalize_containment_text(" ".join(parts))
    candidate_normalized = _normalize_containment_text(candidate)
    if accumulated and candidate_normalized in accumulated:
        return
    parts.append(candidate)


def _iter_options(options: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for option in options:
        yield option
        for component_group in option.get("components", []):
            if isinstance(component_group, list):
                yield from _iter_options(component_group)


def _extract_partial_response(response_text: str) -> dict[str, Any]:
    """Extract translation/literal_translation from a malformed JSON response.

    When the AI returns incomplete JSON (e.g., with template placeholders),
    extract what we can and construct a fallback response.
    """
    fallback: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
    }

    # Try to extract translation using regex
    trans_match = re.search(
        r'"translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if trans_match:
        fallback["translation"] = trans_match.group(1).replace('\\"', '"')

    # Try to extract literal_translation
    lit_match = re.search(
        r'"literal_translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if lit_match:
        fallback["literal_translation"] = lit_match.group(1).replace('\\"', '"')

    # Try to extract valid score entries (those with numeric scores)
    score_matches = re.finditer(
        r'"([^"]+?)"\s*:\s*\{\s*"score"\s*:\s*(\d+)', response_text
    )
    for match in score_matches:
        key = match.group(1)
        score = int(match.group(2))
        fallback["scores"][key] = {"score": score}

    return fallback


def _parse_ai_json(response_text: str) -> tuple[dict[str, Any], str]:
    json_str = response_text.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:-3].strip()
    elif json_str.startswith("```"):
        json_str = json_str[3:-3].strip()

    try:
        return json.loads(json_str), ""
    except json.JSONDecodeError as exc:
        return _extract_partial_response(response_text), str(exc)


def _collect_option_keys(analysis: list[dict[str, Any]]) -> set[str]:
    """Gather every option `key` (including components/deconstructions) in the analysis."""
    keys: set[str] = set()
    for token_data in analysis:
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if isinstance(key, str):
                keys.add(key)
    return keys


def _extract_word_key_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> dict[str, str] | None:
    """Detect a flat or ``{"disambiguation": {...}}`` word-key map.

    Antigravity/Gemini routinely returns this compact shape instead of the required
    ``{translation, literal_translation, scores}`` schema. When the values are real
    option keys from the analysis, the map IS the disambiguation we want. Returns
    ``None`` when the response is not such a map (proper schema, dict-valued, unknown
    keys, or empty).
    """
    if not isinstance(ai_data, dict) or not ai_data:
        return None
    if "scores" in ai_data or "translation" in ai_data:
        return None
    candidate = ai_data
    if set(ai_data) == {"disambiguation"}:
        disambiguation = ai_data["disambiguation"]
        if not isinstance(disambiguation, dict) or not disambiguation:
            return None
        candidate = disambiguation
    valid_keys = _collect_option_keys(analysis)
    if not valid_keys:
        return None
    matched = {
        surface_word: value
        for surface_word, value in candidate.items()
        if isinstance(value, str) and value in valid_keys
    }
    if not matched or len(matched) * 2 < len(candidate):
        return None
    return matched


def _top_level_options_for_word(
    analysis: list[dict[str, Any]], word: str
) -> list[dict[str, Any]]:
    for token_data in analysis:
        if token_data.get("word") != word:
            continue
        options = token_data.get("data", [])
        if not isinstance(options, list):
            return []
        return [option for option in options if isinstance(option, dict)]
    return []


def _matching_key_by_id(
    analysis: list[dict[str, Any]],
    word: str,
    option_id: int,
) -> str | None:
    matched_keys = [
        key
        for option in _top_level_options_for_word(analysis, word)
        if option.get("id") == option_id
        for key in [option.get("key")]
        if isinstance(key, str)
    ]
    if len(matched_keys) == 1:
        return matched_keys[0]
    return None


def _matching_key_by_lemma(
    analysis: list[dict[str, Any]],
    word: str,
    lemma: str,
) -> str | None:
    matched_keys = [
        key
        for option in _top_level_options_for_word(analysis, word)
        if option.get("lemma") == lemma
        for key in [option.get("key")]
        if isinstance(key, str)
    ]
    if len(matched_keys) == 1:
        return matched_keys[0]
    return None


def _structured_selection_result(
    word_key_map: dict[str, str],
    word_meaning_map: dict[str, str],
    candidate_count: int,
) -> tuple[dict[str, str], dict[str, str]] | None:
    if not word_key_map or len(word_key_map) * 2 < candidate_count:
        return None
    return word_key_map, word_meaning_map


def _top_level_key_words(analysis: list[dict[str, Any]]) -> dict[str, set[str]]:
    key_words: dict[str, set[str]] = {}
    for token_data in analysis:
        word = token_data.get("word")
        options = token_data.get("data", [])
        if not isinstance(word, str) or not word or not isinstance(options, list):
            continue
        for option in options:
            if not isinstance(option, dict):
                continue
            key = option.get("key")
            if isinstance(key, str):
                key_words.setdefault(key, set()).add(word)
    return key_words


def _extract_selected_keys_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]] | None:
    """Recover a top-level ``selected_keys`` list into a word-key map."""
    if not isinstance(ai_data, dict) or set(ai_data) != {"selected_keys"}:
        return None
    raw_keys = ai_data["selected_keys"]
    if (
        not isinstance(raw_keys, list)
        or not raw_keys
        or not all(isinstance(key, str) for key in raw_keys)
    ):
        return None

    key_words = _top_level_key_words(analysis)
    word_key_map: dict[str, str] = {}
    for raw_key in raw_keys:
        words = key_words.get(raw_key)
        if not words or len(words) != 1:
            continue
        word = next(iter(words))
        if word in word_key_map:
            return None
        word_key_map[word] = raw_key

    return _structured_selection_result(word_key_map, {}, len(raw_keys))


def _extract_structured_selection_map(
    ai_data: dict[str, Any],
    analysis: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]] | None:
    """Recover wrong-schema structured selections into a word-key map."""
    from .rendering import _strip_grammar_annotations

    if not isinstance(ai_data, dict) or not ai_data:
        return None
    if "scores" in ai_data or "translation" in ai_data:
        return None

    valid_keys = _collect_option_keys(analysis)
    if not valid_keys:
        return None

    if len(ai_data) == 1:
        list_key = next(iter(ai_data))
        if list_key in _SELECTION_LIST_KEYS:
            raw_items = ai_data[list_key]
            if not isinstance(raw_items, list) or not raw_items:
                return None
            if not all(isinstance(item, dict) for item in raw_items):
                return None

            word_key_map: dict[str, str] = {}
            word_meaning_map: dict[str, str] = {}
            for item in raw_items:
                word = item.get("word")
                if not isinstance(word, str) or not word:
                    continue

                selected_key = None
                for field in _SELECTION_KEY_FIELDS:
                    raw_key = item.get(field)
                    if isinstance(raw_key, str):
                        selected_key = raw_key if raw_key in valid_keys else None
                        break

                if selected_key is None:
                    raw_id = item.get("selected_id", item.get("id"))
                    if isinstance(raw_id, int) and not isinstance(raw_id, bool):
                        selected_key = _matching_key_by_id(analysis, word, raw_id)

                if selected_key is None:
                    continue

                word_key_map[word] = selected_key
                meaning = item.get("meaning")
                if isinstance(meaning, str) and meaning.strip():
                    word_meaning_map[word] = _strip_grammar_annotations(meaning)

            return _structured_selection_result(
                word_key_map, word_meaning_map, len(raw_items)
            )

    lemma_items = [
        (word, value)
        for word, value in ai_data.items()
        if isinstance(word, str)
        and isinstance(value, dict)
        and isinstance(value.get("lemma"), str)
    ]
    if not lemma_items or len(lemma_items) * 2 < len(ai_data):
        return None

    word_key_map = {}
    word_meaning_map = {}
    for word, item in lemma_items:
        lemma = item["lemma"]
        if not isinstance(lemma, str):
            continue
        selected_key = _matching_key_by_lemma(analysis, word, lemma)
        if selected_key is None:
            continue
        word_key_map[word] = selected_key
        meaning = item.get("meaning")
        if isinstance(meaning, str) and meaning.strip():
            word_meaning_map[word] = _strip_grammar_annotations(meaning)

    return _structured_selection_result(
        word_key_map, word_meaning_map, len(lemma_items)
    )


def _wrong_schema_has_meaning_evidence(ai_data: dict[str, Any]) -> bool:
    from .retry import _has_non_empty_string

    scores = ai_data.get("scores")
    if isinstance(scores, dict):
        for value in scores.values():
            if isinstance(value, dict) and _has_non_empty_string(
                value.get("contextual_meaning")
            ):
                return True

    for value in ai_data.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _has_non_empty_string(
                    item.get("meaning")
                ):
                    return True
        elif isinstance(value, dict) and _has_non_empty_string(value.get("meaning")):
            return True
    return False


from .prompts import (  # noqa: E402
    _SELECTION_LIST_KEYS,
    _SELECTION_KEY_FIELDS,
    _OCCURRENCE_KEY_PREFIX_RE,
    _DECONSTRUCTED_PLACEHOLDER,
)
