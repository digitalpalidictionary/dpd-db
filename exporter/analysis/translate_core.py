"""Shared prompt-building and analysis utilities for Pāḷi AI translation."""

import copy
import json
import re
from collections.abc import Callable
from typing import Any, cast

from sqlalchemy.orm import Session

from exporter.analysis.analyzer import analyze_sentence, tokenize_sentence
from tools.ai_manager import AIManager
from tools.printer import printer as pr

from ._base import (  # noqa: F401
    _clean_meaning,
    _has_non_empty_string,
    _is_deconstruction_key,
    _is_numeric_score,
    _retry_prompt_groups,
    _strip_grammar_annotations,
)
from .ai_response import (  # noqa: F401
    _append_unique_text_part,
    _coerce_flat_score_map,
    _collect_option_keys,
    _extract_partial_response,
    _extract_selected_keys_map,
    _extract_structured_selection_map,
    _extract_word_key_map,
    _is_deconstructed_placeholder,
    _is_missing_key,
    _iter_options,
    _matching_key_by_id,
    _matching_key_by_lemma,
    _normalize_ai_response,
    _normalize_containment_text,
    _normalize_example_text,
    _parse_ai_json,
    _strip_occurrence_key_prefix,
    _structured_selection_result,
    _texts_overlap,
    _top_level_key_words,
    _top_level_options_for_word,
    _wrong_schema_has_meaning_evidence,
)
from .prompts import (  # noqa: F401
    _DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE,
    _DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE,
    _DECONSTRUCTED_PLACEHOLDER,
    _FINITE_VERB_GRAMMAR_RE,
    _OCCURRENCE_KEY_PREFIX_RE,
    _PARENT_MEANING_STOPWORDS,
    _PARENT_MEANING_TOKEN_RE,
    _QUOTATIVE_TI_SELECTION_SOURCE,
    _RETRY_EQUIVALENT_KEY_GROUPS,
    _RETRY_OPTION_FIELDS,
    _SELECTION_KEY_FIELDS,
    _SELECTION_LIST_KEYS,
    _SENTENCE_SPLIT_RE,
    _TRAILING_PUNCTUATION,
    CHUNK_FIRST_PASS_ATTEMPTS,
    COMMON_PALI_RULES,
    MAX_FIRST_CONTEXT_CHARS,
    MAX_RETRY_BATCHES,
    MAX_RETRY_CONTEXT_CHARS,
    NO_GRAMMAR_NOTES_INSTRUCTION,
    NO_TOOLS_INSTRUCTION,
    PREVIOUS_TRANSLATION_CONTEXT_CHARS,
    REFORMAT_KEYS_MAX_CHARS,
    REFORMAT_MAX_CHARS,
    _build_grounded_translation_prompt,
    _build_missing_scores_prompt,
    _build_reformat_prompt,
    _build_translation_prompt,
    _previous_translation_block,
    _word_keys_overview,
    build_system_prompt,
)
from .ranking import (  # noqa: F401
    _component_contextual_meaning,
    _component_join_fallback_meaning,
    _db_example_rank,
    _deconstruction_fallback_meaning,
    _dictionary_quality_rank,
    _direct_key_rank,
    _first_meaning_sense,
    _meaning_tokens,
    _option_rank,
    _parent_meaning_overlap_rank,
    _select_best_option,
)
from .rendering import (  # noqa: F401
    format_markdown_table,
    generate_markdown_report,
)
from .retry import (  # noqa: F401
    _batch_missing_groups,
    _fan_out_retry_scores,
    _find_missing_score_groups,
    _narrow_db_example_tied_groups,
    _request_missing_score_retry_pass,
    _strip_reformat_context_fields,
    _trim_groups_for_retry,
)
from .scoring import (  # noqa: F401
    _apply_deterministic_scores_to_map,
    _apply_quotative_ti_deconstruction_score,
    _construction_parts,
    _copy_score_context_fields,
    _db_example_group_key,
    _deterministic_score_value,
    _deterministic_selection_source,
    _finite_verb_first_component,
    _is_db_example_tied_score,
    _is_iti_final_deconstruction,
    _is_quotative_ti_token,
    _numeric_score_value,
    _positive_ai_score_value,
    _score_selection_source,
    merge_ai_selections,
    pre_match_db_examples,
)


