"""Retry orchestration for missing score groups in Pāḷi translation."""

import copy
import json
from typing import Any

from tools.ai_manager import AIManager

from .ai_response import (
    _coerce_flat_score_map,
    _iter_options,
    _normalize_ai_response,
    _parse_ai_json,
    _strip_occurrence_key_prefix,
)
from .prompts import (
    _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
    _RETRY_EQUIVALENT_KEY_GROUPS,
    _RETRY_OPTION_FIELDS,
    MAX_RETRY_BATCHES,
    MAX_RETRY_CONTEXT_CHARS,
    NO_TOOLS_INSTRUCTION,
    _build_missing_scores_prompt,
)
from .scoring import (
    _copy_score_context_fields,
    _db_example_group_key,
    _deterministic_score_value,
    _deterministic_selection_source,
    _is_db_example_tied_score,
    _positive_ai_score_value,
)


def _find_missing_score_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> list[dict[str, Any]]:
    missing_groups: list[dict[str, Any]] = []
    seen: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

    def record_equivalent_key_group(
        group: dict[str, Any],
        option_keys: list[str],
    ) -> None:
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS)
        if not isinstance(equivalent_groups, list):
            equivalent_groups = []
            group[_RETRY_EQUIVALENT_KEY_GROUPS] = equivalent_groups
        equivalent_groups.append(option_keys)

    def group_needs_scores(option_keys: list[str]) -> bool:
        score_entries = [scores_map[key] for key in option_keys if key in scores_map]
        if not score_entries:
            return True
        if any(_is_db_example_tied_score(score_entry) for score_entry in score_entries):
            return not any(
                _positive_ai_score_value(score_entry) is not None
                and not _is_db_example_tied_score(score_entry)
                for score_entry in score_entries
            )
        return False

    def inspect_group(
        word: str,
        options: list[dict[str, Any]],
        context: str,
    ) -> None:
        if not options:
            return
        option_keys: list[str] = []
        for option in options:
            key = option.get("key")
            if isinstance(key, str):
                option_keys.append(key)
        if option_keys and group_needs_scores(option_keys):
            signature = (
                word,
                tuple(_strip_occurrence_key_prefix(key) for key in option_keys),
            )
            existing_group = seen.get(signature)
            if existing_group is not None:
                record_equivalent_key_group(existing_group, option_keys)
            else:
                group = {
                    "word": word,
                    "context": context,
                    "missing_keys": option_keys,
                    "options": [
                        {
                            key: option.get(key, "")
                            for key in (
                                "key",
                                "id",
                                "pali",
                                "pos",
                                "grammar",
                                "meaning_1",
                                "meaning_combo",
                                "example_1",
                                "source_1",
                                "example_2",
                                "source_2",
                            )
                        }
                        for option in options
                    ],
                }
                record_equivalent_key_group(group, option_keys)
                seen[signature] = group
                missing_groups.append(group)

        for option in options:
            option_context = str(option.get("pali") or option.get("key") or context)
            for component_group in option.get("components", []):
                if isinstance(component_group, list):
                    inspect_group(word, component_group, option_context)

    for token_data in analysis:
        word = str(token_data.get("word", ""))
        inspect_group(word, token_data.get("data", []), word)

    return missing_groups


def _narrow_db_example_tied_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> None:
    for token_data in analysis:
        db_example_groups: dict[str, list[dict[str, Any]]] = {}
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            if not isinstance(key, str):
                continue
            if not option.get("db_example_match"):
                continue
            if _deterministic_score_value(option) is None:
                continue
            group_key = _db_example_group_key(option)
            if group_key:
                db_example_groups.setdefault(group_key, []).append(option)

        for group_options in db_example_groups.values():
            tied_keys = [
                key
                for option in group_options
                if isinstance(key := option.get("key"), str)
                and _is_db_example_tied_score(scores_map.get(key))
            ]
            if not tied_keys:
                continue

            positive_scores: dict[str, float] = {}
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                score_data = scores_map.get(key)
                if _is_db_example_tied_score(score_data):
                    continue
                positive_score = _positive_ai_score_value(score_data)
                if positive_score is not None:
                    positive_scores[key] = positive_score

            if not positive_scores:
                continue

            top_score = max(positive_scores.values())
            winner_keys = {
                key for key, score in positive_scores.items() if score == top_score
            }
            for option in group_options:
                key = option.get("key")
                if not isinstance(key, str):
                    continue
                score_data = scores_map.get(key)
                if key in winner_keys:
                    winning_score: dict[str, Any] = {
                        "score": 10,
                        "selection_source": _deterministic_selection_source(option),
                    }
                    _copy_score_context_fields(score_data, winning_score)
                    scores_map[key] = winning_score
                elif _is_db_example_tied_score(score_data):
                    scores_map[key] = {
                        "score": 0,
                        "selection_source": _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
                    }


