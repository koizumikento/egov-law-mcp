import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from datetime import date

import httpx

from .client import get_law_article, get_law_text, list_law_revisions, search_law_text, search_laws


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="egov-law-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "search-laws", help="Search by law title.", argument_default=SUPPRESS
    )
    command.add_argument("--title", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.add_argument("--as-of", type=date.fromisoformat)
    command.set_defaults(handler=search_laws)

    command = commands.add_parser(
        "get-law-article",
        help="Get an article by law ID and article number.",
        argument_default=SUPPRESS,
    )
    command.add_argument("--law-id", required=True)
    command.add_argument("--article", required=True)
    command.add_argument("--as-of", type=date.fromisoformat)
    command.set_defaults(handler=get_law_article)

    command = commands.add_parser(
        "list-law-revisions", help="List law revisions.", argument_default=SUPPRESS
    )
    command.add_argument("--law-id", required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.add_argument("--effective-from", type=date.fromisoformat)
    command.add_argument("--effective-to", type=date.fromisoformat)
    command.set_defaults(handler=list_law_revisions)

    command = commands.add_parser(
        "search-law-text", help="Search by keyword in law text.", argument_default=SUPPRESS
    )
    command.add_argument("--keyword", required=True)
    command.add_argument("--law-number")
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.add_argument("--as-of", type=date.fromisoformat)
    command.add_argument("--sentence-text-size", type=int)
    command.set_defaults(handler=search_law_text)

    command = commands.add_parser(
        "get-law-text", help="Read a page of law XML.", argument_default=SUPPRESS
    )
    command.add_argument("--law-id", required=True)
    command.add_argument("--section", choices=("all", "main", "supplementary", "appendix"))
    command.add_argument("--section-number", type=int)
    command.add_argument(
        "--appendix-type", choices=("table", "style", "format", "appendix", "figure")
    )
    command.add_argument("--limit", type=int)
    command.add_argument("--offset", type=int)
    command.add_argument("--as-of", type=date.fromisoformat)
    command.set_defaults(handler=get_law_text)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
