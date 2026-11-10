from __future__ import annotations

from datetime import date
from typing import Annotated, Any

import httpx
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

BASE_URL = "https://laws.e-gov.go.jp/api/2/"
READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)

Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=10000)]
LawId = Annotated[str, Field(pattern=r"^[A-Za-z0-9]+(?:_[A-Za-z0-9]+){0,2}$", max_length=80)]
ArticleNumber = Annotated[str, Field(pattern=r"^[1-9]\d*(?:_[1-9]\d*)*$", max_length=30)]


async def get_response(path: str, **params: str | int | None) -> httpx.Response:
    query = {key: value for key, value in params.items() if value is not None}
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
            response = await client.get(path, params=query)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"Upstream HTTP error {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise ValueError("Could not reach the upstream API.") from exc


async def get_json(path: str, **params: str | int | None) -> dict[str, Any]:
    response = await get_response(path, **params)
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Upstream response was not a JSON object.")
    return data


def create_server() -> MCPServer:
    mcp = MCPServer("egov-law-mcp")

    @mcp.tool(annotations=READ_ONLY)
    async def search_laws(
        title: Query, limit: Limit = 10, offset: Offset = 0, as_of: date | None = None
    ) -> dict[str, Any]:
        """Search by Japanese law title, optionally as of a date (YYYY-MM-DD)."""
        return await get_json(
            "laws",
            law_title=title,
            limit=limit,
            offset=offset,
            asof=as_of.isoformat() if as_of else None,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_law_article(
        law_id: LawId, article: ArticleNumber, as_of: date | None = None
    ) -> dict[str, Any]:
        """Get a main-provision article by law or revision ID. Use 709 or 709_2 for branches."""
        if as_of is not None and "_" in law_id:
            raise ValueError("Specify either a revision ID or an as-of date.")
        result = await get_json(
            f"law_data/{law_id}",
            elm=f"MainProvision-Article_{article}",
            law_full_text_format="json",
            asof=as_of.isoformat() if as_of else None,
        )
        text = result.get("law_full_text") or {}
        if text.get("tag") != "Article" or text.get("attr", {}).get("Num") != article:
            raise ValueError("The requested article number was not returned by the law API.")
        source_id = result["law_info"]["law_id"]
        revision_id = result["revision_info"]["law_revision_id"]
        return {**result, "source_url": f"https://laws.e-gov.go.jp/law/{source_id}/{revision_id}"}

    return mcp
