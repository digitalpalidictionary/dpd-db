from unittest.mock import MagicMock, patch
from exporter.mcp.ai_pali_translate import merge_ai_selections, translate_sentence


def test_merge_simple_selection():
    """Test merging a simple top-level selection."""
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
        "analysis": [
            {
                "word": "buddho",
                "selected_key": "123_0",
                "contextual_meaning": "The Awakened One (nom sg)",
                "selected_pos": "masc",
            }
        ],
    }

    result = merge_ai_selections(analysis_data, ai_response)

    assert result["translation"] == "The Buddha"
    assert result["literal_translation"] == "Awakened One"

    # Check selected flag and adjusted values
    word_data = result["analysis"][0]["data"]
    assert word_data[0]["selected"] is True
    assert word_data[0]["meaning_combo"] == "The Awakened One (nom sg)"
    assert word_data[0]["pos"] == "masc"
    assert word_data[1].get("selected") is None or word_data[1]["selected"] is False


def test_merge_component_selection():
    """Test merging selections for compound components."""
    analysis_data = [
        {
            "word": "compoundword",
            "data": [
                {
                    "key": "999_0",
                    "lemma": "compound",
                    "components": [
                        [  # Component 1 options
                            {"key": "10_0", "lemma": "part1", "grammar": "opt1"},
                            {"key": "10_1", "lemma": "part1", "grammar": "opt2"},
                        ],
                        [  # Component 2 options
                            {"key": "20_0", "lemma": "part2", "grammar": "optA"}
                        ],
                    ],
                }
            ],
        }
    ]

    ai_response = {
        "translation": "Compound Word",
        "analysis": [
            {
                "word": "compoundword",
                "selected_key": "999_0",
                "components": [
                    {"word": "part1", "selected_key": "10_1"},
                    {"word": "part2", "selected_key": "20_0"},
                ],
            }
        ],
    }

    result = merge_ai_selections(analysis_data, ai_response)

    main_entry = result["analysis"][0]["data"][0]
    assert main_entry["selected"] is True

    # Check component 1
    comp1_opts = main_entry["components"][0]
    assert comp1_opts[0].get("selected") is None
    assert comp1_opts[1]["selected"] is True

    # Check component 2
    comp2_opts = main_entry["components"][1]
    assert comp2_opts[0]["selected"] is True


def test_merge_deconstruction_selection():
    """Test merging selections for deconstructions with AI-provided meanings."""
    analysis_data = [
        {
            "word": "vihareyyan'ti",
            "data": [
                {
                    "key": "decon_vihareyyan'ti_0",
                    "id": "",
                    "pali": "vihareyyan'ti",
                    "pos": "sandhi/compound",
                    "meaning_combo": "[Deconstructed]",
                    "components": [
                        [
                            {
                                "key": "69661_0",
                                "lemma": "viharati",
                                "grammar": "opt 1st sg",
                            }
                        ]
                    ],
                }
            ],
        }
    ]

    ai_response = {
        "translation": "I would dwell thus",
        "analysis": [
            {
                "word": "vihareyyan'ti",
                "selected_key": "decon_vihareyyan'ti_0",
                "contextual_meaning": "I would dwell thus",
                "selected_pos": "sandhi",
                "components": [
                    {
                        "word": "vihareyyaṃ",
                        "selected_key": "69661_0",
                        "contextual_meaning": "I would dwell",
                    }
                ],
            }
        ],
    }

    result = merge_ai_selections(analysis_data, ai_response)

    entry = result["analysis"][0]["data"][0]
    assert entry["selected"] is True
    assert entry["meaning_combo"] == "I would dwell thus"
    assert entry["pos"] == "sandhi"

    comp_entry = entry["components"][0][0]
    assert comp_entry["selected"] is True
    assert comp_entry["meaning_combo"] == "I would dwell"


def test_translate_sentence_flow():
    """Test the full pipeline with mocked AI call."""
    mock_session = MagicMock()

    # Mock analyze_sentence to return valid data
    with patch("exporter.mcp.ai_pali_translate.analyze_sentence") as mock_analyze:
        mock_analyze.return_value = [{"word": "test", "data": [{"key": "1_0"}]}]

        # Mock OpenRouterManager
        with patch("exporter.mcp.ai_pali_translate.OpenRouterManager") as MockManager:
            mock_instance = MockManager.return_value
            # Set attributes on the returned object from request()
            mock_response = MagicMock()
            mock_response.content = '{"translation": "Test", "analysis": [{"word": "test", "selected_key": "1_0"}]}'
            mock_instance.request.return_value = mock_response

            result = translate_sentence("test sentence", mock_session)

            assert result["translation"] == "Test"
            assert result["analysis"][0]["data"][0]["selected"] is True
