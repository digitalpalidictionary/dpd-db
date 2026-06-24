# Pali Passage Analysis

This folder contains the standalone DPD-backed Pali analysis pipeline.

The tools here are for taking a CST passage or local text, producing an
editable word-by-word study report, then exporting selected words to TSV/CSV
for Anki or another flashcard workflow. The MCP server still lives in
`exporter/mcp/`, but the passage-analysis and AI-translation logic has moved
out of MCP so it can run as ordinary command-line exporter tools.

---

## Quick Start (new machine)

**Prerequisites:** `uv` installed, repo cloned, `dpd.db` present at the path
`tools/paths.py` returns (typically `dpd.db` in the project root).

**Step 1 — pick an AI provider** (only one is required):

| Option | What to do |
|--------|-----------|
| **Antigravity CLI** (preferred, no API key) | Install `agy` from <https://antigravity.dev> and verify with `agy --version` |
| **OpenRouter** (API key) | Add `openrouter = sk-or-v1-…` to `config.ini` under `[apis]` |
| **DeepSeek** (API key) | Add `deepseek = sk-…` to `config.ini` under `[apis]` |

**Step 2 — run the analyzer:**

```bash
uv run python exporter/analysis/study_passage.py
```

Enter a passage code such as `DHP1`, `MN4`, `SN12.3`, or `AN3.12`.
The report lands in `reports/<source>_study.md`.

**Step 3 — export vocabulary:**

Edit the report (delete unwanted rows, fix IDs), then:

```bash
uv run python exporter/analysis/export_words_csv.py
```

Output goes to `output/<source>_words.csv`.

---

## AI Provider Setup

The passage analysis pipeline sends scoring prompts to an AI provider. It tries
models from `tools/ai_models.json` in this priority order:

The pipeline tries providers in this order:

1. `antigravity_cli` — work models (tried first)
2. `deepseek` — direct API fallback
3. `openrouter` — multiple model fallbacks

Only initialized providers are used. Antigravity requires the local `agy`
executable; DeepSeek and OpenRouter require API keys in `config.ini`.

Additional providers (`claude`, `gemini`, `nvidia`, `codex`) are supported if
their API keys are present in `config.ini`, but they are not in the default
model list used by `study_passage.py`. Use `--provider`/`--model` flags to
reach them explicitly.

### Antigravity CLI (primary)

Antigravity CLI is a local command-line tool that runs supported work models
without a project API key.

Install it from <https://antigravity.dev> and make sure the `agy` executable is
on your PATH. Verify it works:

```bash
agy --version
```

When `agy` is found on PATH it is used automatically. No config file change is
needed. The provider runs `agy --sandbox --print -` from a temporary scratch
directory, not from the repository root; the prompt is piped via stdin, not
passed as an argv argument. Prompts exceeding 4,000,000 UTF-8 bytes are
rejected as a sanity ceiling.

### API-key fallbacks

DeepSeek and OpenRouter are used after the Antigravity work models fail or are
unavailable.

1. Create an account at <https://openrouter.ai> and generate an API key.
2. If using DeepSeek directly, create a DeepSeek API key.
3. Open `config.ini` at the project root and paste keys into the `[apis]`
   section as needed:

```ini
[apis]
deepseek    = sk-...your-key-here...
openrouter  = sk-or-v1-...your-key-here...
gemini      = AIza...your-key-here...
nvidia      = nvapi-...your-key-here...
```

For Anthropic Claude (`claude` provider) the key is read from the
`ANTHROPIC_API_KEY` environment variable, not from `config.ini`.

Configured providers are initialized automatically at runtime.

### Changing the AI model

Model choices are stored in `tools/ai_models.json`. The file has three lists:
`antigravity_cli_work_models`, `default_models`, and `grounded_models`.
`study_passage.py` uses the first two (in order); `grounded_models` is a
separate list for web-search-backed queries and is not used by the passage
analysis flow.

For the current model names and fallback order, see the upstream source:
<https://github.com/digitalpalidictionary/dpd-db/blob/main/tools/ai_models.json>

Edit the file to change the fallback order. No restart is needed; the file is
read fresh each run.

For a one-off run with a specific model, pass both `--provider` and `--model`.
When these flags are used together, only that provider/model is tried; the
normal fallback list is bypassed.

```bash
printf 'DHP23\n' | uv run python exporter/analysis/study_passage.py --debug \
  --provider antigravity_cli \
  --model "Gemini 3.5 Flash (Low)"
```

For multi-paragraph passages, pipe the passage code and paragraph selection:

```bash
printf 'MN4\n2\n' | uv run python exporter/analysis/study_passage.py --debug \
  --provider antigravity_cli \
  --model "Gemini 3.5 Flash (Low)"
```

To check what models are currently available, run `agy models` or see
the Antigravity documentation at <https://antigravity.dev>. Model names change
as new versions are released; the names above were current at the time of
writing.

The `delay` field (seconds between requests) can also be raised if you hit rate
limits.

---

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

**Entry points:**
- `study_passage.py` — Stage 1 interactive tool for creating a study report.
- `export_words_csv.py` — Stage 2 interactive tool for exporting edited report rows to TSV/CSV.
- `passage_extraction.py` — previews extracted passages without DB lookup or AI calls.
- `ai_batch_translate.py` — batch-analyzes extracted verse JSON.
- `ai_pali_translate.py` — direct interactive sentence translator or renderer for one batch-analyzed verse.

