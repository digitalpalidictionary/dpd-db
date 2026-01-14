import copy
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
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
2. **Disambiguate:** For each word in the sentence, identify the correct dictionary option (`key`).
3. **Score Options:** 
   - Assign a score of **10** to the correct `key` for the context.
   - Assign lower scores (0-9) to alternative options if there is ambiguity.
   - Assign **10** to the correct `key` for *components* of compounds as well.
4. **Contextualize:**
   - **`contextual_meaning`**: Adjust the dictionary `meaning_combo` to fit the grammar (e.g., "dwells" -> "I would dwell").
     - **CRITICAL:** Do this for the main word AND for any components that are **sandhi** (pos: "sandhi"). 
     - You do NOT need to adjust meanings for standard compound components unless necessary for clarity.
   - **`selected_pos`**: If `pos` is "sandhi/compound", specify "sandhi" or "compound".
5. **Handle Deconstructions (MANDATORY):** If an option key starts with `decon_` or has `meaning_combo: "[Deconstructed]"`, you **MUST** provide a full English translation of that sandhi/compound in the `contextual_meaning` field. 
   - **NEVER** leave a `decon_` key with a score of 10 without providing its `contextual_meaning`.
   - **Example:** If `okassa` is deconstructed as `oka + assa`, `contextual_meaning` should be something like "to the house" or "of the dwelling".

### Output Format:
Return a JSON object with translations and a flat map of **scores** keyed by the option `key`.

