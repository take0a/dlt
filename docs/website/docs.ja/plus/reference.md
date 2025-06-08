---
title: Command line interface
description: Command line interface (CLI) full reference of dlt
keywords: [command line interface, cli, dlt init]
---

# コマンドラインインターフェースリファレンス

<!-- this page is fully generated from the argparse object of dlt, run make update-cli-docs to update it -->

このページには、dlt CLI で使用できるすべてのコマンドが含まれており、dlt の完全に設定された Python argparse オブジェクトから自動的に生成されます。

:::note
フラグと位置指定コマンドは親コマンドから継承されます。
コマンド文字列内の位置は重要です。
たとえば、パイプラインコマンドでデバッグモードを有効にするには、ベースとなる dlt コマンドにデバッグフラグを追加する必要があります:

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
    {transformation,source,project,profile,pipeline,license,destination,dbt,dataset,cache,telemetry,schema,init,render-docs,deploy}
    ...
```

<details>

<summary>引数とオプションを表示</summary>

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--version` - プログラムのバージョン番号を表示して終了します
* `--disable-telemetry` - コマンド実行前にテレメトリを無効にします
* `--enable-telemetry` - コマンド実行前にテレメトリを有効にします
* `--non-interactive` - 非対話型モード。確認とプロンプトは自動的にデフォルトの選択が行われます。
* `--debug` - 例外発生時にフルスタックトレースを表示します。出力が不明瞭な場合のデバッグに役立ちます。