def extract_variant_options(text: str) -> tuple[str, dict[str, list[str]]]:
    """Resolve GUI-style // variants to first choices and collect options."""
    parts = re.split(r"(\s+)", text)
    options: dict[str, list[str]] = {}
    resolved_parts: list[str] = []

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in _TRAILING_PUNCTUATION:
            suffix = core[-1] + suffix
            core = core[:-1]

        variants = [variant for variant in core.split("//") if variant]
        if not variants:
            resolved_parts.append(part)
            continue

        options[variants[0]] = variants
        resolved_parts.append(f"{variants[0]}{suffix}")

    return "".join(resolved_parts), options


def apply_variant_choices(
    text: str,
    speech_mark_options: dict[str, list[str]],
    variant_choices: dict[str, Any] | None,
) -> str:
    """Build final text from original // variants and AI-provided option indexes."""
    if not variant_choices:
        return extract_variant_options(text)[0]

    parts = re.split(r"(\s+)", text)
    resolved_parts: list[str] = []

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in _TRAILING_PUNCTUATION:
            suffix = core[-1] + suffix
            core = core[:-1]

        variants = [variant for variant in core.split("//") if variant]
        if not variants:
            resolved_parts.append(part)
            continue

        option_key = variants[0]
        configured_variants = speech_mark_options.get(option_key, variants)
        choice_raw = variant_choices.get(option_key, 0)
        try:
            choice_index = int(choice_raw)
        except (TypeError, ValueError):
            choice_index = 0
        if choice_index < 0 or choice_index >= len(configured_variants):
            choice_index = 0

        resolved_parts.append(f"{configured_variants[choice_index]}{suffix}")

    return "".join(resolved_parts)


def sync_analysis_words_to_sentence(
    analysis: list[dict[str, Any]], sentence: str
) -> list[dict[str, Any]]:
    """Return analysis with top-level words replaced by the final sentence tokens."""
    tokens = tokenize_sentence(sentence)
    synced_analysis = copy.deepcopy(analysis)
    if len(tokens) != len(synced_analysis):
        return synced_analysis

    for token_data, token in zip(synced_analysis, tokens, strict=True):
        token_data["word"] = token
    return synced_analysis


def _analysis_context_len(analysis: list[dict[str, Any]]) -> int:
    return len(json.dumps(analysis, ensure_ascii=False, separators=(",", ":")))


def _split_into_sentence_chunks(
    resolved_sentence: str,
    analysis: list[dict[str, Any]],
    max_context_chars: int,
) -> tuple[list[tuple[str, list[dict[str, Any]]]], bool]:
    """Return (chunks, use_grounded_fallback).

    use_grounded_fallback is True when a lone sentence whose JSON exceeds the
    threshold is split word-by-word for scoring; the caller must issue a
    grounded whole-sentence translation after scores are merged.
    """
    whole = json.dumps(analysis, ensure_ascii=False, separators=(",", ":"))
    if len(whole) <= max_context_chars:
        return [(resolved_sentence, analysis)], False

    sentences = [
        sentence
        for sentence in _SENTENCE_SPLIT_RE.split(resolved_sentence)
        if sentence.strip()
    ]
    if len(sentences) < 2:
        # Lone oversize sentence: split by word for scoring only.
        if len(analysis) >= 2:
            word_chunks = [(entry["word"], [entry]) for entry in analysis]
            return word_chunks, True
        return [(resolved_sentence, analysis)], False

    counts = [len(tokenize_sentence(sentence)) for sentence in sentences]
    if sum(counts) != len(analysis):
        return [(resolved_sentence, analysis)], False

    sentence_slices: list[tuple[str, list[dict[str, Any]]]] = []
    start = 0
    for sentence, count in zip(sentences, counts, strict=True):
        end = start + count
        sentence_slices.append((sentence, analysis[start:end]))
        start = end

    chunks: list[tuple[str, list[dict[str, Any]]]] = []
    current_sentences: list[str] = []
    current_analysis: list[dict[str, Any]] = []
    for sentence, sentence_analysis in sentence_slices:
        candidate_analysis = [*current_analysis, *sentence_analysis]
        if (
            current_analysis
            and _analysis_context_len(candidate_analysis) > max_context_chars
        ):
            chunks.append((" ".join(current_sentences), current_analysis))
            current_sentences = [sentence]
            current_analysis = list(sentence_analysis)
        else:
            current_sentences.append(sentence)
            current_analysis = candidate_analysis

    if current_sentences:
        chunks.append((" ".join(current_sentences), current_analysis))
    return chunks or [(resolved_sentence, analysis)], False


