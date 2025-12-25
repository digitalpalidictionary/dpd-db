import json
from mcp.server.fastmcp import FastMCP
from db.db_helpers import get_db_session
from exporter.mcp.config import mcp_config
from exporter.mcp.analyzer import analyze_sentence


# Create FastMCP server
mcp = FastMCP("Pāḷi Dictionary Server")


@mcp.tool()
def get_grammatical_details(sentence: str) -> str:
    """
    Analyze a Pāḷi sentence and retrieve grammatical details for each word from the DPD.

    Args:
        sentence: A Pāḷi sentence to analyze.

    Returns:
        A structured JSON string containing word-by-word analysis.
    """
    db_session = get_db_session(mcp_config.db_path)
    try:
        results = analyze_sentence(sentence, db_session)
        return json.dumps(results, ensure_ascii=False, indent=2)
    finally:
        db_session.close()


if __name__ == "__main__":
    mcp.run()
