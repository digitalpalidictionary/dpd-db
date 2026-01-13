import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from exporter.mcp.analyzer import analyze_sentence
from tools.ai_open_router import OpenRouterManager


def build_system_prompt(analysis: list[dict[str, Any]]) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, indent=2)

    prompt = f"""You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to analyze a Pāḷi sentence and perform word-sense disambiguation using the provided dictionary analysis.

### Dictionary Context (Word-by-Word Analysis Options)
{context_str}

### Instructions:
1. **Analyze the Sentence:** Use the context to understand grammatical relationships.
2. **Disambiguate:** For each word in the sentence, review the provided options. Each option has a unique `key` and specific grammatical info.
3. **Select Best Option:** Select the single `key` that corresponds to the correct meaning AND specific grammatical form (case, number, etc.) for the context.
4. **Handle Compounds/Sandhi:** If a word has components, select the correct `key` for each component as well.
5. **Output Format:** You **MUST** respond with a JSON object exactly in this format:
```json
{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",
  "analysis": [
    {{
      "word": "word_in_sentence",
      "selected_key": "12345_0", 
      "components": [
        {{ "word": "part1", "selected_key": "67890_default" }},
        {{ "word": "part2", "selected_key": "11223_1" }}
      ]
    }}
  ]
}}
```
**CRITICAL:**
- Only output the JSON object.
- `selected_key` must match one of the `key` values provided in the Dictionary Context.
- If a word is found via deconstruction (e.g. `decon_...`), select that key.
- Do not paraphrase or add data; only provide the keys.
"""
    return prompt


def format_markdown_table(
    analysis_data: list[dict[str, Any]], ai_response: dict[str, Any]
) -> str:
    """Reconstruct the Markdown table using AI's selections and DB data."""

    # Build a structured lookup: word -> key -> entry_data
    # This ensures we find the exact specific-grammar option the AI picked.
    token_map = {}

    # Also build a global key lookup for components, as they might be shared or found via deconstruction
    global_key_lookup = {}

    for token_data in analysis_data:
        word = token_data["word"]
        if word not in token_map:
            token_map[word] = {}

        for entry in token_data["data"]:
            entry_key = entry["key"]
            token_map[word][entry_key] = entry
            global_key_lookup[entry_key] = entry

            if "components" in entry:
                for comp_options in entry["components"]:
                    if isinstance(comp_options, list):
                        for comp in comp_options:
                            comp_key = comp.get("key")
                            if comp_key:
                                global_key_lookup[comp_key] = comp

    table_rows = [
        "| ID | Word in Sentence | Grammar | Meaning | Construction | Root |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for selection in ai_response.get("analysis", []):
        word = selection["word"]
        selected_key = str(selection.get("selected_key", ""))

        # Find the main word entry
        hw = None
        if word in token_map and selected_key in token_map[word]:
            hw = token_map[word][selected_key]

        if hw:
            # Use specific grammar from the selected option
            grammar = hw.get("grammar", "")
            table_rows.append(
                f"| {hw.get('id', '')} | {word} | {grammar} | {hw['meaning_combo']} | {hw['construction']} | {hw.get('root_key', '')} |"
            )
        else:
            # Fallback
            table_rows.append(f"| | {word} | | | | |")

        # Component rows
        for comp_sel in selection.get("components", []):
            comp_word = comp_sel["word"]
            # AI might return the word with hyphen, strip it for lookup if needed
            clean_comp_word = comp_word.replace("- ", "").strip()

            comp_key = str(comp_sel.get("selected_key", ""))

            chw = None
            if comp_key in global_key_lookup:
                chw = global_key_lookup[comp_key]

            # Fallback check within parent's components if we have the parent
            if not chw and hw and "components" in hw:
                for comp_options in hw["components"]:
                    for comp in comp_options:
                        if comp.get("key") == comp_key:
                            chw = comp
                            break
                    if chw:
                        break

            if chw:
                grammar = chw.get("grammar", "")
                # Ensure "in comp" prefix if not present, unless it's a sandhi component which might be different?
                # Actually DB usually says "in comp" or user wants it.
                # Let's trust the DB value first. If it looks like a stem, maybe prepend "in comp"?
                # User requested "- " prefix for word.
                table_rows.append(
                    f"| {chw.get('id', '')} | - {clean_comp_word} | {grammar} | {chw['meaning_combo']} | {chw['construction']} | {chw.get('root_key', '')} |"
                )
            else:
                table_rows.append(f"| | - {clean_comp_word} | | | | |")

    return "\n".join(table_rows)


def main():
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        print(f"Error: Database not found at {paths.dpd_db_path}")
        sys.exit(1)

    # Create output directory
    mcp_dir = Path(__file__).parent
    output_dir = mcp_dir / "output"
    output_dir.mkdir(exist_ok=True)

    model = "xiaomi/mimo-v2-flash:free"
    ai_manager = OpenRouterManager()

    print("--- Pāḷi AI Translator (Strict Mode) ---")
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

            sys_prompt = build_system_prompt(analysis)

            print(f"Requesting translation and disambiguation from {model}...")
            response = ai_manager.request(
                prompt=f"Please translate and analyze: {sentence}",
                model=model,
                prompt_sys=sys_prompt,
            )

            if response.content:
                # Attempt to parse JSON from response
                try:
                    # Clean up possible markdown code blocks
                    json_str = response.content.strip()
                    if json_str.startswith("```json"):
                        json_str = json_str[7:-3].strip()
                    elif json_str.startswith("```"):
                        json_str = json_str[3:-3].strip()

                    ai_data = json.loads(json_str)

                    # Generate final report
                    report = []
                    report.append(f"### English Translation")
                    report.append(f"**Translation:** {ai_data.get('translation', '')}")
                    report.append(
                        f"**Literal Translation:** {ai_data.get('literal_translation', '')}"
                    )
                    report.append("\n### Word-by-Word Analysis")
                    report.append(format_markdown_table(analysis, ai_data))

                    final_content = "\n\n".join(report)

                    print("\n--- Final Analysis & Translation ---")
                    print(final_content)
                    print("---------------------------------")

                    # Save output to file
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    clean_sentence = re.sub(
                        r"[^a-zA-Z]", "_", sentence[:10].lower()
                    ).strip("_")
                    filename = f"{timestamp}_{clean_sentence}.md"
                    file_path = output_dir / filename

                    with open(file_path, "w") as f:
                        f.write(f"# Analysis of: {sentence}\n\n")
                        f.write(final_content)

                    print(f"Output saved to: {file_path}")

                except json.JSONDecodeError as je:
                    print(f"Error parsing AI JSON response: {je}")
                    print("Raw response:")
                    print(response.content)

            else:
                print(f"\nError: {response.status_message}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()
        finally:
            db_session.close()


if __name__ == "__main__":
    main()