def _merge_chunk_ai_data(chunk_datas: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
        "variant_choices": {},
    }
    translations: list[str] = []
    literals: list[str] = []
    for data in chunk_datas:
        translation = data.get("translation")
        _append_unique_text_part(translations, translation)
        literal = data.get("literal_translation")
        _append_unique_text_part(literals, literal)
        scores = data.get("scores")
        if isinstance(scores, dict):
            for key, value in scores.items():
                merged["scores"].setdefault(key, value)
        variant_choices = data.get("variant_choices")
        if isinstance(variant_choices, dict):
            for key, value in variant_choices.items():
                merged["variant_choices"].setdefault(key, value)
    merged["translation"] = " ".join(translations)
    merged["literal_translation"] = " ".join(literals)
    return merged


def _handle_compact_map_response(
    *,
    chunk_sentence: str,
    word_key_map: dict[str, str],
    word_meanings: dict[str, str] | None = None,
    previous_translation: str = "",
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
) -> dict[str, Any]:
    if verbose:
        pr.amber(
            "  Word→key disambiguation map detected — using it for scores, "
            "fetching translation only"
        )
    word_key_scores: dict[str, Any] = {
        key: {"score": 10} for key in word_key_map.values()
    }
    if word_meanings:
        for surface_word, key in word_key_map.items():
            contextual_meaning = word_meanings.get(surface_word)
            if isinstance(contextual_meaning, str) and contextual_meaning.strip():
                word_key_scores[key]["contextual_meaning"] = contextual_meaning.strip()
    ai_data: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": word_key_scores,
    }
    if progress:
        progress("ai_translation_start")
    translation_response = ai_manager.request(
        prompt=_build_translation_prompt(
            chunk_sentence,
            list(word_key_map),
            previous_translation=previous_translation,
        ),
        model=model,
        provider_preference=provider,
        prompt_sys=(
            "Return only a JSON object with translation, literal_translation, "
            f"and meanings. No prose. No markdown. {NO_TOOLS_INSTRUCTION}"
        ),
    )
    if progress:
        progress("ai_translation_done")
    if verbose:
        pr.green(f"  Translation response: {translation_response.status_message}")
    translation_data: dict[str, Any] = {}
    translation_error = ""
    if translation_response.content:
        translation_data, translation_error = _parse_ai_json(
            translation_response.content
        )
        if isinstance(translation_data, dict):
            ai_data["translation"] = translation_data.get("translation", "") or ""
            ai_data["literal_translation"] = (
                translation_data.get("literal_translation", "") or ""
            )
            meanings = translation_data.get("meanings", {})
            if isinstance(meanings, dict):
                for surface_word, key in word_key_map.items():
                    contextual_meaning = meanings.get(surface_word)
                    if (
                        isinstance(contextual_meaning, str)
                        and contextual_meaning.strip()
                    ):
                        word_key_scores[key]["contextual_meaning"] = (
                            contextual_meaning.strip()
                        )
    if debug is not None:
        debug["translation_raw_response"] = translation_response.content
        debug["translation_status_message"] = translation_response.status_message
        debug["translation_parsed_response"] = copy.deepcopy(translation_data)
        debug["translation_parse_error"] = translation_error
    return ai_data