def _batch_missing_groups(
    missing_groups: list[dict[str, Any]],
    max_chars: int,
) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_len = 0
    for group in missing_groups:
        group_len = len(json.dumps(group, ensure_ascii=False, separators=(",", ":")))
        if current and current_len + group_len > max_chars:
            batches.append(current)
            current = []
            current_len = 0
        current.append(group)
        current_len += group_len
    if current:
        batches.append(current)
    return batches


def _strip_reformat_context_fields(scores: dict[str, Any]) -> None:
    for value in scores.values():
        if isinstance(value, dict):
            value.pop("contextual_meaning", None)
            value.pop("selected_pos", None)


def _trim_groups_for_retry(
    missing_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for group in missing_groups:
        trimmed_group = {
            "word": group.get("word", ""),
            "context": group.get("context", ""),
            "missing_keys": group.get("missing_keys", []),
            "options": [
                {field: option.get(field, "") for field in _RETRY_OPTION_FIELDS}
                for option in group.get("options", [])
                if isinstance(option, dict)
            ],
        }
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS)
        if isinstance(equivalent_groups, list):
            trimmed_group[_RETRY_EQUIVALENT_KEY_GROUPS] = copy.deepcopy(
                equivalent_groups
            )
        trimmed.append(trimmed_group)
    return trimmed


def _fan_out_retry_scores(
    retry_scores: dict[str, Any],
    retry_groups: list[dict[str, Any]],
) -> None:
    for group in retry_groups:
        representative_keys = group.get("missing_keys", [])
        equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS, [])
        if not isinstance(representative_keys, list) or not isinstance(
            equivalent_groups, list
        ):
            continue

        for representative_key in representative_keys:
            if not isinstance(representative_key, str):
                continue
            if representative_key not in retry_scores:
                continue
            canonical_key = _strip_occurrence_key_prefix(representative_key)
            for equivalent_group in equivalent_groups:
                if not isinstance(equivalent_group, list):
                    continue
                for equivalent_key in equivalent_group:
                    if (
                        isinstance(equivalent_key, str)
                        and equivalent_key not in retry_scores
                        and _strip_occurrence_key_prefix(equivalent_key)
                        == canonical_key
                    ):
                        retry_scores[equivalent_key] = copy.deepcopy(
                            retry_scores[representative_key]
                        )


def _request_missing_score_retry_pass(
    *,
    resolved_sentence: str,
    missing_groups: list[dict[str, Any]],
    scores_map: dict[str, Any],
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    debug: dict[str, Any] | None,
    pass_number: int,
) -> list[dict[str, Any]]:
    retry_groups = _trim_groups_for_retry(missing_groups)
    batches = _batch_missing_groups(retry_groups, MAX_RETRY_CONTEXT_CHARS)
    skipped_groups = [group for batch in batches[MAX_RETRY_BATCHES:] for group in batch]

    for batch in batches[:MAX_RETRY_BATCHES]:
        batch_keys: list[str] = []
        expected_keys: set[str] = set()
        for group in batch:
            missing_keys = group.get("missing_keys", [])
            if isinstance(missing_keys, list):
                valid_missing_keys = [
                    key for key in missing_keys if isinstance(key, str)
                ]
                batch_keys.extend(valid_missing_keys)
                expected_keys.update(valid_missing_keys)
            equivalent_groups = group.get(_RETRY_EQUIVALENT_KEY_GROUPS, [])
            if isinstance(equivalent_groups, list):
                for equivalent_group in equivalent_groups:
                    if isinstance(equivalent_group, list):
                        expected_keys.update(
                            key for key in equivalent_group if isinstance(key, str)
                        )

        retry_prompt = _build_missing_scores_prompt(resolved_sentence, batch)
        retry_response = ai_manager.request(
            prompt=retry_prompt,
            model=model,
            provider_preference=provider,
            prompt_sys=(
                f"Return only JSON with a flat `scores` object. {NO_TOOLS_INSTRUCTION}"
            ),
        )
        retry_data: dict[str, Any] = {}
        retry_parse_error = ""
        if retry_response.content:
            retry_data, retry_parse_error = _parse_ai_json(retry_response.content)
            retry_data = _normalize_ai_response(retry_data)
            retry_data = _coerce_flat_score_map(retry_data, expected_keys)
            retry_data = _normalize_ai_response(retry_data)
            retry_scores = retry_data.get("scores", {})
            if isinstance(retry_scores, dict):
                _fan_out_retry_scores(retry_scores, batch)
                scores_map.update(retry_scores)
        if debug is not None:
            retry_debug: dict[str, Any] = {
                "prompt": retry_prompt,
                "raw_response": retry_response.content,
                "status_message": retry_response.status_message,
                "parsed_response": copy.deepcopy(retry_data),
                "parse_error": retry_parse_error,
                "missing_keys": batch_keys,
            }
            if pass_number > 1:
                retry_debug["pass"] = pass_number
            debug["retry_requests"].append(retry_debug)

    return skipped_groups
