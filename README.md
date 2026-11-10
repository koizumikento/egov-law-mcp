# egov-law-mcp

日本の法令を法令名や本文中の語句から探し、条文・附則・別表や改正履歴を確認できます。読み取り専用で、APIキーの設定は不要です。[uv](https://docs.astral.sh/uv/) と Git が必要です。Python 3.12以上に対応しています。

[MCP登録](#mcpクライアントに登録する) · [CLI](#cliで使う) · [Pythonライブラリ](#pythonライブラリとして使う)

## MCPクライアントに登録する

公開GitHubリポジトリから `uvx` で起動します。初回は依存関係の準備に時間がかかることがあります。

### Codex

```sh
codex mcp add egov-law-mcp -- uvx --python 3.12 --from git+https://github.com/koizumikento/egov-law-mcp.git@main egov-law-mcp
codex mcp list
```

`codex mcp list` で登録を確認し、Codexの新しいセッションで `/mcp` を開くと、接続状態を確認できます。[Codexの公式設定ガイド](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

Codexのデスクトップアプリでは、設定の「MCP servers」でSTDIOサーバーを追加し、下のJSON例と同じコマンド・引数を指定する方法もあります。

### Claude Desktop / Cursor

次のファイルに設定します。

- Claude Desktop（Windows） `%APPDATA%/Claude/claude_desktop_config.json`
- Claude Desktop（macOS） `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor `.cursor/mcp.json`（プロジェクト内）

既に `mcpServers` がある場合は、その中にサーバーの項目を追加してください。保存後にクライアントを再起動し、ツールが表示されるか確認します。[設定ファイルの場所と接続手順](https://py.sdk.modelcontextprotocol.io/get-started/real-host/)

```json
{
  "mcpServers": {
    "egov-law-mcp": {
      "command": "uvx",
      "args": [
        "--python",
        "3.12",
        "--from",
        "git+https://github.com/koizumikento/egov-law-mcp.git@main",
        "egov-law-mcp"
      ]
    }
  }
}
```

`uvx` が見つからない場合は、設定のコマンドに実行ファイルの絶対パスを指定してください。

登録後は、チャットで次のように聞けます。

> 民法第709条の条文と、参照した法令の版を教えて。
>
> 民法の改正履歴を調べて。施行日と、該当する版を参照するためのIDも教えて。

## ツール

| ツール | 用途 |
| --- | --- |
| `search_laws` | 法令名から法令IDを探す。基準日を指定できる |
| `search_law_text` | 本文中の語句を検索し、該当箇所の抜粋を読む。法令番号や基準日で絞り込める |
| `list_law_revisions` | 法令IDから施行日と改正履歴IDを確認する。施行日の範囲で絞り込める |
| `get_law_article` | 法令IDまたは改正履歴IDと条番号から、本則の1条を取得する |
| `get_law_text` | 法令全体、本則、個別の附則や別表などをXMLで読む |

### 版を指定する

`get_law_article` と `get_law_text` では、法令IDに基準日（`as_of`）を添えると、その時点の版を取得できます。版が決まっている場合は、`law_id` に改正履歴IDを渡します。取得結果の `source_url` で参照した版を開けます。改正履歴には将来施行の版も含まれるため、施行日を確認してください。

### 附則と別表を読む

| `get_law_text` の `section` | 取得範囲 |
| --- | --- |
| `all`（既定） | 法令全体 |
| `main` | 本則全体 |
| `supplementary` | 附則。文書内の出現順を `section_number` に指定 |
| `appendix` | 別表など。`appendix_type` で種類を選び、同じ種類の出現順を `section_number` に指定 |

`section_number` は1始まりで、省略すると1件目を取得します。`appendix_type` は `table`（別表、既定）、`style`（別記様式）、`format`（別記書式）、`appendix`（付録）、`figure`（別図）から選べます。個別に選べる種類は法令APIの要素指定に対応しています。添付画像やPDFなどのファイル本体は取得対象外です。

### 続きを取得する

- 本文検索の `limit` には、法令を横断して取得するキーワードの出現箇所数を指定します。`next_offset` が返ったら、同じ検索条件の `offset` に渡します。
- 改正履歴はAPIが返した順にページ分けします。`next_offset` が `null` になるまで、同じ条件で続きを取得できます。
- 法令XMLは `text` に既定で8,000文字、最大20,000文字ずつ返します。XMLタグの途中で区切られることがあるため、完全なXMLが必要な場合は `next_offset` が `null` になるまで同じセクションを取得し、`text` を順につなぎます。途中で版が変わらないよう、2ページ目以降は最初に返った `revision_info.law_revision_id` を指定してください。ページごとにAPIから選択範囲を取得し、返却時に分割します。

## CLIで使う

CLIやPythonライブラリを手元で使う場合は、リポジトリをクローンして準備します。

```sh
git clone https://github.com/koizumikento/egov-law-mcp.git
cd egov-law-mcp
uv sync --locked
```

```sh
uv run egov-law-mcp search-laws --title "民法" --limit 1
uv run egov-law-mcp get-law-article --law-id 129AC0000000089 --article 709
uv run egov-law-mcp search-law-text --keyword "善意" --limit 3
uv run egov-law-mcp list-law-revisions --law-id 129AC0000000089 --limit 3
uv run egov-law-mcp get-law-text --law-id 129AC0000000089 --section supplementary
uv run egov-law-mcp get-law-text --law-id 322CO0000000016 --section appendix --limit 1000
```

結果は標準出力にUTF-8のJSONで出力します。コマンドの引数は `uv run egov-law-mcp search-laws --help` で確認できます。

## Pythonライブラリとして使う

自分のPythonプロジェクト（`pyproject.toml` があるディレクトリ）で依存関係に追加します。

```sh
uv add "git+https://github.com/koizumikento/egov-law-mcp.git@main"
```

次のコードを `example.py` に保存し、同じディレクトリで `uv run python example.py` を実行します。

```python
import asyncio

from egov_law_mcp import get_law_text

page = asyncio.run(get_law_text("129AC0000000089", section="supplementary"))
print(page["text"])
```

「ツール」表の各関数を利用できます。イベントループがある環境では、関数を直接 `await` します。

## 出典と利用条件

コードはMIT Licenseです。取得するデータの権利と利用条件は、API提供元と各データ提供機関の定めに従います。[公式API仕様](https://laws.e-gov.go.jp/api/2/swagger-ui/) · [利用案内](https://laws.e-gov.go.jp/)

## 開発

```sh
uv sync --locked
uv run ruff check .
uv run ty check
uv run pytest
uv build
```
