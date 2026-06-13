"""Test Pāḷi passage variant handling in AI analysis reports."""

import copy
import json
from typing import Any, cast

import pytest

from sqlalchemy.orm import Session

import exporter.analysis.translate_core as translate_core
from tools.ai_manager import AIManager
from exporter.analysis.translate_core import (
    _build_missing_scores_prompt,
    _extract_word_key_map,
    apply_variant_choices,
    build_system_prompt,
    extract_variant_options,
    format_markdown_table,
    generate_markdown_report,
    merge_ai_selections,
    pre_match_db_examples,
    sync_analysis_words_to_sentence,
    translate_sentence,
)


EXPECTED_NO_TOOLS_INSTRUCTION = (
    "Do not use tools, do not plan tasks, and do not wait for anything. "
    "Produce the complete JSON directly in this single response."
)


def test_extract_variant_options_resolves_default_text_and_options() -> None:
    text = (
        "jarāmaraṇaṃ "
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā//"
        "sokaparidevadukkhadomanassupāyāsā sambhavan'ti//sambhavanti."
    )

    resolved, options = extract_variant_options(text)

    assert resolved == (
        "jarāmaraṇaṃ soka-parideva-dukkha-domanass'upāyāsā sambhavan'ti."
    )
    assert options == {
        "soka-parideva-dukkha-domanass'upāyāsā": [
            "soka-parideva-dukkha-domanass'upāyāsā",
            "sokaparidevadukkhadomanass'upāyāsā",
            "sokaparidevadukkhadomanassupāyāsā",
        ],
        "sambhavan'ti": ["sambhavan'ti", "sambhavanti"],
    }


def test_generate_markdown_report_uses_ai_variant_choice_and_prints_options() -> None:
    merged_result = {
        "translation": "They arise.",
        "literal_translation": "They come into being.",
        "variant_choices": {"sambhavan'ti": 1},
        "analysis": [],
    }
    original_sentence = (
        "jarāmaraṇaṃ "
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā sambhavan'ti//sambhavanti."
    )
    variants = {
        "soka-parideva-dukkha-domanass'upāyāsā": [
            "soka-parideva-dukkha-domanass'upāyāsā",
            "sokaparidevadukkhadomanass'upāyāsā",
        ],
        "sambhavan'ti": ["sambhavan'ti", "sambhavanti"],
    }

    report = generate_markdown_report(
        merged_result,
        original_sentence,
        verse_id="SN12.1_p2",
        speech_mark_options=variants,
    )

    assert "jarāmaraṇaṃ soka-parideva-dukkha-domanass'upāyāsā sambhavanti." in report
    assert "### Variants" in report
    assert (
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā" in report
    )
    assert "sambhavan'ti//sambhavanti" in report


def test_apply_variant_choices_builds_sentence_from_indices() -> None:
    text = "a//b c//d."
    options = {"a": ["a", "b"], "c": ["c", "d"]}
    choices = {"a": 1, "c": 1}

    assert apply_variant_choices(text, options, choices) == "b d."


def test_sync_analysis_words_to_sentence_uses_selected_variant() -> None:
    analysis = [
        {"word": "sattā", "status": "found", "data": []},
        {"word": "gacchan'ti", "status": "found", "data": []},
        {"word": "duggatiṃ", "status": "found", "data": []},
    ]

    synced = sync_analysis_words_to_sentence(analysis, "sattā gacchanti duggatiṃ.")

    assert [token["word"] for token in synced] == ["sattā", "gacchanti", "duggatiṃ"]
    assert analysis[1]["word"] == "gacchan'ti"


def test_generate_markdown_report_builds_text_from_variant_choices() -> None:
    merged_result = {
        "translation": "They arise.",
        "literal_translation": "They come into being.",
        "variant_choices": {"sambhavan'ti": 1},
        "analysis": [],
    }
    sentence = "sambhavan'ti//sambhavanti."
    variants = {"sambhavan'ti": ["sambhavan'ti", "sambhavanti"]}

    report = generate_markdown_report(
        merged_result,
        sentence,
        verse_id="SN12.1_p2",
        speech_mark_options=variants,
    )

    assert "# Analysis of: SN12.1_p2\n\nsambhavanti." in report


def test_generate_markdown_report_syncs_table_word_to_selected_variant() -> None:
    merged_result = {
        "translation": "They go.",
        "literal_translation": "They go.",
        "variant_choices": {"gacchan'ti": 1},
        "analysis": [
            {
                "word": "sattā",
                "status": "found",
                "data": [
                    {
                        "key": "57676_0",
                        "id": 57676,
                        "grammar": "masc nom pl of satta",
                        "meaning_combo": "beings",
                    }
                ],
            },
            {
                "word": "gacchan'ti",
                "status": "found",
                "data": [
                    {
                        "key": "24043_0",
                        "id": 24043,
                        "grammar": "pr 3rd pl of gacchati",
                        "meaning_combo": "go",
                    }
                ],
            },
        ],
    }
    sentence = "sattā gacchan'ti//gacchanti."
    variants = {"gacchan'ti": ["gacchan'ti", "gacchanti"]}

    report = generate_markdown_report(
        merged_result,
        sentence,
        verse_id="DHP316",
        speech_mark_options=variants,
    )

    assert "# Analysis of: DHP316\n\nsattā gacchanti." in report
    assert "| 24043 | gacchanti | pr 3rd pl of gacchati | go |  |  |" in report
    assert "| 24043 | gacchan'ti |" not in report


def test_build_system_prompt_requests_variant_choices_not_full_text() -> None:
    prompt = build_system_prompt(
        [],
        {"sambhavan'ti": ["sambhavan'ti", "sambhavanti"]},
    )

    assert '"variant_choices": {"variant option key": 0}' in prompt
    assert "Do not return the\nfull passage text" in prompt
    assert '"verse_text"' not in prompt


def test_build_system_prompt_uses_compact_context_json() -> None:
    analysis = [
        {
            "word": "samma",
            "data": [
                {
                    "key": "12345_0",
                    "pali": "samma",
                    "meaning_combo": "rightly",
                }
            ],
        }
    ]
    missing_groups = [
        {
            "word": "samma",
            "context": "samma",
            "missing_keys": ["12345_0"],
            "options": [{"key": "12345_0", "meaning_combo": "rightly"}],
        }
    ]

    system_prompt = build_system_prompt(analysis)
    missing_scores_prompt = _build_missing_scores_prompt("samma", missing_groups)

    assert '"key":"12345_0"' in system_prompt
    assert '  "key"' not in system_prompt
    assert '"missing_keys":["12345_0"]' in missing_scores_prompt
    assert '  "missing_keys"' not in missing_scores_prompt


def test_build_system_prompt_schema_example_is_not_markdown_fenced() -> None:
    prompt = build_system_prompt([])

    assert "```" not in prompt
    assert '"scores"' in prompt


def test_build_system_prompt_ends_with_schema_reminder() -> None:
    prompt = build_system_prompt([])

    final_line = next(line for line in reversed(prompt.splitlines()) if line.strip())
    assert "Your response MUST be exactly one JSON object" in final_line


def test_system_prompt_contains_no_tools_instruction() -> None:
    prompt = build_system_prompt([])

    assert translate_core.NO_TOOLS_INSTRUCTION == EXPECTED_NO_TOOLS_INSTRUCTION
    assert EXPECTED_NO_TOOLS_INSTRUCTION in prompt


def test_system_prompt_contains_common_pali_rules() -> None:
    prompt = build_system_prompt([])

    assert translate_core.COMMON_PALI_RULES in prompt


def test_common_pali_rules_cover_known_failures() -> None:
    assert "kāyassa bhedā" in translate_core.COMMON_PALI_RULES
    assert "'ti" in translate_core.COMMON_PALI_RULES
    assert "yena" in translate_core.COMMON_PALI_RULES
    assert "vocative" in translate_core.COMMON_PALI_RULES
    assert "vassāni" in translate_core.COMMON_PALI_RULES
    assert "accusative of duration" in translate_core.COMMON_PALI_RULES
    assert "prefer the genitive" in translate_core.COMMON_PALI_RULES
    assert "recipient, purpose, or benefit" in translate_core.COMMON_PALI_RULES


def test_system_prompt_discourages_zero_score_enumeration() -> None:
    prompt = build_system_prompt([])

    assert "Do not list options you would score 0" in prompt
    assert "genuinely plausible alternatives" in prompt
    assert "lower scores (1-9)" in prompt


def test_system_prompt_explains_same_id_grammar_variants() -> None:
    prompt = build_system_prompt([])

    assert "same id" in prompt
    assert "grammar variants" in prompt
    assert "score-10 variant's grammar" in prompt


def test_strip_grammar_annotations_removes_case_notes() -> None:
    assert (
        translate_core._strip_grammar_annotations("the Blessed One (accusative)")
        == "the Blessed One"
    )
    assert (
        translate_core._strip_grammar_annotations(
            "beings (nominative plural masculine)"
        )
        == "beings"
    )
    assert (
        translate_core._strip_grammar_annotations(
            "then (enclitic emphasizing the transition)"
        )
        == "then"
    )
    assert (
        translate_core._strip_grammar_annotations("who (interrogative pronoun)")
        == "who"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("after (abl. sg.)", "after"),
        ("of the body (masc. gen. sg.)", "of the body"),
        ("death (nom. sg.)", "death"),
        ("who (masc. nom. sg. interrogative pronoun)", "who"),
    ],
)
def test_strip_grammar_annotations_removes_abbreviated_case_notes(
    raw: str,
    expected: str,
) -> None:
    assert translate_core._strip_grammar_annotations(raw) == expected


def test_strip_grammar_annotations_preserves_legitimate_parentheticals() -> None:
    assert (
        translate_core._strip_grammar_annotations("talk (of conversation)")
        == "talk (of conversation)"
    )
    assert (
        translate_core._strip_grammar_annotations("honor (as a token of respect)")
        == "honor (as a token of respect)"
    )
    assert (
        translate_core._strip_grammar_annotations("increase (lit. accumulation)")
        == "increase (lit. accumulation)"
    )
    assert translate_core._strip_grammar_annotations("chapter (25)") == "chapter (25)"


def test_strip_grammar_annotations_cleans_whitespace() -> None:
    assert (
        translate_core._strip_grammar_annotations("the Blessed One  (accusative)")
        == "the Blessed One"
    )
    assert (
        translate_core._strip_grammar_annotations("the Blessed One, (accusative)")
        == "the Blessed One"
    )
    assert (
        translate_core._strip_grammar_annotations("goes - (nominative singular)")
        == "goes"
    )


