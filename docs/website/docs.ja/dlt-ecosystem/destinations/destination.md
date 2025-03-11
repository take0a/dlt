---
title: Custom destination
description: Custom `dlt` destination function for reverse ETL
keywords: [reverse etl, sink, function, decorator, destination, custom destination]
---

# カスタム宛先: リバース ETL

`dlt` 宛先デコレータを使用すると、パイプラインを通過するすべてのデータを単純な関数で受信できます。これは、データを API にプッシュバックするリバース ETL に非常に役立ちます。

また、`dlt` でまだサポートされていないキューまたは単純なデータベースの宛先にデータを送信する場合にもこれを使用できますが、この場合は独自の移行を手動で処理する必要があることに注意してください。

また、正規化されたデータのファイルへのパスを簡単に取得することもできます。したがって、parquet ファイルまたは jsonl ファイルに直接アクセスしてどこかにコピーしたり、データベースにプッシュしたりする必要がある場合は、ここでもこれを行うことができます。

## リバース ETL 用の `dlt` をインストールする

追加の依存関係なしで`dlt`をインストールするには:

```sh
pip install dlt
```

## パイプラインの宛先関数を設定する

カスタム宛先デコレータは、接続資格情報を提供する必要がなく、パイプラインの実行またはロード操作中にロードされるすべての項目に対して呼び出される関数を提供するという点で他の宛先とは異なります。`@dlt.destination` を使用すると、2 つの引数を取る任意の関数を `dlt` 宛先に変換できます。

アイテムのリストを宛先関数にプッシュする非常に単純な dlt パイプラインは次のようになります:

```py
import dlt
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema

@dlt.destination(batch_size=10)
def my_destination(items: TDataItems, table: TTableSchema) -> None:
    print(table["name"])
    print(items)

pipeline = dlt.pipeline("custom_destination_pipeline", destination=my_destination)
pipeline.run([1, 2, 3], table_name="items")
```

:::tip
1. この例から型指定情報 (`TDataItems` および `TTableSchema`) を削除することもできます。ただし、型指定は一般に、入力オブジェクトの形状を知るのに役立ちます。
2. 以下に説明するように、パイプラインのカスタム宛先関数を宣言する方法は他にもいくつかあります。
:::

### `@dlt.destination`、カスタム宛先関数、および署名

宛先デコレータの完全なシグネチャとその機能は次のとおりです:

```py
@dlt.destination(
    batch_size=10,
    loader_file_format="jsonl",
    name="my_custom_destination",
    naming_convention="direct",
    max_table_nesting=0,
    skip_dlt_columns_and_tables=True,
    max_parallel_load_jobs=5,
    loader_parallelism_strategy="table-sequential",
)
def my_destination(items: TDataItems, table: TTableSchema) -> None:
    ...
```

### デコレータ引数

* 宛先デコレータの `batch_size` パラメータは、関数呼び出しごとにいくつの項目がバッチ処理され、配列として送信されるかを定義します。バッチ サイズを `0` に設定すると、実際のデータ項目を渡す代わりに、ファイルのパスを項目引数として指定した読み込みジョブごとに 1 回の呼び出しを受け取ります。その後、そのファイルを任意の方法で開いて処理できます。
* 宛先デコレータの `loader_file_format` パラメータは、宛先関数に送信される前にロード パッケージに保存されるファイルの形式を定義します。これは `jsonl` または `parquet` になります。
* 宛先デコレータの `name` パラメータは、宛先デコレータによって作成される宛先の名前を定義します。
* 宛先デコレータの `naming_convention` パラメータは、宛先デコレータによって作成される宛先の名前を定義します。これは、テーブル名と列名がどのように正規化されるかを制御します。デフォルトは `direct` で、すべての名前が同じままになります。
* 宛先デコレータの `max_nesting_level` パラメータは、正規化ツールがデータ内のネストされたフィールドを正規化してサブテーブルを作成する深さを定義します。これにより、`source` の設定が上書きされ、デフォルトではネストされたテーブルを作成しないように 0 に設定されます。
* 宛先デコレータの `skip_dlt_columns_and_tables` パラメータは、内部テーブルと列がカスタム宛先関数に供給されるかどうかを定義します。デフォルトでは、これは `True` に設定されています。
* `max_parallel_load_jobs` パラメータは、スレッド内で並列に実行されるロードジョブの数を定義します。一度に 5 つの接続のみを許可する宛先がある場合は、この値を 5 などに設定できます。
* `loader_parallelism_strategy` パラメータは、ロード ジョブの並列化方法を制御します。デフォルトの `parallel` に設定すると、どのテーブルにロードされるかに関係なく、ジョブは並列化されます。`table-sequential` はロードを並列化しますが、一度に 1 つのテーブルにつき 1 つのロード ジョブのみを実行します。`sequential` は、すべてのロード ジョブをメイン スレッドで順番に実行します。

