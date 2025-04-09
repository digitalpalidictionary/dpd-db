from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import json
from db.models import DpdHeadword
from pathlib import Path
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions

LATEST_PROTOCOL_VERSION = "2024-11-05"

# Database configuration
DATABASE_PATH = Path("dpd.db")

class DpdDbServer:
    def __init__(self):
        from db.db_helpers import get_db_session
        self.db_session = get_db_session(DATABASE_PATH)
        self.server = Server("dpd-db-server", "0.1.0")
        
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            # List available tools
            return [
                types.Tool(
                    name="get_headword_by_lemma",
                    description="Retrieve a DpdHeadword by its lemma",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lemma": {
                                "type": "string",
                                "description": "The lemma of the DpdHeadword to retrieve"
                            }
                        },
                        "required": ["lemma"]
                    },
                )
            ]

        @self.server.call_tool()
        async def get_headword_by_lemma(name: str, arguments: dict) -> types.CallToolResult:
            if name != "get_headword_by_lemma":
                raise Exception(f"Unknown tool: {name}")
            try:
                lemma = arguments.get("lemma")
                if lemma is None:
                    raise Exception("Missing required argument: lemma")
                headword = self.db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == lemma).first()
                if headword:
                    content = [
                        types.TextContent(
                            type="text",
                            text=json.dumps({
                                "id": headword.id,
                                "lemma_1": headword.lemma_1,
                                "pos": headword.pos,
                                "meaning_1": headword.meaning_1,
                            }, indent=2, ensure_ascii=False)
                        )
                    ]
                    return types.CallToolResult(content=list(content))
                else:
                    raise Exception(f"No headword found with lemma '{lemma}'")
            except Exception as e:
                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=str(e))],
                    isError=True
                )

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            initialization_options = InitializationOptions(
                server_name="dpd-db-server",
                server_version="0.1.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
            await self.server.run(read_stream, write_stream, initialization_options)

if __name__ == "__main__":
    import asyncio
    server = DpdDbServer()
    asyncio.run(server.run())