def test_normalize_ai_response_strips_grammar_annotations() -> None:
    ai_data = {
        "scores": {
            "1_0": {
                "score": 10,
                "contextual_meaning": "the Blessed One (accusative)",
            },
            "2_0": {
                "score": 10,
                "contextual_meaning": "talk (of conversation)",
            },
        }
    }

    normalized = translate_core._normalize_ai_response(ai_data)

    assert normalized["scores"]["1_0"]["contextual_meaning"] == "the Blessed One"
    assert normalized["scores"]["2_0"]["contextual_meaning"] == "talk (of conversation)"


def test_normalize_ai_response_coerces_bare_number_scores() -> None:
    ai_data = {"scores": {"123_0": 7, "124_0": {"score": 10}}}

    normalized = translate_core._normalize_ai_response(ai_data)

    assert normalized["scores"] == {
        "123_0": {"score": 7},
        "124_0": {"score": 10},
    }


def test_normalize_ai_response_ignores_bool_score_values() -> None:
    ai_data = {"scores": {"123_0": True}}

    normalized = translate_core._normalize_ai_response(ai_data)

    assert normalized["scores"] == {"123_0": True}


def test_translate_sentence_reports_json_and_ai_progress(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )

    class FakeAIManager:
        def request(self, **_kwargs):
            events.append("request")
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "", "literal_translation": "", "scores": {}}'
                    ),
                    "status_message": "",
                },
            )()

    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        progress=events.append,
    )

    assert events == [
        "json_start",
        "json_done",
        "ai_start",
        "request",
        "ai_done",
    ]


def test_merge_ai_selections_preserves_missing_scores_as_none() -> None:
    analysis = [
        {
            "word": "sammā",
            "status": "found",
            "data": [
                {"key": "60789_0", "meaning_combo": "rightly"},
                {"key": "60693_0", "meaning_combo": "cymbal"},
            ],
        }
    ]
    ai_response = {"scores": {"60693_0": {"score": 0}}}

    merged = merge_ai_selections(analysis, ai_response)
    options = merged["analysis"][0]["data"]

    assert options[0]["ai_score"] is None
    assert options[1]["ai_score"] == 0


def test_merge_ai_selections_ignores_empty_contextual_fields() -> None:
    analysis = [
        {
            "word": "nu",
            "status": "found",
            "data": [
                {
                    "key": "38664_default",
                    "meaning_combo": "now; surely",
                    "grammar": "ind",
                }
            ],
        }
    ]
    ai_response = {
        "scores": {
            "38664_default": {
                "score": 10,
                "contextual_meaning": "",
                "selected_pos": "",
            }
        }
    }

    merged = merge_ai_selections(analysis, ai_response)
    option = merged["analysis"][0]["data"][0]

    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "now; surely"
    assert "selected_pos" not in option


def test_merge_ai_selections_applies_non_empty_contextual_fields() -> None:
    analysis = [
        {
            "word": "nu",
            "status": "found",
            "data": [
                {
                    "key": "38664_default",
                    "meaning_combo": "now; surely",
                    "grammar": "sandhi/compound",
                }
            ],
        }
    ]
    ai_response = {
        "scores": {
            "38664_default": {
                "score": 10,
                "contextual_meaning": "then",
                "selected_pos": "ind",
            }
        }
    }

    merged = merge_ai_selections(analysis, ai_response)
    option = merged["analysis"][0]["data"][0]

    assert option["meaning_combo"] == "then"
    assert option["selected_pos"] == "ind"


def test_find_missing_score_groups_deduplicates_repeated_words() -> None:
    option = {"key": "1_0", "pali": "ca", "pos": "ind"}
    token = {"word": "ca", "data": [option]}
    analysis = [token, copy.deepcopy(token)]

    groups = translate_core._find_missing_score_groups(analysis, scores_map={})

    assert len(groups) == 1


def test_find_missing_score_groups_deduplicates_occurrence_prefixed_keys() -> None:
    analysis = [
        {"word": "ca", "data": [{"key": "w0_1_0", "pali": "ca", "pos": "ind"}]},
        {"word": "ca", "data": [{"key": "w1_1_0", "pali": "ca", "pos": "ind"}]},
    ]

    groups = translate_core._find_missing_score_groups(analysis, scores_map={})

    assert len(groups) == 1
    assert groups[0]["missing_keys"] == ["w0_1_0"]


def test_batch_missing_groups_packs_by_size() -> None:
    groups = [
        {"word": "eka", "context": "eka", "missing_keys": ["1_0"], "options": []},
        {"word": "dve", "context": "dve", "missing_keys": ["2_0"], "options": []},
        {"word": "tayo", "context": "tayo", "missing_keys": ["3_0"], "options": []},
    ]
    first_len = len(json.dumps(groups[0], ensure_ascii=False, separators=(",", ":")))
    second_len = len(json.dumps(groups[1], ensure_ascii=False, separators=(",", ":")))

    batches = translate_core._batch_missing_groups(groups, first_len + second_len)

    assert batches == [groups[:2], groups[2:]]
    assert translate_core._batch_missing_groups([groups[0]], max_chars=1) == [
        [groups[0]]
    ]


def test_trim_groups_for_retry_drops_example_fields() -> None:
    missing_groups = [
        {
            "word": "samma",
            "context": "samma",
            "missing_keys": ["1_0"],
            "options": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "samma",
                    "pos": "ind",
                    "grammar": "adv",
                    "meaning_1": "properly",
                    "meaning_combo": "properly; rightly",
                    "example_1": "distinctive example text",
                    "source_1": "DHP1",
                    "example_2": "another example",
                    "source_2": "DHP2",
                }
            ],
        }
    ]
    original = copy.deepcopy(missing_groups)

    trimmed = translate_core._trim_groups_for_retry(missing_groups)

    assert missing_groups == original
    assert tuple(trimmed[0]["options"][0].keys()) == translate_core._RETRY_OPTION_FIELDS
    assert "example_1" not in trimmed[0]["options"][0]
    assert "source_2" not in trimmed[0]["options"][0]


def test_translate_sentence_retry_prompt_excludes_examples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distinctive_example = "distinctive retry-only example"
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "samma",
                "status": "found",
                "data": [
                    {
                        "key": "1_0",
                        "id": 1,
                        "pali": "samma",
                        "pos": "ind",
                        "grammar": "adv",
                        "meaning_1": "properly",
                        "meaning_combo": "properly; rightly",
                        "example_1": distinctive_example,
                        "source_1": "DHP1",
                        "example_2": "second distinctive example",
                        "source_2": "DHP2",
                    }
                ],
            }
        ],
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = '{"scores": {"1_0": {"score": 10}}}'
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    translate_sentence(
        "samma",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    retry_prompt = calls[1]["prompt"]
    assert distinctive_example not in retry_prompt
    assert '"source_1"' not in retry_prompt
    assert "adv" in retry_prompt
    assert "properly; rightly" in retry_prompt


def test_retry_request_sys_prompt_contains_no_tools_instruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "samma",
                "status": "found",
                "data": [{"key": "1_0", "meaning_combo": "properly"}],
            }
        ],
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = '{"scores": {"1_0": {"score": 10}}}'
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    translate_sentence(
        "samma",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert EXPECTED_NO_TOOLS_INSTRUCTION in calls[1]["prompt_sys"]


def test_missing_scores_prompt_contains_no_grammar_notes_rule() -> None:
    missing_groups = [
        {
            "word": "samma",
            "context": "samma",
            "missing_keys": ["1_0"],
            "options": [{"key": "1_0", "meaning_combo": "properly"}],
        }
    ]

    prompt = _build_missing_scores_prompt("samma", missing_groups)

    assert (
        "Provide ONLY the core meaning. Do NOT append grammatical case notes "
        "in parentheses."
    ) in prompt


def test_missing_scores_prompt_contains_common_pali_rules() -> None:
    missing_groups = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "context": "avijjānīvaraṇānaṃ",
            "missing_keys": ["10531_0", "10531_1"],
            "options": [
                {"key": "10531_0", "grammar": "masc dat pl"},
                {"key": "10531_1", "grammar": "fem gen pl"},
            ],
        }
    ]

    prompt = _build_missing_scores_prompt("avijjānīvaraṇānaṃ", missing_groups)

    assert "Common Pāḷi Disambiguation Rules" in prompt
    assert "prefer the genitive" in prompt


def test_missing_scores_prompt_requests_contextual_meaning_for_best_option() -> None:
    missing_groups = [
        {
            "word": "satta",
            "context": "satta",
            "missing_keys": ["123_0"],
            "options": [{"key": "123_0", "meaning_combo": "being; creature"}],
        }
    ]

    prompt = _build_missing_scores_prompt("satta", missing_groups)

    assert (
        'For the single best option per word (score 10), also include "contextual_meaning"'
        in prompt
    )


def _analysis_with_missing_retry_keys(keys: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "word": f"word{index}",
            "status": "found",
            "data": [
                {
                    "key": key,
                    "id": index,
                    "pali": f"pali{index}",
                    "pos": "noun",
                    "grammar": "nom sg",
                    "meaning_combo": f"meaning {index}",
                    "example_1": "",
                    "example_2": "",
                }
            ],
        }
        for index, key in enumerate(keys, start=1)
    ]


def test_retry_scores_merge_contextual_meanings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(["123_0"]),
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = (
                    '{"scores": {"123_0": {"score": 10, "contextual_meaning": "some"}}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "satta",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "some"
    assert debug["final_scores"]["123_0"]["contextual_meaning"] == "some"


def test_retry_flat_shape_meanings_are_grammar_stripped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(["123_0"]),
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = (
                    '{"123_0": {"score": 10, '
                    '"contextual_meaning": "the Blessed One (accusative)"}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "bhagavantaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "the Blessed One"
    assert debug["final_scores"]["123_0"]["contextual_meaning"] == "the Blessed One"


def test_retry_scores_fan_out_to_equivalent_occurrence_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "ca",
                "status": "found",
                "data": [{"key": "w0_1_0", "pali": "ca", "meaning_combo": "and"}],
            },
            {
                "word": "ca",
                "status": "found",
                "data": [{"key": "w1_1_0", "pali": "ca", "meaning_combo": "and"}],
            },
        ],
    )
    retry_key_batches: list[list[str]] = []
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                retry_key_batches.append(
                    _missing_keys_from_retry_prompt(kwargs["prompt"])
                )
                content = '{"scores": {"w0_1_0": {"score": 10}}}'
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "ca ca",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert retry_key_batches == [["w0_1_0"]]
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [10, 10]
    assert debug["final_scores"]["w1_1_0"]["score"] == 10
    assert debug["missing_score_groups_after_retry"] == []


def _missing_keys_from_retry_prompt(prompt: str) -> list[str]:
    context = prompt.split("Missing dictionary option scores:\n", maxsplit=1)[1]
    groups = cast(list[dict[str, Any]], json.loads(context.strip()))
    return [key for group in groups for key in cast(list[str], group["missing_keys"])]


