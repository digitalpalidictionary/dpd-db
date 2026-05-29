"""Shared prompt-building and analysis utilities for Pāḷi AI translation."""

import copy
import json
import re
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from exporter.analysis.analyzer import analyze_sentence, tokenize_sentence
from tools.ai_manager import AIManager


def extract_variant_options(text: str) -> tuple[str, dict[str, list[str]]]:
    """Resolve GUI-style // variants to first choices and collect options."""
    parts = re.split(r"(\s+)", text)
    options: dict[str, list[str]] = {}
    resolved_parts: list[str] = []
    trailing_punctuation = ".,;:!?)]}”’\""

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in trailing_punctuation:
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
    trailing_punctuation = ".,;:!?)]}”’\""

    for part in parts:
        if "//" not in part:
            resolved_parts.append(part)
            continue

        suffix = ""
        core = part
        while core and core[-1] in trailing_punctuation:
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


def _normalize_ai_response(ai_data: dict[str, Any]) -> dict[str, Any]:
    """Fix malformed AI responses with nested 'scores' keys.

    Some AI models return scores in a nested structure like {"scores": {"scores": {...}}}.
    This function flattens that to the expected {"scores": {...}} format.
    """
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
    return ai_data


def _clean_meaning(meaning: str) -> str:
    """Strip trailing grammar parentheticals that duplicate the Grammar column.

    Removes patterns like '(masculine nominative plural of 'X')' and
    '(component of compound 'X')' that the AI inherits from DPD meaning_combo.
    """
    return re.sub(r"\s*\([^)]*'[^']+'\)\s*$", "", meaning).strip()


