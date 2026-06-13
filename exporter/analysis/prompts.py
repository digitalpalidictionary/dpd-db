"""Prompt builders and shared constants for the Pāḷi translation pipeline."""

import json
import re
from typing import Any

from ._base import _is_deconstruction_key, _retry_prompt_groups

# ~300–360k tokens: deep headroom inside a 1M-token window; sized to model capacity,
# not the old argv transport ceiling.
MAX_FIRST_CONTEXT_CHARS = 900_000

REFORMAT_MAX_CHARS = 3000

REFORMAT_KEYS_MAX_CHARS = 6000

MAX_RETRY_CONTEXT_CHARS = 60_000

MAX_RETRY_BATCHES = 8

CHUNK_FIRST_PASS_ATTEMPTS = 2

PREVIOUS_TRANSLATION_CONTEXT_CHARS = 1200

NO_TOOLS_INSTRUCTION = (
    "Do not use tools, do not plan tasks, and do not wait for anything. "
    "Produce the complete JSON directly in this single response."
)

NO_GRAMMAR_NOTES_INSTRUCTION = (
    "Provide ONLY the core meaning. Do NOT append grammatical case notes in "
    "parentheses."
)

COMMON_PALI_RULES = """### Common Pāḷi Disambiguation Rules:
- In the stock phrase `kāyassa bhedā paraṃ maraṇā`, `kāyassa` is genitive, `bhedā` and `maraṇā` are ablative singular, and `paraṃ` is the indeclinable preposition "after" — never nominative plurals.
- Final-vowel lengthening before quotative `'ti` is sandhi: prefer the deconstruction restoring the short final vowel (e.g., `upapajjanti + iti`) at the end of a quotation unless context clearly requires a long-vowel reading.
- In `yena <person/place> tena upasaṅkami`, `yena` and `tena` are adverbial "where ... there" rows, not plain instrumental pronouns.
- Inside direct speech, a comma-set-off word addressing the listener (e.g., `bho` or a teacher's name) is usually vocative.
- Counted time-spans such as `paṇṇavīsativassāni` / `vassāni` ("for twenty-five years") are accusative of duration, not nominative.
- When dative and genitive variants of the same surface form are offered, prefer the genitive for possession or relation ("of X"); select dative only when the context expresses a recipient, purpose, or benefit ("for/to X").
"""

_TRAILING_PUNCTUATION = '.,;:!?)]}”’"'

