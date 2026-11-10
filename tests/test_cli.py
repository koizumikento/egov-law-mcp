import json
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