:::note
上記の設定により、宛先関数で受信するデータの形状が、データソースに表示されるものと可能な限り近くなります。

* カスタム宛先では、デフォルトで `max_nesting_level` が 0 に設定されるため、正規化フェーズ中にサブテーブルは生成されません。
* カスタム宛先では、デフォルトですべての内部テーブルと列もスキップされます。これらが必要な場合は、`skip_dlt_columns_and_tables` を False に設定します。
:::

### カスタム宛先関数

* カスタム宛先関数の `items` パラメータには、宛先関数に送信される項目が含まれます。
* `table` パラメータには、すべてのテーブルヒントと列を含む、現在の呼び出しが属するスキーマ テーブルが含まれます。たとえば、テーブル名には `table["name"]` でアクセスできます。
* 関数の引数に設定値とシークレットを追加することもできます。以下を参照してください。

## 宛先関数に設定、資格情報、その他の秘密情報を追加する

宛先デコレータは設定とシークレット変数をサポートします。たとえば、APIシークレットまたはログインを必要とするサービスに接続する場合は、次のようにします:

```py
@dlt.destination(batch_size=10, loader_file_format="jsonl", name="my_destination")
def my_destination(items: TDataItems, table: TTableSchema, api_key: str = dlt.secrets.value) -> None:
    ...
```

次に、`.dlt/secrets.toml` に次のように設定変数を設定します:

```toml
[destination.my_destination]
api_key="<my-api-key>"
```

