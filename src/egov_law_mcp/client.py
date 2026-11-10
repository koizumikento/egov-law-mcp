from __future__ import annotations

import base64
from datetime import date
from typing import Annotated, Any, Literal

import httpx
from pydantic import Field, validate_call

BASE_URL = "https://laws.e-gov.go.jp/api/2/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=10000)]
LawId = Annotated[str, Field(pattern=r"^[A-Za-z0-9]+(?:_[A-Za-z0-9]+){0,2}$", max_length=80)]
ArticleNumber = Annotated[str, Field(pattern=r"^[1-9]\d*(?:_[1-9]\d*)*$", max_length=30)]
SectionNumber = Annotated[int, Field(ge=1, le=10000)]
TextPageSize = Annotated[int, Field(ge=1, le=20000)]
TextOffset = Annotated[int, Field(ge=0)]
SnippetSize = Annotated[int, Field(ge=1, le=500)]
LawSection = Literal["all", "main", "supplementary", "appendix"]
AppendixType = Literal["table", "style", "format", "appendix", "figure"]
APPENDIX_TAGS = {
    "table": "AppdxTable",
    "style": "AppdxStyle",
    "format": "AppdxFormat",
    "appendix": "Appdx",
    "figure": "AppdxFig",
}


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


@validate_call
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


@validate_call
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


@validate_call
async def list_law_revisions(
    law_id: LawId,
    limit: Limit = 10,
    offset: Offset = 0,
    effective_from: date | None = None,
    effective_to: date | None = None,
) -> dict[str, Any]:
    """List revisions by law ID, optionally filtering by inclusive effective dates."""
    if "_" in law_id:
        raise ValueError("Use a law ID to list revisions.")
    if effective_from and effective_to and effective_from > effective_to:
        raise ValueError("The start date must be on or before the end date.")
    result = await get_json(
        f"law_revisions/{law_id}",
        amendment_date_from=effective_from.isoformat() if effective_from else None,
        amendment_date_to=effective_to.isoformat() if effective_to else None,
    )
    revisions = result.get("revisions")
    if not isinstance(revisions, list):
        raise ValueError("The law API did not return a revision list.")
    end = offset + limit
    return {
        **result,
        "revisions": revisions[offset:end],
        "offset": offset,
        "total_count": len(revisions),
        "next_offset": end if end < len(revisions) else None,
    }


@validate_call
async def search_law_text(
    keyword: Query,
    law_number: Query | None = None,
    limit: Limit = 10,
    offset: Offset = 0,
    as_of: date | None = None,
    sentence_text_size: SnippetSize = 100,
) -> dict[str, Any]:
    """Find keyword occurrences in law text. The limit counts matching positions across laws."""
    return await get_json(
        "keyword",
        keyword=keyword,
        law_num=law_number,
        limit=limit,
        offset=offset,
        asof=as_of.isoformat() if as_of else None,
        sentence_text_size=sentence_text_size,
    )


@validate_call
async def get_law_text(
    law_id: LawId,
    section: LawSection = "all",
    section_number: SectionNumber | None = None,
    offset: TextOffset = 0,
    limit: TextPageSize = 8000,
    as_of: date | None = None,
    appendix_type: AppendixType | None = None,
) -> dict[str, Any]:
    """Read a character page of law XML, optionally selecting a provision or appendix."""
    if as_of is not None and "_" in law_id:
        raise ValueError("Specify either a revision ID or an as-of date.")
    if section_number is not None and section in ("all", "main"):
        raise ValueError("The section number applies to supplementary provisions and appendices.")
    if appendix_type is not None and section != "appendix":
        raise ValueError("The appendix type requires the appendix section.")
    if section in ("supplementary", "appendix"):
        section_number = section_number or 1
    if section == "appendix":
        appendix_type = appendix_type or "table"
        selector = f"{APPENDIX_TAGS[appendix_type]}[{section_number}]"
    else:
        selector = {
            "all": None,
            "main": "MainProvision",
            "supplementary": f"SupplProvision[{section_number}]",
        }[section]
    result = await get_json(
        f"law_data/{law_id}",
        elm=selector,
        law_full_text_format="xml",
        asof=as_of.isoformat() if as_of else None,
    )
    encoded = result.get("law_full_text")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("The law API did not return XML for the requested section.")
    try:
        xml = base64.b64decode(encoded, validate=True).decode("utf-8")
    except ValueError as exc:
        raise ValueError("The law API returned invalid base64 UTF-8 XML.") from exc
    source_id = result["law_info"]["law_id"]
    revision_id = result["revision_info"]["law_revision_id"]
    end = offset + limit
    return {
        "law_info": result["law_info"],
        "revision_info": result["revision_info"],
        "section": section,
        "section_number": section_number,
        "appendix_type": appendix_type,
        "format": "xml",
        "text": xml[offset:end],
        "offset": offset,
        "total_chars": len(xml),
        "next_offset": end if end < len(xml) else None,
        "source_url": f"https://laws.e-gov.go.jp/law/{source_id}/{revision_id}",
    }
