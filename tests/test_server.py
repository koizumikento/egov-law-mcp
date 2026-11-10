import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from egov_law_mcp import create_server
from egov_law_mcp.server import BASE_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "egov_law_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {"search_laws", "get_law_article"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_tool_response() -> None:
    route = respx.get(
        BASE_URL + "law_data/129AC0000000089?elm=MainProvision-Article_709"
        "&law_full_text_format=json&asof=2025-01-01"
    ).mock(
        return_value=httpx.Response(
            200,
            json=json.loads(
                '{"law_info":{"law_id":"129AC0000000089"},"revision_info":{"law_revision_id":"129AC0000000089_20250101_000000000000000"},"law_full_text":{"tag":"Article","attr":{"Num":"709"}}}'
            ),
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "get_law_article",
            {"law_id": "129AC0000000089", "article": "709", "as_of": "2025-01-01"},
        )
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["law_full_text"]["attr"]["Num"] == "709"
    assert payload["source_url"].endswith(payload["revision_info"]["law_revision_id"])
