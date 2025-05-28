---
title: Accessing loaded data in Python
description: Conveniently accessing the data loaded to any destination in python
keywords: [destination, schema, data, access, retrieval]
---

# Python でロードされたデータにアクセスする

このガイドでは、`dlt` Python ライブラリを使用して、出力先にロードされたデータにアクセスし、操作する方法について説明します。パイプラインを実行してデータをロードした後、`ReadableDataset` クラスと `ReadableRelation` クラスを使用して、プログラムでデータを操作できます。

**注:** `ReadableDataset` オブジェクトと `ReadableRelation` オブジェクトは**遅延読み込み** です。これらのオブジェクトは、DataFrame へのデータのフェッチやデータの反復処理など、必要なアクションが実行された場合にのみ、データのクエリと取得を行います。つまり、これらのオブジェクトを作成しただけではデータがメモリにロードされず、コードの効率が向上します。

## クイックスタートの例

パイプラインからデータを取得し、Pandas DataFrame または PyArrow テーブルにロードする方法の完全な例を以下に示します。

```py
# Assuming you have a Pipeline object named 'pipeline'
# and you have loaded data to a table named 'items' in the destination

# Step 1: Get the readable dataset from the pipeline
dataset = pipeline.dataset()

# Step 2: Access a table as a ReadableRelation
items_relation = dataset.items  # Or dataset["items"]

# Step 3: Fetch the entire table as a Pandas DataFrame
df = items_relation.df()

# Alternatively, fetch as a PyArrow Table
arrow_table = items_relation.arrow()
```

## はじめに

`Pipeline` オブジェクト（ここでは `pipeline` と呼びます）があると仮定すると、`ReadableDataset` を取得し、`ReadableRelation` オブジェクトとしてテーブルにアクセスできます。

### `ReadableDataset` にアクセスする

```py
# Get the readable dataset from the pipeline
dataset = pipeline.dataset()

# print the row counts of all tables in the destination as dataframe
print(dataset.row_counts().df())
```

### `ReadableRelation` としてテーブルにアクセスする

データセット内のテーブルには、属性アクセスまたはアイテムアクセスのいずれかを使用してアクセスできます。

```py
# Using attribute access
items_relation = dataset.items

# Using item access
items_relation = dataset["items"]
```

## データの読み取り

`ReadableRelation` を作成すると、さまざまな形式とサイズのデータ​​を読み取ることができます。

### テーブル全体を取得する

:::caution
制限や反復処理を行わずにテーブル全体をメモリにロードすると、大量のメモリを消費し、テーブルが大きすぎる場合はプログラムがクラッシュする可能性があります。大規模なデータセットを扱う場合は、チャンク反復処理を使用するか、制限を適用することをお勧めします。
:::

#### As a Pandas DataFrame

```py
df = items_relation.df()
```

#### As a PyArrow Table

```py
arrow_table = items_relation.arrow()
```

#### As a list of Python tuples

```py
items_list = items_relation.fetchall()
```

## 遅延読み込み動作

`ReadableDataset` オブジェクトと `ReadableRelation` オブジェクトは**遅延読み込み** です。つまり、作成時にすぐにデータを取得するわけではありません。データは、`.df()` や `.arrow()` の呼び出し、データの反復処理など、必要なアクションが実行された場合にのみ取得されます。このアプローチにより、パフォーマンスが最適化され、不要なデータ読み込みが削減されます。

## データをチャンク単位で反復処理する

大規模なデータセットを効率的に処理するには、データを小さなチャンク単位で処理します。

### Iterate as Pandas DataFrames

```py
for df_chunk in items_relation.iter_df(chunk_size=500):
    # Process each DataFrame chunk
    pass
```

### Iterate as PyArrow Tables

```py
for arrow_chunk in items_relation.iter_arrow(chunk_size=500):
    # Process each PyArrow chunk
    pass
```

### Iterate as lists of tuples

