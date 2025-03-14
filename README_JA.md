# mcp-server-salesforce MCP サーバー

Salesforce と連携するための Model Context Protocol サーバー実装

## コンポーネント

### リソース

サーバーは以下の2つのカテゴリのリソースを実装しています：

1. ノート保存システム:
   - カスタム note:// URI スキームで個別のノートにアクセス
   - 各ノートリソースには名前、説明、text/plain マイムタイプがあります

2. Salesforce オブジェクト:
   - カスタム salesforce:// URI スキームで Salesforce オブジェクトとレコードにアクセス
   - 各オブジェクトリソースには名前、説明、application/json マイムタイプがあります

### プロンプト

サーバーは以下のプロンプトを提供します：

- summarize-notes: すべての保存されたノートの要約を作成
  - オプションの "style" 引数で詳細レベルを制御（brief/detailed）
  - 現在のすべてのノートとスタイル設定を組み合わせたプロンプトを生成

- analyze-salesforce-data: Salesforce オブジェクトからデータを分析
  - 必須の "object" 引数で Salesforce オブジェクト名を指定（例：Account, Contact）
  - オプションの "limit" 引数で最大レコード数を制御（デフォルト：10）
  - 分析用にデータを取得してフォーマット

### ツール

サーバーは以下のツールを実装しています：

1. ノート管理:
   - add-note: サーバーに新しいノートを追加
     - "name" と "content" を必須の文字列引数として受け取る
     - サーバー状態を更新し、クライアントにリソース変更を通知

2. Salesforce 連携:
   - salesforce-query: Salesforce に対して SOQL クエリを実行
     - "query" を必須の文字列引数として受け取る（有効な SOQL クエリ）
     - クエリ結果を JSON で返す

   - salesforce-create: Salesforce に新しいレコードを作成
     - "object"（例："Account"）と "data"（フィールド値）を必須引数として受け取る
     - 作成されたレコードの ID を返す

   - salesforce-update: 既存の Salesforce レコードを更新
     - "object"、"id"、"data" を必須引数として受け取る
     - 指定されたレコードを新しいフィールド値で更新

   - salesforce-delete: Salesforce レコードを削除
     - "object" と "id" を必須引数として受け取る
     - 指定されたレコードを削除

## 設定

Salesforce 機能を使用するには、認証資格情報を設定する必要があります。
サーバーは環境変数または .env ファイル（プロジェクトルートに配置）をサポートしています。

必要な環境変数:
- SALESFORCE_USERNAME: Salesforce ユーザー名（通常はメールアドレス）
- SALESFORCE_PASSWORD: Salesforce パスワード
- SALESFORCE_SECURITY_TOKEN: Salesforce セキュリティトークン
- SALESFORCE_DOMAIN: （オプション）Salesforce ログインドメイン（デフォルト: "login"）

## クイックスタート

### インストール

#### Claude Desktop

MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>開発/未公開サーバー構成</summary>
  ```
  "mcpServers": {
    "mcp-server-salesforce": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-salesforce",
        "run",
        "mcp-server-salesforce"
      ]
    }
  }
  ```
</details>

<details>
  <summary>公開サーバー構成</summary>
  ```
  "mcpServers": {
    "mcp-server-salesforce": {
      "command": "uvx",
      "args": [
        "mcp-server-salesforce"
      ]
    }
  }
  ```
</details>

## 開発

### ビルドと公開

パッケージを配布用に準備するには：

1. 依存関係の同期とロックファイルの更新：
```bash
uv sync
```

2. パッケージのビルド：
```bash
uv build
```

これにより、`dist/` ディレクトリにソースとホイールの配布物が作成されます。

3. PyPI への公開：
```bash
uv publish
```

注意：環境変数またはコマンドフラグで PyPI 認証情報を設定する必要があります：
- トークン：`--token` または `UV_PUBLISH_TOKEN`
- またはユーザー名/パスワード：`--username`/`UV_PUBLISH_USERNAME` と `--password`/`UV_PUBLISH_PASSWORD`

### デバッグ

MCP サーバーは stdio 経由で実行されるため、デバッグは困難な場合があります。最適なデバッグ体験のために、[MCP Inspector](https://github.com/modelcontextprotocol/inspector) の使用を強くお勧めします。

[`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) を使って次のコマンドで MCP Inspector を起動できます：

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-server-salesforce run mcp-server-salesforce
```

起動すると、Inspector はブラウザでアクセスできる URL を表示し、デバッグを開始できます。

## テスト

テストを実行するには:

```bash
uv pip install -e ".[test]"
python -m pytest
```

詳細な出力でテストを実行するには:

```bash
python -m pytest -v
```

テストカバレッジを確認するには:

```bash
python -m pytest --cov=mcp_server_salesforce
```