def test_translate_sentence_passes_provider_and_model_to_every_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(["1_0"]),
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = "Here is prose instead of JSON."
            elif len(calls) == 2:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = '{"scores": {"1_0": {"score": 10}}}'
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    translate_sentence(
        "eka",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        model="m-x",
        provider="prov-x",
    )

    assert len(calls) >= 3
    for call in calls:
        assert call["provider_preference"] == "prov-x"
        assert call["model"] == "m-x"


def test_translate_sentence_default_provider_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(["1_0"]),
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                content = '{"scores": {"1_0": {"score": 10}}}'
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    translate_sentence(
        "eka",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert len(calls) >= 2
    for call in calls:
        assert call.get("provider_preference") is None


def test_translate_sentence_batches_oversized_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(
            ["1_0", "2_0", "3_0"]
        ),
    )
    monkeypatch.setattr(
        "exporter.analysis.retry.MAX_RETRY_CONTEXT_CHARS", 1, raising=False
    )
    calls: list[dict[str, Any]] = []
    retry_key_batches: list[list[str]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                batch_keys = _missing_keys_from_retry_prompt(kwargs["prompt"])
                retry_key_batches.append(batch_keys)
                scores = {key: {"score": 10} for key in batch_keys}
                content = json.dumps({"scores": scores})
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "eka dve tayo",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) >= 3
    assert retry_key_batches == [["1_0"], ["2_0"], ["3_0"]]
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        10,
        10,
    ]
    assert len(debug["retry_requests"]) == 3
    assert debug["missing_score_groups_after_retry"] == []


def test_translate_sentence_runs_second_retry_pass_for_leftovers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(
            ["1_0", "2_0"]
        ),
    )
    calls: list[dict[str, Any]] = []
    retry_key_batches: list[list[str]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            elif len(calls) == 2:
                batch_keys = _missing_keys_from_retry_prompt(kwargs["prompt"])
                retry_key_batches.append(batch_keys)
                content = '{"scores": {"1_0": {"score": 10}}}'
            else:
                batch_keys = _missing_keys_from_retry_prompt(kwargs["prompt"])
                retry_key_batches.append(batch_keys)
                scores = {key: {"score": 10} for key in batch_keys}
                content = json.dumps({"scores": scores})
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "eka dve",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert retry_key_batches == [["1_0", "2_0"], ["2_0"]]
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        10,
    ]
    assert len(debug["retry_requests"]) == 2
    assert debug["retry_requests"][1]["pass"] == 2
    assert debug["missing_score_groups_after_retry"] == []


def test_translate_sentence_retry_batch_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _analysis_with_missing_retry_keys(
            ["1_0", "2_0", "3_0"]
        ),
    )
    monkeypatch.setattr(
        "exporter.analysis.retry.MAX_RETRY_CONTEXT_CHARS", 1, raising=False
    )
    monkeypatch.setattr("exporter.analysis.retry.MAX_RETRY_BATCHES", 1, raising=False)
    calls: list[dict[str, Any]] = []
    retry_key_batches: list[list[str]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "done", "literal_translation": "done", '
                    '"scores": {}}'
                )
            else:
                batch_keys = _missing_keys_from_retry_prompt(kwargs["prompt"])
                retry_key_batches.append(batch_keys)
                content = json.dumps(
                    {"scores": {key: {"score": 10} for key in batch_keys}}
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "eka dve",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 3
    assert retry_key_batches == [["1_0"], ["2_0"]]
    assert len(debug["retry_requests"]) == 2
    assert debug["retry_requests"][1]["pass"] == 2
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        10,
        None,
    ]
    assert [
        key for group in debug["retry_skipped_groups"] for key in group["missing_keys"]
    ] == ["3_0"]
    assert [
        key
        for group in debug["missing_score_groups_after_retry"]
        for key in group["missing_keys"]
    ] == ["3_0"]


def test_pre_match_db_examples_requires_text_overlap() -> None:
    analysis = [
        {
            "word": "dukkhakkhandhassa",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "DN1.12",
                    "example_2": "",
                    "source_2": "",
                },
                {
                    "key": "2_0",
                    "example_1": "unrelated example",
                    "source_1": "SN12.1",
                    "example_2": "",
                    "source_2": "",
                },
            ],
        }
    ]
    sentence = (
        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti. nirodho, nirodho'ti"
    )

    pre_match_db_examples(analysis, "SN12.1", sentence)

    matched, source_only = analysis[0]["data"]
    assert matched["ai_score"] == 10
    assert matched["db_example_match"] is True
    assert matched["db_example_match_type"] == "text_overlap"
    assert "ai_score" not in source_only
    assert "db_example_match" not in source_only


def test_pre_match_db_examples_ranks_source_text_overlap_strongest() -> None:
    analysis = [
        {
            "word": "dukkhakkhandhassa",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "DN1.12",
                    "example_2": "",
                    "source_2": "",
                },
                {
                    "key": "2_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "SN12.1",
                    "example_2": "",
                    "source_2": "",
                },
            ],
        }
    ]
    sentence = "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."

    pre_match_db_examples(analysis, "SN12.1", sentence)

    text_only, source_text = analysis[0]["data"]
    assert text_only["db_example_match_type"] == "text_overlap"
    assert source_text["db_example_match_type"] == "source_text_overlap"


def test_split_into_sentence_chunks_single_chunk_under_budget() -> None:
    analysis = [
        {"word": "buddho", "status": "found", "data": []},
        {"word": "dhammo", "status": "found", "data": []},
    ]
    sentence = "buddho dhammo."

    chunk_list, use_grounded = translate_core._split_into_sentence_chunks(
        sentence,
        analysis,
        max_context_chars=10_000,
    )

    assert chunk_list == [(sentence, analysis)]
    assert not use_grounded


def test_split_into_sentence_chunks_packs_sentences() -> None:
    sentence = "buddho bhagavā. dhammo."
    analysis = [
        {"word": "buddho", "status": "found", "data": [{"key": "1_0"}]},
        {"word": "bhagavā", "status": "found", "data": [{"key": "2_0"}]},
        {"word": "dhammo", "status": "found", "data": [{"key": "3_0"}]},
    ]
    # 118 chars fits entries 1+2; 176 chars (all 3) exceeds; each entry alone fits (59-60)
    threshold = 120

    chunk_list, use_grounded = translate_core._split_into_sentence_chunks(
        sentence,
        analysis,
        max_context_chars=threshold,
    )

    assert chunk_list == [
        ("buddho bhagavā.", analysis[:2]),
        ("dhammo.", analysis[2:]),
    ]
    assert [entry for _, chunk in chunk_list for entry in chunk] == analysis
    for _, chunk in chunk_list:
        assert translate_core._analysis_context_len(chunk) <= threshold
    assert not use_grounded


def test_split_into_sentence_chunks_falls_back_on_token_mismatch() -> None:
    sentence = "buddho bhagavā. dhammo."
    analysis = [
        {"word": "buddho", "status": "found", "data": []},
        {"word": "dhammo", "status": "found", "data": []},
    ]

    chunk_list, use_grounded = translate_core._split_into_sentence_chunks(
        sentence,
        analysis,
        max_context_chars=10,
    )

    assert chunk_list == [(sentence, analysis)]
    assert not use_grounded


def test_split_into_sentence_chunks_lone_oversize_returns_word_chunks() -> None:
    analysis = [
        {"word": "buddho", "status": "found", "data": [{"key": "1_0"}]},
        {"word": "bhagavā", "status": "found", "data": [{"key": "2_0"}]},
    ]
    sentence = "buddho bhagavā."

    chunk_list, use_grounded = translate_core._split_into_sentence_chunks(
        sentence,
        analysis,
        max_context_chars=10,
    )

    assert use_grounded
    assert chunk_list == [("buddho", [analysis[0]]), ("bhagavā", [analysis[1]])]


def test_translate_sentence_grounded_fallback_fires_and_replaces_translation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = [
        {
            "word": "buddho",
            "status": "found",
            "data": [{"key": "1_0", "meaning_combo": "awakened"}],
        },
        {
            "word": "bhagavā",
            "status": "found",
            "data": [{"key": "2_0", "meaning_combo": "blessed one"}],
        },
    ]
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _s, _db: analysis,
    )
    monkeypatch.setattr(translate_core, "MAX_FIRST_CONTEXT_CHARS", 10, raising=False)

    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            prompt = kwargs.get("prompt", "")
            if (
                "translation" in prompt
                and "literal_translation" in prompt
                and "word senses" in prompt
            ):
                # grounded translation call
                content = (
                    '{"translation": "Grounded T", "literal_translation": "Grounded L"}'
                )
            else:
                # scoring calls for individual words
                word = "buddho" if "buddho" in prompt else "bhagavā"
                content = json.dumps(
                    {
                        "translation": word,
                        "literal_translation": word,
                        "scores": {
                            ("1_0" if word == "buddho" else "2_0"): {"score": 10}
                        },
                    }
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "buddho bhagavā.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    grounded_call = next(
        (c for c in calls if "word senses" in c.get("prompt", "")), None
    )
    assert grounded_call is not None
    assert result["translation"] == "Grounded T"
    assert result["literal_translation"] == "Grounded L"


def test_translate_sentence_grounded_fallback_not_triggered_for_normal_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _s, _db: [
            {"word": "buddho", "status": "found", "data": [{"key": "1_0"}]},
        ],
    )

    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            return type(
                "R",
                (),
                {
                    "content": '{"translation": "T", "literal_translation": "L", "scores": {"1_0": {"score": 10}}}',
                    "status_message": "ok",
                },
            )()

    translate_sentence(
        "buddho.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert not any("word senses" in c.get("prompt", "") for c in calls)


def _patch_basic_chunked_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    analysis = [
        {
            "word": "buddho",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "pali": "buddho",
                    "pos": "noun",
                    "meaning_combo": "awakened one",
                }
            ],
        },
        {
            "word": "bhagavā",
            "status": "found",
            "data": [
                {
                    "key": "2_0",
                    "pali": "bhagavā",
                    "pos": "noun",
                    "meaning_combo": "blessed one",
                }
            ],
        },
        {
            "word": "dhammo",
            "status": "found",
            "data": [
                {
                    "key": "3_0",
                    "pali": "dhammo",
                    "pos": "noun",
                    "meaning_combo": "teaching",
                }
            ],
        },
    ]
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: analysis,
    )
    monkeypatch.setattr(translate_core, "MAX_FIRST_CONTEXT_CHARS", 10, raising=False)