def _handle_reformat_response(
    *,
    chunk_sentence: str,
    raw_response: str,
    analysis: list[dict[str, Any]],
    ai_data: dict[str, Any],
    parse_error: str,
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
) -> dict[str, Any]:
    if verbose:
        if parse_error:
            pr.amber(f"  Non-JSON response — parse error: {parse_error}")
        else:
            pr.amber(
                "  Valid JSON but wrong schema — "
                f"scores key is {type(ai_data.get('scores')).__name__}, expected dict"
            )
        pr.amber("  Full raw response:")
        pr.amber(raw_response)
        pr.amber("  Reformatting...")
    if progress:
        progress("ai_reformat_start")
    reformat_response = ai_manager.request(
        prompt=_build_reformat_prompt(
            chunk_sentence,
            raw_response,
            _word_keys_overview(analysis),
        ),
        model=model,
        provider_preference=provider,
        prompt_sys=(
            "Return only a valid JSON object. No prose. No markdown. "
            f"{NO_TOOLS_INSTRUCTION}"
        ),
    )
    if progress:
        progress("ai_reformat_done")
    if verbose:
        pr.green(f"  Reformat response: {reformat_response.status_message}")
    if reformat_response.content:
        reformat_data, reformat_error = _parse_ai_json(reformat_response.content)
        reformat_scores = reformat_data.get("scores")
        reformat_ok = not reformat_error and isinstance(reformat_scores, dict)
        if reformat_ok:
            reformat_scores = cast(dict[str, Any], reformat_scores)
            if not parse_error and not _wrong_schema_has_meaning_evidence(ai_data):
                _strip_reformat_context_fields(reformat_scores)
            salvaged_scores = ai_data.get("scores")
            if isinstance(salvaged_scores, dict) and salvaged_scores:
                reformat_data["scores"] = {
                    **reformat_scores,
                    **salvaged_scores,
                }
            ai_data = reformat_data
            if verbose:
                pr.yes("  Reformat succeeded — scores dict present")
        else:
            if verbose:
                pr.no(
                    f"  Reformat failed — parse_error={reformat_error!r}, "
                    f"scores type={type(reformat_data.get('scores')).__name__}"
                )
        if debug is not None:
            debug["reformat_raw_response"] = reformat_response.content
            debug["reformat_status_message"] = reformat_response.status_message
            debug["reformat_parsed_response"] = copy.deepcopy(reformat_data)
            debug["reformat_parse_error"] = reformat_error

    return ai_data


def _request_first_pass(
    chunk_sentence: str,
    full_sentence: str,
    analysis: list[dict[str, Any]],
    ai_manager: AIManager,
    model: str | None,
    provider: str | None,
    speech_mark_options: dict[str, list[str]] | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
    previous_translation: str = "",
) -> dict[str, Any]:
    sys_prompt = build_system_prompt(analysis, speech_mark_options)
    continuation_block = _previous_translation_block(previous_translation)
    if chunk_sentence == full_sentence:
        user_prompt = f"Return JSON for: {chunk_sentence}"
    else:
        user_prompt = (
            f"Return JSON for: {chunk_sentence}\n"
            "Full passage for context (score ONLY the words in your part): "
            f"{full_sentence}"
        )
    if continuation_block:
        user_prompt = f"{user_prompt}{continuation_block}"
    if debug is not None:
        debug["chunk_sentence"] = chunk_sentence
        debug["system_prompt"] = sys_prompt
        debug["user_prompt"] = user_prompt

    if progress:
        progress("ai_start")
    response = ai_manager.request(
        prompt=user_prompt,
        model=model,
        provider_preference=provider,
        prompt_sys=sys_prompt,
    )
    if progress:
        progress("ai_done")

    if not response.content:
        raise ValueError(f"AI Request Failed: {response.status_message}")

    if verbose:
        pr.green(f"  AI response: {response.status_message}")

    ai_data, parse_error = _parse_ai_json(response.content)
    if debug is not None:
        debug["raw_response"] = response.content
        debug["status_message"] = response.status_message
        debug["parsed_response"] = copy.deepcopy(ai_data)
        debug["parse_error"] = parse_error

    word_key_map = _extract_word_key_map(ai_data, analysis) if not parse_error else None
    word_meanings: dict[str, str] = {}
    if word_key_map is None and not parse_error:
        structured = _extract_structured_selection_map(ai_data, analysis)
        if structured is not None:
            word_key_map, word_meanings = structured
    if word_key_map is None and not parse_error:
        selected_keys = _extract_selected_keys_map(ai_data, analysis)
        if selected_keys is not None:
            word_key_map, word_meanings = selected_keys

    if word_key_map is not None:
        ai_data = _handle_compact_map_response(
            chunk_sentence=chunk_sentence,
            word_key_map=word_key_map,
            word_meanings=word_meanings,
            previous_translation=previous_translation,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            progress=progress,
            verbose=verbose,
            debug=debug,
        )
        needs_reformat = False
    else:
        needs_reformat = bool(
            parse_error or not isinstance(ai_data.get("scores"), dict)
        )

    if needs_reformat and response.content:
        ai_data = _handle_reformat_response(
            chunk_sentence=chunk_sentence,
            raw_response=response.content,
            analysis=analysis,
            ai_data=ai_data,
            parse_error=parse_error,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            progress=progress,
            verbose=verbose,
            debug=debug,
        )

    return ai_data


