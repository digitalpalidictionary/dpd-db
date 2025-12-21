# exporter/mcp_server/

## Purpose & Rationale
`mcp_server/` is the project's interface for the next generation of AI-assisted scholarship. Its rationale is to implement the Model Context Protocol (MCP), allowing Large Language Models (LLMs) and AI agents to "browse" the DPD database as a tool. By providing a standardized way for AI to query Pāḷi headwords and definitions, it enables more accurate translations and deeper linguistic analysis within AI environments.

## Architectural Logic
This subsystem follows a "Protocol Server" pattern:
1.  **Server Implementation:** `dpd_db_server.py` uses the `mcp` library to define a server that listens for standardized requests (typically via stdio).
2.  **Tool Definition:** It exposes "Tools" (like `get_headword_by_lemma`) that map protocol-level calls to project-specific database queries.
3.  **Data Exchange:** It handles the translation of SQLAlchemy models into JSON objects that AI agents can consume.
4.  **Testing:** `test_dpd_db_client.py` provides a mock client to ensure the server correctly responds to protocol requests.

## Relationships & Data Flow
- **Data Source:** Pulls directly from the `dpd.db` SQLite file using **db/** models.
- **Consumption:** Intended to be used by AI-powered IDEs (like Cursor) or specialized linguistic AI agents.
- **Protocol:** Adheres to the Model Context Protocol (MCP) specification.

## Interface
- **Run Server:** `uv run python exporter/mcp_server/dpd_db_server.py`
- **Test Client:** `uv run python exporter/mcp_server/test_dpd_db_client.py`
