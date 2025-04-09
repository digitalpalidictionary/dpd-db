import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["mcp_server/dpd_db_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:", tools)

            result = await session.call_tool("get_headword_by_lemma", arguments={"lemma": "aṭṭhi"})
            print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