def translate_sentence(
    sentence: str,
    db_session: Session,
    ai_manager: AIManager | None = None,
    model: str | None = None,
    provider: str | None = None,
    verse_source: str | None = None,
    speech_mark_options: dict[str, list[str]] | None = None,
    progress: Callable[[str], None] | None = None,
    verbose: bool = False,
    debug: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full pipeline: Analyze → AI Translate → Merge. Returns the enriched analysis object."""
    if ai_manager is None:
        ai_manager = AIManager()

    resolved_sentence, extracted_options = extract_variant_options(sentence)
    if speech_mark_options:
        speech_mark_options = {**extracted_options, **speech_mark_options}
    else:
        speech_mark_options = extracted_options or None

    if progress:
        progress("json_start")
    analysis = cast(
        list[dict[str, Any]], analyze_sentence(resolved_sentence, db_session)
    )

    if verse_source:
        pre_match_db_examples(analysis, verse_source, resolved_sentence)

    if progress:
        progress("json_done")

    chunks, use_grounded_fallback = _split_into_sentence_chunks(
        resolved_sentence,
        analysis,
        MAX_FIRST_CONTEXT_CHARS,
    )
    if len(chunks) == 1:
        ai_data = _request_first_pass(
            resolved_sentence,
            resolved_sentence,
            analysis,
            ai_manager,
            model,
            provider,
            speech_mark_options,
            progress,
            verbose,
            debug,
        )
    else:
        chunk_debugs: list[dict[str, Any]] = []
        chunk_datas: list[dict[str, Any]] = []
        previous_translation_parts: list[str] = []
        last_chunk_error: ValueError | None = None
        for chunk_index, (chunk_text, chunk_analysis) in enumerate(chunks, start=1):
            chunk_data: dict[str, Any] | None = None
            chunk_debug: dict[str, Any] | None = None
            first_error: ValueError | None = None
            previous_translation = " ".join(previous_translation_parts)
            for attempt in range(1, CHUNK_FIRST_PASS_ATTEMPTS + 1):
                attempt_debug: dict[str, Any] | None = {} if debug is not None else None
                try:
                    chunk_data = _request_first_pass(
                        chunk_text,
                        resolved_sentence,
                        chunk_analysis,
                        ai_manager,
                        model,
                        provider,
                        speech_mark_options,
                        progress,
                        verbose,
                        attempt_debug,
                        previous_translation=previous_translation,
                    )
                except ValueError as error:
                    if attempt == 1:
                        first_error = error
                    last_chunk_error = error
                    if attempt < CHUNK_FIRST_PASS_ATTEMPTS:
                        continue
                    if debug is not None:
                        error_debug = attempt_debug if attempt_debug is not None else {}
                        error_debug.setdefault("chunk_sentence", chunk_text)
                        if first_error is not None:
                            error_debug["chunk_error_attempt_1"] = str(first_error)
                        error_debug["chunk_error"] = str(error)
                        chunk_debugs.append(error_debug)
                    if verbose:
                        pr.amber(
                            f"  Skipping chunk {chunk_index}/{len(chunks)} after AI failure: {error}"
                        )
                    break
                else:
                    chunk_debug = attempt_debug
                    if chunk_debug is not None and first_error is not None:
                        chunk_debug["chunk_error_attempt_1"] = str(first_error)
                    break
            if chunk_data is None:
                continue
            normalized_chunk_data = _normalize_ai_response(chunk_data)
            chunk_datas.append(normalized_chunk_data)
            _append_unique_text_part(
                previous_translation_parts,
                normalized_chunk_data.get("translation"),
            )
            if chunk_debug is not None:
                chunk_debugs.append(chunk_debug)
        if not chunk_datas and last_chunk_error is not None:
            raise last_chunk_error
        ai_data = _merge_chunk_ai_data(chunk_datas)
        if debug is not None:
            debug["chunk_requests"] = chunk_debugs

    if debug is not None:
        debug["retry_requests"] = []

    ai_data = _normalize_ai_response(ai_data)
    scores_map = ai_data.setdefault("scores", {})
    if not isinstance(scores_map, dict):
        scores_map = {}
        ai_data["scores"] = scores_map
    _apply_deterministic_scores_to_map(analysis, scores_map)

    missing_groups = _find_missing_score_groups(analysis, scores_map)
    if debug is not None:
        debug["missing_score_groups_after_first_response"] = missing_groups
    retry_skipped_groups: list[dict[str, Any]] = []
    if missing_groups:
        retry_skipped_groups = _request_missing_score_retry_pass(
            resolved_sentence=resolved_sentence,
            missing_groups=missing_groups,
            scores_map=scores_map,
            ai_manager=ai_manager,
            model=model,
            provider=provider,
            debug=debug,
            pass_number=1,
        )
        missing_groups_after_retry = _find_missing_score_groups(analysis, scores_map)
        if missing_groups_after_retry:
            retry_skipped_groups = _request_missing_score_retry_pass(
                resolved_sentence=resolved_sentence,
                missing_groups=missing_groups_after_retry,
                scores_map=scores_map,
                ai_manager=ai_manager,
                model=model,
                provider=provider,
                debug=debug,
                pass_number=2,
            )

    _narrow_db_example_tied_groups(analysis, scores_map)

    if debug is not None:
        if retry_skipped_groups:
            debug["retry_skipped_groups"] = retry_skipped_groups
        debug["missing_score_groups_after_retry"] = _find_missing_score_groups(
            analysis, scores_map
        )
        debug["final_scores"] = copy.deepcopy(scores_map)
    merged = merge_ai_selections(analysis, ai_data)

    if use_grounded_fallback:
        word_table = format_markdown_table(merged["analysis"])
        grounded_prompt = _build_grounded_translation_prompt(
            resolved_sentence, word_table
        )
        grounded_response = ai_manager.request(
            prompt=grounded_prompt,
            prompt_sys="",
            model=model,
            provider_preference=provider,
        )
        if grounded_response.content:
            try:
                grounded_data = json.loads(grounded_response.content)
                if isinstance(grounded_data, dict):
                    if isinstance(grounded_data.get("translation"), str):
                        merged["translation"] = grounded_data["translation"]
                    if isinstance(grounded_data.get("literal_translation"), str):
                        merged["literal_translation"] = grounded_data[
                            "literal_translation"
                        ]
            except (json.JSONDecodeError, AttributeError):
                pass  # keep concatenated word-level translations on failure

    merged["speech_mark_options"] = speech_mark_options or {}
    merged["variant_choices"] = ai_data.get("variant_choices", {})
    if speech_mark_options:
        merged["verse_text"] = apply_variant_choices(
            sentence,
            speech_mark_options,
            merged["variant_choices"],
        )
        merged["analysis"] = sync_analysis_words_to_sentence(
            merged["analysis"],
            merged["verse_text"],
        )
    return merged
