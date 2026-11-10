from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_law_article, get_law_text, list_law_revisions, search_law_text, search_laws

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("egov-law-mcp")
    mcp.tool(annotations=READ_ONLY)(search_laws)
    mcp.tool(annotations=READ_ONLY)(get_law_article)
    mcp.tool(annotations=READ_ONLY)(list_law_revisions)
    mcp.tool(annotations=READ_ONLY)(search_law_text)
    mcp.tool(annotations=READ_ONLY)(get_law_text)
    return mcp