**利用可能なサブコマンド**
* [`transformation`](#dlt-transformation) - dlt+ プロジェクトの変換を実行します。試験的機能です。
* [`source`](#dlt-source) - dlt+ プロジェクトのソースを管理します
* [`project`](#dlt-project) - dlt+ プロジェクトを管理します
* [`profile`](#dlt-profile) - dlt+ プロジェクトのプロファイルを管理します
* [`pipeline`](#dlt-pipeline) - ローカルで実行されたパイプラインの操作
* [`license`](#dlt-license) - dlt+ ライセンスのステータスを表示します
* [`destination`](#dlt-destination) - プロジェクトの宛先を管理します
* [`dbt`](#dlt-dbt) - Dlt+ dbt 変換ジェネレーター
* [`dataset`](#dlt-dataset) - dlt+ プロジェクトのデータセットを管理します
* [`cache`](#dlt-cache) - dlt+ プロジェクトのローカルデータキャッシュを管理します。試験運用版です。
* [`telemetry`](#dlt-telemetry) - テレメトリのステータスを表示します。
* [`schema`](#dlt-schema) - スキーマを表示、変換、アップグレードします。
* [`init`](#dlt-init) - 既存の検証済みソースを追加するか、テンプレートから新しいソースを作成して、現在のフォルダにパイプラインプロジェクトを作成します。
* [`render-docs`](#dlt-render-docs) - CLI ドキュメントの Markdown 版をレンダリングします。
* [`deploy`](#dlt-deploy) - 選択したパイプラインスクリプトのデプロイメントパッケージを作成します。

</details>

## `dlt transformation`

dlt+ プロジェクトの変換を実行します。実験的。

**使用方法**

```sh
dlt transformation [-h] [--project PROJECT] [--profile PROFILE] pond_name
    {list,info,run,verify-inputs,verify-outputs,populate,flush,transform,populate-state,flush-state,render-t-layer}
    ...
```

**説明**

dlt+ プロジェクトでローカルキャッシュに対して変換を実行するコマンド

**これは試験的な機能であり、将来的に大幅に変更される予定です。**

**本番環境では使用しないでください。**

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `pond_name` - 変換の名前。プロジェクト内で最初に見つかったものには「.」を使用します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル

**使用可能なサブコマンド**
* [`list`](#dlt-transformation-list) - このディレクトリで検出されたすべての変換を一覧表示します
* [`info`](#dlt-transformation-info) - 変換情報（場所、キャッシュステータスなど）
* [`run`](#dlt-transformation-run) - キャッシュを同期し、変換を実行して出力をコミットします
* [`verify-inputs`](#dlt-transformation-verify-inputs) - キャッシュが定義済みのすべての入力に接続できること、および宣言されたテーブルが利用可能であることを検証します
* [`verify-outputs`](#dlt-transformation-verify-outputs) - 出力キャッシュがデータセットには宣言されたすべてのテーブルが含まれます
* [`populate`](#dlt-transformation-populate) - 入力から入力キャッシュデータセットにデータを同期します
* [`flush`](#dlt-transformation-flush) - 出力キャッシュデータセットから出力にデータをフラッシュします
* [`transform`](#dlt-transformation-transform) - 入力キャッシュデータセットに対して変換を実行し、出力キャッシュデータセットに書き込みます
* [`populate-state`](#dlt-transformation-populate-state) - 定義された出力から変換状態を設定します
* [`flush-state`](#dlt-transformation-flush-state) - 定義された出力に変換状態をフラッシュします
* [`render-t-layer`](#dlt-transformation-render-t-layer) - Tレイヤーの開始点をレンダリングします

</details>

### `dlt transformation list`

このディレクトリで検出されたすべての変換を一覧表示します。

**使用方法**
```sh
dlt transformation pond_name list [-h]
```

**説明**

このディレクトリで検出されたすべての変換を一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation info`

変換情報: 場所、キャッシュ ステータスなど。

**使用方法**
```sh
dlt transformation pond_name info [-h]
```

**説明**

変換情報: 場所、キャッシュ ステータスなど。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation run`

キャッシュを同期し、変換を実行して出力をコミットします。

**使用方法**
```sh
dlt transformation pond_name run [-h]
```

**説明**

キャッシュを同期し、変換を実行して出力をコミットします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation verify-inputs`

キャッシュが定義されたすべての入力に接続できること、および宣言されたテーブルが使用可能であることを確認します。

**使用方法**
```sh
dlt transformation pond_name verify-inputs [-h]
```

**説明**

キャッシュが定義されたすべての入力に接続できること、および宣言されたテーブルが使用可能であることを確認します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation verify-outputs`

出力キャッシュ データセットに宣言されたすべてのテーブルが含まれていることを確認します。

**使用方法**
```sh
dlt transformation pond_name verify-outputs [-h]
```

**説明**

出力キャッシュ データセットに宣言されたすべてのテーブルが含まれていることを確認します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation populate`

入力からのデータを入力キャッシュ データセットに同期します。

**使用方法**
```sh
dlt transformation pond_name populate [-h]
```

**説明**

入力からのデータを入力キャッシュ データセットに同期します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation flush`

出力キャッシュ データセットから出力にデータをフラッシュします。

**使用方法**
```sh
dlt transformation pond_name flush [-h]
```

**説明**

出力キャッシュ データセットから出力にデータをフラッシュします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation transform`

入力キャッシュ データセットに対して変換を実行し、出力キャッシュ データセットに書き込みます。

**使用方法**
```sh
dlt transformation pond_name transform [-h]
```

**説明**

入力キャッシュ データセットに対して変換を実行し、出力キャッシュ データセットに書き込みます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation populate-state`

定義された出力から変換状態を入力します。

**使用方法**
```sh
dlt transformation pond_name populate-state [-h]
```

**説明**

定義された出力から変換状態を入力します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation flush-state`

変換状態を定義された出力にフラッシュします。

**使用方法**
```sh
dlt transformation pond_name flush-state [-h]
```

**説明**

変換状態を定義された出力にフラッシュします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt transformation render-t-layer`

T レイヤーの開始点をレンダリングします。

**使用方法**
```sh
dlt transformation pond_name render-t-layer [-h]
```

**説明**

T レイヤーの開始点をレンダリングします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt 変換`](#dlt-transformation) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt source`

dlt+ プロジェクト ソースを管理します。

**使用方法**
```sh
dlt source [-h] [--project PROJECT] [--profile PROFILE] [source_name]
    {check,list,add} ...
```

**説明**

プロジェクトのソースを管理するためのコマンド。
引数なしで実行すると、現在のプロジェクト内のすべてのソースが一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `source_name` - 追加するソースの名前。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します。
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス。
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル。

**利用可能なサブコマンド**
* [`check`](#dlt-source-check) - (一時的な機能) ソースがインポート可能かどうかを確認します。sources フォルダ内のソースに対してのみ機能します。
* [`list`](#dlt-source-list) - プロジェクト内のすべてのソースを一覧表示します。
* [`add`](#dlt-source-add) - プロジェクトに新しいソースを追加します。

</details>

### `dlt source check`

(一時的な機能) ソースがインポート可能かどうかを確認します。ソース フォルダー内のソースに対してのみ機能します。

**使用方法**
```sh
dlt source [source_name] check [-h]
```

**説明**

(一時的な機能) ソースがインポート可能かどうかを確認します。ソース フォルダー内のソースに対してのみ機能します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt source`](#dlt-source) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt source list`

プロジェクト内のすべてのソースを一覧表示します。

**使用方法**
```sh
dlt source [source_name] list [-h]
```

**説明**

プロジェクト コンテキスト内のすべてのソースを一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt source`](#dlt-source) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt source add`

プロジェクトに新しいソースを追加します。

**使用方法**
```sh
dlt source [source_name] add [-h] [source_type]
```

**説明**

プロジェクトコンテキストに新しいソースを追加します。

* ソースタイプが指定されていない場合、ソースタイプはソース名と同じになります。
* 指定されたソースタイプが見つからない場合は、デフォルトのソーステンプレートが使用されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt source`](#dlt-source) から引数を継承します。

**位置引数**
* `source_type` - 追加するソースのタイプ。指定されていない場合、ソースタイプはソース名と同じになります。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt project`

dlt+ プロジェクトを管理します。

**使用方法**
```sh
dlt project [-h] [--project PROJECT] [--profile PROFILE]
    {config,clean,init,list,info,audit} ...
```

**説明**

dlt+プロジェクトを管理するためのコマンド。引数なしで実行すると、スコープ内のすべてのプロジェクトが一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル

**利用可能なサブコマンド**
* [`config`](#dlt-project-config) - 設定管理コマンド
* [`clean`](#dlt-project-clean) - 選択したプロファイルのローカルデータを消去します。プロジェクトファイルで tmp_dir が定義されている場合は削除されます。パイプラインと変換の作業ディレクトリもデフォルトで削除されます。リモートの保存先のデータは影響を受けません。
* [`init`](#dlt-project-init) - 新しい dlt+ プロジェクトを初期化します。
* [`list`](#dlt-project-list) - インストール済みの dlt パッケージに含まれるすべてのプロジェクトを一覧表示します。
* [`info`](#dlt-project-info) - 現在のプロジェクトの基本情報を一覧表示します。
* [`audit`](#dlt-project-audit) - 現在のプロファイルのリソースとシークレットの監査を作成し、ロックします。

</details>

### `dlt project config`

構成管理コマンド。

**使用方法**
```sh
dlt project config [-h] {validate,show} ...
```

**説明**

構成管理コマンド。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**位置引数**
* `validate` - 設定ファイルを検証する
* `show` - 設定を表示する

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt project config validate`

構成ファイルを検証します。

**使用方法**
```sh
dlt project config validate [-h]
```

**説明**

構成ファイルを検証します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt プロジェクト設定`](#dlt-project-config) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt project config show`

構成を表示します。

**使用方法**
```sh
dlt project config show [-h] [--format {json,yaml}] [--section SECTION]
```

**説明**

構成を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt プロジェクト設定`](#dlt-project-config) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--format {json,yaml}` - 出力フォーマット
* `--section SECTION` - 特定の設定セクション（例：ソース、パイプライン）を表示します

</details>

### `dlt project clean`

選択したプロファイルのローカルデータを消去します。
プロジェクトファイルでtmp_dirが定義されている場合は削除されます。
パイプラインと変換の作業ディレクトリもデフォルトで削除されます。
リモートの保存先のデータは影響を受けません。

**使用方法**
```sh
dlt project clean [-h] [--skip-data-dir]
```

**説明**

選択したプロファイルのローカルデータを消去します。
プロジェクトファイルでtmp_dirが定義されている場合は削除されます。
パイプラインと変換の作業ディレクトリもデフォルトで削除されます。
リモートの保存先のデータは影響を受けません。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--skip-data-dir` - パイプラインと変換の作業ディレクトリを削除しません。

</details>

### `dlt project init`

新しい dlt+ プロジェクトを初期化します。

**使用方法**
```sh
dlt project init [-h] [--project-name PROJECT_NAME] [--package] [--force]
    [source] [destination]
```

**説明**

新しい dlt+ プロジェクトを初期化します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**位置引数**
* `source` - DLTプロジェクトのソース名
* `destination` - DLTプロジェクトの宛先名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project-name PROJECT_NAME, -n PROJECT_NAME` - DLTプロジェクトの任意の名前
* `--package` - フラットプロジェクトではなくpipパッケージを作成します
* `--force` - 既存のプロジェクトでも上書きします

</details>

### `dlt project list`

インストールされた dlt パッケージ内にあるすべてのプロジェクトを一覧表示します。

**使用方法**
```sh
dlt project list [-h]
```

**説明**

インストールされた dlt パッケージ内にあるすべてのプロジェクトを一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt project info`

現在のプロジェクトの基本プロジェクト情報を一覧表示します。

**使用方法**
```sh
dlt project info [-h]
```

**説明**

現在のプロジェクトの基本プロジェクト情報を一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt project audit`

現在のプロファイルのリソースとシークレット監査を作成してロックします。

**使用方法**
```sh
dlt project audit [-h]
```

**説明**

現在のプロファイルのリソースとシークレット監査を作成してロックします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt project`](#dlt-project) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt profile`

dlt+ プロジェクト プロファイルを管理します。

**使用方法**
```sh
dlt profile [-h] [--project PROJECT] [--profile PROFILE] [profile_name]
    {info,list,add,pin} ...
```

**説明**

プロジェクトのプロファイルを管理するためのコマンド。
引数なしで実行すると、すべてのプロファイル、デフォルトプロファイル、および現在のプロジェクト内の固定プロファイルが一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `profile_name` - 追加するプロファイルの名前

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル

**使用可能なサブコマンド**
* [`info`](#dlt-profile-info) - プロファイル設定に関する情報を表示します。
* [`list`](#dlt-profile-list) - プロジェクト内のすべてのプロファイルのリストを表示します。
* [`add`](#dlt-profile-add) - プロジェクトに新しいプロファイルを追加します。
* [`pin`](#dlt-profile-pin) - プロファイルをプロジェクトに固定します。

</details>

### `dlt profile info`

プロフィール設定に関する情報を表示します。

**使用方法**
```sh
dlt profile [profile_name] info [-h]
```

**説明**

プロフィール設定に関する情報を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt profile`](#dlt-profile) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt profile list`

プロジェクト内のすべてのプロファイルのリストを表示します。

**使用方法**
```sh
dlt profile [profile_name] list [-h]
```

**説明**

プロジェクト内のすべてのプロファイルのリストを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt profile`](#dlt-profile) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt profile add`

プロジェクトに新しいプロファイルを追加します。

**使用方法**
```sh
dlt profile [profile_name] add [-h]
```

**説明**

プロジェクトに新しいプロファイルを追加します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt profile`](#dlt-profile) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt profile pin`

プロジェクトにプロフィールをピン留めします。

**使用方法**
```sh
dlt profile [profile_name] pin [-h]
```

**説明**

プロファイルをプロジェクトにピン留めします。
ピン留めされている間は、これが新しいデフォルト プロファイルになります。

<details>

<summary>引数とオプションを表示</summary>

[`dlt profile`](#dlt-profile) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt pipeline`

ローカルで実行されたパイプラインに対する操作。

**使用方法**
```sh
dlt pipeline [-h] [--project PROJECT] [--profile PROFILE] [--list-pipelines]
    [--hot-reload] [--pipelines-dir PIPELINES_DIR] [--verbose] [pipeline_name]
    {info,show,failed-jobs,drop-pending-packages,sync,trace,schema,drop,load-package,list,add,run}
    ...
```

**説明**

`dlt pipeline` コマンドは、パイプラインの作業ディレクトリ、テーブル、および宛先のデータを検査し、データのロード中に発生した問題をチェックするための一連のコマンドを提供します。

引数なしで実行すると、現在のプロジェクト内のすべてのパイプラインが一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `pipeline_name` - パイプライン名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル
* `--list-pipelines, -l` - ローカルパイプラインを一覧表示します
* `--hot-reload` - streamlit アプリをリロードします (コア開発用)
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
* [`list`](#dlt-pipeline-list) - プロジェクト内のすべてのパイプラインを一覧表示します。
* [`add`](#dlt-pipeline-add) - 現在のプロジェクトに新しいパイプラインを追加します。
* [`run`](#dlt-pipeline-run) - パイプラインを実行します。
</details>

### `dlt pipeline info`

パイプラインの状態を表示します。詳細については -v または -vv を使用してください。

**使用方法**
```sh
dlt pipeline [pipeline_name] info [-h]
```

**説明**

パイプラインの作業ディレクトリの内容を表示します。データセット名、宛先、スキーマのリスト、スキーマ内のリソース、完了して正規化されたロード パッケージのリスト、およびオプションで、抽出プロセス中にリソースによって設定されたパイプラインの状態。

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

読み込みステータスとデータセットエクスプローラーを備えた Streamlit (https://streamlit.io/) アプリを生成し、起動します。

これは、出力先のスキーマとデータ、パイプラインの状態、読み込みステータス/統計情報を確認できるシンプルなアプリです。
出力先の認証情報にアクセスするには、パイプラインスクリプトを実行したフォルダと同じフォルダから実行する必要があります。

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

このコマンドは、すべてのロード パッケージをスキャンして失敗したジョブを探し、ロードされたファイルに関する情報と宛先からの失敗メッセージを表示します。

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
上記のコマンドは、このようなパッケージを削除します。**パイプラインの状態** は、削除されたパッケージが作成された時点の状態に戻らないことに注意してください。
出力先が状態同期をサポートしている場合は、`dlt pipeline ... sync` を使用することをお勧めします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline sync`

パイプラインのローカル状態を削除し、すべてのスキーマをリセットして、宛先から復元します。宛先の状態、データ、スキーマはそのまま残ります。

**使用方法**
```sh
dlt pipeline [pipeline_name] sync [-h] [--destination DESTINATION]
    [--dataset-name DATASET_NAME]
```

**説明**

このコマンドは、保留中のパッケージ、同期されていない状態の変更、スキーマを含むパイプラインの作業ディレクトリを削除し、宛先から最後に同期されたデータを取得します。
パイプラインがロードしているデータセットを削除すると、このコマンドによってパイプラインの状態が完全にリセットされます。

作業ディレクトリのないパイプラインの場合は、このコマンドを使用して宛先から作業ディレクトリを作成できます。
これを行うには、データセット名と宛先名をCLIに渡し、`pipeline sync`コマンドを実行するフォルダにある宛先（つまり、`.dlt/secrets.toml`）に接続するための認証情報を提供する必要があります。

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

最後のパイプライン実行のトレースを表示します。実行開始日、経過時間、およびすべてのステップ（`extract`、`normalize`、`load`）の同じ情報が含まれます。
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

`dlt` は、削除されたテーブルの名前とリセットされるリソース状態スロットを通知します:

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

1. 正規表現を使用してリソースを選択できます。正規表現パターンを指定するには、先頭に `re:` 文字列を追加します。
以下の例では、`repo` で始まるすべてのリソースを選択します。

```sh
dlt pipeline github_events drop "re:^repo"
```

2. 指定されたスキーマ内のすべてのテーブルを削除できます:

```sh
dlt pipeline chess drop --drop-all
```

3. ソース状態にJsonPathを渡すことで、リセットする追加の状態スロットを指定できます。
以下の例では、ソース状態の`archives`スロットをリセットしています:

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

### `dlt pipeline list`

プロジェクト内のすべてのパイプラインを一覧表示します。

**使用方法**
```sh
dlt pipeline [pipeline_name] list [-h]
```

**説明**

プロジェクト内のすべてのパイプラインを一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt pipeline add`

現在のプロジェクトに新しいパイプラインを追加します。

**使用方法**
```sh
dlt pipeline [pipeline_name] add [-h] [--dataset-name DATASET_NAME] source_name
    destination_name
```

**説明**

現在のプロジェクトに新しいパイプラインを追加します。
ソースや宛先は作成されませんが、他のエンティティを名前で参照できます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**位置引数**
* `source_name` - 追加するソースの名前
* `destination_name` - 追加する宛先の名前

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--dataset-name DATASET_NAME` - 追加するデータセットの名前

</details>

### `dlt pipeline run`

パイプラインを実行します。

**使用方法**
```sh
dlt pipeline [pipeline_name] run [-h] [--limit LIMIT] [--resources RESOURCES]
```

**説明**

パイプラインを実行します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt pipeline`](#dlt-pipeline) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--limit LIMIT` - すべてのリソースの抽出ページ数を制限します。source.add_limit を参照してください。
* `--resources RESOURCES` - リソース名のカンマ区切りリスト。

</details>

## `dlt license`

dlt+ ライセンスのステータスを表示します。

**使用方法**
```sh
dlt license [-h] {show,scopes} ...
```

**説明**

dlt+ ライセンスのステータスを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

**利用可能なサブコマンド**
* [`show`](#dlt-license-show) - インストールされているライセンスを表示します
* [`scopes`](#dlt-license-scopes) - 利用可能なスコープを表示します

</details>

### `dlt license show`

インストールされているライセンスを表示します。

**使用方法**
```sh
dlt license show [-h]
```

**説明**

インストールされているライセンスを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt license`](#dlt-license) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt license scopes`

利用可能なスコープを表示します。

**使用方法**
```sh
dlt license scopes [-h]
```

**説明**

利用可能なスコープを表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt license`](#dlt-license) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

## `dlt destination`

プロジェクトの宛先を管理します。

**使用方法**
```sh
dlt destination [-h] [--project PROJECT] [--profile PROFILE] [destination_name]
    {list,list-available,add} ...
```

**説明**

プロジェクトの宛先を管理するためのコマンド。
引数なしで実行すると、現在のプロジェクト内のすべての宛先が一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `destination_name` - 出力先の名前

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル

**使用可能なサブコマンド**
* [`list`](#dlt-destination-list) - プロジェクト内のすべての出力先を一覧表示します。
* [`list-available`](#dlt-destination-list-available) - プロジェクトに追加できるすべての出力先タイプを一覧表示します。
* [`add`](#dlt-destination-add) - プロジェクトに新しい出力先を追加します

</details>

### `dlt destination list`

プロジェクト内のすべての宛先を一覧表示します。

**使用方法**
```sh
dlt destination [destination_name] list [-h]
```

**説明**

プロジェクト内のすべての宛先を一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt destination`](#dlt-destination) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt destination list-available`

プロジェクトに追加できるすべての宛先タイプを一覧表示します。

**使用方法**
```sh
dlt destination [destination_name] list-available [-h]
```

**説明**

プロジェクトに追加できるすべての宛先タイプを一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt destination`](#dlt-destination) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt destination add`

プロジェクトに新しい宛先を追加します。

**使用方法**
```sh
dlt destination [destination_name] add [-h] [--dataset-name DATASET_NAME]
    [destination_type]
```

**説明**

プロジェクトに新しい宛先を追加します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt destination`](#dlt-destination) から引数を継承します。

**位置引数**
* `destination_type` - 指定されていない場合は、デフォルトで保存先名が使用されます。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します。
* `--dataset-name DATASET_NAME` - データセットセクションに追加するデータセットの名前。指定されていない場合はデータセットは追加されません。

</details>

## `dlt dbt`

dlt+ dbt 変換ジェネレーター。

**使用方法**
```sh
dlt dbt [-h] {generate} ...
```

**説明**

dlt+ dbt 変換ジェネレーター。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

**利用可能なサブコマンド**
* [`generate`](#dlt-dbt-generate) - dbt プロジェクトを生成します

</details>

### `dlt dbt generate`

dbt プロジェクトを生成します。

**使用方法**
```sh
dlt dbt generate [-h] [--include_dlt_tables] [--fact [FACT]] [--force]
    [--mart_table_prefix [MART_TABLE_PREFIX]] pipeline_name
```

**説明**

dbt プロジェクトを生成します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt dbt`](#dlt-dbt) から引数を継承します。

**位置引数**
* `pipeline_name` - dbt プロジェクトを作成するパイプライン

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--include_dlt_tables` - _dlt テーブルをレンダリングしません
* `--fact [FACT]` - 指定されたテーブルのファクトテーブルを作成します
* `--force` - 既存のファイルを強制的に上書きします
* `--mart_table_prefix [MART_TABLE_PREFIX]` - mart テーブルのプレフィックス

</details>

## `dlt dataset`

dlt+ プロジェクト データセットを管理します。

**使用方法**
```sh
dlt dataset [-h] [--project PROJECT] [--profile PROFILE] [--destination
    DESTINATION] [--schema SCHEMA] [dataset-name]
    {list,info,drop,show,row-counts,head} ...
```

**説明**

プロジェクトのデータセットを管理するためのコマンド。
引数なしで実行すると、現在のプロジェクト内のすべてのデータセットが一覧表示されます。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `dataset-name` - データセット名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル
* `--destination DESTINATION` - 出力先名（複数指定可能な場合）
* `--schema SCHEMA` - マルチスキーマデータセットの場合、名前付きスキーマに制限を設定します

**使用可能なサブコマンド**
* [`list`](#dlt-dataset-list) - データセットを一覧表示します
* [`info`](#dlt-dataset-info) - データセット情報
* [`drop`](#dlt-dataset-drop) - データセットとそれに含まれるすべてのデータを削除します
* [`show`](#dlt-dataset-show) - データセットの内容を表示しますstreamlit の場合
* [`row-counts`](#dlt-dataset-row-counts) - データセット内のすべてのテーブルの行数を表示します
* [`head`](#dlt-dataset-head) - テーブルの最初の x 行を表示します。デフォルトは 5 です

</details>

### `dlt dataset list`

データセットを一覧表示します。

**使用方法**
```sh
dlt dataset [dataset-name] list [-h]
```

**説明**

データセットを一覧表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt dataset info`

データセット情報。

**使用方法**
```sh
dlt dataset [dataset-name] info [-h]
```

**説明**

データセット情報。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt dataset drop`

データセットとそこに含まれるすべてのデータを削除します。

**使用方法**
```sh
dlt dataset [dataset-name] drop [-h]
```

**説明**

データセットとそこに含まれるすべてのデータを削除します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt dataset show`

Streamlit 内のデータセットの内容を表示します。

**使用方法**
```sh
dlt dataset [dataset-name] show [-h]
```

**説明**

Streamlit 内のデータセットの内容を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt dataset row-counts`

データセット内のすべてのテーブルの行数を表示します。

**使用方法**
```sh
dlt dataset [dataset-name] row-counts [-h]
```

**説明**

データセット内のすべてのテーブルの行数を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt dataset head`

テーブルの最初の x 行を表示します。デフォルトは 5 です。

**使用方法**
```sh
dlt dataset [dataset-name] head [-h] [--limit LIMIT] table_name
```

**説明**

テーブルの最初の x 行を表示します。デフォルトは 5 です。

<details>

<summary>引数とオプションを表示</summary>

[`dlt データセット`](#dlt-dataset) から引数を継承します。

**位置引数**
* `table_name` - テーブル名

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--limit LIMIT` - 表示する行数

</details>

## `dlt cache`

dlt+ プロジェクトのローカル データ キャッシュを管理します。実験的。

**使用方法**
```sh
dlt cache [-h] [--project PROJECT] [--profile PROFILE]
    {info,show,drop,populate,flush,create-persistent-secrets,clear-persistent-secrets}
    ...
```

**説明**

dlt+ プロジェクトのローカルデータキャッシュを管理するためのコマンドです。

**これは試験的な機能であり、将来大幅に変更される予定です。**

**本番環境では使用しないでください。**

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します
* `--project PROJECT` - dlt.yml を含む dlt パッケージの名前またはパス
* `--profile PROFILE` - プロジェクト設定ファイルで使用するプロファイル

**利用可能なサブコマンド**
* [`info`](#dlt-cache-info) - キャッシュ情報を表示します
* [`show`](#dlt-cache-show) - キャッシュエンジンに接続します
* [`drop`](#dlt-cache-drop) - キャッシュを削除します
* [`populate`](#dlt-cache-populate) - 定義された入力からキャッシュにデータを入力します
* [`flush`](#dlt-cache-flush) - 定義された出力にキャッシュをフラッシュします
* [`create-persistent-secrets`](#dlt-cache-create-persistent-secrets) - キャッシュに永続シークレットを作成しますリモートアクセス用。
* [`clear-persistent-secrets`](#dlt-cache-clear-persistent-secrets) - リモートアクセス用のキャッシュから永続的なシークレットをクリアします。

</details>

### `dlt cache info`

キャッシュ情報を表示します。

**使用方法**
```sh
dlt cache info [-h]
```

**説明**

キャッシュ情報を表示します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache show`

キャッシュ エンジンに接続します。

**使用方法**
```sh
dlt cache show [-h]
```

**説明**

キャッシュ エンジンに接続します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache drop`

キャッシュを削除します。

**使用方法**
```sh
dlt cache drop [-h]
```

**説明**

キャッシュを削除します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache populate`

定義された入力からキャッシュを作成します。

**使用方法**
```sh
dlt cache populate [-h]
```

**説明**

定義された入力からキャッシュを作成します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache flush`

定義された出力にキャッシュをフラッシュします。

**使用方法**
```sh
dlt cache flush [-h]
```

**説明**

定義された出力にキャッシュをフラッシュします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache create-persistent-secrets`

リモート アクセス用にキャッシュ上に永続的なシークレットを作成します。

**使用方法**
```sh
dlt cache create-persistent-secrets [-h]
```

**説明**

リモート アクセス用にキャッシュ上に永続的なシークレットを作成します。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

### `dlt cache clear-persistent-secrets`

リモート アクセス用のキャッシュから永続的な秘密をクリアします。

**使用方法**
```sh
dlt cache clear-persistent-secrets [-h]
```

**説明**

リモート アクセス用のキャッシュから永続的な秘密をクリアします。

<details>

<summary>引数とオプションを表示</summary>

[`dlt cache`](#dlt-cache) から引数を継承します。

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

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

## `dlt schema`

スキーマを表示、変換、アップグレードします。

**使用方法**
```sh
dlt schema [-h] [--format {json,yaml}] [--remove-defaults] file
```

**説明**

`dlt schema` コマンドは、dlt スキーマ `dlt schema path/to/my_schema_file.yaml` を読み込み、検証して出力します。

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

## `dlt init`

既存の検証済みソースを追加するか、テンプレートから新しいソースを作成して、現在のフォルダーにパイプライン プロジェクトを作成します。

**使用方法**
```sh
dlt init [-h] [--list-sources] [--location LOCATION] [--branch BRANCH] [--eject]
    [source] [destination]
```

**説明**

`dlt init` コマンドは、`source` から `destination` にデータをロードする新しい dlt パイプライン スクリプトを作成します。このコマンドを実行すると、以下の処理が行われます。

1. 現在のフォルダが空の場合、`.dlt/config.toml`、`.dlt/secrets.toml`、`.gitignore` ファイルを追加して、基本的なプロジェクト構造を作成します。
2. `source` 引数が検証済みのソースのいずれかと一致するかどうかを確認し、一致する場合はプロジェクトに追加します。
3. `source` が不明な場合は、汎用テンプレートを使用して開始します。
4. `destination` を使用するようにパイプライン スクリプトを書き換えます。
5. 指定されたソースと宛先のサンプル構成と認証情報を `secrets.toml` と `config.toml` に作成します。
6. ソースと宛先に必要な依存関係を含む `requirements.txt` を作成します。存在する場合は、それに追加する内容の指示を表示します。

このコマンドは同じフォルダ内で複数回使用して、ソース、宛先、パイプラインを追加できます。
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
* `--location LOCATION` - 高度なオプション。検証済みソースリポジトリへの特定の URL またはローカルパスを使用します。
* `--branch BRANCH` - 高度なオプション。検証済みソースリポジトリの特定のブランチを使用してテンプレートを取得します。
* `--eject` - sql_database や rest_api などのコア ソースのソース コードが排出され、編集できるようになります。

</details>

## `dlt render-docs`

cli ドキュメントのマークダウン バージョンをレンダリングします。

**使用方法**
```sh
dlt render-docs [-h] [--compare] file_name
```

**説明**

`dlt render-docs` コマンドは、argparse ヘルプ出力を解析してマークダウン ファイルを生成することで、cli ドキュメントのマークダウン バージョンをレンダリングします。
ドキュメント Web サイトでこれを読んでいる場合は、このコマンドによって生成された cli ドキュメントのレンダリング バージョンを見ていることになります。

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
dlt deploy [-h] pipeline-script-path
```

**説明**

`dlt deploy` コマンドは、パイプラインのデプロイメントを準備し、その実行方法を段階的に説明します。
この機能を有効にするには、まず `pip install "dlt[cli]"` を実行して、現在の環境にパッケージを追加してください。

<details>

<summary>引数とオプションを表示</summary>

[`dlt`](#dlt) から引数を継承します。

**位置引数**
* `pipeline-script-path` - パイプラインスクリプトへのパス

**オプション**
* `-h, --help` - このヘルプメッセージを表示して終了します

</details>

