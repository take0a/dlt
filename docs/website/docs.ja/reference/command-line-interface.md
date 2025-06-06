---
title: Command Line Interface
description: Command line interface (CLI) full reference of dlt
keywords: [command line interface, cli, dlt init]
---


# Command Line Interface Reference

<!-- this page is fully generated from the argparse object of dlt, run make update-cli-docs to update it -->

This page contains all commands available in the dlt CLI and is generated automatically from the fully populated python argparse object of dlt.

:::note
フラグと位置指定コマンドは親コマンドから継承されます。
コマンド文字列内の位置は重要です。
たとえば、パイプラインコマンドでデバッグモードを有効にするには、ベースとなる dlt コマンドにデバッグフラグを追加する必要があります。

```sh
dlt --debug pipeline
```

パイプラインキーワードの後に​​フラグを追加しても機能しません。
:::

## `dlt`

DLTパイプラインを作成、追加、検査、デプロイします。
詳細なヘルプは https://dlthub.com/docs/reference/command-line-interface でご覧いただけます。

**使用方法**

```sh
dlt [-h] [--version] [--disable-telemetry] [--enable-telemetry]
    [--non-interactive] [--debug]
    {telemetry,studio,schema,pipeline,init,render-docs,deploy,ai} ...
```

<details>

<summary>引数とオプションを表示</summary>

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--version` - プログラムのバージョン番号を表示して終了します
* `--disable-telemetry` - コマンド実行前にテレメトリを無効にします
* `--enable-telemetry` - コマンド実行前にテレメトリを有効にします
* `--non-interactive` - 非対話型モード。確認とプロンプトにはデフォルトの選択が自動的に行われます。
* `--debug` - 例外発生時のフルスタックトレースを表示します。出力が十分に明確でない場合のデバッグに役立ちます。

**利用可能なサブコマンド**
* [`telemetry`](#dlt-telemetry) - テレメトリのステータスを表示します
* [`studio`](#dlt-studio) - Starts the dlt studio marimo app
* [`schema`](#dlt-schema) - スキーマを表示、変換、アップグレードします
* [`pipeline`](#dlt-pipeline) - ローカルで実行されたパイプラインに対する操作を実行します
* [`init`](#dlt-init) - 既存の検証済みソースを追加するか、テンプレートから新しいソースを作成して、現在のフォルダにパイプラインプロジェクトを作成します
* [`render-docs`](#dlt-render-docs) - CLI ドキュメントの Markdown 版をレンダリングします
* [`deploy`](#dlt-deploy) - 選択したパイプラインスクリプトのデプロイメントパッケージを作成します
* [`ai`](#dlt-ai) - Use ai-powered development tools and utilities

</details>

## `dlt telemetry`

テレメトリのステータスを表示します。

**使用方法**

```sh
dlt telemetry [-h]
```

**説明**

`dlt telemetry` コマンドは、dlt テレメトリの現在のステータスを表示します。
テレメトリと送信される内容の詳細については、テレメトリのドキュメントをご覧ください。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt studio`

Starts the dlt studio marimo app.

**Usage**
```sh
dlt studio [-h]
```

**Description**

The `dlt studio` command starts the dlt studio app. You can use the studio:

* to list and inspect local pipelines
* browse the full pipeline schema and all hints
* browse the data in the destination
* inspect the pipeline state.

<details>

<summary>Show Arguments and Options</summary>