def _normalize_example_text(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = text.replace("'", "")
    text = re.sub(r"[^\w]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _texts_overlap(first_text: str, second_text: str) -> bool:
    first = _normalize_example_text(first_text)
    second = _normalize_example_text(second_text)
    return bool(first and second and (first in second or second in first))


def _iter_options(options: list[dict[str, Any]]):
    for option in options:
        yield option
        for component_group in option.get("components", []):
            if isinstance(component_group, list):
                yield from _iter_options(component_group)


def pre_match_db_examples(
    analysis: list[dict[str, Any]],
    verse_source: str,
    verse_text: str,
) -> None:
    """Mark options whose curated example text overlaps the analyzed passage."""
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


def _apply_deterministic_scores_to_map(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> None:
    for token_data in analysis:
        for option in _iter_options(token_data.get("data", [])):
            key = option.get("key")
            score = option.get("ai_score")
            if key and option.get("db_example_match") and isinstance(score, int | float):
                scores_map[key] = {
                    "score": score,
                    "selection_source": option.get("selection_source", "deterministic"),
                }
            elif key and key not in scores_map and isinstance(score, int | float):
                scores_map[key] = {
                    "score": score,
                    "selection_source": option.get("selection_source", "deterministic"),
                }


def _find_missing_score_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> list[dict[str, Any]]:
    missing_groups: list[dict[str, Any]] = []

    def inspect_group(
        word: str,
        options: list[dict[str, Any]],
        context: str,
    ) -> None:
        if not options:
            return
        option_keys = [
            option.get("key")
            for option in options
            if isinstance(option.get("key"), str)
        ]
        if option_keys and not any(key in scores_map for key in option_keys):
            missing_groups.append(
                {
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
            )

        for option in options:
            option_context = str(option.get("pali") or option.get("key") or context)
            for component_group in option.get("components", []):
                if isinstance(component_group, list):
                    inspect_group(word, component_group, option_context)

    for token_data in analysis:
        word = str(token_data.get("word", ""))
        inspect_group(word, token_data.get("data", []), word)

    return missing_groups


def _build_missing_scores_prompt(
    sentence: str,
    missing_groups: list[dict[str, Any]],
) -> str:
    context = json.dumps(missing_groups, ensure_ascii=False, indent=2)
    return f"""Please supply missing dictionary option scores for this Pāḷi sentence:
{sentence}

Only score the option keys in this focused context. Return JSON with a flat `scores`
object. Do not translate again and do not explain.

Missing dictionary option scores:
{context}
"""


def translate_sentence(
    sentence: str,
    db_session: Session,
    ai_manager: AIManager | None = None,
    model: str | None = None,
    verse_source: str | None = None,
    speech_mark_options: dict[str, list[str]] | None = None,
    progress: Callable[[str], None] | None = None,
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
    analysis = analyze_sentence(resolved_sentence, db_session)

    if verse_source:
        pre_match_db_examples(analysis, verse_source, resolved_sentence)

    sys_prompt = build_system_prompt(analysis, speech_mark_options)
    user_prompt = f"Please translate and analyze: {resolved_sentence}"
    if debug is not None:
        debug["system_prompt"] = sys_prompt
        debug["user_prompt"] = user_prompt
        debug["retry_requests"] = []
    if progress:
        progress("json_done")

    if progress:
        progress("ai_start")
    response = ai_manager.request(
        prompt=user_prompt,
        model=model,
        prompt_sys=sys_prompt,
    )
    if progress:
        progress("ai_done")

    if not response.content:
        raise ValueError(f"AI Request Failed: {response.status_message}")

    ai_data, parse_error = _parse_ai_json(response.content)
    if debug is not None:
        debug["raw_response"] = response.content
        debug["status_message"] = response.status_message
        debug["parsed_response"] = ai_data
        debug["parse_error"] = parse_error

    ai_data = _normalize_ai_response(ai_data)
    scores_map = ai_data.setdefault("scores", {})
    if not isinstance(scores_map, dict):
        scores_map = {}
        ai_data["scores"] = scores_map
    _apply_deterministic_scores_to_map(analysis, scores_map)

    missing_groups = _find_missing_score_groups(analysis, scores_map)
    if debug is not None:
        debug["missing_score_groups_after_first_response"] = missing_groups
    if missing_groups:
        retry_prompt = _build_missing_scores_prompt(resolved_sentence, missing_groups)
        retry_response = ai_manager.request(
            prompt=retry_prompt,
            model=model,
            prompt_sys="Return only JSON with a flat `scores` object.",
        )
        retry_data: dict[str, Any] = {}
        retry_parse_error = ""
        if retry_response.content:
            retry_data, retry_parse_error = _parse_ai_json(retry_response.content)
            retry_data = _normalize_ai_response(retry_data)
            retry_scores = retry_data.get("scores", {})
            if isinstance(retry_scores, dict):
                scores_map.update(retry_scores)
        if debug is not None:
            debug["retry_requests"].append(
                {
                    "prompt": retry_prompt,
                    "raw_response": retry_response.content,
                    "status_message": retry_response.status_message,
                    "parsed_response": retry_data,
                    "parse_error": retry_parse_error,
                    "missing_keys": [
                        key
                        for group in missing_groups
                        for key in group["missing_keys"]
                    ],
                }
            )

    if debug is not None:
        debug["final_scores"] = scores_map
    merged = merge_ai_selections(analysis, ai_data)
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


def generate_markdown_report(
    merged_result: dict[str, Any],
    sentence: str,
    verse_id: str = "",
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Render a merged analysis result as a markdown document."""
    if speech_mark_options is None:
        speech_mark_options = merged_result.get("speech_mark_options") or None
    if speech_mark_options:
        display_sentence = apply_variant_choices(
            sentence,
            speech_mark_options,
            merged_result.get("variant_choices"),
        )
    else:
        display_sentence = sentence
    display_analysis = sync_analysis_words_to_sentence(
        merged_result["analysis"],
        display_sentence,
    )

    if verse_id:
        parts: list[str] = [f"# Analysis of: {verse_id}", display_sentence]
    else:
        parts = [f"# Analysis of: {display_sentence}"]
    parts += [
        "### English Translation",
        f"**Translation:** {merged_result.get('translation', '')}",
        f"**Literal Translation:** {merged_result.get('literal_translation', '')}",
    ]
    if speech_mark_options:
        variant_lines = [
            "//".join(variants) for variants in speech_mark_options.values()
        ]
        parts += ["### Variants", "\n\n".join(variant_lines)]
    parts += [
        "### Word-by-Word Analysis",
        format_markdown_table(display_analysis),
    ]
    return "\n\n".join(parts)


def build_system_prompt(
    analysis: list[dict[str, Any]],
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, indent=2)

    disambiguation_block = ""
    verse_text_field = ""
    if speech_mark_options:
        options_lines = "\n".join(
            f"- '{word}': {variants}" for word, variants in speech_mark_options.items()
        )
        disambiguation_block = f"""
### Passage Text Disambiguation
The following words in this passage have multiple possible apostrophe/hyphen/sandhi forms.
Based on your grammatical analysis, choose the correct form for each. Return only the
zero-based option index for each key in the `variant_choices` field. Do not return the
full passage text.
{options_lines}
"""
        verse_text_field = (
            '\n  "variant_choices": {"variant option key": 0},'
        )

    prompt = f"""You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to analyze a Pāḷi sentence and perform word-sense disambiguation using the provided dictionary analysis.

### Dictionary Context (Word-by-Word Analysis Options)
{context_str}

### Instructions:
1. **Analyze the Sentence:** Use the context to understand grammatical relationships.
2. **Disambiguate:** For each word in the sentence, identify the correct dictionary option (`key`).
3. **Score Options:**
   - Assign a score of **10** to the correct `key` for the context.
   - Assign lower scores (0-9) to alternative options if there is ambiguity.
   - Assign **10** to the correct `key` for *components* of compounds as well.
4. **Contextualize:**
   - **`contextual_meaning`**: Adjust the dictionary `meaning_combo` to fit the grammar (e.g., "dwells" -> "I would dwell").
     - **CRITICAL:** Do this for the main word AND for any components that are **sandhi** (pos: "sandhi").
     - You do NOT need to adjust meanings for standard compound components unless necessary for clarity.
     - **CRITICAL:** Provide ONLY the core meaning. Do NOT append grammatical case notes in parentheses — never add phrases like "(masculine nominative plural of 'X')" or "(component of compound 'X')". The Grammar column already shows this information.
   - **`selected_pos`**: If `pos` is "sandhi/compound", specify "sandhi" or "compound".
5. **Handle Deconstructions (MANDATORY):** If an option key starts with `decon_` or has `meaning_combo: "[Deconstructed]"`, you **MUST** provide a full English translation of that sandhi/compound in the `contextual_meaning` field.
   - **NEVER** leave a `decon_` key with a score of 10 without providing its `contextual_meaning`.
   - **Example:** If `okassa` is deconstructed as `oka + assa`, `contextual_meaning` should be something like "to the house" or "of the dwelling".
6. **Use Existing Examples for Disambiguation:**
   - Each option includes `example_1`/`source_1` and `example_2`/`source_2` — real curated examples from the dictionary that illustrate the exact meaning of that entry.
   - Options marked `db_example_match: true` already have this exact verse as their curated example. **Strongly prefer them** — they represent the editor-validated meaning for this context. Their `ai_score` is pre-set to 10; confirm by scoring them 10 in your output as well.
   - For options without `db_example_match`, use the examples to understand which meaning best fits the verse context before assigning scores.
{disambiguation_block}
### Output Format:
Return a JSON object with translations and a flat map of **scores** keyed by the option `key`.

```json
{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",{verse_text_field}
  "scores": {{
    "decon_word_0": {{
      "score": 10,
      "contextual_meaning": "Full meaning of the deconstruction",
      "selected_pos": "sandhi"
    }},
    "12345_0": {{
      "score": 10,
      "contextual_meaning": "I would dwell",
      "selected_pos": "verb"
    }}
  }}
}}
```
**CRITICAL:**
- **Keys in `scores` MUST match the `key` values in the Dictionary Context.**
- Only output the JSON object. Do not explain.
"""
    return prompt


def _is_numeric_score(score: Any) -> bool:
    return isinstance(score, int | float) and not isinstance(score, bool)


def _direct_key_rank(option: dict[str, Any]) -> int:
    key = str(option.get("key", ""))
    if not key or key.startswith(("decon_", "missing_")):
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


def _option_rank(option: dict[str, Any], is_component: bool = False) -> tuple:
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
        component_pos_rank,
        _dictionary_quality_rank(option),
        option.get("score", 0),
        stable_id_rank,
    )


def _select_best_option(
    options: list[dict[str, Any]],
    is_component: bool = False,
) -> dict[str, Any] | None:
    return max(
        options,
        key=lambda option: _option_rank(option, is_component=is_component),
        default=None,
    )


def format_markdown_table(enriched_analysis: list[dict[str, Any]]) -> str:
    """
    Reconstruct the Markdown table using the enriched Python structure.
    We iterate through the Python data (which contains all components)
    and simply pick the highest-scored option to display.
    """

    table_rows = [
        "| ID | Word in Sentence | Grammar | Meaning | Construction | Root |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def add_rows_recursive(option: dict[str, Any], depth: int, parent_pos: str = ""):
        if "components" in option:
            for part_options in option["components"]:
                if not part_options:
                    continue

                # Each part has multiple lookups (homonyms). Pick the best scored one.
                # If all options have the same ai_score (e.g., 0 for sub-components),
                # prefer noun forms when parent is a noun compound.
                best_part = _select_best_option(part_options, is_component=True)
                if not best_part:
                    continue

                # Format component row
                clean_comp_word = best_part.get("pali", "").replace("- ", "").strip()
                indent_prefix = "- " * depth

                comp_meaning = best_part.get("meaning_combo", "")

                # Cleanup if AI failed to provide a meaning for a deconstruction
                if not comp_meaning and best_part.get("key", "").startswith("decon_"):
                    comp_meaning = "*(AI analysis of deconstruction)*"

                comp_meaning = _clean_meaning(comp_meaning)

                # Prefer grammar (for sandhi/comp vb), fallback to POS (for pure compound parts)
                comp_grammar = best_part.get("grammar") or best_part.get("pos", "")

                if "selected_pos" in best_part and best_part["selected_pos"]:
                    if comp_grammar == "sandhi/compound":
                        comp_grammar = best_part["selected_pos"]

                # Construction Column: prefer compound_construction if available, else construction
                comp_construction = best_part.get("compound_construction", "")
                if not comp_construction:
                    comp_construction = best_part.get("construction", "")
                # Clean up formatting if needed (though analyzer usually sends clean strings for construction)
                comp_construction = comp_construction.replace("<b>", "").replace(
                    "</b>", ""
                )

                table_rows.append(
                    f"| {best_part.get('id', '')} | {indent_prefix}{clean_comp_word} | {comp_grammar} | {comp_meaning} | {comp_construction} | {best_part.get('root_key', '')} |"
                )

                # Only recurse into components of real compounds/sandhi, not etymological breakdowns
                if (
                    best_part.get("compound_type", "")
                    or best_part.get("pos", "") in {"sandhi", "sandhi/compound"}
                    or best_part.get("key", "").startswith("decon_")
                ):
                    add_rows_recursive(best_part, depth + 1, best_part.get("pos", ""))

    for token_data in enriched_analysis:
        word = token_data["word"]
        options = token_data["data"]

        if not options:
            table_rows.append(f"| | {word} | | | | |")
            continue

        # Sort options by AI score (desc), then by completeness/original score
        # We assume 'ai_score' has been merged into the options. Default to 0.
        best_option = _select_best_option(options)
        if not best_option:
            table_rows.append(f"| | {word} | | | | |")
            continue

        # Determine values to display
        hw_id = best_option.get("id", "")
        meaning = best_option.get("meaning_combo", "")

        # Cleanup if AI failed to provide a meaning for a deconstruction
        if not meaning and best_option.get("key", "").startswith("decon_"):
            meaning = "*(AI analysis of deconstruction)*"

        meaning = _clean_meaning(meaning)

        grammar = best_option.get("grammar", "")

        # Handle POS override
        if "selected_pos" in best_option and best_option["selected_pos"]:
            if grammar == "sandhi/compound":
                grammar = best_option["selected_pos"]

        # Prepend adj POS when grammar exists but doesn't already label the word class
        if (
            best_option.get("pos", "") == "adj"
            and grammar
            and not grammar.startswith("adj")
        ):
            grammar = f"adj, {grammar}"

        # Construction Column: prefer compound_construction if available
        construction = best_option.get("compound_construction", "")
        if not construction:
            construction = best_option.get("construction", "")
        construction = construction.replace("<b>", "").replace("</b>", "")

        table_rows.append(
            f"| {hw_id} | {word} | {grammar} | {meaning} | {construction} | {best_option.get('root_key', '')} |"
        )

        # Start Recursion
        add_rows_recursive(best_option, 1, best_option.get("pos", ""))

    return "\n".join(table_rows)


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
                item["ai_score"] = update.get("score", 0)
                if "selection_source" in update:
                    item["selection_source"] = update["selection_source"]

                # Apply contextual info if score is positive (implying relevance)
                if update.get("score", 0) > 0:
                    if "contextual_meaning" in update:
                        item["meaning_combo"] = update["contextual_meaning"]
                    if "selected_pos" in update:
                        item["selected_pos"] = update["selected_pos"]
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