```json
{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",
  "scores": {{
    "decon_word_0": {{ 
      "score": 10, 
      "contextual_meaning": "Full meaning of the deconstruction", 
      "selected_pos": "sandhi" 
    }},
    "12345_0": {{ 
      "score": 10, 
      "contextual_meaning": "I would dwell", 
      "selected_pos": "verb" 
    }}
  }}
}}
```
**CRITICAL:**
- **Keys in `scores` MUST match the `key` values in the Dictionary Context.**
- Only output the JSON object. Do not explain.
"""
    return prompt


def format_markdown_table(
    enriched_analysis: list[dict[str, Any]]
) -> str:
    """
    Reconstruct the Markdown table using the enriched Python structure.
    We iterate through the Python data (which contains all components)
    and simply pick the highest-scored option to display.
    """

    table_rows = [
        "| ID | Word in Sentence | Grammar | Meaning | Construction | Root |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def add_rows_recursive(option: dict[str, Any], depth: int):
        if "components" in option:
            for part_options in option["components"]:
                if not part_options:
                    continue
                
                # Each part has multiple lookups (homonyms). Pick the best scored one.
                best_part = max(part_options, key=lambda x: x.get("ai_score", 0))
                
                # Format component row
                clean_comp_word = best_part.get("pali", "").replace("- ", "").strip()
                indent_prefix = "- " * depth
                
                comp_meaning = best_part.get("meaning_combo", "")
                
                # Cleanup if AI failed to provide a meaning for a deconstruction
                if not comp_meaning and best_part.get("key", "").startswith("decon_"):
                     comp_meaning = "*(AI analysis of deconstruction)*"

                # Prefer grammar (for sandhi/comp vb), fallback to POS (for pure compound parts)
                comp_grammar = best_part.get("grammar") or best_part.get("pos", "")
                
                if "selected_pos" in best_part and best_part["selected_pos"]:
                     if comp_grammar == "sandhi/compound":
                         comp_grammar = best_part["selected_pos"]
                
                # Construction Column: prefer compound_construction if available, else construction
                comp_construction = best_part.get("compound_construction", "")
                if not comp_construction:
                    comp_construction = best_part.get("construction", "")
                # Clean up formatting if needed (though analyzer usually sends clean strings for construction)
                comp_construction = comp_construction.replace("<b>", "").replace("</b>", "")

                table_rows.append(
                    f"| {best_part.get('id', '')} | {indent_prefix}{clean_comp_word} | {comp_grammar} | {comp_meaning} | {comp_construction} | {best_part.get('root_key', '')} |"
                )
                
                # Recurse
                add_rows_recursive(best_part, depth + 1)

    for token_data in enriched_analysis:
        word = token_data["word"]
        options = token_data["data"]
        
        if not options:
             table_rows.append(f"| | {word} | | | | |")
             continue

        # Sort options by AI score (desc), then by completeness/original score
        # We assume 'ai_score' has been merged into the options. Default to 0.
        best_option = max(options, key=lambda x: x.get("ai_score", 0))
        
        # Determine values to display
        hw_id = best_option.get("id", "")
        meaning = best_option.get("meaning_combo", "")
        
        # Cleanup if AI failed to provide a meaning for a deconstruction
        if not meaning and best_option.get("key", "").startswith("decon_"):
             meaning = "*(AI analysis of deconstruction)*"
             
        grammar = best_option.get("grammar", "")
        
        # Handle POS override
        if "selected_pos" in best_option and best_option["selected_pos"]:
             if grammar == "sandhi/compound":
                 grammar = best_option["selected_pos"]
        
        # Construction Column: prefer compound_construction if available
        construction = best_option.get("compound_construction", "")
        if not construction:
            construction = best_option.get("construction", "")
        construction = construction.replace("<b>", "").replace("</b>", "")

        table_rows.append(
            f"| {hw_id} | {word} | {grammar} | {meaning} | {construction} | {best_option.get('root_key', '')} |"
        )

        # Start Recursion
        add_rows_recursive(best_option, 1)

    return "\n".join(table_rows)


def merge_ai_selections(analysis_data: list[dict[str, Any]], ai_response: dict[str, Any]) -> dict[str, Any]:
    """
    Merge AI scores and meanings into the analysis data structure.
    Returns a new object containing translation and the enriched analysis.
    """
    # Create a deep copy to avoid mutating the original input
    enriched_analysis = copy.deepcopy(analysis_data)
    scores_map = ai_response.get("scores", {})

    # Helper to traverse and update
    def update_entries(data_list):
        for item in data_list:
            key = item.get("key")
            if key in scores_map:
                update = scores_map[key]
                item["ai_score"] = update.get("score", 0)
                
                # Apply contextual info if score is positive (implying relevance)
                if update.get("score", 0) > 0:
                    if "contextual_meaning" in update:
                        item["meaning_combo"] = update["contextual_meaning"]
                    if "selected_pos" in update:
                        item["selected_pos"] = update["selected_pos"]
            else:
                item["ai_score"] = 0

            # Recursively update components
            if "components" in item:
                for comp_list in item["components"]:
                    if isinstance(comp_list, list):
                        update_entries(comp_list)

    for word_obj in enriched_analysis:
        update_entries(word_obj["data"])

    return {
        "translation": ai_response.get("translation", ""),
        "literal_translation": ai_response.get("literal_translation", ""),
        "analysis": enriched_analysis
    }


def translate_sentence(sentence: str, db_session: Session, model: str = "xiaomi/mimo-v2-flash:free") -> dict[str, Any]:
    """
    Full pipeline: Analyze -> AI Translate -> Merge.
    Returns the enriched analysis object.
    """
    # 1. Analyze
    analysis = analyze_sentence(sentence, db_session)
    
    # 2. Build Prompt
    sys_prompt = build_system_prompt(analysis)
    
    # 3. Call AI
    ai_manager = OpenRouterManager()
    
    response = ai_manager.request(
        prompt=f"Please translate and analyze: {sentence}",
        model=model,
        prompt_sys=sys_prompt,
    )
    
    if not response.content:
        raise ValueError(f"AI Request Failed: {response.status_message}")
        
    # 4. Parse Response
    json_str = response.content.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:-3].strip()
    elif json_str.startswith("```"):
        json_str = json_str[3:-3].strip()
        
    try:
        ai_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from AI: {e}\nResponse: {response.content}")
        
    # 5. Merge
    result = merge_ai_selections(analysis, ai_data)
    return result


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

                    # 5. Merge (Logic duplicated from translate_sentence for standalone main)
                    # Ideally we should just call translate_sentence but here we want streaming/print control
                    # Let's just use the merge function we defined
                    merged_result = merge_ai_selections(analysis, ai_data)
                    enriched_analysis = merged_result["analysis"]

                    # Generate final report
                    report = []
                    report.append(f"### English Translation")
                    report.append(f"**Translation:** {merged_result.get('translation', '')}")
                    report.append(
                        f"**Literal Translation:** {merged_result.get('literal_translation', '')}"
                    )
                    report.append("\n### Word-by-Word Analysis")
                    report.append(format_markdown_table(enriched_analysis))

                    final_content = "\n\n".join(report)

                    print("\n--- Final Analysis & Translation ---")
                    print(final_content)
                    print("---------------------------------")

                    # Save output to file
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    clean_sentence = re.sub(r"[^a-zA-Z]", "_", sentence[:10].lower()).strip(
                        "_"
                    )
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