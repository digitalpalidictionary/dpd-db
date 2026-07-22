"""Tests for AI response parsing in proofreader."""

import json
from unittest.mock import MagicMock
from tools.proofreader import process_batch, batch_data, construct_prompt
from tools.ai_manager import AIResponse


def test_batch_data() -> None:
    """Test batching logic."""
    data = [{"id": i} for i in range(10)]
    batches = batch_data(data, batch_size=3)
    assert len(batches) == 4
    assert len(batches[0]) == 3
    assert len(batches[-1]) == 1


def test_construct_prompt() -> None:
    """Test prompt construction."""
    batch = [{"id": 1, "meaning_1": "test"}]
    prompt = construct_prompt(batch)
    assert "British" in prompt
    assert "omit that entry" in prompt
    assert "Do NOT rewrite for style" in prompt
    assert '"id": 1' in prompt
    assert '"meaning_1": "test"' in prompt


def test_process_batch_success() -> None:
    """Test successful AI response parsing on the primary model."""
    mock_ai_manager = MagicMock()
    batch = [{"id": 1, "meaning_1": "eror"}]
    mock_content = json.dumps([{"id": 1, "meaning_1_corrected": "error"}])
    mock_ai_manager.request.return_value = AIResponse(
        content=mock_content, status_message="Success"
    )

    success, results = process_batch(mock_ai_manager, batch)
    assert success is True
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["meaning_1_corrected"] == "error"
    assert mock_ai_manager.request.call_count == 1


def test_process_batch_success_with_no_corrections() -> None:
    """A valid response that lists nothing to fix is still a success."""
    mock_ai_manager = MagicMock()
    batch = [{"id": 1, "meaning_1": "already correct"}]
    mock_ai_manager.request.return_value = AIResponse(
        content="[]", status_message="Success"
    )

    success, results = process_batch(mock_ai_manager, batch)
    assert success is True
    assert results == []
    assert mock_ai_manager.request.call_count == 1


def test_process_batch_markdown() -> None:
    """Test AI response parsing with markdown blocks."""
    mock_ai_manager = MagicMock()
    batch = [{"id": 1}]
    mock_content = (
        "```json\n" + json.dumps([{"id": 1, "meaning_1_corrected": "fixed"}]) + "\n```"
    )
    mock_ai_manager.request.return_value = AIResponse(
        content=mock_content, status_message="Success"
    )

    success, results = process_batch(mock_ai_manager, batch)
    assert success is True
    assert len(results) == 1
    assert results[0]["meaning_1_corrected"] == "fixed"


def test_process_batch_error() -> None:
    """Test handling of invalid JSON response from both models — a hard failure."""
    mock_ai_manager = MagicMock()
    batch = [{"id": 1}]
    mock_ai_manager.request.return_value = AIResponse(
        content="not json", status_message="Success"
    )

    success, results = process_batch(mock_ai_manager, batch)
    assert success is False
    assert results == []
    assert mock_ai_manager.request.call_count == 2


def test_process_batch_falls_back_to_secondary_model() -> None:
    """Primary model failure should retry the same batch on the fallback model."""
    mock_ai_manager = MagicMock()
    batch = [{"id": 1, "meaning_1": "eror"}]
    mock_content = json.dumps([{"id": 1, "meaning_1_corrected": "error"}])
    mock_ai_manager.request.side_effect = [
        AIResponse(content=None, status_message="primary failed"),
        AIResponse(content=mock_content, status_message="Success"),
    ]

    success, results = process_batch(mock_ai_manager, batch)
    assert success is True
    assert len(results) == 1
    assert results[0]["meaning_1_corrected"] == "error"
    assert mock_ai_manager.request.call_count == 2

    first_call_kwargs = mock_ai_manager.request.call_args_list[0].kwargs
    second_call_kwargs = mock_ai_manager.request.call_args_list[1].kwargs
    assert first_call_kwargs["provider_preference"] == "zai"
    assert first_call_kwargs["model"] == "glm-5.2"
    assert second_call_kwargs["provider_preference"] == "deepseek"
    assert second_call_kwargs["model"] == "deepseek-v4-flash"
