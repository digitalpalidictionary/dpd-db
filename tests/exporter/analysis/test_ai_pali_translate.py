"""Verify AI translation merge helpers and mocked translation flow."""

from unittest.mock import MagicMock, patch

from exporter.analysis.translate_core import (
    merge_ai_selections,
    pre_match_db_examples,
    translate_sentence,
)


def test_merge_simple_selection() -> None:
    """Test merging a simple top-level selection via scores map."""
    analysis_data = [
        {
            "word": "buddho",
            "data": [
                {
                    "key": "123_0",
                    "lemma": "buddha",
                    "grammar": "nom sg",
                    "components": [],
                },
                {
                    "key": "123_1",
                    "lemma": "buddha",
                    "grammar": "voc sg",
                    "components": [],
                },
            ],
        }
    ]

    ai_response = {
        "translation": "The Buddha",
        "literal_translation": "Awakened One",
        "scores": {
            "123_0": {
                "score": 10,
                "contextual_meaning": "The Awakened One",
                "selected_pos": "masc",
            },
            "123_1": {"score": 2},
        },
    }

    result = merge_ai_selections(analysis_data, ai_response)

    assert result["translation"] == "The Buddha"
    assert result["literal_translation"] == "Awakened One"
    word_data = result["analysis"][0]["data"]
    assert word_data[0]["ai_score"] == 10
    assert word_data[0]["meaning_combo"] == "The Awakened One"
    assert word_data[0]["selected_pos"] == "masc"
    assert word_data[1]["ai_score"] == 2


def test_merge_component_selection() -> None:
    """Test merging scores for compound components."""
    analysis_data = [
        {
            "word": "compoundword",
            "data": [
                {
                    "key": "999_0",
                    "lemma": "compound",
                    "components": [
                        [
                            {"key": "10_0", "lemma": "part1"},
                            {"key": "10_1", "lemma": "part1"},
                        ],
                        [{"key": "20_0", "lemma": "part2"}],
                    ],
                }
            ],
        }
    ]

    ai_response = {
        "translation": "Compound Word",
        "literal_translation": "",
        "scores": {
            "999_0": {"score": 10},
            "10_1": {"score": 10, "contextual_meaning": "part one chosen"},
            "10_0": {"score": 3},
            "20_0": {"score": 10},
        },
    }

    result = merge_ai_selections(analysis_data, ai_response)

    main_entry = result["analysis"][0]["data"][0]
    assert main_entry["ai_score"] == 10
    comp1_opts = main_entry["components"][0]
    assert comp1_opts[0]["ai_score"] == 3
    assert comp1_opts[1]["ai_score"] == 10
    assert comp1_opts[1]["meaning_combo"] == "part one chosen"
    comp2_opts = main_entry["components"][1]
    assert comp2_opts[0]["ai_score"] == 10


def test_merge_deconstruction_selection() -> None:
    """Test merging a decon_ key with AI-provided contextual_meaning."""
    analysis_data = [
        {
            "word": "vihareyyan'ti",
            "data": [
                {
                    "key": "decon_vihareyyan'ti_0",
                    "id": "",
                    "pos": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "components": [[{"key": "69661_0", "lemma": "viharati"}]],
                }
            ],
        }
    ]

    ai_response = {
        "translation": "I would dwell thus",
        "literal_translation": "",
        "scores": {
            "decon_vihareyyan'ti_0": {
                "score": 10,
                "contextual_meaning": "I would dwell thus",
                "selected_pos": "sandhi",
            },
            "69661_0": {"score": 10, "contextual_meaning": "I would dwell"},
        },
    }

    result = merge_ai_selections(analysis_data, ai_response)

    entry = result["analysis"][0]["data"][0]
    assert entry["ai_score"] == 10
    assert entry["meaning_combo"] == "I would dwell thus"
    assert entry["selected_pos"] == "sandhi"
    comp_entry = entry["components"][0][0]
    assert comp_entry["ai_score"] == 10
    assert comp_entry["meaning_combo"] == "I would dwell"


def test_merge_missing_score_defaults_to_none() -> None:
    """Options not in scores map get ai_score=None."""
    analysis_data = [
        {
            "word": "test",
            "data": [
                {"key": "1_0"},
                {"key": "1_1"},
            ],
        }
    ]
    ai_response = {
        "translation": "",
        "literal_translation": "",
        "scores": {"1_0": {"score": 7}},
    }
    result = merge_ai_selections(analysis_data, ai_response)
    data = result["analysis"][0]["data"]
    assert data[0]["ai_score"] == 7
    assert data[1]["ai_score"] is None


def test_pre_match_db_examples_source_1() -> None:
    """Options whose source_1 matches verse_source get preselected."""
    analysis = [
        {
            "word": "susamāhito",
            "data": [
                {
                    "key": "64447_default",
                    "source_1": "DHP5",
                    "source_2": "",
                    "example_1": "not matching",
                },
                {
                    "key": "64446_default",
                    "source_1": "DHP10",
                    "source_2": "",
                    "example_1": "susamāhito",
                },
            ],
        }
    ]
    pre_match_db_examples(analysis, "DHP10", "susamāhito")
    data = analysis[0]["data"]
    assert data[0].get("ai_score", 0) == 0
    assert "db_example_match" not in data[0]
    assert data[1]["ai_score"] == 10
    assert data[1]["db_example_match"] is True


def test_pre_match_db_examples_source_2() -> None:
    """Match also works via source_2."""
    analysis = [
        {
            "word": "damma",
            "data": [
                {
                    "key": "99_default",
                    "source_1": "DHP1",
                    "source_2": "DHP10",
                    "example_2": "damma",
                },
            ],
        }
    ]
    pre_match_db_examples(analysis, "DHP10", "damma")
    assert analysis[0]["data"][0]["ai_score"] == 10
    assert analysis[0]["data"][0]["db_example_match"] is True


def test_pre_match_db_examples_no_match() -> None:
    """Options with no matching source are untouched."""
    analysis = [
        {
            "word": "test",
            "data": [
                {"key": "1_0", "source_1": "MN1", "source_2": "", "example_1": "test"}
            ],
        }
    ]
    pre_match_db_examples(analysis, "DHP10", "mismatch")
    assert "ai_score" not in analysis[0]["data"][0]
    assert "db_example_match" not in analysis[0]["data"][0]


def test_translate_sentence_flow() -> None:
    """Test the full pipeline with mocked AI and DB calls."""
    mock_session = MagicMock()
    analysis_stub = [
        {"word": "test", "data": [{"key": "1_0", "source_1": "", "source_2": ""}]}
    ]
    ai_json = '{"translation": "Test", "literal_translation": "lit", "scores": {"1_0": {"score": 10}}}'

    with patch(
        "exporter.analysis.translate_core.analyze_sentence", return_value=analysis_stub
    ):
        mock_manager = MagicMock()
        mock_response = MagicMock()
        mock_response.content = ai_json
        mock_manager.request.return_value = mock_response

        result = translate_sentence(
            "test sentence", mock_session, ai_manager=mock_manager, verse_source="DHP1"
        )

        assert result["translation"] == "Test"
        assert result["analysis"][0]["data"][0]["ai_score"] == 10