**Pipeline modules (called by entry points):**
- `translate_core.py` — orchestrates the full AI workflow: prompts → AI call → score merge → retry → render.
- `analyzer.py` — tokenizes Pali, looks up DPD headwords, expands compounds and sandhi, returns candidate options.
- `prompts.py` — builds AI prompts and manages formatting constants.
- `ai_response.py` — parses and normalizes AI JSON output into score maps.
- `scoring.py` — applies deterministic scoring rules and tie-breaks.
- `retry.py` — manages batching and fan-out for targeted retry queries.
- `ranking.py` — evaluates options based on heuristics to select the winner.
- `rendering.py` — cleans text and formats the final Markdown report.
- `analysis_types.py` — shared type definitions used across pipeline modules.
- `_base.py` — pure constants and functions used to avoid circular imports.

**Support:**
- `paths.py` — creates and returns `input/`, `reports/`, and `output/`.
- `ui_utils.py` — shared helpers for printing progress, building raw response logs, and writing debug artifacts.
- `passage_by_code.py` — resolves passage codes like `DHP1`, `UD12`, `ITI37`, `SN12.3`, `AN3.12` into CST passage text.
- `book_to_verses.py` — extracts a whole CST book into structured JSON for batch verse analysis.
- `example_bolding.py` — bolds the selected word or component inside the source passage example.
- `column_options.py` — defines export column presets and custom columns.

**Docs:**
- `README.md` — this overview.
- `examples.md` — worked examples.

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

Use `--debug` when diagnosing model behavior:

```bash
uv run python exporter/analysis/study_passage.py --debug
```

Stage 1 writes:

- `reports/<source>_study.md`
- `output/<source>_study.json`
- `output/<source>_ai_debug.json`
- `reports/<source>_ai_raw.txt` when `--debug` is enabled

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
   - `reports/<source>_ai_raw.txt` when `--debug` is enabled

The debug JSON keeps the prompt, raw AI response, parsed response, retry
requests, missing score groups, and final scores. It is meant for diagnosing
bad or missing AI choices.

The AI recovery path is intentionally tolerant:

- Accepts normal `scores` JSON.
- Accepts compact word-to-option-key maps and fetches translation separately.
- Reformats valid-but-wrong-schema or non-standard responses.
- Retries missing score groups, with a supplemental retry pass when needed.
- Splits oversized first-pass work into JSON-size-driven, sentence-boundary chunks (threshold: 900,000 compact-JSON chars). For a single lone sentence whose JSON alone exceeds the threshold, splits by word for scoring only and then issues one grounded whole-sentence translation built from the chosen senses.
- Records provider/model status for first responses, reformats, translations,
  and retry requests in the debug JSON and raw debug log.

## Known Limitations

- AI scores are keyed by dictionary option key, not by token occurrence. If the
  same surface word appears more than once in one sentence or chunk with
  different grammatical functions, every occurrence receives the same shared
  selection and contextual meaning. For example, AN3.33 paragraph 1 contains
  `bhagavā` as both nominative narrative text and vocative address.

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

You can optionally specify a custom provider and model, and enable verbose debug logging:

```bash
uv run python exporter/analysis/ai_batch_translate.py --book kn2 --provider gemini_cli --model gemini-3-flash-preview --debug
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


## Developer Notes: Pipeline Architecture

The core pipeline (`translate_core.py`) orchestrates several internal modules:
- `prompts.py` — Builds the prompts and manages formatting constants.
- `ai_response.py` — Parses and normalizes AI JSON output into maps.
- `scoring.py` — Applies deterministic scoring rules and tie-breaks.
- `retry.py` — Manages batching and fan-out for targeted retry queries.
- `ranking.py` — Evaluates options based on heuristics to select the winner.
- `rendering.py` — Cleans text and formats the final Markdown report.

### Regression Harness

The analysis engine is protected by a zero-network regression harness in
`tests/exporter/analysis/test_passage_regression.py`. It tests five canonical
passages (`TH215`, `MN41_p2`, `SN15.1_p2`, `DHP211`, `AN3.33_p1`).

Each fixture in `tests/exporter/analysis/fixtures/passages/<name>/` contains:
- `ai_debug.json` — recorded AI responses from a prior live run.
- `metadata.json` — the `provider`, `model`, and `stdin` that produced the recording.

The test replays `ai_debug.json` through `RecordedAIManager` (responses are
served strictly in recorded order, with no network calls) and then asserts
passage-specific invariants on the output (e.g. correct grammatical tags,
no empty meanings, no `[Deconstructed]` placeholders). The test does not
compare bytes or golden output files.

**When to re-record:** If `MAX_FIRST_CONTEXT_CHARS` or another constant that
controls chunking changes, existing fixtures may desync (the pipeline makes a
different number of AI calls than the fixture recorded). Re-record by re-running
`study_passage.py` with the provider and stdin from `metadata.json`:

```bash
printf '<stdin from metadata.json>' | uv run python exporter/analysis/study_passage.py \
  --provider <provider> \
  --model "<model>"
```

Then copy the fresh artifacts over the fixture:
- `output/<stem>_ai_debug.json` → `fixtures/passages/<name>/ai_debug.json`
- `output/<stem>_study.json`    → `fixtures/passages/<name>/study.json`
- `reports/<stem>_study.md`     → `fixtures/passages/<name>/study.md`

Update `metadata.json` only if the model string returned by the provider
differs from the one already recorded.

**Invariant failures after re-recording** are a behaviour signal — the model
chose different senses that now violate a real constraint. Do not re-roll the
recording or weaken the assertion; surface it for review instead.
