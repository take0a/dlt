---
title: Access datasets in Python
description: Conveniently access the data loaded to any destination in Python
keywords: [destination, schema, data, access, retrieval]
---

# Python でロードされたデータにアクセスする

This guide explains how to access and manipulate data that has been loaded into your destination using the `dlt` Python library. After running your pipelines and loading data, you can use the `pipeline.dataset()` and data frame expressions, Ibis or SQL to query the data and read it as records, Pandas frames or Arrow tables.

## クイックスタートの例

パイプラインからデータを取得し、Pandas DataFrame または PyArrow テーブルにロードする方法の完全な例を以下に示します。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::quick_start_example-->


## はじめに

`Pipeline` オブジェクト（ここでは `pipeline` と呼びます）があると仮定すると、`ReadableDataset` を取得し、`ReadableRelation` オブジェクトとしてテーブルにアクセスできます。

**Note:** The `ReadableDataset` and `ReadableRelation` objects are **lazy-loading**. They will only query and retrieve data when you perform an action that requires it, such as fetching data into a DataFrame or iterating over the data. This means that simply creating these objects does not load data into memory, making your code more efficient.


### Access the dataset

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::getting_started-->

### データセットとしてテーブルにアクセスする

データセット内のテーブルには、属性アクセスまたはアイテムアクセスのいずれかを使用してアクセスできます。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::accessing_tables-->

## データの読み取り

`ReadableRelation` を作成すると、さまざまな形式とサイズのデータ​​を読み取ることができます。

### テーブル全体を取得する

:::caution
制限や反復処理を行わずにテーブル全体をメモリにロードすると、大量のメモリを消費し、テーブルが大きすぎる場合はプログラムがクラッシュする可能性があります。大規模なデータセットを扱う場合は、チャンク反復処理を使用するか、制限を適用することをお勧めします。
:::

#### As a Pandas DataFrame

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::fetch_entire_table_df-->

#### As a PyArrow Table

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::fetch_entire_table_arrow-->

#### As a list of Python tuples

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::fetch_entire_table_fetchall-->

## 遅延読み込み動作

`ReadableDataset` オブジェクトと `ReadableRelation` オブジェクトは**遅延読み込み** です。つまり、作成時にすぐにデータを取得するわけではありません。データは、`.df()` や `.arrow()` の呼び出し、データの反復処理など、必要なアクションが実行された場合にのみ取得されます。このアプローチにより、パフォーマンスが最適化され、不要なデータ読み込みが削減されます。

## データをチャンク単位で反復処理する

大規模なデータセットを効率的に処理するには、データを小さなチャンク単位で処理します。

### Iterate as Pandas DataFrames

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::iterating_df_chunks-->

### Iterate as PyArrow Tables

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::iterating_arrow_chunks-->

### Iterate as lists of tuples

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::iterating_fetch_chunks-->

