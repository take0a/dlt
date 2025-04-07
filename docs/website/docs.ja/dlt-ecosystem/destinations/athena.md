---
title: AWS Athena / Glue Catalog
description: AWS Athena `dlt` destination
keywords: [aws, athena, glue catalog]
---

# AWS Athena / Glue Catalog

Athena の宛先は、データを Parquet ファイルとして S3 バケットに保存し、[AWS Athena の外部テーブル](https://docs.aws.amazon.com/athena/latest/ug/creating-tables.html) を作成します。その後、Athena SQL コマンドを使用してこれらのテーブルをクエリできます。このコマンドは、Parquet ファイルのフォルダー全体をスキャンして結果を返します。この宛先は、マージ書き込み処理が現時点ではサポートされていないことを除いて、他の SQL ベースの宛先と非常によく似た動作をします。`dlt` メタデータは、Parquet ファイルと同じバケットに保存されますが、Iceberg テーブルとして保存されます。Athena は、個々のデータ テーブルを Iceberg テーブルとして書き込むこともサポートしているため、後で操作できます。一般的な使用例は、それらから GDPR データを削除することです。

## Athena で dlt をインストールする

**Athena 依存関係を持つ dlt ライブラリをインストールするには:**

```sh
pip install "dlt[athena]"
```

## セットアップガイド

### 1. dlt プロジェクトを初期化する

まず、新しい `dlt` プロジェクトを次のように初期化します:

   ```sh
   dlt init chess athena
   ```

   > 💡 このコマンドは、ファイルシステムのステージング先を使用して、チェスをソースとして、AWS Athena を宛先としてパイプラインを初期化します。


### 2. バケットストレージと Athena 認証情報を設定する

まず、依存関係をインストールします:

```sh
pip install -r requirements.txt
```

または、`pip install "dlt[athena]"` を使用すると、`s3fs`、`pyarrow`、`pyathena`、および `botocore` パッケージがインストールされます。

:::caution

依存関係を個別にインストールすることもできます。

```sh
pip install dlt
pip install s3fs
pip install pyarrow
pip install pyathena
```
そうすると、pip はバックトラックで失敗しません。
:::

シークレット情報を含む `dlt` 認証情報ファイルを編集するには、`.dlt/secrets.toml` を開きます。アップロードされた parquet ファイルを保持する `bucket_url`、Athena がクエリ結果を書き込むために使用する `query_result_bucket`、およびこれら 2 つのバケットへの書き込みおよび読み取りアクセス権と、完全な Athena アクセス AWS ロールを持つ認証情報を提供する必要があります。

TOMLファイルは次のようになります:

```toml
[destination.filesystem]
bucket_url = "s3://[your_bucket_name]" # replace with your bucket name,

[destination.filesystem.credentials]
aws_access_key_id = "please set me up!" # copy the access key here
aws_secret_access_key = "please set me up!" # copy the secret access key here

[destination.athena]
query_result_bucket="s3://[results_bucket_name]" # replace with your query results bucket name

[destination.athena.credentials]
aws_access_key_id="please set me up!" # same as credentials for filesystem
aws_secret_access_key="please set me up!" # same as credentials for filesystem
region_name="please set me up!" # set your AWS region, for example "eu-central-1" for Frankfurt
```

認証情報が `~/.aws/credentials` に保存されている場合は、上記の **[destination.filesystem.credentials]** および **[destination.athena.credentials]** セクションを削除するだけで、`dlt` はローカル認証情報の **default** プロファイルに戻ります。プロファイルを切り替える場合は、次のようにプロファイル名を渡します (ここでは `dlt-ci-user`):

```toml
[destination.filesystem.credentials]
profile_name="dlt-ci-user"

[destination.athena.credentials]
profile_name="dlt-ci-user"
```

## 追加の宛先設定

Athenaワークグループは次のように提供できます。:

```toml
[destination.athena]
athena_work_group="my_workgroup"
```

You can force all tables to be in iceberg format:
```toml
[destination.athena]
force_iceberg = true
`

## 書き込み処理

`athena` 宛先は書き込み処理を次のように処理します。:

- `append` - このようなテーブルに属するファイルはデータセット フォルダーに追加されます。
- `replace` - そのようなテーブルに属するすべてのファイルはデータセット フォルダーから削除され、現在のファイル セットが追加されます。
- `merge` - `append` にフォールバックします ([iceberg](#iceberg-data-tables) テーブルを使用している場合を除きます)。

## データのロード

データのロードは、S3 バケットに parquet ファイルを保存し、Athena でスキーマを定義することによって行われます。Athena で SQL クエリを使用してデータをクエリする場合、返されるデータはバケットをスキャンし、そこに含まれる関連するすべての parquet ファイルを読み取ることによって読み取られます。

`dlt` 内部テーブルは Iceberg テーブルとして保存されます。

### データ型

Athena テーブルはタイムスタンプをミリ秒の精度で保存し、その精度で parquet ファイルを生成します。Iceberg テーブルの精度はマイクロ秒であることに留意してください。

Athena は JSON フィールドをサポートしていないため、JSON は文字列として保存されます。

:::caution
**Athena は parquet ファイルの TIME 列をサポートしていません**. `dlt` では、このようなジョブは永久に失敗します。`datetime.time` オブジェクトを `str` または `datetime.datetime` に変換してロードしてください。
:::

### テーブルと列の識別子

Athena は大文字と小文字を区別しない識別子を使用し、INFORMATION SCHEMA に保存される **すべての識別子を小文字にします**。[大文字と小文字を区別する命名規則](../../general-usage/naming-convention.md#case-sensitive-and-insensitive-destinations) は使用しないでください。いずれにしても大文字と小文字は削除され、識別子の衝突が発生するリスクがあります。これは `dlt` によって検出され、ロード プロセスが失敗します。

内部的には、Athena は DDL (カタログ) と DML/クエリに異なる SQL エンジンを使用します:

* DDL は HIVE エスケープを使用します ``````
* その他のクエリでは、PRESTO と通常の SQL エスケープが使用されます。

## ステージングサポート

Athena 宛先を使用する場合は、ステージング宛先の使用が必須です。ステージングを `filesystem` に設定しない場合は、`dlt` が自動的にこれを実行します。

[ファイル名レイアウト](./filesystem#data-loading)をデフォルト値から変更する場合は、Athenaが確実にテーブルを構築できるように、次の点に注意してください:

 - `{table_name}` プレースホルダーを指定する必要があり、このプレースホルダーの後にはスラッシュを続ける必要があります。
 - `{file_id}` プレースホルダーを指定する必要があり、これは `{table_name}` プレースホルダーの後のどこかに配置する必要があります。
 - `{table_name}` はレイアウトの最初のプレースホルダーである必要があります。

## 追加の宛先オプション

### Iceberg データテーブル

テーブルをアイスバーグテーブルとして Athena に保存できます。これにより、たとえば、後で必要に応じてデータを削除できるようになります。リソースをアイスバーグテーブル形式に切り替えるには、次のように table_format 引数を指定します:

```py
@dlt.resource(table_format="iceberg")
def data() -> Iterable[TDataItem]:
    ...
```

Iceberg テーブルとして作成されたすべてのテーブルについて、Athena 宛先は、ファイルシステムと Athena グルー カタログの両方のステージング データセットに通常の Athena テーブルを作成し、ファイルシステムとグルー カタログの両方の同じデータセット内の非 Iceberg テーブルとともに存在する最終的な Iceberg テーブルにすべてのデータをコピーします。Iceberg テーブルから通常のテーブルへの切り替え、またはその逆の切り替えはサポートされていません。

See [athena adapter](#athena-adapter) for partitioning and other options.

You can also force all tables to be in iceberg format:
```toml
[destination.athena]
force_iceberg = true
```

#### `merge` サポート

Iceberg テーブルを使用する場合、Athena では `merge` 書き込み処理がサポートされます。

:::note
1. Athena はトランザクションをサポートしておらず、`dlt` は複数の DELETE/UPDATE/INSERT ステートメントを使用して `merge` を実装するため、パイプラインの実行が途中で失敗した場合にテーブルが不整合な状態になるリスクがあります。
2. `dlt` は、Athena の一時テーブル不足を回避するために、ステージング スキーマに `insert_<table name>` および `delete_<table name>` と呼ばれる追加のヘルパー テーブルを作成します。
:::

### dbt サポート

Athena は `dbt-athena-community` を介してサポートされます。認証情報は、生成された dbt プロファイルの `aws_access_key_id` と `aws_secret_access_key` に渡されます。Iceberg テーブルはサポートされていますが、ソース テーブルが Iceberg の場合は、モデルを Iceberg テーブルとしてマテリアライズする必要があります。Iceberg (ナノ秒) と通常の Athena テーブル (ミリ秒) の精度が異なるため、日時列のマテリアライズで問題が発生しました。
Athena アダプタでは、以下の Athena 設定で **region_name** を設定する必要があります。また、テーブル カタログ名を設定して、デフォルトを変更することもできます: **awsdatacatalog**

```toml
[destination.athena]
aws_data_catalog="awsdatacatalog"
```

### `dlt` の状態の同期

- この宛先は、[dlt state sync.](../../general-usage/state#syncing-state-with-destination) を完全にサポートしています。状態は S3 バケットの Athena Iceberg テーブルに保存されます。

## サポートされているファイル形式

* [Parquet](../file-formats/parquet.md) が、デフォルトです。

## Athena アダプター

`athena_adapter` を使用して、Athena テーブルにパーティションを追加できます。これは現在、Iceberg テーブルでのみサポートされています。

Iceberg テーブルは、パーティション分割のためのいくつかの変換関数をサポートしています。サポートされているすべての関数の詳細については、[AWS ドキュメント](https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg-creating-tables.html#querying-iceberg-creating-tables-query-editor)を参照してください。

これらの関数のパーティションヒントを生成するには、`athena_partition` ヘルパーを使用します:

* `athena_partition.year(column_name: str)`: 日付/日時列の年ごとにパーティション分割します。
* `athena_partition.month(column_name: str)`: 日付/日時列の月ごとにパーティション分割します。
* `athena_partition.day(column_name: str)`: 日付/日時列の日付でパーティション分割します。
* `athena_partition.hour(column_name: str)`: 日付/日時列の時間でパーティション分割します。
* `athena_partition.bucket(n: int, column_name: str)`: ハッシュ値で `n` 個のバケットに分割する
* `athena_partition.truncate(length: int, column_name: str)`: 切り捨てられた値を `length` (数値の場合は幅) で分割します。

アダプタを使用してテーブルをパーティション分割する方法の例を次に示します:

```py
from datetime import date

import dlt
from dlt.destinations.adapters import athena_partition, athena_adapter

data_items = [
    (1, "A", date(2021, 1, 1)),
    (2, "A", date(2021, 1, 2)),
    (3, "A", date(2021, 1, 3)),
    (4, "A", date(2021, 2, 1)),
    (5, "A", date(2021, 2, 2)),
    (6, "B", date(2021, 1, 1)),
    (7, "B", date(2021, 1, 2)),
    (8, "B", date(2021, 1, 3)),
    (9, "B", date(2021, 2, 1)),
    (10, "B", date(2021, 3, 2)),
]

@dlt.resource(table_format="iceberg")
def partitioned_data():
    yield [{"id": i, "category": c, "created_at": d} for i, c, d in data_items]

# Add partitioning hints to the table
athena_adapter(
    partitioned_data,
    partition=[
        # Partition per category and month
        "category",
        athena_partition.month("created_at"),
    ],
)


pipeline = dlt.pipeline("athena_example")
pipeline.run(partitioned_data)
```
<!--@@@DLT_TUBA athena-->