カスタム宛先は、[通常の名前付き宛先](../../general-usage/destination.md#configure-a-destination)と同じ構成ルールに従います。

## `dlt` パイプラインでカスタム宛先を使用する

カスタム宛先関数を`dlt`パイプラインに渡す方法は複数あります:

- 宛先関数を直接参照する

  ```py
  @dlt.destination(batch_size=10)
  def local_destination_func(items: TDataItems, table: TTableSchema) -> None:
      ...

  # Reference function directly
  p = dlt.pipeline("my_pipe", destination=local_destination_func)
  ```

  [通常の宛先](../../general-usage/destination.md#pass-explicit-credentials)と同様に、宛先関数に構成と資格情報を明示的に渡すことができます。
  
  ```py
  @dlt.destination(batch_size=10, loader_file_format="jsonl", name="my_destination")
  def my_destination(items: TDataItems, table: TTableSchema, api_key: str = dlt.secrets.value) -> None:
      ...

  p = dlt.pipeline("my_pipe", destination=my_destination(api_key=os.getenv("API_KEY"))) # type: ignore[call-arg]
  ```

- 宛先への参照を介して直接。この場合、宛先関数のデコレータを使用しないでください。

  ```py
  # File my_destination.py

  from dlt.common.destination import Destination

  # Don't use the decorator
  def local_destination_func(items: TDataItems, table: TTableSchema) -> None:
      ...

  # Via destination reference
  p = dlt.pipeline(
      "my_pipe",
      destination=Destination.from_reference(
          "destination", destination_callable=local_destination_func
      )
  )
  ```

- 関数の場所への完全修飾文字列経由 (これは `config.toml` または環境変数を通じて設定できます)。宛先関数は別のファイルに配置する必要があります。

  ```py
  # File my_pipeline.py

  from dlt.common.destination import Destination

  # Fully qualified string to function location
  p = dlt.pipeline(
      "my_pipe",
      destination=Destination.from_reference(
          "destination", destination_callable="my_destination.local_destination_func"
      )
  )
  ```

## アトミックロードのバッチサイズと再試行ポリシーを調整する

宛先には、処理された `DataItems` の数のローカル レコードが保持されるため、たとえば、カスタム宛先を使用して `DataItems` をリモート API にプッシュし、ロード中にこの API が使用できなくなり、`dlt` パイプラインの実行が失敗した場合、後でパイプラインの実行を繰り返すことができ、カスタム宛先は **失敗したバッチ全体から再開します**。データが失われないようにしていますが、たとえばバッチの半分をデータベースにコミットしてから失敗した場合は、データが重複する可能性があります。
**バッチのアトミック性を維持するのはあなたの責任です**。このため、1 つのトランザクション (1 つの API 要求または 1 つのデータベース トランザクションなど) で処理できるバッチ サイズを選択するのが合理的です。そうすれば、この要求またはトランザクションが繰り返し失敗した場合でも、重複したデータをリモート ロケーションにプッシュせずに、次回の実行時に繰り返すことができます。トランザクションがなく、重複したデータを許容しないシステムの場合は、サイズ 1 のバッチを使用できます。

例外を発生させる宛先関数は、中止する前に 5 回再試行されます (`load.raise_on_max_retries` 構成オプション)。パイプラインを再度実行すると、新しいデータを抽出する前にロードが再開されます。

例外が `DestinationTerminalException` から派生していた場合、ロードジョブ全体が失敗としてマークされ、再試行されません。

:::caution
パイプラインフォルダー (ジョブファイルと宛先の状態が保存される場所) を消去すると、最後に失敗したバッチから再開できなくなります。
ただし、パイプライン ディレクトリのバックアップと復元は非常に簡単です。[詳細は以下を参照](#manage-pipeline-state-for-incremental-loading)。
:::

## ロードの並列処理を増減する

デフォルトでは、宛先関数の呼び出しは複数のスレッドで実行されるため、宛先関数の外部からスレッドセーフでない非ローカル変数またはグローバル変数を使用していないことを確認する必要があります。すべての呼び出しを同じスレッドから実行する必要がある場合は、`workers` [ロード ステップの構成変数](../../reference/performance.md#load) を 1 に設定できます。

:::tip
パフォーマンス上の理由から、マルチスレッドアプローチを維持し、たとえば、リモートデータベースまたはキューへのスレッドセーフな接続プールを使用することをお勧めします。
:::

## 書き込み処理

`@dlt.destination` は、パイプラインの実行中に検出されたすべての正規化された `DataItems` をカスタム宛先関数に転送するため、「書き込み処理」という概念はありません。

## ステージングサポート

現時点では、`@dlt.destination` は呼び出される前にリモートの場所にあるファイルのステージングをサポートしていません。この機能が必要な場合は、お知らせください。

## インクリメンタルローディングのパイプラインの状態を管理する

カスタム宛先には、パイプラインの状態を復元するための一般的なメカニズムがありません。これは、保持されている状態に依存するデータソース (つまり、すべてのインクリメンタルなリソース) に影響します。
パイプライン ディレクトリを消去すると (つまり、フォルダーを削除するか、クリーンなランナーを取得する AWS Lambda または GitHub Actions で実行すると)、インクリメンタルローディングの進行状況が失われます。次回の実行時に、データを最初から再取得します。

プラグ可能な状態ストレージに取り組んでいるなら、上記の問題は次のように修正できます:

1. パイプライン ディレクトリを消去しない。たとえば、EC インスタンスでパイプラインを定期的に実行すると、状態は保持されます。
2. パイプライン ディレクトリの実行前/実行後に、そのディレクトリの復元/バックアップを実行します。これは思ったよりずっと簡単です。[再利用できるスクリプトはこちら](https://gist.github.com/rudolfix/ee6e16d8671f26ac4b9ffc915ad24b6e)。

## 次は？

* [カスタム BigQuery 宛先](../../examples/custom_destination_bigquery/) の例をご覧ください。
* カスタム宛先の構築についてサポートが必要ですか? [Slack コミュニティ](https://dlthub.com/community) のテクニカル サポート チャネルで質問してください。