def test_translate_sentence_tolerates_single_chunk_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_basic_chunked_analysis(monkeypatch)
    calls: list[str] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            prompt = kwargs["prompt"]
            calls.append(prompt)
            if prompt.startswith("Return JSON for: buddho bhagavā."):
                return type(
                    "FakeResponse",
                    (),
                    {"content": "", "status_message": "chunk timed out"},
                )()
            if prompt.startswith("Return JSON for: dhammo."):
                content = (
                    '{"translation": "T2", "literal_translation": "L2", '
                    '"scores": {"3_0": {"score": 10}}}'
                )
            else:
                content = '{"scores": {"1_0": {"score": 10}, "2_0": {"score": 9}}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "buddho bhagavā. dhammo.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        9,
        10,
    ]
    assert (
        len(
            [
                call
                for call in calls
                if call.startswith("Return JSON for: buddho bhagavā.")
            ]
        )
        == 2
    )
    assert debug["chunk_requests"][0]["chunk_sentence"] == "buddho bhagavā."
    assert "chunk_error" in debug["chunk_requests"][0]
    assert debug["retry_requests"][0]["missing_keys"] == ["1_0", "2_0"]


def test_translate_sentence_retries_failed_chunk_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_basic_chunked_analysis(monkeypatch)
    first_chunk_attempts = 0

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            nonlocal first_chunk_attempts
            prompt = kwargs["prompt"]
            if prompt.startswith("Return JSON for: buddho bhagavā."):
                first_chunk_attempts += 1
                if first_chunk_attempts == 1:
                    return type(
                        "FakeResponse",
                        (),
                        {"content": "", "status_message": "chunk timed out"},
                    )()
                content = (
                    '{"translation": "T1", "literal_translation": "L1", '
                    '"scores": {"1_0": {"score": 10}, "2_0": {"score": 10}}}'
                )
            else:
                content = (
                    '{"translation": "T2", "literal_translation": "L2", '
                    '"scores": {"3_0": {"score": 10}}}'
                )
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "buddho bhagavā. dhammo.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert first_chunk_attempts == 2
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        10,
        10,
    ]
    assert "chunk_error" not in debug["chunk_requests"][0]
    assert "chunk_error_attempt_1" in debug["chunk_requests"][0]


def test_translate_sentence_raises_when_all_chunks_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_basic_chunked_analysis(monkeypatch)
    call_count = 0

    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            nonlocal call_count
            call_count += 1
            return type(
                "FakeResponse",
                (),
                {"content": "", "status_message": "chunk timed out"},
            )()

    with pytest.raises(ValueError, match="AI Request Failed"):
        translate_sentence(
            "buddho bhagavā. dhammo.",
            cast(Session, object()),
            ai_manager=cast(AIManager, FakeAIManager()),
        )

    assert call_count == 4


def test_single_chunk_failure_still_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "buddho",
                "status": "found",
                "data": [{"key": "1_0", "meaning_combo": "awakened"}],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            return type(
                "FakeResponse",
                (),
                {"content": "", "status_message": "empty"},
            )()

    with pytest.raises(ValueError, match="AI Request Failed"):
        translate_sentence(
            "buddho",
            cast(Session, object()),
            ai_manager=cast(AIManager, FakeAIManager()),
        )


def test_translate_sentence_chunks_oversized_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = [
        {
            "word": "buddho",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "pali": "buddho",
                    "pos": "noun",
                    "meaning_combo": "awakened one",
                }
            ],
        },
        {
            "word": "bhagavā",
            "status": "found",
            "data": [
                {
                    "key": "2_0",
                    "pali": "bhagavā",
                    "pos": "noun",
                    "meaning_combo": "blessed one",
                }
            ],
        },
        {
            "word": "dhammo",
            "status": "found",
            "data": [
                {
                    "key": "3_0",
                    "pali": "dhammo",
                    "pos": "noun",
                    "meaning_combo": "teaching",
                }
            ],
        },
    ]
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: analysis,
    )
    monkeypatch.setattr(translate_core, "MAX_FIRST_CONTEXT_CHARS", 10, raising=False)
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "T1", "literal_translation": "L1", '
                    '"scores": {"1_0": {"score": 10}, "2_0": {"score": 10}}}'
                )
            else:
                content = (
                    '{"translation": "T2", "literal_translation": "L2", '
                    '"scores": {"3_0": {"score": 10}}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "buddho bhagavā. dhammo.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert "buddho bhagavā." in calls[0]["prompt"]
    assert "Earlier sentences of this passage" not in calls[0]["prompt"]
    assert (
        "Full passage for context (score ONLY the words in your part)"
        in calls[0]["prompt"]
    )
    assert "Earlier sentences of this passage" in calls[1]["prompt"]
    assert "T1" in calls[1]["prompt"]
    assert result["translation"] == "T1 T2"
    assert result["literal_translation"] == "L1 L2"
    assert [entry["data"][0]["ai_score"] for entry in result["analysis"]] == [
        10,
        10,
        10,
    ]
    assert len(debug["chunk_requests"]) == 2
    assert debug["chunk_requests"][0]["raw_response"] == (
        '{"translation": "T1", "literal_translation": "L1", '
        '"scores": {"1_0": {"score": 10}, "2_0": {"score": 10}}}'
    )
    assert "raw_response" not in debug
    assert debug["retry_requests"] == []


def test_first_pass_debug_records_chunk_sentence() -> None:
    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "Awake.", '
                        '"literal_translation": "Awake.", '
                        '"scores": {"1_0": {"score": 10}}}'
                    ),
                    "status_message": "ok",
                },
            )()

    debug: dict[str, Any] = {}
    translate_core._request_first_pass(
        chunk_sentence="buddho.",
        full_sentence="buddho. dhammo.",
        analysis=[
            {
                "word": "buddho",
                "status": "found",
                "data": [{"key": "1_0", "meaning_combo": "awakened"}],
            }
        ],
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        speech_mark_options=None,
        progress=None,
        verbose=False,
        debug=debug,
    )

    assert debug["chunk_sentence"] == "buddho."


def test_merge_chunk_ai_data_drops_contained_duplicate_translation() -> None:
    merged = translate_core._merge_chunk_ai_data(
        [
            {
                "translation": "Who goes to the lower realm? Who goes to heaven?",
                "literal_translation": "who lower-realm goes who heaven goes",
                "scores": {"1_0": {"score": 10}},
            },
            {
                "translation": "who goes to heaven?",
                "literal_translation": "who heaven goes",
                "scores": {"2_0": {"score": 10}},
            },
        ]
    )

    assert merged["translation"] == "Who goes to the lower realm? Who goes to heaven?"
    assert merged["literal_translation"] == "who lower-realm goes who heaven goes"
    assert merged["scores"] == {"1_0": {"score": 10}, "2_0": {"score": 10}}


def test_merge_chunk_ai_data_keeps_distinct_translations() -> None:
    merged = translate_core._merge_chunk_ai_data(
        [
            {"translation": "The first sentence.", "literal_translation": "first"},
            {"translation": "The second sentence.", "literal_translation": "second"},
        ]
    )

    assert merged["translation"] == "The first sentence. The second sentence."
    assert merged["literal_translation"] == "first second"


def test_translate_sentence_retries_missing_component_scores(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "sammāsambuddhassa",
                "status": "found",
                "data": [
                    {
                        "key": "60847_0",
                        "id": 60847,
                        "pali": "sammāsambuddhassa",
                        "pos": "noun",
                        "grammar": "masc gen sg of sammāsambuddha",
                        "meaning_combo": "perfectly awakened Buddha",
                        "components": [
                            [
                                {
                                    "key": "60693_0",
                                    "id": 60693,
                                    "pali": "sammā",
                                    "pos": "nt",
                                    "meaning_1": "cymbal",
                                    "meaning_combo": "cymbal",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                                {
                                    "key": "60789_0",
                                    "id": 60789,
                                    "pali": "sammā",
                                    "pos": "ind",
                                    "meaning_1": "perfectly",
                                    "meaning_combo": "perfectly; rightly",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                            ]
                        ],
                    }
                ],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"scores": {"60789_0": {"score": 10}}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict = {}
    result = translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert len(calls) == 2
    assert "missing dictionary option scores" in calls[1]
    assert component_options[0]["ai_score"] is None
    assert component_options[1]["ai_score"] == 10
    assert debug["retry_requests"][0]["missing_keys"] == ["60693_0", "60789_0"]


def _patch_sammasambuddhassa_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "sammāsambuddhassa",
                "status": "found",
                "data": [
                    {
                        "key": "60847_0",
                        "id": 60847,
                        "pali": "sammāsambuddhassa",
                        "pos": "noun",
                        "grammar": "masc gen sg of sammāsambuddha",
                        "meaning_combo": "perfectly awakened Buddha",
                        "components": [
                            [
                                {
                                    "key": "60693_0",
                                    "id": 60693,
                                    "pali": "sammā",
                                    "pos": "nt",
                                    "meaning_1": "cymbal",
                                    "meaning_combo": "cymbal",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                                {
                                    "key": "60789_0",
                                    "id": 60789,
                                    "pali": "sammā",
                                    "pos": "ind",
                                    "meaning_1": "perfectly",
                                    "meaning_combo": "perfectly; rightly",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                            ]
                        ],
                    }
                ],
            }
        ],
    )


def test_translate_sentence_retry_accepts_flat_score_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"60789_0": {"score": 10}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict = {}
    result = translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert component_options[1]["ai_score"] == 10


def test_debug_parsed_response_is_snapshot_not_live_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"scores": {"60789_0": {"score": 10}}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict[str, Any] = {}
    translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert "60789_0" not in debug["parsed_response"]["scores"]


def test_translate_sentence_retry_ignores_unrelated_flat_score_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"unrelated_key": {"score": 5}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict = {}
    result = translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert "unrelated_key" not in debug["final_scores"]
    assert component_options[1]["ai_score"] is None


def test_coerce_flat_score_map_shapes() -> None:
    expected = {"a_0", "b_0"}

    assert translate_core._coerce_flat_score_map({"a_0": {"score": 3}}, expected) == {
        "scores": {"a_0": {"score": 3}}
    }
    assert translate_core._coerce_flat_score_map({"a_0": 7}, expected) == {
        "scores": {"a_0": {"score": 7}}
    }
    untouched = {"scores": {"a_0": {"score": 1}}}
    assert translate_core._coerce_flat_score_map(untouched, expected) is untouched
    prose_like = {"x": "y", "z": "w", "a_0": {"score": 1}}
    assert translate_core._coerce_flat_score_map(prose_like, expected) is prose_like


def test_deterministic_scores_promote_finite_verb_quotative_ti_deconstruction() -> None:
    analysis = [
        {
            "word": "upapajjantī'ti",
            "status": "found",
            "data": [
                {
                    "key": "decon_upapajjantīti_0",
                    "pali": "upapajjantīti",
                    "pos": "sandhi",
                    "grammar": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "construction": "upapajjantī + iti",
                    "components": [
                        [
                            {
                                "key": "79845_0",
                                "pali": "upapajjantī",
                                "pos": "prp",
                                "grammar": "fem nom sg of upapajjanta",
                                "meaning_combo": "being reborn",
                            }
                        ],
                        [
                            {
                                "key": "13466_default",
                                "pali": "iti",
                                "pos": "ind",
                                "grammar": "ind, adv",
                            }
                        ],
                    ],
                },
                {
                    "key": "decon_upapajjantīti_1",
                    "pali": "upapajjantīti",
                    "pos": "sandhi",
                    "grammar": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "construction": "upapajjanti + iti",
                    "components": [
                        [
                            {
                                "key": "15855_0",
                                "pali": "upapajjanti",
                                "pos": "verb",
                                "grammar": "pr 3rd pl of upapajjati",
                                "meaning_combo": "are reborn",
                            }
                        ],
                        [
                            {
                                "key": "13466_default",
                                "pali": "iti",
                                "pos": "ind",
                                "grammar": "ind, adv",
                            }
                        ],
                    ],
                },
            ],
        }
    ]
    scores_map: dict[str, Any] = {
        "decon_upapajjantīti_0": {"score": 10, "contextual_meaning": "being reborn"},
        "decon_upapajjantīti_1": {"score": 0},
    }

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)

    assert scores_map["decon_upapajjantīti_0"]["score"] == 0
    assert scores_map["decon_upapajjantīti_1"] == {
        "score": 10,
        "selection_source": "deterministic_quotative_ti_deconstruction",
        "contextual_meaning": "are reborn",
    }


def test_deterministic_scores_do_not_boost_feminine_quotative_ti_deconstruction() -> (
    None
):
    analysis = [
        {
            "word": "dharaṇī'ti",
            "status": "found",
            "data": [
                {
                    "key": "decon_dharaṇīti_0",
                    "pali": "dharaṇīti",
                    "pos": "sandhi",
                    "grammar": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "construction": "dharaṇī + iti",
                    "components": [
                        [
                            {
                                "key": "35009_0",
                                "pali": "dharaṇī",
                                "pos": "fem",
                                "grammar": "fem nom sg of dharaṇī",
                                "meaning_combo": "earth",
                            }
                        ],
                        [
                            {
                                "key": "13466_default",
                                "pali": "iti",
                                "pos": "ind",
                                "grammar": "ind, adv",
                            }
                        ],
                    ],
                }
            ],
        }
    ]
    scores_map: dict[str, Any] = {}

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)

    assert scores_map == {}


