# egov-law-mcp

日本の法令を名前で探し、指定した条文と参照した法令の版を確認できます。読み取り専用で、APIキーの設定は不要です。[uv](https://docs.astral.sh/uv/) と Git が必要です。Python 3.12以上に対応しています。

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

## ツール

| ツール | 用途 |
| --- | --- |
| `search_laws` | 法令名・任意の基準日で検索 |
| `get_law_article` | 法令ID・条番号で本則の条文と版情報を取得 |

法令名で検索し、法令IDまたは改正履歴IDで本則の条文を取得します。日付を指定した場合は指定時点の版を参照します。

## CLI

CLIやPythonライブラリを手元で使う場合は、リポジトリをクローンして準備します。

```sh
git clone https://github.com/koizumikento/egov-law-mcp.git
cd egov-law-mcp
uv sync --locked
```

```sh
uv run egov-law-mcp search-laws --title "民法" --limit 1
uv run egov-law-mcp get-law-article --law-id 129AC0000000089 --article 709
```

結果は標準出力にUTF-8のJSONで出力します。コマンドの引数は `uv run egov-law-mcp search-laws --help` で確認できます。

## Pythonライブラリ

パッケージをインストールしたPython環境で、下記の非同期関数を直接呼び出せます。

```python
import asyncio

from egov_law_mcp import search_laws

result = asyncio.run(search_laws(title="民法", limit=1))
print(result)
```

公開関数 `search_laws`、`get_law_article` を利用できます。イベントループがある環境では、関数を直接 `await` します。

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