ReadableRelation で利用可能なメソッドは、SQL クライアントから返されるカーソルで利用可能なメソッドに対応しています。詳細については、[SQL クライアント](./sql-client.md#supported-methods-on-the-cursor) ガイドを参照してください。

## Connection Handling

For every call that actually fetches data from the destination, such as `df()`, `arrow()`, `fetchall()` etc., the dataset will open a connection and close it after it has been retrieved or the iterator is completed. You can keep the connection open for multiple requests with the dataset context manager:

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::context_manager-->

## 特別なクエリ

`row_counts` メソッドを使用すると、出力先にあるすべてのテーブルの行数を DataFrame として取得できます。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::row_counts-->

## クエリの変更

レコード数を制限したり、特定の列を選択したり、これらの操作を連鎖させたりすることで、データ取得を絞り込むことができます。

### レコード数を制限する

```py
# Get the first 50 items as a PyArrow table
arrow_table = items_relation.limit(50).arrow()
```

#### `head()` を使用して最初の 5 つのレコードを取得する

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::head_records-->

### Select specific columns

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::select_columns-->

### チェーン操作

`select`、`limit`、その他のメソッドを組み合わせることができます。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::chain_operations-->

## ibis 式を使ったクエリの変更

素晴らしい [ibis](https://ibis-project.org/) ライブラリをインストールすると、ibis 式を使ってクエリを変更できます。

```sh
pip install ibis-framework
```

次に、dlt は内部的に `ibis.UnboundTable` を `ReadableIbisRelation` オブジェクトでラップし、ibis 式を使用してリレーションのクエリを変更できるようにします:

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::ibis_expressions-->

使用可能な式の詳細については、[ibis for sql users](https://ibis-project.org/tutorials/ibis-for-sql-users) ページを参照してください。

:::note
実行されたクエリを変更するメソッドのみ使用でき、ibisが提供するデータ取得メソッドは使用できないことに注意してください。これは、上記で説明した通常のリレーションで定義されているものと同じメソッドを使用して実行されます。ibisのネイティブ統合を完全に必要とする場合は、後述の高度なセクションにあるibisのセクションをお読みください。また、すべてのibis式がすべての出力先およびSQL方言でサポートされているわけではありません。
:::

## サポートされている出力先

All SQL and filesystem destinations supported by `dlt` can utilize this data access interface.

### Reading data from filesystem
For filesystem destinations, `dlt` [uses **DuckDB** under the hood](./sql-client.md#the-filesystem-sql-client) to create views on iceberg and delta tables or from Parquet, JSONL and csv files. This allows you to query data stored in files using the same interface as you would with SQL databases. If you plan on accessing data in buckets or the filesystem a lot this way, it is advised to load data into delta or iceberg tables, as **DuckDB** is able to only load the parts of the data actually needed for the query to work.

:::tip
By default `dlt` will not autorefresh views created on iceberg tables and files when new data is loaded. This prevents wasting resources on
file globbing and reloading iceberg metadata for every query. You can [change this behavior](sql-client.md#control-data-freshness) with `always_refresh_views` flag.

Note: `delta` tables are by default on autorefresh which is implemented by delta core and seems to be pretty efficient.
:::

## Examples

### 1つのレコードをタプルとして取得する

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::fetch_one-->

### 多数のレコードをタプルとして取得する

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::fetch_many-->

### 制限と列選択を使用してデータを反復処理します

**注:** ファイルシステムテーブルを反復処理する場合、基盤となる DuckDB は、テーブルが基にしている Parquet ファイルのサイズに応じて異なるチャンクサイズを返すことがあります。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::iterating_with_limit_and_select-->

## 高度な使用法

### カスタム SQL クエリを使用して `ReadableRelations` を作成する

データセットに対してカスタム SQL クエリを直接使用して `ReadableRelation` を作成できます。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::custom_sql-->

:::note
`dataset()` でカスタム SQL クエリを使用する場合、`limit` や `select` などのメソッドは機能しません。フィルタリングや列選択は SQL クエリに直接含めてください。
:::


### `ReadableRelation` をパイプラインテーブルにロードする

`iter_arrow` メソッドと `iter_df` メソッドは、`ReadableRelation` 全体をチャンク単位で反復処理するジェネレーターであるため、別の（または同じ）`dlt` パイプラインのリソースとして使用できます。

<!--@@@DLT_SNIPPET ./dataset_snippets/dataset_snippets.py::loading_to_pipeline-->

[Arrow テーブルまたは DataFrame を使用して Python でデータを変換する](../../dlt-ecosystem/transformations/python) の詳細をご覧ください。

### `ibis` を使用したデータクエリ

詳細については、[ネイティブ Ibis 統合](./ibis-backend.md) ガイドをご覧ください。

## 重要な考慮事項

- **メモリ使用量:** 反復処理や制限処理を行わずにテーブル全体をメモリにロードすると、大量のメモリが消費され、データセットが大きい場合はクラッシュにつながる可能性があります。常に制限またはチャンク反復処理の使用を検討してください。

- **遅延評価:** `ReadableDataset` オブジェクトと `ReadableRelation` オブジェクトは、必要なときまでデータの取得を遅延します。この設計により、パフォーマンスとリソース使用率が向上します。

- **カスタム SQL クエリ:** カスタム SQL クエリを実行する際は、`limit()` や `select()` などの追加メソッドはクエリを変更しないことに注意してください。必要な句はすべて SQL 文に直接含めてください。

