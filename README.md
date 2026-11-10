# egov-law-mcp

e-Gov法令API v2の公式APIを参照する読み取り専用のMCPサーバーです。Python 3.12以上とuv（0.13.4で検証）を使います。上流APIのキー設定は不要です。

## MCPクライアント設定

GitHubリポジトリへのアクセス権がある環境でクローンします。

```sh
git clone https://github.com/koizumikento/egov-law-mcp.git
cd egov-law-mcp
uv sync --locked
```

クライアントの設定に、クローン先の絶対パスを指定します。

```json
{
  "mcpServers": {
    "egov-law-mcp": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/egov-law-mcp", "run", "--locked", "egov-law-mcp"]
    }
  }
}
```

## ツール

| ツール | 用途 |
| --- | --- |
| `search_laws` | 法令名・任意の基準日で検索 |
| `get_law_article` | 法令ID・条番号で本則の条文と版情報を取得 |

法令名で検索し、法令IDまたは改正履歴IDで本則の条文を取得します。日付を指定した場合は指定時点の版を参照します。

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