def _db_example_option(key: str, option_id: int, grammar: str) -> dict[str, Any]:
    return {
        "key": key,
        "id": option_id,
        "pali": "avijjānīvaraṇānaṃ",
        "pos": "adj",
        "grammar": grammar,
        "meaning_1": "hindered by ignorance",
        "meaning_combo": "hindered by ignorance",
        "ai_score": 10,
        "db_example_match": True,
        "db_example_match_type": "source_text_overlap",
        "selection_source": "db_example_source_text_overlap",
    }


def test_deterministic_scores_ignore_empty_contextual_fields() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [_db_example_option("10531_0", 10531, "masc dat pl")],
        }
    ]
    scores_map: dict[str, Any] = {
        "10531_0": {"score": 10, "contextual_meaning": "", "selected_pos": ""}
    }

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)

    assert scores_map["10531_0"] == {
        "score": 10,
        "selection_source": "db_example_source_text_overlap",
    }


def test_deterministic_scores_preserve_ai_positive_variant_choice() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [
                _db_example_option("10531_0", 10531, "masc dat pl"),
                _db_example_option("10531_1", 10531, "fem gen pl"),
                _db_example_option("10531_2", 10531, "nt dat pl"),
            ],
        }
    ]
    scores_map: dict[str, Any] = {
        "10531_0": {"score": 0},
        "10531_1": {
            "score": 10,
            "contextual_meaning": "hindered by ignorance",
            "selected_pos": "adj",
        },
        "10531_2": {"score": 0},
    }

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)
    merged = merge_ai_selections(
        analysis,
        {"translation": "", "literal_translation": "", "scores": scores_map},
    )
    best = translate_core._select_best_option(merged["analysis"][0]["data"])

    assert scores_map["10531_0"]["score"] == 0
    assert scores_map["10531_1"] == {
        "score": 10,
        "selection_source": "db_example_source_text_overlap",
        "contextual_meaning": "hindered by ignorance",
        "selected_pos": "adj",
    }
    assert scores_map["10531_2"]["score"] == 0
    assert best is not None
    assert best["key"] == "10531_1"


def test_deterministic_scores_promote_all_db_variants_without_ai_positive() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [
                _db_example_option("10531_0", 10531, "masc dat pl"),
                _db_example_option("10531_1", 10531, "fem gen pl"),
            ],
        }
    ]
    scores_map: dict[str, Any] = {}

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)

    assert scores_map["10531_0"]["score"] == 10
    assert scores_map["10531_1"]["score"] == 10
    assert scores_map["10531_0"]["selection_source"] == "db_example_all_variants_tied"
    assert scores_map["10531_1"]["selection_source"] == "db_example_all_variants_tied"


def test_find_missing_score_groups_includes_db_example_tied_variants() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [
                _db_example_option("10531_0", 10531, "masc dat pl"),
                _db_example_option("10531_1", 10531, "fem gen pl"),
            ],
        }
    ]
    scores_map: dict[str, Any] = {}

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)
    groups = translate_core._find_missing_score_groups(analysis, scores_map)

    assert len(groups) == 1
    assert groups[0]["missing_keys"] == ["10531_0", "10531_1"]


def test_deterministic_scores_zero_missing_variants_when_ai_selects_sibling() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [
                _db_example_option("10531_0", 10531, "masc dat pl"),
                _db_example_option("10531_1", 10531, "fem gen pl"),
                _db_example_option("10531_2", 10531, "nt dat pl"),
            ],
        }
    ]
    scores_map: dict[str, Any] = {"10531_1": {"score": 10}}

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)

    assert scores_map["10531_0"] == {
        "score": 0,
        "selection_source": "db_example_variant_not_selected",
    }
    assert scores_map["10531_1"]["score"] == 10
    assert scores_map["10531_2"] == {
        "score": 0,
        "selection_source": "db_example_variant_not_selected",
    }


def test_deterministic_scores_db_match_still_outranks_other_ai_id() -> None:
    analysis = [
        {
            "word": "avijjānīvaraṇānaṃ",
            "status": "found",
            "data": [
                _db_example_option("10531_0", 10531, "masc dat pl"),
                {
                    "key": "99999_0",
                    "id": 99999,
                    "pali": "avijjānīvaraṇānaṃ",
                    "pos": "adj",
                    "grammar": "masc nom pl",
                    "meaning_combo": "different homonym",
                },
            ],
        }
    ]
    scores_map: dict[str, Any] = {"99999_0": {"score": 10}}

    translate_core._apply_deterministic_scores_to_map(analysis, scores_map)
    merged = merge_ai_selections(
        analysis,
        {"translation": "", "literal_translation": "", "scores": scores_map},
    )
    best = translate_core._select_best_option(merged["analysis"][0]["data"])

    assert best is not None
    assert best["key"] == "10531_0"


