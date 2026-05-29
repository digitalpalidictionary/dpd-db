# Pali Passage Analysis

This folder contains the standalone DPD-backed Pali analysis pipeline.

The tools here are for taking a CST passage or local text, producing an
editable word-by-word study report, then exporting selected words to TSV/CSV
for Anki or another flashcard workflow. The MCP server still lives in
`exporter/mcp/`, but the passage-analysis and AI-translation logic has moved
out of MCP so it can run as ordinary command-line exporter tools.

## What Changed

The old MCP analysis scripts were split into two responsibilities:

- `exporter/analysis/` now owns passage extraction, DPD lookup analysis, AI
  scoring, markdown reports, and word-list export.
- `exporter/mcp/` now stays small and only exposes the MCP server entry point.
  It imports `analyze_sentence()` from `exporter.analysis.analyzer`.

This makes the analyzer usable without starting an MCP server and keeps report
generation, batch processing, and CSV export in one dedicated exporter folder.

## Runtime Folders

The first script run creates these folders automatically:

- `input/` - source text files and verse JSON extracted from CST.
- `reports/` - editable markdown study reports from Stage 1.
- `output/` - AI JSON, rendered markdown, and Stage 2 TSV/CSV exports.

Existing data from the old `exporter/mcp/` location has been moved here.

These runtime folders are ignored by git. They are generated working data, not
source code.

## File Map

- `README.md` - this overview.
- `paths.py` - creates and returns `input/`, `reports/`, and `output/`.
- `passage_by_code.py` - resolves passage codes like `DHP1`, `UD12`,
  `ITI37`, `SN12.3`, and `AN3.12` into CST passage text.
- `passage_extraction.py` - previews extracted passages without DB lookup or
  AI calls.
- `book_to_verses.py` - extracts a whole CST book into structured JSON for
  batch verse analysis.
- `analyzer.py` - tokenizes Pali, looks up DPD headwords, expands compounds
  and sandhi, and returns candidate dictionary options.
- `translate_core.py` - shared AI workflow: builds prompts, merges AI scores,
  retries missing score groups, handles variant choices, and renders markdown.
- `study_passage.py` - Stage 1 interactive tool for creating a study report.
- `export_words_csv.py` - Stage 2 interactive tool for exporting edited report
  rows to TSV/CSV.
- `example_bolding.py` - bolds the selected word or component inside the
  source passage example.
- `column_options.py` - defines export column presets and custom columns.
- `ai_batch_translate.py` - batch-analyzes extracted verse JSON.
- `ai_pali_translate.py` - direct interactive sentence translator or renderer
  for one batch-analyzed verse.
- `examples.md` - examples moved from the old MCP analysis location.

## Main Passage Workflow

1. Preview extraction without AI:

```bash
uv run python exporter/analysis/passage_extraction.py AN3.12
```

2. Run Stage 1 AI analysis:

```bash
uv run python exporter/analysis/study_passage.py
```

Enter a passage code such as `DHP1`, `SNP1`, `SN12.3`, or `AN3.12`. For multi-unit passages, select paragraphs or verses with inputs such as `1`, `1-3`, or `1-2 4`.

Stage 1 writes:

- `reports/<source>_study.md`
- `output/<source>_study.json`

3. Edit the markdown report:

- Delete rows you do not want in the final vocabulary export.
- Fix wrong DPD IDs in the first column.
- Keep component rows such as `- mano` under their parent compound when needed.

4. Run Stage 2 vocabulary export:

```bash
uv run python exporter/analysis/export_words_csv.py
```

Enter the same source used by the report, for example `SN12.3_p1`. Select `basic`, `advanced`, or `custom`.

Stage 2 writes:

- `output/<base-source>_words.csv`

For passage selections, Stage 2 keeps the selected report lookup (`SN12.3_p1`) but writes the canonical source (`SN12.3`) into the output filename and `source` column.

## Stage 1 Details

`study_passage.py` does this:

1. Accepts a passage code or falls back to a `.txt` file from `input/`.
2. Retrieves CST text through `passage_by_code.py`.
3. Lets you select one or more paragraphs/verses for multi-unit passages.
4. Applies speech-mark cleanup for apostrophes and hyphens.
5. Builds local DPD analysis JSON with `analyzer.py`.
6. Sends the candidate options to AI through `translate_core.py`.
7. Writes:
   - `reports/<source>_study.md`
   - `output/<source>_study.json`
   - `output/<source>_ai_debug.json`

The debug JSON keeps the prompt, raw AI response, parsed response, retry
requests, missing score groups, and final scores. It is meant for diagnosing
bad or missing AI choices.

## Stage 2 Details

`export_words_csv.py` does this:

1. Lists available markdown reports from `reports/`.
2. Lets you select a report source.
3. Reads the edited word table from the markdown report.
4. Preserves component nesting so compound parts can be bolded correctly.
5. Loads each selected DPD headword.
6. Builds a passage example with the chosen word/component bolded.
7. Writes a tab-delimited CSV/TSV file to `output/<source>_words.csv`.

Before running Stage 2, edit the markdown report manually:

- Delete rows you do not want exported.
- Correct wrong DPD IDs in the first column.
- Keep useful compound component rows under their parent compound.

## Supported Passage Codes

Current code support:

- Verse style: `DHP`, `UD`, `ITI`, `SNP`, `TH`, `THI`
- Prose style: `DN`, `MN`, `SN`, `AN`

`AN` maps dynamically from the nipāta number. For example, `AN3.12` reads from
`an3`.

`UD` and `ITI` can use prebuilt verse JSON files in `input/` when available.
If no JSON index exists, verse extraction falls back to CST search.

## Batch Verse Workflow

Extract CST verses into `input/`:

```bash
uv run python exporter/analysis/book_to_verses.py --book kn2
```

Analyze the extracted verses:

```bash
uv run python exporter/analysis/ai_batch_translate.py --book kn2
```

Use `--limit N` for a small batch and `--dry-run` to inspect work without AI calls.

Render one analyzed verse to markdown:

```bash
uv run python exporter/analysis/ai_pali_translate.py --book kn2 --verse DHP1
```

## Custom CSV Columns

Edit `column_options.py` and change `CUSTOM` to control the Stage 2 `custom` profile. Use keys from `REGISTRY`.

The built-in profiles are:

- `basic` - ID, lemma, grammar, meaning, source, sutta, and bolded example.
- `advanced` - wider DPD export fields for richer flashcard imports.
- `custom` - whatever keys are listed in `CUSTOM`.

## MCP Relationship

`exporter/mcp/server.py` still exposes `get_grammatical_details` for agents.
The server now imports the analyzer from `exporter.analysis.analyzer`.

The old MCP-local AI translation script was removed from `exporter/mcp/`.
Use the command-line tools in `exporter/analysis/` for AI passage analysis,
markdown reports, and vocabulary export.