Inherits arguments from [`dlt`](#dlt).

**Options**
* `-h, --help` - Show this help message and exit

</details>

## `dlt schema`

スキーマを表示、変換、アップグレードします。

**使用方法**

```sh
dlt schema [-h] [--format {json,yaml}] [--remove-defaults] file
```

**説明**

`dlt schema` コマンドは、dlt スキーマ `dlt schema path/to/my_schema_file.yaml` を読み込み、検証し、出力します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `file` - スキーマファイル名（yaml または json 形式）。拡張子に基づいて自動検出されます。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します。
* `--format {json,yaml}` - この形式でスキーマを表示します。
* `--remove-defaults` - デフォルトのヒント値を表示しません。

</details>

## `dlt pipeline`

ローカルで実行されたパイプラインに対する操作。

**使用方法**
```sh
dlt pipeline [-h] [--list-pipelines] [--hot-reload] [--pipelines-dir
    PIPELINES_DIR] [--verbose] [pipeline_name]
    {info,show,failed-jobs,drop-pending-packages,sync,trace,schema,drop,load-package}
    ...
```

**説明**

`dlt pipeline` コマンドは、パイプラインの作業ディレクトリ、テーブル、および宛先のデータを検査し、データのロード中に発生した問題をチェックするための一連のコマンドを提供します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `pipeline_name` - パイプライン名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--list-pipelines, -l` - ローカルパイプラインを一覧表示します
* `--hot-reload` - streamlit アプリをリロードします（コア開発用）
* `--pipelines-dir PIPELINES_DIR` - パイプラインの作業ディレクトリ
* `--verbose, -v` - 特定のコマンドの詳細情報を表示します

**利用可能なサブコマンド**
* [`info`](#dlt-pipeline-info) - パイプラインの状態を表示します。詳細については -v または -vv を使用してください。
* [`show`](#dlt-pipeline-show) - 読み込みステータスとデータセットエクスプローラーを備えた Streamlit アプリを生成して起動します。
* [`failed-jobs`](#dlt-pipeline-failed-jobs) - 完了したパッケージ、失敗したジョブ、および関連するエラーメッセージに含まれる、失敗した読み込みに関する情報を表示します。
* [`drop-pending-packages`](#dlt-pipeline-drop-pending-packages) - 部分的に読み込まれたパッケージも含め、抽出および正規化されたすべてのパッケージを削除します。
* [`sync`](#dlt-pipeline-sync) - パイプラインのローカル状態を削除し、すべてのスキーマをリセットして、出力先から復元します。出力先の状態、データ、スキーマはそのまま残ります。
* [`trace`](#dlt-pipeline-trace) - 前回の実行トレースを表示します。詳細については -v または -vv を使用してください。
* [`schema`](#dlt-pipeline-schema) - デフォルトのスキーマを表示します。
* [`drop`](#dlt-pipeline-drop) - 選択したテーブルを削除し、状態をリセットします。
* [`load-package`](#dlt-pipeline-load-package) - ロードパッケージに関する情報を表示します。詳細については -v または -vv を使用してください。

</details>

### `dlt pipeline info`

パイプラインの状態を表示します。詳細については -v または -vv を使用してください。

**使用方法**
```sh
dlt pipeline [pipeline_name] info [-h]
```

**説明**

パイプラインの作業ディレクトリの内容を表示します。データセット名、出力先、スキーマのリスト、スキーマ内のリソース、完了および正規化されたロードパッケージのリスト、そしてオプションで、抽出プロセス中にリソースによって設定されたパイプラインの状態を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline show`

読み込みステータスとデータセット エクスプローラーを備えた Streamlit アプリを生成して起動します。

**使用方法**
```sh
dlt pipeline [pipeline_name] show [-h]
```

**説明**

読み込みステータスとデータセットエクスプローラーを備えたStreamlit (https://streamlit.io/) アプリを生成し、起動します。

これは、出力先のスキーマとデータ、パイプラインの状態、読み込みステータス/統計情報を確認できるシンプルなアプリです。出力先の認証情報にアクセスするには、パイプラインスクリプトを実行したフォルダと同じフォルダから実行する必要があります。

現在の環境に `streamlit` がインストールされている必要があります: `pip install streamlit`。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline failed-jobs`

すべての完了したパッケージ、失敗したジョブ、および関連するエラー メッセージ内のすべての失敗したロードに関する情報を表示します。

**使用方法**
```sh
dlt pipeline [pipeline_name] failed-jobs [-h]
```

**説明**

このコマンドは、すべてのロードパッケージをスキャンして失敗したジョブを検索し、ロードされたファイルの情報と、ロード先からの失敗メッセージを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline drop-pending-packages`

部分的にロードされたものも含め、抽出され正規化されたすべてのパッケージを削除します。

**使用方法**

```sh
dlt pipeline [pipeline_name] drop-pending-packages [-h]
```

**説明**

パイプラインの作業ディレクトリにある、抽出および正規化されたすべてのパッケージを削除します。
`dlt` は、抽出および正規化されたロードパッケージをパイプラインの作業ディレクトリに保持します。
`run` メソッドが呼び出されると、まず保留中のパッケージの正規化とロードを試みます。
上記のコマンドは、これらのパッケージを削除します。
**パイプラインの状態** は、削除されたパッケージが作成された時点の状態に戻らないことに注意してください。
出力先が状態同期をサポートしている場合は、`dlt pipeline ... sync` を使用することをお勧めします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline sync`

パイプラインのローカル状態を削除し、すべてのスキーマをリセットして、宛先から復元します。
宛先の状態、データ、スキーマはそのまま残ります。

**使用方法**

```sh
dlt pipeline [pipeline_name] sync [-h] [--destination DESTINATION]
    [--dataset-name DATASET_NAME]
```

**説明**

このコマンドは、パイプラインの作業ディレクトリ（保留中のパッケージ、同期されていない状態の変更、スキーマを含む）を削除し、出力先から最後に同期されたデータを取得します。
パイプラインがロードしているデータセットを削除した場合、このコマンドはパイプラインの状態を完全にリセットします。

パイプラインに作業ディレクトリがない場合、このコマンドを使用して出力先から作業ディレクトリを作成できます。
これを行うには、データセット名と出力先名をCLIに渡し、`pipeline sync`コマンドを実行するフォルダにある出力先（`.dlt/secrets.toml`）に接続するための認証情報を提供する必要があります。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--destination DESTINATION` - ローカルパイプラインの状態が不明な場合に、この出力先から同期します。
* `--dataset-name DATASET_NAME` - ローカルパイプラインの状態が不明な場合に、同期元のデータセット名を指定します。

</details>

### `dlt pipeline trace`

最後の実行トレースを表示します。詳細については -v または -vv を使用してください。

**使用方法**

```sh
dlt pipeline [pipeline_name] trace [-h]
```

**説明**

パイプラインの最後の実行のトレースを表示します。実行開始日、経過時間、およびすべてのステップ（`extract`、`normalize`、`load`）の同じ情報が含まれます。
いずれかのステップが失敗した場合は、その問題の原因となった例外のメッセージが表示されます。
`load` および `run` ステップが成功した場合は、代わりにロード情報が表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline schema`

デフォルトのスキーマを表示します。

**使用方法**

```sh
dlt pipeline [pipeline_name] schema [-h] [--format {json,yaml}]
    [--remove-defaults]
```

**説明**

選択したパイプラインのデフォルトのスキーマを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--format {json,yaml}` - この形式でスキーマを表示します
* `--remove-defaults` - デフォルトのヒント値を表示しません

</details>

### `dlt pipeline drop`

テーブルを選択的に削除し、状態をリセットします。

**使用方法**

```sh
dlt pipeline [pipeline_name] drop [-h] [--destination DESTINATION]
    [--dataset-name DATASET_NAME] [--drop-all] [--state-paths [STATE_PATHS ...]]
    [--schema SCHEMA_NAME] [--state-only] [resources ...]
```

**説明**

テーブルを選択的に削除し、状態をリセットします。

```sh
dlt pipeline <pipeline name> drop [resource_1] [resource_2]
```

選択したリソースによって生成されたテーブルを削除し、それらに関連付けられた状態をリセットします。
主に、選択したテーブルを強制的に完全更新するために使用されます。
以下の例では、GitHub パイプラインの `repo_events` リソースによって生成されたすべてのテーブルを削除します。

```sh
dlt pipeline github_events drop repo_events
```

`dlt` は、削除されたテーブルの名前とリセットされるリソース状態スロットを通知します。

```text
About to drop the following data in dataset airflow_events_1 in destination dlt.destinations.duckdb:
Selected schema:: github_repo_events
Selected resource(s):: ['repo_events']
Table(s) to drop:: ['issues_event', 'fork_event', 'pull_request_event', 'pull_request_review_event', 'pull_request_review_comment_event', 'watch_event', 'issue_comment_event', 'push_event__payload__commits', 'push_event']
Resource(s) state to reset:: ['repo_events']
Source state path(s) to reset:: []
Do you want to apply these changes? [y/N]
```

上記のコマンドを実行すると、以下の処理が実行されます。

1. 指定されたすべてのテーブルが、コピー先から削除されます。
`dlt` はネストされたテーブルも削除することに注意してください。
2. 指定されたすべてのテーブルが、指定されたスキーマから削除されます。
3. リソース `repo_events` の状態が検出され、リセットされます。
4. 新しいスキーマと状態がコピー先に保存されます。

`drop` コマンドは、いくつかの高度な設定を受け付けます。

1. 正規表現を使用してリソースを選択できます。
正規表現パターンを示すには、先頭に `re:` 文字列を追加します。
以下の例では、`repo` で始まるすべてのリソースを選択します。

```sh
dlt pipeline github_events drop "re:^repo"
```

2. 指定されたスキーマ内のすべてのテーブルを削除できます:

```sh
dlt pipeline chess drop --drop-all
```

3. ソース状態にJsonPathを渡すことで、リセットする追加の状態スロットを指定できます。
以下の例では、ソース状態の`archives`スロットをリセットしています。

```sh
dlt pipeline chess_pipeline drop --state-paths archives
```

これにより、`chess` ソース内の `archives` キーが選択されます。

```json
{
  "sources":{
    "chess": {
      "archives": [
        "https://api.chess.com/pub/player/magnuscarlsen/games/2022/05"
      ]
    }
  }
}
```

**このコマンドはまだ実験的** であり、インターフェースは変更される可能性があります。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**位置引数**
* `resources` - 削除する1つ以上のリソース。リソース名（複数可）または正規表現パターン（複数可）を指定できます。正規表現パターンは re: で始まる必要があります。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します。
* `--destination DESTINATION` - ローカルパイプラインの状態が不明な場合、この出力先から同期します。
* `--dataset-name DATASET_NAME` - ローカルパイプラインの状態が不明な場合、同期元のデータセット名を指定します。
* `--drop-all` - スキーマ内にあるすべてのリソースを削除します。[resources] 引数よりも優先されます。
* `--state-paths [STATE_PATHS ...]` - 削除する状態キーまたはJSONパス
* `--schema SCHEMA_NAME` - 削除するスキーマ名（デフォルトスキーマ以外の場合）。
* `--state-only` - テーブルを削除せずに、一致するリソースの状態のみを消去します。

</details>

### `dlt pipeline load-package`

ロード パッケージに関する情報を表示します。詳細については -v または -vv を使用してください。

**使用方法**
```sh
dlt pipeline [pipeline_name] load-package [-h] [load-id]
```

**説明**

指定された `load_id` を持つロードパッケージの情報を表示します。`load_id` パラメータはデフォルトで最新のパッケージに設定されます。
パッケージ情報には、パッケージの状態（`COMPLETED/PROCESSED`）と、パッケージ内のすべてのジョブのリスト（ステータス、ファイルサイズ、タイプ、そして失敗したジョブの場合は出力先からのエラーメッセージ）が含まれます。
`dlt pipeline -v ...` で詳細フラグを設定すると、そのパッケージのロード中に出力先に​​作成されたすべてのテーブルと列のリストも表示できます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**位置引数**
* `load-id` - 完了または正規化されたパッケージのロードID。デフォルトは最新のパッケージです。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt init`

既存の検証済みソースを追加するか、テンプレートから新しいソースを作成して、現在のフォルダーにパイプライン プロジェクトを作成します。

**使用方法**
```sh
dlt init [-h] [--list-sources] [--list-destinations] [--location LOCATION]
    [--branch BRANCH] [--eject] [source] [destination]
```

**説明**

`dlt init` コマンドは、`source` から `destination` にデータをロードする新しい DLT パイプライン スクリプトを作成します。
コマンドを実行すると、以下の処理が行われます。

1. 現在のフォルダが空の場合、`.dlt/config.toml`、`.dlt/secrets.toml`、`.gitignore` ファイルを追加して、基本的なプロジェクト構造を作成します。
2. `source` 引数が検証済みのソースのいずれかと一致するかどうかを確認し、一致する場合はプロジェクトに追加します。
3. `source` が不明な場合は、汎用テンプレートを使用して開始します。
4. `destination` を使用するようにパイプライン スクリプトを書き換えます。
5. 指定されたソースと宛先のサンプル構成と認証情報を `secrets.toml` と `config.toml` に作成します。
6. ソースとデスティネーションに必要な依存関係を含む `requirements.txt` を作成します。存在する場合は、追加する内容の指示を表示します。

このコマンドは同じフォルダ内で複数回使用して、ソース、デスティネーション、パイプラインを追加できます。
また、既存の `source` 名で再度実行すると、検証済みのソースコードが最新バージョンに更新されます。
ファイルが上書きされる場合、または特定のパイプラインを実行するために `dlt` バージョンのアップグレードが必要な場合は、警告が表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `source` - パイプラインを作成するデータソースの名前。既存の検証済みソースを追加するか、データソースの検証済みソースがまだ実装されていない場合は新しいパイプラインテンプレートを作成します。
* `destination` - 出力先の名前（例：BigQuery または Redshift）

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します。
* `--list-sources, -l` - 利用可能なすべての検証済みソースとその簡単な説明を表示します。各ソースについて、ローカルの `dlt` バージョンの更新が必要かどうかを確認し、関連する警告を出力します。
* `--list-destinations` - すべてのコア DLT 出力先の名前を表示します。
* `--location LOCATION` - 高度な設定。検証済みソースリポジトリへの特定の URL またはローカルパスを使用します。
* `--branch BRANCH` - 高度な設定。検証済みソースリポジトリの特定のブランチを使用してテンプレートを取得します。
* `--eject` - sql_database や rest_api などのコア ソースのソース コードが排出され、編集できるようになります。

</details>

## `dlt render-docs`

cli ドキュメントのマークダウン バージョンをレンダリングします。

**使用方法**
```sh
dlt render-docs [-h] [--compare] file_name
```

**説明**

`dlt render-docs` コマンドは、argparse ヘルプ出力を解析して Markdown ファイルを生成することで、CLI ドキュメントの Markdown 版をレンダリングします。
ドキュメント Web サイトでこれを読んでいる場合は、このコマンドによって生成された CLI ドキュメントのレンダリング版を参照していることになります。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `file_name` - 出力ファイル名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--compare` - 変更を比較し、出力が更新される場合は例外を発生します

</details>

## `dlt deploy`

選択したパイプライン スクリプトのデプロイメント パッケージを作成します。

**使用方法**
```sh
dlt deploy [-h] pipeline-script-path {github-action,airflow-composer} ...
```

**説明**

`dlt deploy` コマンドは、パイプラインのデプロイメントを準備し、その手順を段階的に説明します。
この機能を有効にするには、まず `pip install "dlt[cli]"` を実行して、現在の環境にパッケージを追加してください。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `pipeline-script-path` - パイプラインスクリプトへのパス

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

**利用可能なサブコマンド**
* [`github-action`](#dlt-deploy-github-action) - パイプラインを github アクションにデプロイします
* [`airflow-composer`](#dlt-deploy-airflow-composer) - パイプラインを Airflow にデプロイします

</details>

### `dlt deploy github-action`

パイプラインを Github Actions にデプロイします。

**使用方法**
```sh
dlt deploy pipeline-script-path github-action [-h] [--location LOCATION]
    [--branch BRANCH] --schedule SCHEDULE [--run-manually] [--run-on-push]
```

**説明**

パイプラインを GitHub Actions にデプロイします。

GitHub Actions (https://github.com/features/actions) は、パイプラインの実行に使用できる大規模な無料枠を備えた CI/CD ランナーです。

GitHub Actions を実行するタイミングは、cron スケジュール式を使用して指定する必要があります。このコマンドは、追加のフラグも受け取ります。
`--run-on-push` (デフォルトは False) と `--run-manually` (デフォルトは True)。cron スケジュール式は引用符で囲むことを忘れないでください。

ドキュメントに記載されている chess.com API の例では、`dlt deploy chess.py github-action --schedule "*/30 * * * *"` でデプロイできます。

詳細については、ドキュメントの GitHub Actions を使用したパイプラインのデプロイ方法に関するガイドをご覧ください。

<details>

<summary>引数とオプションを表示</summary>

[`dlt deploy`](#dlt-deploy) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--location LOCATION` - 高度な設定。パイプラインリポジトリへの特定のURLまたはローカルパスを使用します。
* `--branch BRANCH` - 高度な設定。テンプレートを取得するために、デプロイリポジトリの特定のブランチを使用します。
* `--schedule SCHEDULE` - パイプラインを実行するスケジュール（cron形式）。例: '*/30 * * * *' は、パイプラインを30分ごとに実行します。スケジューラ式は引用符で囲むことを忘れないでください。
* `--run-manually` - GitHub Actions UIからパイプラインを手動で実行できるようにします。
* `--run-on-push` - リポジトリへのプッシュごとにパイプラインを実行します。

</details>

### `dlt deploy airflow-composer`

パイプラインを Airflow にデプロイします。

**使用方法**
```sh
dlt deploy pipeline-script-path airflow-composer [-h] [--location LOCATION]
    [--branch BRANCH] [--secrets-format {env,toml}]
```

**説明**

Google Composer (https://cloud.google.com/composer?hl=en) は、Google が提供するマネージド Airflow 環境です。詳細については、Airflow を使用してパイプラインをデプロイする方法についてのドキュメントガイドをご覧ください。このコマンドは、次の処理を実行します。

* パイプライン スクリプト用に、カスタマイズ可能な Airflow DAG を作成します。

DAG は、このプロセスを容易にするために `dlt` Airflow ラッパー (https://github.com/dlt-hub/dlt/blob/devel/dlt/helpers/airflow_helper.py#L37) を使用します。

* Airflow に追加する必要がある環境変数とシークレットを提供します。

* GitHub リポジトリを Airflow Composer インスタンスの `dag` フォルダと同期するための cloudbuild ファイルを提供します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt deploy`](#dlt-deploy) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--location LOCATION` - 高度な設定。パイプラインリポジトリへの特定のURLまたはローカルパスを使用します。
* `--branch BRANCH` - 高度な設定。デプロイリポジトリの特定のブランチを使用してテンプレートを取得します。
* `--secrets-format {env,toml}` - シークレットのフォーマット

</details>

## `dlt ai`

Use AI-powered development tools and utilities.

**Usage**
```sh
dlt ai [-h] {setup} ...
```

**Description**

The `dlt ai` command provides commands to configure your LLM-enabled IDE and MCP server.

<details>

<summary>Show Arguments and Options</summary>

Inherits arguments from [`dlt`](#dlt).

**Options**
* `-h, --help` - Show this help message and exit

**Available subcommands**
* [`setup`](#dlt-ai-setup) - Generate ide-specific configuration and rules files

</details>

### `dlt ai setup`

Generate IDE-specific configuration and rules files.

**Usage**
```sh
dlt ai setup [-h] [--location LOCATION] [--branch BRANCH]
    {cursor,continue,cline,claude_desktop}
```

**Description**

Get AI rules files and configuration into your local project for the selected IDE.
Files are fetched from https://github.com/dlt-hub/verified-sources by default.

<details>

<summary>Show Arguments and Options</summary>

Inherits arguments from [`dlt ai`](#dlt-ai).

**Positional arguments**

**Options**
* `-h, --help` - Show this help message and exit
* `--location LOCATION` - Advanced. specify git url or local path to rules files and config.
* `--branch BRANCH` - Advanced. specify git branch to fetch rules files and config.

</details>

