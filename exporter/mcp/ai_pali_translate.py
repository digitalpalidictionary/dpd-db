import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from exporter.mcp.analyzer import analyze_sentence
from tools.ai_open_router import OpenRouterManager


def build_system_prompt(analysis: list[dict[str, Any]], examples: str) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, indent=2)

    prompt = f"""You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to translate a Pāḷi sentence into English using the provided dictionary analysis as your primary context.

### Dictionary Context (Word-by-Word Analysis)
{context_str}

### Examples of Expected Output Format
{examples}

### Instructions:
1. **Analyze the Sentence:** Use the provided word-by-word data (lemmas, parts of speech, and meanings) to understand the grammatical relationships.
2. **Translation:** Provide a fluent, natural English translation.
3. **Literal Translation:** Provide a word-for-word literal translation that preserves Pāḷi word order or syntax as much as possible.
4. **Word-by-Word Analysis Table:** Provide a Markdown table with exactly the following 6 columns:
    1. **ID**: The DPD ID of the headword.
    2. **Word in Sentence**: The word as it appears in the original Pāḷi sentence.
    3. **Grammar**: The specific grammatical role of this word in this sentence.
    4. **Meaning**: The most contextually appropriate English meaning for this word in this sentence.
    5. **Construction**: The compound construction details (e.g., prefix + root + suffix or compound components).
    6. **Root**: The Pāḷi root and its meaning (e.g., √su (hear)).

    **CRITICAL:** Ensure the Markdown table separator row is properly formatted for all 6 columns (e.g., `| :--- | :--- | :--- | :--- | :--- | :--- |`). Do not omit the dashes in any column.
5. **Grammatical Commentary:** Briefly explain any interesting grammatical features, such as sandhi, unusual case usage, or specific nuances from the dictionary that influenced your translation.

Provide your response in a clear, structured format.
"""
    return prompt


def main():
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        print(f"Error: Database not found at {paths.dpd_db_path}")
        sys.exit(1)

    # Load examples
    mcp_dir = Path(__file__).parent
    examples_path = mcp_dir / "examples.md"
    examples_content = ""
    if examples_path.exists():
        examples_content = examples_path.read_text()

    # Create output directory
    output_dir = mcp_dir / "output"
    output_dir.mkdir(exist_ok=True)

    model = "xiaomi/mimo-v2-flash:free"
    ai_manager = OpenRouterManager()

    print("--- Pāḷi AI Translator ---")
    print("Type your sentence and press Enter to translate.")
    print("Type 'x' and press Enter to exit.")
    print("-" * 26)

    while True:
        sentence = input("\nPāḷi sentence: ").strip()
        if sentence.lower() == "x":
            print("Exiting...")
            break
        if not sentence:
            continue

        db_session = get_db_session(paths.dpd_db_path)
        try:
            print(f"Analyzing: {sentence}")
            analysis = analyze_sentence(sentence, db_session)

            print("\n--- Raw Analysis Data (from DB) ---")
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
            print("-----------------------------------\
")

            sys_prompt = build_system_prompt(analysis, examples_content)

            print("--- System Prompt Sent to LLM ---")
            print(sys_prompt)
            print("---------------------------------\
")

            print(f"Requesting translation from {model}...")
            response = ai_manager.request(
                prompt=f"Please translate this sentence: {sentence}",
                model=model,
                prompt_sys=sys_prompt
            )

            if response.content:
                print("\n--- AI Analysis & Translation ---")
                print(response.content)
                print("---------------------------------")
                print(f"\nStatus: {response.status_message}")

                # Save output to file
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                # Clean up sentence for filename: first 10 chars, lower, no special chars
                clean_sentence = re.sub(r"[^a-zA-Z]", "_", sentence[:10].lower()).strip("_")
                filename = f"{timestamp}_{clean_sentence}.md"
                file_path = output_dir / filename
                
                with open(file_path, "w") as f:
                    f.write(f"# Analysis of: {sentence}\n\n")
                    f.write(response.content)
                
                print(f"Output saved to: {file_path}")

            else:
                print(f"\nError: {response.status_message}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            db_session.close()


if __name__ == "__main__":
    main()