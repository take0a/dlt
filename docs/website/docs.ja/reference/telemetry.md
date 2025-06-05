---
title: Telemetry
description: Anonymous usage information with dlt telemetry
keywords: [telemetry, usage information, opt out]
---

# テレメトリ

`dlt` は**匿名**の使用情報を収集し、報告します。
この情報は、ライブラリの改善方法を決定する上で不可欠です。
テレメトリは個人データを送信しません。
ランダムなトラッキング Cookie を作成し、`~/.dlt` ディレクトリに保存します。
テレメトリはいつでも無効にしたり、独自のサーバーに送信したりできます。

## オプトアウトの方法

任意の dlt [コマンド](command-line-interface.md) に `--disable-telemetry` を追加することで、テレメトリを無効にできます。

このコマンドは、現在のプロジェクトとマシン全体の両方でテレメトリを無効にします。

```sh
dlt --disable-telemetry
```

このコマンドはテレメトリを永続的に無効にし、`chess` パイプラインを初期化します。

```sh
dlt --disable-telemetry init chess duckdb
```

次のコマンドで現在のテレメトリ ステータスを確認できます。

```sh
dlt telemetry
```

テレメトリを無効にする別の方法は、`.dlt` フォルダーの `config.toml` ファイルで `runtime.dlthub_telemetry` オプションを設定することです。

```toml
[runtime]

dlthub_telemetry=false
```

## 送信内容

匿名テレメトリは、以下の場合に送信されます。

- コマンドラインから任意の `dlt` コマンドが実行された場合。

データにはコマンド名が含まれます。

`dlt init` コマンドの場合は、要求された出力先とデータソース名も送信されます。
- `pipeline.run` が呼び出された場合、[抽出、正規化、ロード](explainers/how-dlt-works.md) ステップが完了した時点で情報が送信されます。
データには、出力先名 (例: `duckdb`)、データセット名のハッシュ、パイプライン名、デフォルトのスキーマ名、出力先フィンガープリント (選択された出力先設定フィールドのハッシュ)、経過時間、およびステップの成功/失敗が含まれます。
- `dbt` および `airflow` ヘルパーが使用された場合

`dlt init` テレメトリメッセージの例を次に示します。

```json
{
  "anonymousId": "933dd165453d196a58adaf49444e9b4c",
  "context": {
    "ci_run": false,
    "cpu": 8,
    "exec_info": [],
    "library": {
      "name": "dlt",
      "version": "0.2.0a25"
    },
    "os": {
      "name": "Linux",
      "version": "4.19.128-microsoft-standard"
    },
    "python": "3.8.11"
  },
  "event": "command_init",
  "properties": {
    "destination_name": "bigquery",
    "elapsed": 3.1720383167266846,
    "event_category": "command",
    "event_name": "init",
    "pipeline_name": "pipedrive",
    "success": true
  }
}
```

`load` パイプライン実行ステップの例:

```json
{
  "anonymousId": "570816b273a41d16caacc26a797204d9",
  "context": {
    "ci_run": false,
    "cpu": 3,
    "exec_info": [],
    "library": {
      "name": "dlt",
      "version": "0.2.0a26"
    },
    "os": {
      "name": "Darwin",
      "version": "21.6.0"
    },
    "python": "3.10.10"
  },
  "event": "pipeline_load",
  "properties": {
    "destination_name": "duckdb",
    "destination_fingerprint": "",
    "pipeline_name_hash": "OpVShb3cX7qQAmOZSbV8",
    "dataset_name_hash": "Hqk0a3Ov5AD55KjSg2rC",
    "default_schema_name_hash": "Hqk0a3Ov5AD55KjSg2rC",
    "elapsed": 2.234885,
    "event_category": "pipeline",
    "event_name": "load",
    "success": true,
    "transaction_id": "39c3b69c858836c36b9b7c6e046eb391"
  }
}
```

## メッセージ `context`

メッセージ `context` には以下の情報が含まれます。

- `anonymousId`: `~/.dlt/.anonymous_id` に保存されるランダムなトラッキング Cookie。
- `ci_run`: メッセージが CI 環境 (例: `GitHub Actions`、`Travis CI`) から送信されたかどうかを示すフラグ。
- `cpu`: コア数。
- `exec_info`: 実行環境を識別する文字列のリスト (例: `kubernetes`、`docker`、`airflow`)。
- `library`、`os`、`python` は、`dlt` の実行環境に関する情報を提供します。

## 独自のトラッカーにテレメトリデータを送信

独自のトラッカーを設定して、テレメトリイベントを受信できます。
[`dlt` と Cloudflare を使用](https://dlthub.com/blog/dlt-segment-migration)、スケーラブルでグローバルに分散されたエッジサービスを作成できます。

トラッカーが起動したら、`dlt` をトラッカーに指定します。
グローバル `config.toml` を使用して、特定のマシン上のすべてのパイプラインをリダイレクトできます。

```toml
[runtime]
dlthub_telemetry_endpoint="telemetry-tracker.services4745.workers.dev"
```

### Segment でイベントを追跡する

匿名テレメトリをご自身の [Segment](https://segment.com/) アカウントに送信できます。
HTTP サーバーソースを作成し、WRITE KEY を生成して、次のように `config.toml` に渡す必要があります。

```toml
[runtime]
dlthub_telemetry_endpoint="https://api.segment.io/v1/track"
dlthub_telemetry_segment_write_key="<write_key>"
```