_RETRY_OPTION_FIELDS = (
    "key",
    "id",
    "pali",
    "pos",
    "grammar",
    "meaning_1",
    "meaning_combo",
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_SELECTION_LIST_KEYS = ("disambiguation", "sentence_analysis", "selected_meanings")

_SELECTION_KEY_FIELDS = ("selected_key", "selected_lemma_key", "key")

_FINITE_VERB_GRAMMAR_RE = re.compile(
    r"\b(?:pr|aor|fut|cond|imp|opt)\s+\d(?:st|nd|rd)\b"
)

_QUOTATIVE_TI_SELECTION_SOURCE = "deterministic_quotative_ti_deconstruction"

_PARENT_MEANING_TOKEN_RE = re.compile(r"[a-z][a-z'’-]*")

_PARENT_MEANING_STOPWORDS = {"of", "the", "a", "an", "to", "in", "is", "one's"}

_OCCURRENCE_KEY_PREFIX_RE = re.compile(r"^w\d+_(.+)$")

_RETRY_EQUIVALENT_KEY_GROUPS = "_equivalent_missing_key_groups"

_DECONSTRUCTED_PLACEHOLDER = "[Deconstructed]"

_DB_EXAMPLE_ALL_VARIANTS_TIED_SOURCE = "db_example_all_variants_tied"

_DB_EXAMPLE_VARIANT_NOT_SELECTED_SOURCE = "db_example_variant_not_selected"


def _previous_translation_block(previous_translation: str) -> str:
    normalized = re.sub(r"\s+", " ", previous_translation).strip()
    if not normalized:
        return ""
    context = normalized[-PREVIOUS_TRANSLATION_CONTEXT_CHARS:]
    return (
        "\n\nEarlier sentences of this passage were already translated as:\n"
        f"{context}\n"
        "Translate ONLY the Pāḷi text given above, as a continuation. Do not "
        "repeat already-translated sentences. Keep names, forms of address "
        "(e.g. 'monks'), and recurring terminology consistent with the earlier "
        "translation."
    )


def _word_keys_overview(analysis: list[dict[str, Any]]) -> str:
    """Build a compact top-level option-key map for the reformat prompt."""
    word_keys: dict[str, list[str]] = {}
    for token_data in analysis:
        word = token_data.get("word")
        options = token_data.get("data", [])
        if not isinstance(word, str) or not word or not isinstance(options, list):
            continue

        keys = word_keys.setdefault(word, [])
        for option in options:
            if not isinstance(option, dict):
                continue
            key = option.get("key")
            if not isinstance(key, str):
                continue
            seen_keys = {display_key.split(" ", 1)[0] for display_key in keys}
            if key in seen_keys:
                continue
            grammar = option.get("grammar")
            if isinstance(grammar, str) and grammar.strip():
                keys.append(f"{key} ({grammar.strip()})")
            else:
                keys.append(key)

        if not keys:
            word_keys.pop(word, None)

    if not word_keys:
        return ""

    overview = json.dumps(word_keys, ensure_ascii=False, separators=(",", ":"))
    if len(overview) > REFORMAT_KEYS_MAX_CHARS:
        return ""
    return overview


def _build_translation_prompt(
    sentence: str,
    surface_words: list[str] | None = None,
    previous_translation: str = "",
) -> str:
    """Build a lightweight translation-only follow-up prompt.

    Used when the first call returned a usable word→key map but no translation; we only
    need the prose and contextual meanings, so this prompt is small and does not re-send
    the dictionary context.
    """
    surface_words_instruction = ""
    if surface_words:
        surface_words_json = json.dumps(surface_words, ensure_ascii=False)
        surface_words_instruction = (
            f"\nUse exactly these surface-word keys in meanings: {surface_words_json}\n"
        )
    continuation_block = _previous_translation_block(previous_translation)
    continuation_section = f"{continuation_block}\n\n" if continuation_block else ""
    return (
        f'Translate this Pāḷi sentence into English: "{sentence}"\n\n'
        f"{continuation_section}"
        "Return ONLY a JSON object with these three keys and nothing else:\n"
        "{\n"
        '  "translation": "Fluent English translation of the sentence",\n'
        '  "literal_translation": "Literal word-by-word English translation",\n'
        '  "meanings": {"surface_word": "short contextual English meaning"}\n'
        "}\n"
        f"{surface_words_instruction}"
        f"{NO_GRAMMAR_NOTES_INSTRUCTION}\n"
        "No prose, no markdown fences, no scores."
    )


def _build_reformat_prompt(
    sentence: str,
    prose_response: str,
    word_keys_json: str = "",
) -> str:
    """Build a follow-up prompt asking the AI to reformat its response into the required JSON schema."""
    keys_block = ""
    if word_keys_json:
        keys_block = (
            '\n\nValid option keys per word (entries may be shown as "key (grammar)"; '
            'keys in "scores" MUST use the key before the first space):\n'
            f"{word_keys_json}"
        )

    return (
        f'Your previous response for the Pāḷi sentence "{sentence}" did not match '
        "the required format. Please reformat it as a JSON object matching this structure exactly:\n\n"
        "{\n"
        '  "translation": "Fluent English translation of the sentence",\n'
        '  "literal_translation": "Literal word-by-word English translation",\n'
        '  "scores": {\n'
        '    "w0_12345_0": {"score": 10, "contextual_meaning": "..."},\n'
        "    ...\n"
        "  }\n"
        "}\n\n"
        "Extract the translation from your previous analysis and convert each selected "
        "lemma to a score entry of 10 with its key. "
        f"{NO_GRAMMAR_NOTES_INSTRUCTION} "
        "Do not invent contextual_meaning; include contextual_meaning only when it "
        "appeared explicitly in the previous analysis for that selected word/key. "
        "Return only the JSON object. No prose, no markdown fences."
        f"{keys_block}\n\n"
        "Your previous analysis:\n"
        f"{prose_response[:REFORMAT_MAX_CHARS]}"
    )


def _build_missing_scores_prompt(
    sentence: str,
    missing_groups: list[dict[str, Any]],
) -> str:
    context = json.dumps(
        _retry_prompt_groups(missing_groups),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    has_decon = any(
        _is_deconstruction_key(key)
        for group in missing_groups
        for key in group.get("missing_keys", [])
    )
    decon_instruction = ""
    if has_decon:
        decon_instruction = (
            '\nFor deconstruction keys containing "decon_", you MUST include "contextual_meaning" '
            "with a full English translation of that sandhi/compound in the context of the sentence. "
            'Example: "w0_decon_okassa_0": {"score": 10, "contextual_meaning": "to the dwelling"}\n'
        )

    return f"""Please supply missing dictionary option scores for this Pāḷi sentence:
{sentence}

Only score the option keys in this focused context. Return JSON with a flat `scores`
object where each value is {{"score": N}} (an integer 0–10). Do not translate again and do not explain.
For the single best option per word (score 10), also include "contextual_meaning": a short English meaning fitted to this sentence.
{NO_GRAMMAR_NOTES_INSTRUCTION}
{decon_instruction}
{COMMON_PALI_RULES}
Missing dictionary option scores:
{context}
"""


def build_system_prompt(
    analysis: list[dict[str, Any]],
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, separators=(",", ":"))

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
        verse_text_field = '\n  "variant_choices": {"variant option key": 0},'

    prompt = f"""IMPORTANT: Your response MUST be a valid JSON object only. Do NOT write prose, markdown, explanations, or any text outside the JSON. Start your response with {{ and end with }}. {NO_TOOLS_INSTRUCTION}

You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to analyze a Pāḷi sentence and perform word-sense disambiguation using the provided dictionary analysis.

### Dictionary Context (Word-by-Word Analysis Options)
{context_str}

### Instructions:
1. **Analyze the Sentence:** Use the context to understand grammatical relationships.
2. **Disambiguate:** For each word in the sentence, identify the correct dictionary option (`key`). Some keys include a word-occurrence prefix; always echo the full key verbatim.
3. **Score Options:**
   - Assign a score of **10** to the correct `key` for the context.
   - If multiple keys share the same id, treat them as grammar variants; choose the variant whose grammar matches your parse because the score-10 variant's grammar is what readers see in the table.
   - Assign lower scores (1-9) only to genuinely plausible alternatives if there is ambiguity.
   - Do not list options you would score 0; omitted options are treated as unselected.
   - Assign **10** to the correct `key` for *components* of compounds as well.
4. **Contextualize:**
   - **`contextual_meaning`**: Adjust the dictionary `meaning_combo` to fit the grammar (e.g., "dwells" -> "I would dwell").
     - **CRITICAL:** Do this for the main word AND for any components that are **sandhi** (pos: "sandhi").
     - You do NOT need to adjust meanings for standard compound components unless necessary for clarity.
     - **CRITICAL:** Provide ONLY the core meaning. Do NOT append grammatical case notes in parentheses — never add phrases like "(masculine nominative plural of 'X')" or "(component of compound 'X')". The Grammar column already shows this information.
   - **`selected_pos`**: If `pos` is "sandhi/compound", specify "sandhi" or "compound".
5. **Handle Deconstructions (MANDATORY):** If an option key contains `decon_` or has `meaning_combo: "[Deconstructed]"`, you **MUST** provide a full English translation of that sandhi/compound in the `contextual_meaning` field.
   - **NEVER** leave a deconstruction key with a score of 10 without providing its `contextual_meaning`.
   - **Example:** If `okassa` is deconstructed as `oka + assa`, `contextual_meaning` should be something like "to the house" or "of the dwelling".
6. **Use Existing Examples for Disambiguation:**
   - Each option includes `example_1`/`source_1` and `example_2`/`source_2` — real curated examples from the dictionary that illustrate the exact meaning of that entry.
   - Options marked `db_example_match: true` already have this exact verse as their curated example. **Strongly prefer them** — they represent the editor-validated meaning for this context. Their `ai_score` is pre-set to 10; confirm by scoring them 10 in your output as well.
   - For options without `db_example_match`, use the examples to understand which meaning best fits the verse context before assigning scores.
{COMMON_PALI_RULES}
{disambiguation_block}
### Output Format:
Return a JSON object with translations and a flat map of **scores** keyed by the option `key`.

{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",{verse_text_field}
  "scores": {{
    "w0_decon_word_0": {{
      "score": 10,
      "contextual_meaning": "Full meaning of the deconstruction",
      "selected_pos": "sandhi"
    }},
    "w0_12345_0": {{
      "score": 10,
      "contextual_meaning": "I would dwell",
      "selected_pos": "verb"
    }}
  }}
}}
**CRITICAL:**
- **Keys in `scores` MUST match the `key` values in the Dictionary Context.**
- Only output the JSON object. Do not explain.
Your response MUST be exactly one JSON object with translation, literal_translation, and scores.
"""
    return prompt


def _build_grounded_translation_prompt(
    sentence: str,
    word_table_md: str,
) -> str:
    """Build a prompt asking only for translation + literal_translation grounded in the chosen senses.

    Used as a fallback when a single sentence's JSON alone exceeds MAX_FIRST_CONTEXT_CHARS.
    The word table comes from format_markdown_table(merged["analysis"]) — the already-scored
    word senses — so the translation is grounded rather than free-formed.
    """
    return (
        f"{NO_TOOLS_INSTRUCTION}\n\n"
        "You are a Pāḷi translator. Using ONLY the word senses provided in the table "
        "below, translate the Pāḷi sentence into natural English. "
        "Do not introduce senses not listed.\n\n"
        f"Sentence:\n{sentence}\n\n"
        f"Chosen word senses:\n{word_table_md}\n\n"
        "Return a JSON object with exactly two keys:\n"
        '{"translation": "<natural English>", "literal_translation": "<word-by-word>"}'
    )