def test_translate_sentence_retries_db_example_tie_and_preserves_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "avijjānīvaraṇānaṃ",
                "status": "found",
                "data": [
                    _db_example_option("10531_0", 10531, "masc dat pl"),
                    _db_example_option("10531_1", 10531, "fem gen pl"),
                ],
            }
        ],
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = '{"translation": "", "literal_translation": "", "scores": {}}'
            else:
                content = (
                    '{"scores": {"10531_1": {"score": 10, '
                    '"contextual_meaning": "hindered by ignorance", '
                    '"selected_pos": "adj"}}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "avijjānīvaraṇānaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert '"missing_keys":["10531_0","10531_1"]' in calls[1]["prompt"]
    assert debug["final_scores"]["10531_0"] == {
        "score": 0,
        "selection_source": "db_example_variant_not_selected",
    }
    assert debug["final_scores"]["10531_1"] == {
        "score": 10,
        "selection_source": "db_example_source_text_overlap",
        "contextual_meaning": "hindered by ignorance",
        "selected_pos": "adj",
    }
    assert debug["missing_score_groups_after_retry"] == []
    assert result["analysis"][0]["data"][0]["ai_score"] == 0
    assert result["analysis"][0]["data"][1]["ai_score"] == 10
    assert result["analysis"][0]["data"][1]["meaning_combo"] == (
        "hindered by ignorance"
    )


def test_translate_sentence_curated_example_match_overrides_ai_score(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dukkhakkhandhassa",
                "status": "found",
                "data": [
                    {
                        "key": "1_0",
                        "id": 1,
                        "pali": "dukkhakkhandhassa",
                        "meaning_1": "mass of suffering",
                        "meaning_combo": "mass of suffering",
                        "example_1": (
                            "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                        ),
                        "source_1": "SN12.1",
                        "example_2": "",
                        "source_2": "",
                    }
                ],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **_kwargs):
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "", "literal_translation": "", '
                        '"scores": {"1_0": {"score": 0}}}'
                    ),
                    "status_message": "ok",
                },
            )()

    result = translate_sentence(
        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="SN12.1",
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["selection_source"] == "db_example_source_text_overlap"


def test_translate_sentence_db_example_preserves_ai_contextual_meaning(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_1": "earth",
                        "meaning_combo": "earth; world; lit. carrier",
                        "example_1": "dharaṇī siñcati.",
                        "source_1": "TH50",
                        "example_2": "",
                        "source_2": "",
                    }
                ],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **_kwargs):
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "", "literal_translation": "", '
                        '"scores": {"35009_0": {"score": 10, '
                        '"contextual_meaning": "earth", '
                        '"selected_pos": "fem"}}}'
                    ),
                    "status_message": "ok",
                },
            )()

    result = translate_sentence(
        "dharaṇī siñcati.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="TH50",
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "earth"
    assert option["selected_pos"] == "fem"
    assert option["selection_source"] == "db_example_source_text_overlap"


def test_format_markdown_table_fallback_rejects_samma_cymbal() -> None:
    analysis = [
        {
            "word": "sammāsambuddhassa",
            "status": "found",
            "data": [
                {
                    "key": "60847_0",
                    "id": 60847,
                    "pali": "sammāsambuddhassa",
                    "pos": "noun",
                    "grammar": "masc gen sg of sammāsambuddha",
                    "meaning_combo": "perfectly awakened Buddha",
                    "compound_construction": "sammā + sambuddha",
                    "construction": "sammā + sambuddha",
                    "root_key": "",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "60693_0",
                                "id": 60693,
                                "pali": "sammā",
                                "pos": "nt",
                                "meaning_1": "cymbal",
                                "meaning_combo": "cymbal",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                            {
                                "key": "60789_0",
                                "id": 60789,
                                "pali": "sammā",
                                "pos": "ind",
                                "meaning_1": "perfectly",
                                "meaning_combo": "perfectly; rightly; correctly",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 60693 | - sammā | nt | cymbal |" not in table
    assert "| 60789 | - sammā | ind | perfectly; rightly; correctly |" in table


def test_format_markdown_table_fallback_uses_meaning_1_quality() -> None:
    analysis = [
        {
            "word": "testcompound",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "testcompound",
                    "pos": "noun",
                    "meaning_combo": "compound",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "10_0",
                                "id": 10,
                                "pali": "part",
                                "pos": "nt",
                                "meaning_1": "",
                                "meaning_combo": "display text",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                            {
                                "key": "11_0",
                                "id": 11,
                                "pali": "part",
                                "pos": "nt",
                                "meaning_1": "real meaning",
                                "meaning_combo": "real meaning",
                                "example_1": "",
                                "example_2": "",
                                "ai_score": None,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 11 | - part | nt | real meaning |" in table


def test_format_markdown_table_hides_deconstructed_placeholder() -> None:
    analysis = [
        {
            "word": "okassa",
            "status": "found",
            "data": [
                {
                    "key": "w0_decon_okassa_0",
                    "id": "",
                    "pali": "okassa",
                    "pos": "sandhi",
                    "grammar": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "construction": "oka + assa",
                    "components": [
                        [
                            {
                                "key": "w0_1_0",
                                "id": 1,
                                "pali": "oka",
                                "pos": "nt",
                                "meaning_combo": "dwelling; home",
                                "ai_score": 10,
                            }
                        ],
                        [
                            {
                                "key": "w0_2_0",
                                "id": 2,
                                "pali": "assa",
                                "pos": "pron",
                                "meaning_combo": "of him; his",
                                "ai_score": 10,
                            }
                        ],
                    ],
                    "ai_score": 10,
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "[Deconstructed]" not in table
    assert "*(AI analysis of deconstruction)*" not in table
    assert "dwelling + of him" in table


def test_format_markdown_table_deconstructed_without_component_meaning_uses_placeholder() -> (
    None
):
    analysis = [
        {
            "word": "okassa",
            "status": "found",
            "data": [
                {
                    "key": "w0_decon_okassa_0",
                    "id": "",
                    "pali": "okassa",
                    "pos": "sandhi",
                    "grammar": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "construction": "oka + assa",
                    "components": [],
                    "ai_score": 10,
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "*(AI analysis of deconstruction)*" in table


def test_format_markdown_table_component_overlap_prefers_parent_meaning() -> None:
    analysis = [
        {
            "word": "cetosanti",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "cetosanti",
                    "pos": "noun",
                    "meaning_combo": "peace of mind",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "61527_0",
                                "id": 61527,
                                "pali": "santi",
                                "pos": "ind",
                                "meaning_1": "own; personal; self-",
                                "meaning_combo": "own; personal; self-",
                                "ai_score": 0,
                            },
                            {
                                "key": "58258_0",
                                "id": 58258,
                                "pali": "santi",
                                "pos": "fem",
                                "meaning_1": "peace",
                                "meaning_combo": "peace; calm; tranquillity",
                                "ai_score": 0,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 58258 | - santi | fem | peace; calm; tranquillity |" in table
    assert "| 61527 | - santi | ind | own; personal; self- |" not in table


def test_format_markdown_table_component_overlap_keeps_matching_ind() -> None:
    analysis = [
        {
            "word": "mattam'pi",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "mattam'pi",
                    "pos": "sandhi",
                    "meaning_combo": "even a finger-snap measure",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "13469_0",
                                "id": 13469,
                                "pali": "api",
                                "pos": "ind",
                                "meaning_1": "even",
                                "meaning_combo": "even",
                                "ai_score": 0,
                            },
                            {
                                "key": "999_0",
                                "id": 999,
                                "pali": "api",
                                "pos": "fem",
                                "meaning_1": "water",
                                "meaning_combo": "water",
                                "ai_score": 0,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 13469 | - api | ind | even |" in table


def test_format_markdown_table_component_no_overlap_keeps_ind_fallback() -> None:
    analysis = [
        {
            "word": "testcompound",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "testcompound",
                    "pos": "noun",
                    "meaning_combo": "unrelated compound",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "61527_0",
                                "id": 61527,
                                "pali": "santi",
                                "pos": "ind",
                                "meaning_1": "own; personal; self-",
                                "meaning_combo": "own; personal; self-",
                                "ai_score": 0,
                            },
                            {
                                "key": "58258_0",
                                "id": 58258,
                                "pali": "santi",
                                "pos": "fem",
                                "meaning_1": "peace",
                                "meaning_combo": "peace; calm; tranquillity",
                                "ai_score": 0,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 61527 | - santi | ind | own; personal; self- |" in table


def test_build_system_prompt_json_instruction_at_start() -> None:
    prompt = build_system_prompt([])
    first_line = prompt.strip().splitlines()[0]
    assert "JSON" in first_line


def test_translate_sentence_reformat_triggered_when_prose_returned(
    monkeypatch,
) -> None:
    """When the first response is not JSON, a second reformat request is made."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = "Here is a detailed prose analysis of the verse..."
            else:
                content = '{"translation": "reformatted", "literal_translation": "lit", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert len(calls) == 2
    assert result["translation"] == "reformatted"


def test_reformat_request_sys_prompt_contains_no_tools_instruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = "Here is a detailed prose analysis of the verse..."
            else:
                content = (
                    '{"translation": "reformatted", "literal_translation": "lit", '
                    '"scores": {}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert EXPECTED_NO_TOOLS_INSTRUCTION in calls[1]["prompt_sys"]


def test_translate_sentence_reformat_progress_events(monkeypatch) -> None:
    """Reformat path emits ai_reformat_start and ai_reformat_done progress events."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    events: list[str] = []

    class FakeAIManager:
        def request(self, **kwargs):
            events.append("request")
            if len([e for e in events if e == "request"]) == 1:
                content = "Prose analysis, not JSON."
            else:
                content = '{"translation": "", "literal_translation": "", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        progress=events.append,
    )

    assert "ai_reformat_start" in events
    assert "ai_reformat_done" in events
    assert events.index("ai_reformat_start") < events.index("ai_reformat_done")


def test_translate_sentence_reformat_debug_keys_populated(monkeypatch) -> None:
    """Debug dict gets reformat keys when prose response triggers reformat."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = "Prose, not JSON."
            else:
                content = (
                    '{"translation": "ok", "literal_translation": "ok", "scores": {}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert "reformat_raw_response" in debug
    assert "reformat_status_message" in debug
    assert "reformat_parse_error" in debug
    assert debug["reformat_parse_error"] == ""


def test_translate_sentence_reformat_prefers_salvaged_score_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reformat should not overwrite scores salvaged from full-context output."""
    calls: list[dict[str, Any]] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"translation": "x", "literal_translation": "y", '
                    '"scores": {"60847_0": {"score": 1}, '
                    '"60789_0": {"score": 7}, "60693_0": {"sco'
                )
            else:
                content = (
                    '{"translation": "reformatted", "literal_translation": "lit", '
                    '"scores": {"60847_0": {"score": 8}, '
                    '"60693_0": {"score": 3}}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert debug["final_scores"]["60847_0"]["score"] == 1
    assert debug["final_scores"]["60693_0"]["score"] == 3
    assert debug["final_scores"]["60789_0"]["score"] == 7
    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert component_options[1]["ai_score"] == 7


def test_reformat_merge_fills_gaps_from_reformat_response() -> None:
    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            content = (
                '{"translation": "reformatted", "literal_translation": "lit", '
                '"scores": {"gap_0": {"score": 9}}}'
            )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_core._handle_reformat_response(
        chunk_sentence="atha puriso",
        raw_response='{"translation": "x", "scores": {"kept_0": {"score": 10}',
        analysis=[],
        ai_data={
            "translation": "x",
            "literal_translation": "y",
            "scores": {"kept_0": {"score": 10}},
        },
        parse_error="truncated",
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    assert result["scores"]["kept_0"]["score"] == 10
    assert result["scores"]["gap_0"]["score"] == 9


def test_reformat_strips_contextual_meaning_for_key_only_wrong_schema() -> None:
    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            content = (
                '{"translation": "reformatted", "literal_translation": "lit", '
                '"scores": {"w68_18134_default": {"score": 10, '
                '"contextual_meaning": "disaster", "selected_pos": "noun"}}}'
            )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_core._handle_reformat_response(
        chunk_sentence="evaṃ",
        raw_response='{"selected_keys": ["w68_18134_default"]}',
        analysis=_selected_keys_analysis(),
        ai_data={"selected_keys": ["w68_18134_default"]},
        parse_error="",
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    score = result["scores"]["w68_18134_default"]
    assert score["score"] == 10
    assert "contextual_meaning" not in score
    assert "selected_pos" not in score


def test_reformat_preserves_contextual_meaning_when_source_had_meaning() -> None:
    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            content = (
                '{"translation": "reformatted", "literal_translation": "lit", '
                '"scores": {"w68_18134_default": {"score": 10, '
                '"contextual_meaning": "thus", "selected_pos": "ind"}}}'
            )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_core._handle_reformat_response(
        chunk_sentence="evaṃ",
        raw_response='{"selected_meanings": [{"word": "evaṃ", "meaning": "thus"}]}',
        analysis=_selected_keys_analysis(),
        ai_data={"selected_meanings": [{"word": "evaṃ", "meaning": "thus"}]},
        parse_error="",
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    score = result["scores"]["w68_18134_default"]
    assert score["contextual_meaning"] == "thus"
    assert score["selected_pos"] == "ind"


def test_reformat_preserves_contextual_meaning_for_parse_error() -> None:
    class FakeAIManager:
        def request(self, **_kwargs: Any) -> object:
            content = (
                '{"translation": "reformatted", "literal_translation": "lit", '
                '"scores": {"w68_18134_default": {"score": 10, '
                '"contextual_meaning": "thus", "selected_pos": "ind"}}}'
            )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_core._handle_reformat_response(
        chunk_sentence="evaṃ",
        raw_response='{"translation": "thus", "scores": {"w68_18134_default": {"sco',
        analysis=_selected_keys_analysis(),
        ai_data={"translation": "thus", "scores": {}},
        parse_error="truncated",
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    score = result["scores"]["w68_18134_default"]
    assert score["contextual_meaning"] == "thus"
    assert score["selected_pos"] == "ind"


def test_build_reformat_prompt_includes_valid_keys_block() -> None:
    word_keys_json = '{"atha":["2794_default"],"puriso":["29188_3"]}'

    prompt = translate_core._build_reformat_prompt(
        "atha puriso",
        "Use atha and puriso.",
        word_keys_json,
    )

    assert 'entries may be shown as "key (grammar)"' in prompt
    assert 'keys in "scores" MUST use the key before the first space' in prompt
    assert word_keys_json in prompt


def test_build_reformat_prompt_without_keys_unchanged() -> None:
    prompt = translate_core._build_reformat_prompt(
        "atha puriso",
        "Use atha and puriso.",
        "",
    )

    assert "Valid option keys per word" not in prompt


def test_build_reformat_prompt_contains_no_grammar_notes_instruction() -> None:
    prompt = translate_core._build_reformat_prompt(
        "atha puriso",
        "Use atha and puriso.",
        "",
    )

    assert translate_core.NO_GRAMMAR_NOTES_INSTRUCTION in prompt


def test_build_reformat_prompt_contains_no_invented_context_instruction() -> None:
    prompt = translate_core._build_reformat_prompt(
        "atha puriso",
        "Use atha and puriso.",
        "",
    )

    assert "Do not invent contextual_meaning" in prompt


def test_word_keys_overview_includes_grammar_context() -> None:
    analysis = [
        {
            "word": "kāyassa",
            "data": [
                {"key": "21131_0", "grammar": "masc dat sg"},
                {"key": "21131_1", "grammar": "masc gen sg"},
            ],
        }
    ]

    assert (
        translate_core._word_keys_overview(analysis)
        == '{"kāyassa":["21131_0 (masc dat sg)","21131_1 (masc gen sg)"]}'
    )


def test_word_keys_overview_top_level_only() -> None:
    analysis = [
        {
            "word": "sammāsambuddhassa",
            "data": [
                {
                    "key": "60847_0",
                    "components": [[{"key": "60693_0"}, {"key": "60789_0"}]],
                },
                {"key": "60847_1"},
            ],
        }
    ]

    assert (
        translate_core._word_keys_overview(analysis)
        == '{"sammāsambuddhassa":["60847_0","60847_1"]}'
    )


def test_word_keys_overview_oversize_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.prompts.REFORMAT_KEYS_MAX_CHARS", 10, raising=False
    )
    analysis = [{"word": "sammā", "data": [{"key": "60847_0"}]}]

    assert translate_core._word_keys_overview(analysis) == ""


def test_extract_word_key_map_detects_disambiguation_map() -> None:
    """A flat {word: option_key} map whose values are real keys is recognised."""
    analysis = [
        {"word": "x", "data": [{"key": "35009_0"}, {"key": "62854_0"}]},
    ]

    assert _extract_word_key_map(
        {"dharaṇī": "35009_0", "siñcati": "62854_0"}, analysis
    ) == {"dharaṇī": "35009_0", "siñcati": "62854_0"}


def test_extract_word_key_map_detects_nested_disambiguation_map() -> None:
    """A nested antigravity disambiguation map is recognised."""
    analysis = [
        {"word": "x", "data": [{"key": "35009_0"}, {"key": "62854_0"}]},
    ]

    assert _extract_word_key_map(
        {"disambiguation": {"dharaṇī": "35009_0", "siñcati": "62854_0"}},
        analysis,
    ) == {"dharaṇī": "35009_0", "siñcati": "62854_0"}


def test_extract_word_key_map_rejects_non_map_shapes() -> None:
    """Proper schema, dict-valued, unknown-key, and empty responses are not maps."""
    analysis = [{"word": "x", "data": [{"key": "35009_0"}]}]

    # Proper {translation, scores} schema is not a disambiguation map.
    assert _extract_word_key_map({"translation": "x", "scores": {}}, analysis) is None
    # Dict-valued wrong schema (matches the reformat fallback test) is not a map.
    assert _extract_word_key_map({"passa": {"lemma": "passati"}}, analysis) is None
    # String values that match no real option key are not a map.
    assert _extract_word_key_map({"a": "nope", "b": "nada"}, analysis) is None
    # Empty response is not a map.
    assert _extract_word_key_map({}, analysis) is None
    # No analysis keys to match against → never a map.
    assert _extract_word_key_map({"dharaṇī": "35009_0"}, []) is None


def _structured_selection_analysis() -> list[dict[str, Any]]:
    return [
        {
            "word": "atha",
            "status": "found",
            "data": [
                {
                    "key": "2794_default",
                    "id": 2794,
                    "lemma": "atha",
                    "meaning_combo": "then",
                },
                {
                    "key": "2794_1",
                    "id": 2794,
                    "lemma": "atha 2",
                    "meaning_combo": "moreover",
                },
            ],
        },
        {
            "word": "puriso",
            "status": "found",
            "data": [
                {
                    "key": "29188_3",
                    "id": 29188,
                    "lemma": "purisa 1",
                    "meaning_combo": "man",
                },
                {
                    "key": "29189_0",
                    "id": 29189,
                    "lemma": "purisa 2",
                    "meaning_combo": "soul",
                },
            ],
        },
        {
            "word": "taṃ",
            "status": "found",
            "data": [
                {
                    "key": "42000_0",
                    "id": 42000,
                    "lemma": "ta 1.1",
                    "meaning_combo": "that",
                }
            ],
        },
    ]


def test_structured_selection_disambiguation_list_with_selected_key() -> None:
    ai_data = {
        "disambiguation": [
            {"word": "atha", "selected_key": "2794_default", "meaning": "then"},
            {"word": "puriso", "selected_key": "29188_3", "meaning": "man"},
        ]
    }

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == (
        {"atha": "2794_default", "puriso": "29188_3"},
        {"atha": "then", "puriso": "man"},
    )


def test_structured_selection_meanings_are_stripped() -> None:
    ai_data = {
        "disambiguation": [
            {
                "word": "atha",
                "selected_key": "2794_default",
                "meaning": "then (enclitic emphasizing the transition)",
            },
            {
                "word": "puriso",
                "selected_key": "29188_3",
                "meaning": "man (nominative singular masculine)",
            },
        ]
    }

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == (
        {"atha": "2794_default", "puriso": "29188_3"},
        {"atha": "then", "puriso": "man"},
    )


def test_structured_selection_sentence_analysis_selected_lemma_key() -> None:
    ai_data = {
        "sentence_analysis": [
            {
                "word": "puriso",
                "selected_lemma_key": "29188_3",
                "meaning": "a person",
            }
        ]
    }

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == ({"puriso": "29188_3"}, {"puriso": "a person"})


def test_structured_selection_selected_id_unique_match() -> None:
    ai_data = {"selected_meanings": [{"word": "taṃ", "selected_id": 42000}]}

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == ({"taṃ": "42000_0"}, {})


def test_structured_selection_selected_id_ambiguous_skipped() -> None:
    ai_data = {
        "selected_meanings": [
            {"word": "atha", "selected_id": 2794},
            {"word": "taṃ", "selected_id": 42000},
        ]
    }

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == ({"taṃ": "42000_0"}, {})


def test_structured_selection_gloss_map_lemma_match() -> None:
    ai_data = {
        "puriso": {"lemma": "purisa 1", "meaning": "man"},
        "taṃ": {"lemma": "ta 1.1", "meaning": "that"},
    }

    assert translate_core._extract_structured_selection_map(
        ai_data, _structured_selection_analysis()
    ) == (
        {"puriso": "29188_3", "taṃ": "42000_0"},
        {"puriso": "man", "taṃ": "that"},
    )


def test_structured_selection_gloss_map_ambiguous_lemma_skipped() -> None:
    analysis = _structured_selection_analysis()
    analysis[0]["data"][1]["lemma"] = "atha"
    ai_data = {
        "atha": {"lemma": "atha", "meaning": "then"},
        "taṃ": {"lemma": "ta 1.1", "meaning": "that"},
    }

    assert translate_core._extract_structured_selection_map(ai_data, analysis) == (
        {"taṃ": "42000_0"},
        {"taṃ": "that"},
    )


def test_structured_selection_rejects_proper_schema() -> None:
    ai_data = {
        "translation": "Then the man saw that.",
        "scores": {"29188_3": {"score": 10}},
    }

    assert (
        translate_core._extract_structured_selection_map(
            ai_data, _structured_selection_analysis()
        )
        is None
    )


def test_structured_selection_low_match_ratio_returns_none() -> None:
    ai_data = {
        "selected_meanings": [
            {"word": "atha", "selected_key": "2794_default"},
            {"word": "puriso", "selected_key": "not_real"},
            {"word": "taṃ", "selected_key": "also_not_real"},
        ]
    }

    assert (
        translate_core._extract_structured_selection_map(
            ai_data, _structured_selection_analysis()
        )
        is None
    )


def _selected_keys_analysis() -> list[dict[str, Any]]:
    return [
        {
            "word": "evaṃ",
            "status": "found",
            "data": [
                {
                    "key": "w68_18134_default",
                    "id": 18134,
                    "lemma": "evaṃ",
                    "meaning_combo": "thus",
                },
                {
                    "key": "w68_18135_default",
                    "id": 18135,
                    "lemma": "evaṃ 2",
                    "meaning_combo": "in this way",
                },
            ],
        },
        {
            "word": "dīgharattaṃ",
            "status": "found",
            "data": [
                {
                    "key": "w69_32757_default",
                    "id": 32757,
                    "lemma": "dīgharattaṃ",
                    "meaning_combo": "for a long time",
                }
            ],
        },
        {
            "word": "vo",
            "status": "found",
            "data": [
                {
                    "key": "w70_31017_2",
                    "id": 31017,
                    "lemma": "tumha 2",
                    "meaning_combo": "your",
                }
            ],
        },
    ]


def test_structured_selection_selected_keys_list_maps_top_level_keys() -> None:
    assert translate_core._extract_selected_keys_map(
        {
            "selected_keys": [
                "w68_18134_default",
                "w69_32757_default",
                "w70_31017_2",
            ]
        },
        _selected_keys_analysis(),
    ) == (
        {
            "evaṃ": "w68_18134_default",
            "dīgharattaṃ": "w69_32757_default",
            "vo": "w70_31017_2",
        },
        {},
    )


def test_structured_selection_selected_keys_rejects_duplicate_surface_word() -> None:
    assert (
        translate_core._extract_selected_keys_map(
            {"selected_keys": ["w68_18134_default", "w68_18135_default"]},
            _selected_keys_analysis(),
        )
        is None
    )


def test_structured_selection_selected_keys_requires_enough_valid_keys() -> None:
    assert (
        translate_core._extract_selected_keys_map(
            {
                "selected_keys": [
                    "w68_18134_default",
                    "unknown_1",
                    "unknown_2",
                ]
            },
            _selected_keys_analysis(),
        )
        is None
    )


def test_first_pass_routes_structured_selection_to_compact_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "atha",
                "status": "found",
                "data": [
                    {
                        "key": "2794_default",
                        "id": 2794,
                        "lemma": "atha",
                        "meaning_combo": "then",
                    }
                ],
            },
            {
                "word": "puriso",
                "status": "found",
                "data": [
                    {
                        "key": "29188_3",
                        "id": 29188,
                        "lemma": "purisa 1",
                        "meaning_combo": "man",
                    }
                ],
            },
        ],
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"disambiguation": ['
                    '{"word": "atha", "selected_key": "2794_default"},'
                    '{"word": "puriso", "selected_key": "29188_3"}]}'
                )
            else:
                content = (
                    '{"translation": "Then the man.", '
                    '"literal_translation": "then man.", "meanings": {}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "atha puriso",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert "Translate" in calls[1]["prompt"]
    assert "did not match" not in calls[1]["prompt"]
    assert "reformat_raw_response" not in debug
    assert debug["final_scores"]["2794_default"]["score"] == 10
    assert debug["final_scores"]["29188_3"]["score"] == 10
    assert result["analysis"][0]["data"][0]["ai_score"] == 10
    assert result["analysis"][1]["data"][0]["ai_score"] == 10


def test_first_pass_routes_selected_keys_to_compact_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: _selected_keys_analysis(),
    )
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"selected_keys": ['
                    '"w68_18134_default",'
                    '"w69_32757_default",'
                    '"w70_31017_2"]}'
                )
            else:
                content = (
                    '{"translation": "Thus, for a long time, your ...", '
                    '"literal_translation": "thus long-time your", '
                    '"meanings": {}}'
                )
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()

    debug: dict[str, Any] = {}
    result = translate_sentence(
        "evaṃ dīgharattaṃ vo",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert "Translate" in calls[1]["prompt"]
    assert "did not match" not in calls[1]["prompt"]
    assert "reformat_raw_response" not in debug
    assert debug["final_scores"]["w68_18134_default"]["score"] == 10
    assert debug["final_scores"]["w69_32757_default"]["score"] == 10
    assert debug["final_scores"]["w70_31017_2"]["score"] == 10
    assert result["analysis"][0]["data"][0]["meaning_combo"] == "thus"
    assert result["analysis"][1]["data"][0]["meaning_combo"] == "for a long time"
    assert result["analysis"][2]["data"][0]["meaning_combo"] == "your"


def test_compact_map_prefills_contextual_meaning_from_word_meanings() -> None:
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "Done.", "literal_translation": "Done.", '
                        '"meanings": {"override": "translation meaning"}}'
                    ),
                    "status_message": "ok",
                },
            )()

    ai_data = translate_core._handle_compact_map_response(
        chunk_sentence="prefill override",
        word_key_map={"prefill": "1_0", "override": "2_0"},
        word_meanings={"prefill": "structured meaning", "override": "old meaning"},
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    scores = ai_data["scores"]
    assert len(calls) == 1
    assert scores["1_0"]["contextual_meaning"] == "structured meaning"
    assert scores["2_0"]["contextual_meaning"] == "translation meaning"


def test_translation_prompt_contains_no_grammar_notes_rule() -> None:
    prompt = translate_core._build_translation_prompt("samma")

    assert (
        "Provide ONLY the core meaning. Do NOT append grammatical case notes "
        "in parentheses."
    ) in prompt


def test_translation_prompt_includes_truncated_previous_translation() -> None:
    previous_translation = "start " + ("middle " * 250) + "final sentence."

    prompt = translate_core._build_translation_prompt(
        "dhammo",
        previous_translation=previous_translation,
    )

    assert "Earlier sentences of this passage were already translated as:" in prompt
    assert "Translate ONLY the Pāḷi text given above" in prompt
    assert "final sentence." in prompt
    assert "start" not in prompt


def test_translation_request_sys_prompt_contains_no_tools_instruction() -> None:
    calls: list[dict[str, Any]] = []

    class FakeAIManager:
        def request(self, **kwargs: Any) -> object:
            calls.append(kwargs)
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "Done.", "literal_translation": "Done.", '
                        '"meanings": {}}'
                    ),
                    "status_message": "ok",
                },
            )()

    translate_core._handle_compact_map_response(
        chunk_sentence="atha puriso",
        word_key_map={"atha": "1_0"},
        ai_manager=cast(AIManager, FakeAIManager()),
        model=None,
        provider=None,
        progress=None,
        verbose=False,
        debug={},
    )

    assert EXPECTED_NO_TOOLS_INSTRUCTION in calls[0]["prompt_sys"]


def test_translate_sentence_uses_word_key_map_skips_reformat(monkeypatch) -> None:
    """A word→key first response drives scores directly and fetches only the translation.

    The wasteful prose-reformat round-trip must NOT fire; instead a lightweight
    translation-only call supplies translation/literal_translation.
    """
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth",
                    }
                ],
            },
            {
                "word": "siñcati",
                "status": "found",
                "data": [
                    {
                        "key": "62854_0",
                        "id": 62854,
                        "pali": "siñcati",
                        "pos": "verb",
                        "meaning_combo": "sprinkles",
                    }
                ],
            },
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = '{"dharaṇī": "35009_0", "siñcati": "62854_0"}'
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles."}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    result = translate_sentence(
        "dharaṇī siñcati",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    # Exactly two calls: the map first call + a translation-only call. No retry,
    # because the map already supplies every top-level option key.
    assert len(calls) == 2
    # The second call is the translation prompt, NOT the prose-reformat prompt.
    assert "did not match" not in calls[1]["prompt"]
    assert "Translate" in calls[1]["prompt"]
    # Scores come straight from the discarded-no-longer first call.
    assert result["analysis"][0]["data"][0]["ai_score"] == 10
    assert result["analysis"][1]["data"][0]["ai_score"] == 10
    # Translation comes from the follow-up call.
    assert result["translation"] == "The earth is sprinkled."
    assert result["literal_translation"] == "earth sprinkles."
    # The prose-reformat debug keys are absent because reformat never ran.
    assert "reformat_raw_response" not in debug
    assert debug["translation_raw_response"]


def test_translate_sentence_word_key_map_applies_contextual_meanings(
    monkeypatch,
) -> None:
    """A word→key map path should apply contextual meanings from the follow-up."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth; world; lit. carrier",
                        "example_1": "dharaṇī siñcati.",
                        "source_1": "TH50",
                        "example_2": "",
                        "source_2": "",
                    }
                ],
            }
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = '{"dharaṇī": "35009_0"}'
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles.", '
                    '"meanings": {"dharaṇī": "earth"}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "dharaṇī siñcati.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="TH50",
    )

    option = result["analysis"][0]["data"][0]
    assert '"meanings"' in calls[1]["prompt"]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "earth"
    assert option["selection_source"] == "db_example_source_text_overlap"


def test_translate_sentence_uses_nested_word_key_map_skips_reformat(
    monkeypatch,
) -> None:
    """A nested disambiguation map follows the same translation-only path."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth",
                    }
                ],
            },
            {
                "word": "siñcati",
                "status": "found",
                "data": [
                    {
                        "key": "62854_0",
                        "id": 62854,
                        "pali": "siñcati",
                        "pos": "verb",
                        "meaning_combo": "sprinkles",
                    }
                ],
            },
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"disambiguation": {"dharaṇī": "35009_0", "siñcati": "62854_0"}}'
                )
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles."}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    result = translate_sentence(
        "dharaṇī siñcati",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert "did not match" not in calls[1]["prompt"]
    assert "Translate" in calls[1]["prompt"]
    assert result["analysis"][0]["data"][0]["ai_score"] == 10
    assert result["analysis"][1]["data"][0]["ai_score"] == 10
    assert result["translation"] == "The earth is sprinkled."
    assert result["literal_translation"] == "earth sprinkles."
    assert "reformat_raw_response" not in debug
    assert debug["translation_raw_response"]


def test_translate_sentence_reformat_triggered_on_wrong_schema(monkeypatch) -> None:
    """Valid JSON in the wrong schema (no translation/scores keys) triggers reformat."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = '{"passa": {"lemma": "passati", "meaning": "see"}}'
            else:
                content = '{"translation": "Behold!", "literal_translation": "See!", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "passa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert call_count == 2
    assert result["translation"] == "Behold!"


def test_missing_scores_prompt_specifies_score_object_format() -> None:
    """Retry prompt must include an explicit {"score": N} value format example."""
    missing_groups = [
        {
            "word": "sammā",
            "context": "sammā",
            "missing_keys": ["60789_0"],
            "options": [{"key": "60789_0", "meaning_combo": "rightly"}],
        }
    ]
    prompt = _build_missing_scores_prompt("sammā", missing_groups)
    assert '"score"' in prompt


def test_missing_scores_prompt_requires_contextual_meaning_for_decon_keys() -> None:
    """When missing keys include a decon_ key, prompt must contain contextual_meaning instruction."""
    missing_groups = [
        {
            "word": "okassa",
            "context": "okassa",
            "missing_keys": ["decon_okassa_0"],
            "options": [{"key": "decon_okassa_0", "meaning_combo": "[Deconstructed]"}],
        }
    ]
    prompt = _build_missing_scores_prompt("okassa", missing_groups)
    assert "contextual_meaning" in prompt


def test_translate_sentence_retry_contextual_meaning_applied_to_decon_option(
    monkeypatch,
) -> None:
    """When retry returns contextual_meaning for a decon_ key, meaning_combo is updated."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "okassa",
                "status": "found",
                "data": [
                    {
                        "key": "decon_okassa_0",
                        "id": 0,
                        "pali": "okassa",
                        "pos": "sandhi",
                        "meaning_combo": "[Deconstructed]",
                    }
                ],
            }
        ],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = '{"translation": "to the dwelling", "literal_translation": "to the house", "scores": {}}'
            else:
                content = '{"scores": {"decon_okassa_0": {"score": 10, "contextual_meaning": "to the dwelling"}}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "okassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "to the dwelling"


def test_build_grounded_translation_prompt_contains_sentence_and_word_table() -> None:
    from exporter.analysis.prompts import _build_grounded_translation_prompt

    sentence = "buddho bhagavā."
    word_table = "| buddho | awakened one |\n| bhagavā | blessed one |"

    prompt = _build_grounded_translation_prompt(sentence, word_table)

    assert sentence in prompt
    assert word_table in prompt
    assert "translation" in prompt
    assert "literal_translation" in prompt