```py
for items_chunk in items_relation.iter_fetch(chunk_size=500):
    # Process each chunk of tuples
    pass
```

ReadableRelation で利用可能なメソッドは、SQL クライアントから返されるカーソルで利用可能なメソッドに対応しています。詳細については、[SQL クライアント](./sql-client.md#supported-methods-on-the-cursor) ガイドを参照してください。

## 特別なクエリ

`row_counts` メソッドを使用すると、出力先にあるすべてのテーブルの行数を DataFrame として取得できます。

```py
# print the row counts of all tables in the destination as dataframe
print(dataset.row_counts().df())

# or as tuples
print(dataset.row_counts().fetchall())
```

## クエリの変更

レコード数を制限したり、特定の列を選択したり、これらの操作を連鎖させたりすることで、データ取得を絞り込むことができます。

### レコード数を制限する

```py
# Get the first 50 items as a PyArrow table
arrow_table = items_relation.limit(50).arrow()
```

#### `head()` を使用して最初の 5 つのレコードを取得する

```py
df = items_relation.head().df()
```

### Select specific columns

```py
# Select only 'col1' and 'col2' columns
items_list = items_relation.select("col1", "col2").fetchall()

# Alternate notation with brackets
items_list = items_relation[["col1", "col2"]].fetchall()

# Only get one column
items_list = items_relation["col1"].fetchall()

```

### チェーン操作

`select`、`limit`、その他のメソッドを組み合わせることができます。

```py
# Select columns and limit the number of records
arrow_table = items_relation.select("col1", "col2").limit(50).arrow()
```

## ibis 式を使ったクエリの変更

素晴らしい [ibis](https://ibis-project.org/) ライブラリをインストールすると、ibis 式を使ってクエリを変更できます。

```sh
pip install ibis-framework
```

次に、dlt は内部的に `ibis.UnboundTable` を `ReadableIbisRelation` オブジェクトでラップし、ibis 式を使用してリレーションのクエリを変更できるようにします:

```py
# now that ibis is installed, we can get a dataset with ibis relations
dataset = pipeline.dataset()

# get two relations
items_relation = dataset["items"]
order_relation = dataset["orders"]

# join them using an ibis expression
joined_relation = items_relation.join(order_relation, items_relation.id == order_relation.item_id)

# now we can use the ibis expression to filter the data
filtered_relation = joined_relation.filter(order_relation.status == "completed")

# we can inspect the query that will be used to read the data
print(filtered_relation.query)

# and finally fetch the data as a pandas dataframe, the same way we would do with a normal relation
df = filtered_relation.df()

# a few more examples

# filter for rows where the id is in the list of ids
items_relation.filter(items_relation.id.isin([1, 2, 3])).df()

# limit and offset
items_relation.limit(10, offset=5).arrow()

# mutate columns by adding a new colums that always is 10 times the value of the id column
items_relation.mutate(new_id=items_relation.id * 10).df()

# sort asc and desc
import ibis
items_relation.order_by(ibis.desc("id"), ibis.asc("price")).limit(10)

# group by and aggregate
items_relation.group_by("item_group").having(items_table.count() >= 1000).aggregate(sum_id=items_table.id.sum()).df()

# subqueries
items_relation.filter(items_table.category.isin(beverage_categories.name)).df()
```

使用可能な式の詳細については、[ibis for sql users](https://ibis-project.org/tutorials/ibis-for-sql-users) ページを参照してください。

:::note
実行されたクエリを変更するメソッドのみ使用でき、ibisが提供するデータ取得メソッドは使用できないことに注意してください。これは、上記で説明した通常のリレーションで定義されているものと同じメソッドを使用して実行されます。ibisのネイティブ統合を完全に必要とする場合は、後述の高度なセクションにあるibisのセクションをお読みください。また、すべてのibis式がすべての出力先およびSQL方言でサポートされているわけではありません。
:::

## サポートされている出力先

`dlt` でサポートされているすべての SQL およびファイルシステムの出力先は、このデータアクセスインターフェースを利用できます。ファイルシステムの出力先の場合、`dlt` は [内部的に **DuckDB** を使用](./sql-client.md#the-filesystem-sql-client)、Parquet または JSONL ファイルから動的にビューを作成します。これにより、SQL データベースと同じインターフェースを使用して、ファイルに保存されたデータをクエリできます。この方法でバケットやファイルシステム内のデータに頻繁にアクセスする場合は、JSONL ではなく Parquet としてデータをロードすることをお勧めします。**DuckDB** は、クエリの実行に実際に必要なデータ部分のみをロードできるためです。

## Examples

### 1つのレコードをタプルとして取得する

```py
record = items_relation.fetchone()
```

### 多数のレコードをタプルとして取得する

```py
records = items_relation.fetchmany(chunk_size=10)
```

### 制限と列選択を使用してデータを反復処理します

**注:** ファイルシステムテーブルを反復処理する場合、基盤となる DuckDB は、テーブルが基にしている Parquet ファイルのサイズに応じて異なるチャンクサイズを返すことがあります。

```py

# Dataframes
for df_chunk in items_relation.select("col1", "col2").limit(100).iter_df(chunk_size=20):
    ...

# Arrow tables
for arrow_table in items_relation.select("col1", "col2").limit(100).iter_arrow(chunk_size=20):
    ...

# Python tuples
for records in items_relation.select("col1", "col2").limit(100).iter_fetch(chunk_size=20):
    # Process each modified DataFrame chunk
    ...
```

## 高度な使用法

### カスタム SQL クエリを使用して `ReadableRelations` を作成する

データセットに対してカスタム SQL クエリを直接使用して `ReadableRelation` を作成できます。

```py
# Join 'items' and 'other_items' tables
custom_relation = dataset("SELECT * FROM items JOIN other_items ON items.id = other_items.id")
arrow_table = custom_relation.arrow()
```

:::note
`dataset()` でカスタム SQL クエリを使用する場合、`limit` や `select` などのメソッドは機能しません。フィルタリングや列選択は SQL クエリに直接含めてください。
:::


### `ReadableRelation` をパイプラインテーブルにロードする

`iter_arrow` メソッドと `iter_df` メソッドは、`ReadableRelation` 全体をチャンク単位で反復処理するジェネレーターであるため、別の（または同じ）`dlt` パイプラインのリソースとして使用できます。

```py
# Create a readable relation with a limit of 1m rows
limited_items_relation = dataset.items.limit(1_000_000)

# Create a new pipeline
other_pipeline = dlt.pipeline(pipeline_name="other_pipeline", destination="duckdb")

# We can now load these 1m rows into this pipeline in 10k chunks
other_pipeline.run(limited_items_relation.iter_arrow(chunk_size=10_000), table_name="limited_items")
```

[Arrow テーブルまたは DataFrame を使用して Python でデータを変換する](../../dlt-ecosystem/transformations/python) の詳細をご覧ください。

### `ibis` を使用したデータクエリ

詳細については、[ネイティブ Ibis 統合](./ibis-backend.md) ガイドをご覧ください。

## 重要な考慮事項

- **メモリ使用量:** 反復処理や制限処理を行わずにテーブル全体をメモリにロードすると、大量のメモリが消費され、データセットが大きい場合はクラッシュにつながる可能性があります。常に制限またはチャンク反復処理の使用を検討してください。

- **遅延評価:** `ReadableDataset` オブジェクトと `ReadableRelation` オブジェクトは、必要なときまでデータの取得を遅延します。この設計により、パフォーマンスとリソース使用率が向上します。

- **カスタム SQL クエリ:** カスタム SQL クエリを実行する際は、`limit()` や `select()` などの追加メソッドはクエリを変更しないことに注意してください。必要な句はすべて SQL 文に直接含めてください。

