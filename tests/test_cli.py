import json
from datetime import date
from unittest.mock import AsyncMock

import pytest

from egov_law_mcp import cli


def test_cli_uses_public_function(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    payload = {"name": "日本語"}
    handler = AsyncMock(return_value=payload)
    monkeypatch.setattr(cli, "search_laws", handler)
    args = ["search-laws", "--title", "民法", "--limit", "1"]
    cli.run_cli(args)
    handler.assert_awaited_once_with(**{"title": "民法", "limit": 1})
    assert json.loads(capsysbinary.readouterr().out) == payload


def test_cli_reads_a_selected_xml_page(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    payload = {"text": "<AppdxFig>別図</AppdxFig>", "next_offset": None}
    handler = AsyncMock(return_value=payload)
    monkeypatch.setattr(cli, "get_law_text", handler)
    cli.run_cli(
        [
            "get-law-text",
            "--law-id",
            "322CO0000000016",
            "--section",
            "appendix",
            "--section-number",
            "2",
            "--appendix-type",
            "figure",
            "--as-of",
            "2025-01-01",
            "--offset",
            "400",
        ]
    )
    handler.assert_awaited_once_with(
        law_id="322CO0000000016",
        section="appendix",
        section_number=2,
        appendix_type="figure",
        as_of=date(2025, 1, 1),
        offset=400,
    )
    assert json.loads(capsysbinary.readouterr().out) == payload
