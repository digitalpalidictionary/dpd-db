"""Markdown rendering helpers for Pāḷi study reports."""

from typing import Any

from ._base import _clean_meaning, _is_deconstruction_key
from .ai_response import _is_deconstructed_placeholder
from .ranking import _deconstruction_fallback_meaning, _select_best_option


def generate_markdown_report(
    merged_result: dict[str, Any],
    sentence: str,
    verse_id: str = "",
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Render a merged analysis result as a markdown document."""
    from .translate_core import apply_variant_choices, sync_analysis_words_to_sentence

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
                parent_meaning = option.get("meaning_combo", "")
                if not isinstance(parent_meaning, str):
                    parent_meaning = ""
                best_part = _select_best_option(
                    part_options,
                    is_component=True,
                    parent_meaning=parent_meaning,
                )
                if not best_part:
                    continue

                # Format component row
                clean_comp_word = best_part.get("pali", "").replace("- ", "").strip()
                indent_prefix = "- " * depth

                comp_meaning = best_part.get("meaning_combo", "")

                # Cleanup if AI failed to provide a meaning for a deconstruction
                if (
                    not comp_meaning or _is_deconstructed_placeholder(comp_meaning)
                ) and _is_deconstruction_key(best_part.get("key")):
                    comp_meaning = _deconstruction_fallback_meaning(best_part)

                comp_meaning = _clean_meaning(comp_meaning)

                # Prefer grammar (for sandhi/comp vb), fallback to POS (for pure compound parts)
                comp_grammar = best_part.get("grammar") or best_part.get("pos", "")

                if best_part.get("selected_pos") and comp_grammar == "sandhi/compound":
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
                    or _is_deconstruction_key(best_part.get("key"))
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
        if (
            not meaning or _is_deconstructed_placeholder(meaning)
        ) and _is_deconstruction_key(best_option.get("key")):
            meaning = _deconstruction_fallback_meaning(best_option)

        meaning = _clean_meaning(meaning)

        grammar = best_option.get("grammar", "")

        # Handle POS override
        if best_option.get("selected_pos") and grammar == "sandhi/compound":
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
