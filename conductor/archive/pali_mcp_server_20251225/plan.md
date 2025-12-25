# Pāḷi MCP Server Implementation Plan

## Phase 1: Environment & Scaffolding
- [x] Task: Research MCP Python SDK best practices for SQLite integration.
- [x] Task: Create directory structure for the MCP server in `exporter/mcp/`.
- [x] Task: Define basic configuration and project paths integration in `exporter/mcp/config.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment & Scaffolding' (Protocol in workflow.md)

## Phase 2: Core Logic Implementation
- [x] Task: Create `exporter/mcp/analyzer.py` with the sentence tokenization and normalization logic.
- [x] Task: Implement TDD for tokenization: Write tests in `tests/test_mcp_analyzer.py` and implement code to pass.
- [~] Task: Implement database lookup logic in `exporter/mcp/analyzer.py` using `DpdHeadword` and `Lookup` models.
- [ ] Task: Implement TDD for database lookup: Write tests for single word lookup and full sentence analysis.
- [ ] Task: Handle "not_found" status for tokens missing from the dictionary.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Core Logic Implementation' (Protocol in workflow.md)

## Phase 3: MCP Server Integration
- [x] Task: Create the main MCP server entry point in `exporter/mcp/server.py` using the `mcp` SDK.
- [x] Task: Register the `get_grammatical_details` tool and link it to the analyzer logic.
- [~] Task: Implement TDD for the tool response format: Verify JSON structure matches the specification.
- [x] Task: Conductor - User Manual Verification 'Phase 3: MCP Server Integration' (Protocol in workflow.md)

## Phase 4: Verification & Documentation
- [x] Task: Create a README.md in `exporter/mcp/` explaining how to run and connect to the server.
- [x] Task: Perform manual verification using a mock MCP host (e.g., `mcp dev`).
- [x] Task: Run project-wide quality gates (Ruff, type hints).
- [x] Task: Conductor - User Manual Verification 'Phase 4: Verification & Documentation' (Protocol in workflow.md)
