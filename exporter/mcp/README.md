# DPD MCP Server

This directory contains a Model Context Protocol (MCP) server that provides AI agents with structured access to the Digital Pāḷi Dictionary (DPD).

## Installation

Ensure you have `uv` installed. The server dependencies are managed via the project's root `pyproject.toml`.

## Running the Server

To run the server locally for development and testing:

```bash
uv run python exporter/mcp/server.py
```

## Connecting to the Server

### Using MCP Inspector (Development)

You can use the MCP Inspector to interact with the server:

```bash
npx @modelcontextprotocol/inspector uv run python exporter/mcp/server.py
```

### Claude Desktop Configuration

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pali-dictionary": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/dpd-db",
        "run",
        "python",
        "exporter/mcp/server.py"
      ]
    }
  }
}
```

Replace `/path/to/dpd-db` with the absolute path to this repository.

## Server Files

- `server.py`: The main MCP server entry point using the `mcp` Python SDK.
- `config.py`: Handles project-wide path integration and database connection.
