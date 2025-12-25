"""Tests for AI response parsing in proofreader."""

import json
from unittest.mock import MagicMock
import pytest
from tools.proofreader import process_batch, batch_data, construct_prompt
from tools.ai_manager import AIResponse

def test_batch_data():
    """Test batching logic."""
    data = [{"id": i} for i in range(10)]
    batches = batch_data(data, batch_size=3)
    assert len(batches) == 4
    assert len(batches[0]) == 3
    assert len(batches[-1]) == 1

def test_construct_prompt():
    """Test prompt construction."""
    batch = [{"id": 1, "meaning_1": "test"}]
    prompt = construct_prompt(batch)
    assert "Correct the spelling and grammar" in prompt
    assert '"id": 1' in prompt
    assert '"meaning_1": "test"' in prompt

def test_process_batch_success():
    """Test successful AI response parsing."""
    mock_gemini = MagicMock()
    batch = [{"id": 1, "meaning_1": "eror"}]
    mock_content = json.dumps([{"id": 1, "meaning_1_corrected": "error"}])
    mock_gemini.request.return_value = AIResponse(content=mock_content, status_message="Success")
    
    results = process_batch(mock_gemini, batch)
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["meaning_1_corrected"] == "error"

def test_process_batch_markdown():
    """Test AI response parsing with markdown blocks."""
    mock_gemini = MagicMock()
    batch = [{"id": 1}]
    mock_content = "```json\n" + json.dumps([{"id": 1, "meaning_1_corrected": "fixed"}]) + "\n```"
    mock_gemini.request.return_value = AIResponse(content=mock_content, status_message="Success")
    
    results = process_batch(mock_gemini, batch)
    assert len(results) == 1
    assert results[0]["meaning_1_corrected"] == "fixed"

def test_process_batch_error():
    """Test handling of invalid JSON response."""
    mock_gemini = MagicMock()
    batch = [{"id": 1}]
    mock_gemini.request.return_value = AIResponse(content="not json", status_message="Success")
    
    results = process_batch(mock_gemini, batch)
    assert results == []
