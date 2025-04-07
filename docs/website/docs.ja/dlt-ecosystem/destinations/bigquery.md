---
title: Google BigQuery
description: Google BigQuery `dlt` destination
keywords: [bigquery, destination, data warehouse]
---

# Google BigQuery

## BigQuery で dlt をインストールする

**BigQuery の依存関係を持つ dlt ライブラリをインストールするには:**

```sh
pip install "dlt[bigquery]"
```

## セットアップガイド

**1. 以下を実行して、BigQuery にロードするパイプラインでプロジェクトを初期化します:**

```sh
dlt init chess bigquery
```

**2. BigQueryに必要な依存関係をインストールするには、以下を実行します:**

```sh
pip install -r requirements.txt
```

これにより、BigQuery クライアントに必要なすべての依存関係が含まれる `bigquery` などとともに dlt がインストールされます。

**3. Google Cloud アカウントにログインまたは作成する**

Web ブラウザで [Google Cloud Platform](https://console.cloud.google.com/) にサインアップまたはログインします。

**4. 新しい Google Cloud プロジェクトを作成する**

[Google Cloud コンソールのウェルカム ページ](https://console.cloud.google.com/welcome) にアクセスしたら、左上にあるプロジェクトセレクターをクリックし、`新しいプロジェクト` ボタンをクリックし、最後にプロジェクトに任意の名前を付けて `作成` ボタンをクリックします。

**5. サービスアカウントを作成し、BigQuery 権限を付与する**

次に、[サービス アカウントを作成](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating)する必要があります。リンクされたドキュメント ページで `サービス アカウントの作成に移動` ボタンをクリックした後、作成したプロジェクトを選択し、サービス アカウントに任意の名前を付けます。

`続行`ボタンをクリックして次のロールを付与し、`dlt` がスキーマを作成してデータをロードできるようにします。:

- *BigQuery Data Editor*
- *BigQuery Job User*
- *BigQuery Read Session User*

現時点ではユーザーにこのサービス アカウントへのアクセスを許可する必要はないので、`完了`ボタンをクリックします。

**6. サービスアカウントJSONをダウンロードする**

上記の手順に従って`完了`をクリックした後にリダイレクトされるサービスアカウントテーブルページで、作成したサービスアカウントの`アクション`列の下の 3 つのドットを選択し、`キーの管理`を選択します。

これにより、`キーの追加` ボタン、`新しいキーの作成` ボタン、最後に `作成` ボタンをクリックできるページが表示されます。`JSON` オプションは事前に選択されています。

サービス アカウントの秘密キーを含む `JSON` ファイルがダウンロードされます。

**7. サービス アカウント情報を使用して `dlt` 認証情報ファイルを更新します。**

`dlt` 認証情報ファイルを開く:

```sh
open .dlt/secrets.toml
```

`project_id`、`private_key`、`client_email` を、ダウンロードした `JSON` ファイルの値に置き換えます:

```toml
[destination.bigquery]
location = "US"

[destination.bigquery.credentials]
project_id = "project_id" # please set me up!
private_key = "private_key" # please set me up!
client_email = "client_email" # please set me up!
```

データの場所を指定できます。つまり、デフォルトの `US` ではなく `EU` を指定できます。

### OAuth 2.0 認証

OAuth 2.0認証を使用できます。適切なスコープで**リフレッシュトークン**を生成する必要があります（詳細についてはGPT-4アシスタントに問い合わせることをお勧めします）。次に、`secrets.toml` に次の情報を入力できます:

```toml
[destination.bigquery]
location = "US"

[destination.bigquery.credentials]
project_id="project_id"  # please set me up!
client_id = "client_id"  # please set me up!
client_secret = "client_secret"  # please set me up!
refresh_token = "refresh_token"  # please set me up!
```

### デフォルトの資格情報の使用

Google は、`GOOGLE_APPLICATION_CREDENTIALS` 環境変数やメタデータ サービスなど、デフォルトの認証情報を取得する方法をいくつか提供しています。GCP で利用可能な VM (クラウド ファンクション、Composer ランナー、Colab ノートブック) には、関連付けられたサービス アカウントまたは認証済みユーザーがあります。シークレットに何も明示的に指定されていない場合、`dlt` はデフォルトの認証情報を使用しようとします。

```toml
[destination.bigquery]
location = "US"
```

### 異なる `project_id` を使用する

アカウントがアクセスできる場合は、構成内の `project_id` を資格情報内のものと異なる値に設定できます:

```toml
[destination.bigquery]
project_id = "project_id_destination"

[destination.bigquery.credentials]
project_id = "project_id_credentials"
```

このシナリオでは、`project_id_credentials` が認証に使用され、`project_id_destination` がデータの送信先として使用されます。

## 書き込み処理

すべての書き込み処理がサポートされています。

[`replace` 戦略](../../general-usage/full-loading.md) を `staging-optimized` に設定すると、宛先テーブルが削除され、ステージング テーブルから [clone コマンド](https://cloud.google.com/bigquery/docs/table-clones-create) を使用して再作成されます。

## データのロード

`dlt` は、ローカル ファイル システムまたは GCS バケットからファイルを送信する `BigQuery` ロード ジョブを使用します。
ローダーは、ジョブを再試行および終了するときに [Google の推奨事項](https://cloud.google.com/bigquery/docs/error-messages) に従います。
Google BigQuery クライアントは、クエリとファイルのアップロードに対して精巧な再試行メカニズムとタイムアウトを実装しており、これらは宛先オプションで設定できます。

BigQuery の宛先では、[ストリーミング挿入](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery) もサポートされています。このモードでは、小規模なバッチ (<500 レコード) でパフォーマンスが向上しますが、データがバッファリングされるため、更新/削除操作ができなくなります。このため、ストリーミング挿入は `write_disposition="append"` でのみ使用でき、挿入されたデータは最大 90 分間編集がブロックされます (ただし、読み取りはすぐに使用できます)。[詳細はこちら](https://cloud.google.com/bigquery/quotas#streaming_inserts)。

リソースをストリーミング挿入モードに切り替えるには、ヒントを使用します:

```py
@dlt.resource(write_disposition="append")
def streamed_resource():
    yield {"field1": 1, "field2": 2}

streamed_resource.apply_hints(additional_table_hints={"x-insert-api": "streaming"})
```

### ネストされたフィールドに BigQuery スキーマの自動検出を使用する

BigQuery にスキーマを推測させて、`dlt` の代わりに宛先テーブルを作成させることができます。その結果、`dlt` が現時点でサポートしていないネストされたフィールド (つまり、`RECORD`) (JSON として保存されます) が作成されることがあります。[BigQuery アダプタ](#bigquery-adapter) を使用して特定のリソースを選択することも、次の構成オプションを使用してすべてのリソースを選択することもできます:

```toml
[destination.bigquery]
autodetect_schema=true
```

リソースから [Arrow テーブル](../verified-sources/arrow-pandas.md) を生成し、Parquet ファイル形式を使用してデータをロードすることをお勧めします。その場合、`dlt` と BigQuery によって生成されるスキーマは同一になります。BigQuery は、生成された parquet ファイルの列の順序も保持します。[pyarrow または duckdb](../verified-sources/arrow-pandas.md#loading-json-documents) を使用して、JSON データを Arrow テーブルに変換できます。

```py
import pyarrow.json as paj

import dlt
from dlt.destinations.adapters import bigquery_adapter

@dlt.resource(name="cve")
def load_cve():
  with open("cve.json", 'rb') as f:
    # autodetect arrow schema and yield arrow table
    yield paj.read_json(f)

pipeline = dlt.pipeline("load_json_struct", destination="bigquery")
pipeline.run(
  bigquery_adapter(load_cve(), autodetect_schema=True)
)
```

上記では、`pyarrow` ライブラリを使用して JSON ドキュメントを Arrow テーブルに変換し、`bigquery_adapter` を使用して **cve** リソースのスキーマの自動検出を有効にしています。

Python 辞書/リストを生成し、それを JSONL としてロードすることもできます。多くの場合、結果として得られるネストされた構造は、pyarrow/duckdb や parquet で取得されたものよりも単純です。ただし、`dlt` からの推論された型には若干の違いがあります (BigQuery は型をより積極的に強制します)。また、BigQuery は、JSON 内のフィールドの順序に関連して列の順序を保持しようとしません。

```py
import dlt
from dlt.destinations.adapters import bigquery_adapter

@dlt.resource(name="cve", max_table_nesting=1)
def load_cve():
  with open("cve.json", 'rb') as f:
    yield json.load(f)

pipeline = dlt.pipeline("load_json_struct", destination="bigquery")
pipeline.run(
  bigquery_adapter(load_cve(), autodetect_schema=True)
)
```

以下の例では、JSON データをネスト レベル 1 までのテーブルとして表します。このネスト レベルより上では、BigQuery によってネストされたフィールドが作成されます。

:::caution
データを Python オブジェクト (辞書) として生成し、このデータを Parquet としてロードすると、ネストされたフィールドは文字列に変換されます。これは、`dlt` がネストされたフィールドを推測できないことの結果の 1 つです。
:::

## サポートされているファイル形式

BigQueryにデータをロードするには、次のファイル形式を設定できます:

* [JSONL](../file-formats/jsonl.md) は、デフォルトです。
* [Parquet](../file-formats/parquet.md) は、サポートされています。

ステージングが有効になっている場合:

* [JSONL](../file-formats/jsonl.md) は、デフォルトです。
* [Parquet](../file-formats/parquet.md) は、サポートされています。

:::caution
**BigQuery は Parquet ファイルから JSON 列を読み込むことができません**. `dlt` では、そのようなジョブは永久に失敗します。代わりに:
* JSON を適切に読み込んで解析するには、JSONL に切り替えます。
* スキーマを使用する [自動検出とネストされたフィールド](#use-bigquery-schema-autodetect-for-nested-fields)
:::

## サポートされている列のヒント

BigQuery は次の[列ヒント](../../general-usage/schema#tables-and-columns)をサポートしています:

* `partition` - 装飾された列に日単位の粒度でパーティションを作成します (`PARTITION BY DATE`)。
`datetime`、`date`、および `bigint` データ型で使用できます。
テーブルごとに 1 つの列のみがサポートされ、新しいテーブルが作成される場合にのみサポートされます。
BigQuery のパーティション分割の詳細については、[公式ドキュメント](https://cloud.google.com/bigquery/docs/partitioned-tables) をご覧ください。

  > ❗ `bigint` は BigQuery の **INT64** データ型にマップされます。
  > 自動パーティション分割では、INT64 列を UNIX タイムスタンプに変換する必要がありますが、これは `GENERATE_ARRAY` ではネイティブにサポートされていません。
  > パーティションの制限が 10,000 個あるため、INT64 の範囲全体をカバーすることはありません。
  > 代わりに、毎日のパーティショニングを可能にするために 86,400 秒の境界を設定しました。
  > これは典型的な値を取得しますが、極端に大きい/小さい外れ値は `__UNPARTITIONED__` キャッチオールパーティションに送られます。

* `cluster` - クラスター列を作成します。テーブルごとに複数の列がサポートされており、新しいテーブルが作成される場合のみです。

### テーブルと列の識別子

BigQuery はデフォルトで大文字と小文字を区別する識別子を使用しており、`dlt` もこれを前提としています。使用するデータセットに大文字と小文字を区別しない識別子がある場合 (データセットの作成時にそのようなオプションがあります)、大文字と小文字を区別しない [命名規則](../../general-usage/naming-convention.md#case-sensitive-and-insensitive-destinations) を使用するか、識別子の衝突が適切に検出されるように `dlt` にその旨を伝えるようにしてください。

```toml
[destination.bigquery]
has_case_sensitive_identifiers=false
```

`dlt` に、新しく作成されたデータセットの大文字と小文字の区別を設定させるオプションがあります。その場合、現在の命名規則の大文字と小文字の区別に従います (つまり、デフォルトの **snake_case** は、大文字と小文字を区別しない識別子を持つデータセットを作成します)。

```toml
[destination.bigquery]
should_set_case_sensitivity_on_new_dataset=true
```

上記のオプションはデフォルトではオフになっています。

## ステージングサポート

BigQuery は、ファイルのステージング先として GCS をサポートしています。`dlt` は parquet 形式のファイルを GCS にアップロードし、BigQuery にそのデータを直接データベースにコピーするよう要求します。bucket_url と認証情報を使用して GCS バケットを設定する方法については、[Google Storage ファイルシステムのドキュメント](./filesystem.md#google-storage) を参照してください。GCS と Redshift デプロイメントに同じサービス アカウントを使用する場合、BigQuery がバケットから読み取ることができるように追加の認証を提供する必要はありません。

parquet ファイルの代わりに、ステージング ファイル形式として jsonl を指定することもできます。そのためには、パイプラインの `run` コマンドの `loader_file_format` 引数を `jsonl` に設定します。

### BigQuery/GCS ステージングの例

```py
# Create a dlt pipeline that will load
# chess player data to the BigQuery destination
# via a GCS bucket.
pipeline = dlt.pipeline(
    pipeline_name='chess_pipeline',
    destination='bigquery',
    staging='filesystem', # Add this to activate the staging location.
    dataset_name='player_data'
)
```

## 追加の宛先オプション

以下のようにデータの場所とさまざまなタイムアウトを設定できます。この情報は秘密ではないので、`config.toml`にも配置できます:

```toml
[destination.bigquery]
location="US"
http_timeout=15.0
file_upload_timeout=1800.0
retry_deadline=60.0
```

* `location` は [BigQuery データの場所](https://cloud.google.com/bigquery/docs/locations) を設定します (デフォルト: **US**)
* `http_timeout` は、BigQuery API に接続して応答を取得する際のタイムアウトを設定します (デフォルト: **15 秒**)
* `file_upload_timeout` は、ローカルファイルをロードする際のファイルアップロードのタイムアウトです。アップロードの合計時間は、この値を超えてはなりません (デフォルト: **30 分**、秒単位で設定)
* `retry_deadline` is a deadline for a [DEFAULT_RETRY used by Google](https://cloud.google.com/python/docs/reference/storage/1.39.0/retry_timeout)
* `ignore_unknown_values` is a configuration option that allows BigQuery to ignore rows with unknown or unexpected values during data loading. When enabled, rows containing fields that are not defined in the schema will be skipped instead of causing the entire load job to fail. This can be useful when dealing with inconsistent or evolving data sources.

### dbt サポート

この宛先は、[dbt-bigquery](https://github.com/dbt-labs/dbt-bigquery) を介して [dbt と統合](../transformations/dbt/dbt.md) します。
認証情報は、明示的に定義されている場合、**場所**、再試行、タイムアウトなどの他の設定とともに `dbt` と共有されます。
暗黙的な認証情報 (つまり、クラウド関数で使用可能) の場合、`dlt` は `project_id` を共有し、認証情報の取得を `dbt` アダプターに委任します。

### dlt の状態の同期

この宛先は、[dlt state sync](../../general-usage/state#syncing-state-with-destination)を完全にサポートします。

## BigQuery アダプタ

`bigquery_adapter` を使用すると、BigQuery 固有のヒントをリソースに追加できます。
これらのヒントは、パーティション分割、クラスタリング、数値列の丸めモードの指定など、BigQuery テーブルへのデータのロード方法に影響します。
ヒントは、列レベルとテーブルレベルの両方で定義できます。

アダプターは、宛先列とテーブル DDL オプションに関するメタデータを使用して DltResource を更新します。

### アダプタを使用してリソースにヒントを適用する

ここでは、`bigquery_adapter` メソッドを使用して、列レベルとテーブルレベルの両方でリソースにヒントを適用する方法の例を示します:

```py

import dlt
from dlt.destinations.adapters import bigquery_adapter


@dlt.resource(
    columns=[
        {"name": "event_date", "data_type": "date"},
        {"name": "user_id", "data_type": "bigint"},
        # Other columns.
    ]
)
def event_data():
    yield from [
        {"event_date": datetime.date.today() + datetime.timedelta(days=i)} for i in range(100)
    ]


# Apply column options.
bigquery_adapter(
    event_data, partition="event_date", cluster=["event_date", "user_id"]
)

# Apply table level options.
bigquery_adapter(event_data, table_description="Dummy event data.")

# Load data in "streaming insert" mode (only available with
# write_disposition="append").
bigquery_adapter(event_data, insert_api="streaming")
```

上記の例では、アダプタは、テーブルの作成時に、パーティション分割に `event_date` を使用し、クラスタリングに `event_date` と `user_id` の両方を (指定された順序で) 使用するように指定しています。

アダプタの動作に関する注意点:

- パーティション分割できるのは1つの列のみです（[サポートされているヒント](#supported-column-hints)を参照）。
- 必要な数の列をクラスター化できます。
- 同じリソースに対する連続的なアダプタ呼び出しは、OR 演算に似たパラメータを蓄積し、統一された実行を実現します。

:::caution
執筆時点では、`ALTER` 操作ではテーブルレベルのオプションはサポートされていません。

`bigquery_adapter` はリソースを *その場で* 更新しますが、便宜上リソースを返すことに注意してください。つまり、次の両方とも有効です:

```py
bigquery_adapter(my_resource, partition="partition_column_name")
my_resource = bigquery_adapter(my_resource, partition="partition_column_name")
```

詳細については、[完全な API 仕様](../../api_reference/destinations/impl/bigquery/bigquery_adapter)を参照してください。
:::

<!--@@@DLT_TUBA bigquery-->

