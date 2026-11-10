import base64
import json
import sys
from datetime import date

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from egov_law_mcp import create_server, get_law_text, list_law_revisions, search_law_text
from egov_law_mcp.client import BASE_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "egov_law_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {
        "search_laws",
        "get_law_article",
        "list_law_revisions",
        "search_law_text",
        "get_law_text",
    }
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


@pytest.mark.asyncio
@respx.mock
async def test_revision_pages_keep_upstream_order_and_use_effective_dates() -> None:
    route = respx.get(
        BASE_URL + "law_revisions/129AC0000000089?amendment_date_from=2025-01-01"
    ).mock(return_value=httpx.Response(200, json={"revisions": [{"id": 3}, {"id": 2}]}))

    effective_from = date(2025, 1, 1)
    first = await list_law_revisions("129AC0000000089", limit=1, effective_from=effective_from)
    assert route.called
    assert first["revisions"] == [{"id": 3}]
    assert first["total_count"] == 2
    assert first["next_offset"] == 1
    last = await list_law_revisions(
        "129AC0000000089", limit=1, offset=first["next_offset"], effective_from=effective_from
    )
    assert last["revisions"] == [{"id": 2}]
    assert last["next_offset"] is None


@pytest.mark.asyncio
@respx.mock
async def test_keyword_keeps_match_cursor_and_text() -> None:
    law_number = "明治二十九年法律第八十九号"
    route = respx.get(
        BASE_URL + "keyword",
        params={
            "keyword": "善意",
            "law_num": law_number,
            "limit": "10",
            "offset": "5",
            "asof": "2025-01-01",
            "sentence_text_size": "80",
        },
    )
    payload = {"next_offset": 15, "items": [{"sentences": [{"text": "<span>善意</span>"}]}]}
    route.mock(return_value=httpx.Response(200, json=payload))

    assert (
        await search_law_text(
            "善意",
            law_number=law_number,
            offset=5,
            as_of=date(2025, 1, 1),
            sentence_text_size=80,
        )
        == payload
    )
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_xml_page_can_continue_using_revision_id_and_appendix_selector() -> None:
    law_id = "322CO0000000016"
    revision_id = f"{law_id}_20260101_000000000000000"
    xml = "<AppdxFig>別図</AppdxFig>"
    payload = {
        "law_info": {"law_id": law_id},
        "revision_info": {"law_revision_id": revision_id},
        "law_full_text": base64.b64encode(xml.encode()).decode(),
    }
    query = "?elm=AppdxFig%5B2%5D&law_full_text_format=xml"
    first_route = respx.get(BASE_URL + f"law_data/{law_id}{query}").mock(
        return_value=httpx.Response(200, json=payload)
    )
    last_route = respx.get(BASE_URL + f"law_data/{revision_id}{query}").mock(
        return_value=httpx.Response(200, json=payload)
    )

    async with Client(create_server()) as client:
        result = await client.call_tool(
            "get_law_text",
            {
                "law_id": law_id,
                "section": "appendix",
                "section_number": 2,
                "appendix_type": "figure",
                "limit": 11,
            },
        )
    assert first_route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    first = json.loads(result.content[0].text)
    assert first["text"] == xml[:11]
    assert first["total_chars"] == len(xml)
    last = await get_law_text(
        revision_id,
        section="appendix",
        section_number=2,
        appendix_type="figure",
        offset=first["next_offset"],
    )
    assert last_route.called
    assert first["text"] + last["text"] == xml
    assert last["next_offset"] is None
    assert last["source_url"].endswith(revision_id)
