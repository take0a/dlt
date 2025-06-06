---
title: AI workflows
description: Explore data in your dlt+ project with Claude Desktop using the Model Context Protocol
keywords: [dlt+, Claude Desktop, MCP, Model Context Protocol]
---

# AI workflows

dlt+の一環として、AIワークフローを活用した開発を強化するためのツールをいくつか開発しています。
その1つが、Claude Desktopのデータ探索用プラグインである[Model Context Protocol (MCP)](https://modelcontextprotocol.io)です。

## 前提条件

- 仮想環境に dlt+ がインストールされている（[インストールガイド](../getting-started/installation.md) を参照）
- [Claude Desktop](https://claude.ai/download) がインストールされている

## MCPサポート付きのdlt+をインストールします。

仮想環境がアクティブ化されていることを確認し、以下の手順を実行してください。

```sh
pip install dlt-plus[mcp]
```

## dlt+ プロジェクトの設定または使用

既存の dlt+ プロジェクトを使用することも、簡単なテストプロジェクトを作成して MCP ワークフローを試すこともできます。

### 既存のプロジェクトの使用

既に dlt+ プロジェクトをお持ちの場合は、そのまま使用できます。ただし、少なくとも 1 つのパイプラインを実行し、探索可能なデータがあることを確認してください。
プロジェクトの準備が整っている場合は、[Claude Desktop の設定](#configure-claude-desktop) に進んでください。

### テストプロジェクトの作成

まだプロジェクトをお持ちでない場合は、以下の手順に従って簡単なプロジェクトを作成してください。

Unix ベースのシステムの場合：

```sh
touch dlt.yml
```

または、任意のテキストエディタで空の dlt.yml ファイルを作成することもできます。

以下の設定をコピーして `dlt.yml` ファイルに貼り付けます:

```yaml
sources:
  pokemon_api:
    type: dlt.sources.rest_api.rest_api
    client:
      base_url: https://pokeapi.co/api/v2
    resource_defaults:
      endpoint:
        params:
          limit: 1000
    resources:
      - pokemon
      - berry
      - location

destinations:
  pokemon_local:
    type: filesystem
    bucket_url: pokemon_data

pipelines:
  pokemon:
    source: pokemon_api
    destination: pokemon_local
    dataset_name: pokemon_dataset

datasets:
  pokemon_dataset:
    destination:
      - pokemon_local
```

これにより、Pokemon API からデータを読み込み、ローカルディレクトリに保存する単一のパイプラインを持つ dlt+ プロジェクトが作成されます。

プロジェクト構成を検証します:

```sh
dlt project config validate
```

構成が有効な場合は、次のメッセージが表示されます:

```sh
Configuration validation successful!
```

つまり、パイプラインを実行してデータを取得できるようになりました:

```sh
dlt pipeline pokemon run
```

パイプラインが正常に実行されると、次のメッセージが表示されます:

```sh
1 load package(s) were loaded to destination pokemon_local and into dataset pokemon_dataset
The pokemon_local destination used file:///path/to/your/project/_data/dev/local/pokemon_data location to store data
Load package 1739383145.0668569 is LOADED and contains no failed jobs
```

プロジェクトにデータがいくつか追加されました。
次のステップはClaude Desktopの設定ですが、そのためには`dlt`実行ファイルへのパスを取得する必要があります。
仮想環境を使用している場合、`dlt`実行ファイルは通常、`bin`ディレクトリにあります（Unix系システムの場合）。
例えば、仮想環境が`.venv`ディレクトリにある場合、`dlt`実行ファイルへのパスは`.venv/bin/dlt`です。
ターミナルで`which dlt`を実行すると、`dlt`実行ファイルへのパスが表示されます。
このパスをメモしておいてください。次のステップで使用します。

## Claude Desktop を設定する

[Claude Desktop](https://claude.ai/download) がインストールされ、アカウントを持っていることを確認してください。

### Claude デスクトップの設定を更新します。

Claude デスクトップで設定（macOS の場合は「Claude」>「設定」）に移動し、「開発者」の下にある「設定を編集」をクリックします。
`claude_desktop_config.json` ファイルの場所が表示されます。

テキストエディタでファイルを開き、以下の設定を追加します。

```json
{
  "mcpServers": {
    "dlt+ project": {
      "command": "</path/to/your/project/.venv/bin/dlt>",
      "args": [
        "project",
        "--project",
        "<path/to/your/project>",
        "mcp"
      ]
    }
  }
}
```

`</path/to/your/project/.venv/bin/dlt>` を前の手順の `dlt` 実行可能ファイルへのパスに置き換えて、ファイルを保存します。

:::warning
[環境変数](../../general-usage/credentials/setup.md#environment-variables)を使用して dlt を構成する場合は、それらを `dlt` 実行可能ファイルの前のコマンドの一部として必ず含めてください。
:::

### Claude デスクトップを再起動してください

**重要**: 新しい設定を読み込むため、Claude デスクトップを再起動してください。

:::note
設定を更新した後は、必ず Claude Desktop を再起動してください。
:::

### 接続を確認してください

Claude Desktop を再起動した後、チャットボックスの右下にあるツールアイコンで接続を確認できます。

![Claude Desktop connection icon](https://storage.googleapis.com/dlt-blog-images/plus/mcp/claude-desktop-tool-icon.png)

アイコンが表示されない場合は、`claude_desktop_config.json` が正しく保存されていること、および Claude Desktop が完全に再起動されていることを確認してください。

アイコンをクリックすると、「利用可能な MCP ツール」ポップアップとツールの説明が表示されます。

![Claude Desktop available MCP tools](https://storage.googleapis.com/dlt-blog-images/plus/mcp/claude-desktop-available-tools.png)

## チャットを始めましょう

Claude Desktop とチャットを開始し、dlt+ プロジェクト内のデータについて質問することができます。

例えば、「パイプラインにはどのテーブルがありますか？」と尋ねることができます。

![Claude Desktop chat example](https://storage.googleapis.com/dlt-blog-images/plus/mcp/claude-desktop-chat-example.png)

Claude は、ツールをローカルで実行する許可を求めます。

![Claude Desktop permission request](https://storage.googleapis.com/dlt-blog-images/plus/mcp/claude-desktop-permission-request.png)

権限を付与すると、Claude Desktop はツール (available_datasets) を実行し、(結果に応じて) 他のツールの選択と実行に進む場合があります。

:::tip
利用可能なすべてのツールを表示するには、チャット ボックスの右下隅にあるツール アイコンをクリックします。
:::

他にも以下のようなクエリ例があります。

- 「ポケモンテーブルにはどんな列がありますか？」
- 「ポケモンテーブルには何行ありますか？」
- 「ポケモンテーブルを変換して、ポケモンの名前の長さを入力する新しい列を追加してください。」
- 「ポケモンの平均身長はどれくらいですか？」

これで完了です！これで、Claude Desktop から MCP を使用して dlt+ プロジェクトを操作できるようになりました。

