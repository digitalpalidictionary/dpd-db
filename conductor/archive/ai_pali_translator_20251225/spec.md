# AI Pāḷi Translator Specification

## Overview
A CLI tool that provides high-quality Pāḷi-to-English translations by combining structured dictionary data with Large Language Models (LLMs). The tool uses the existing DPD analysis logic to provide the LLM with a detailed "word-by-word" context, significantly improving translation accuracy.

## Functional Requirements

### 1. Analysis Integration
- Use `analyze_sentence` from `exporter/mcp/analyzer.py` to get grammatical details for each word in the input sentence.

### 2. Prompt Construction
- **System Prompt:** Define the LLM's role as an expert Pāḷi translator.
- **Context:** Provide the JSON output from the analyzer as the primary linguistic context.
- **Task:** Instruct the LLM to provide:
    - A fluent English translation.
    - A literal translation.
    - A brief commentary on any interesting grammatical features or nuances found in the analysis.

### 3. LLM Interaction
- Use `tools/ai_open_router.py` to send the prompt to OpenRouter.
- **Model:** `xiaomi/mimo-v2-flash:free` (as requested by the user).
- Handle API errors gracefully and provide clear feedback.

### 4. CLI Interface
- Simple command-line input for the Pāḷi sentence.
- Output the translation and analysis in a readable format.

## Acceptance Criteria
- [ ] The script successfully fetches data from DPD for each word.
- [ ] The prompt includes all relevant grammatical fields (lemma, pos, grammar, meaning_combo).
- [ ] The LLM returns a translation that reflects the provided dictionary context.
- [ ] The tool handles words not found in DPD gracefully.
