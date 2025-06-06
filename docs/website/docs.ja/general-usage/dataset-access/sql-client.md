---
title: Access data with dlt sql client
description: Technical details about the destination sql client
keywords: [data, dataset, sql]
---

# The SQL client

:::note
このページには、SQLクライアントの実装に関する技術的な詳細と、低レベルAPIの使用方法に関する情報が記載されています。単にデータをクエリしたい場合は、このセクションの「dlt」データセット、Streamlit、またはIbisを介したデータアクセスに関するページを読むことをお勧めします。
:::

ほとんどの `dlt` 出力先は、データがロードされる物理的な出力先に接続するために `SqlClientBase` クラスの実装を使用します。DDL ステートメント、データの挿入または更新コマンド、SQL のマージおよび置換クエリは、このクライアント上の接続を介して実行されます。また、[Streamlit アプリ](./streamlit.md) および [`dlt` データセット経由のデータアクセス](./dataset.md) のデータ読み取りにも使用されます。

すべての SQL 宛先は SQL クライアントを使用します。さらに、ファイルシステムには SQL クライアントの特別な実装があり、これについては [以下](#the-filesystem-sql-client) で確認できます。

## SQL クライアントでのクエリの実行

パイプラインの `sql_client` メソッドを介して、接続先の SQL クライアントにアクセスできます。以下のコードは、SQL クライアントを使用してクエリを実行する方法を示しています。

```py
pipeline = dlt.pipeline(destination="bigquery", dataset_name="crm")
with pipeline.sql_client() as client:
    with client.execute_query(
        "SELECT id, name, email FROM customers WHERE id = %s",
        10
    ) as cursor:
        # get all data from the cursor as a list of tuples
        print(cursor.fetchall())
```

## 異なる形式でのデータの取得

`execute_query` によって返されるカーソルには、データを取得するための複数の方法があります。サポートされている形式は、Python タプル、Pandas DataFrame、および Arrow テーブルです。

以下のコードは、データを Pandas DataFrame として取得し、メモリ内で操作する方法を示しています:

```py
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
with pipeline.sql_client() as client:
    with client.execute_query(
        'SELECT "reactions__+1", "reactions__-1", reactions__laugh, reactions__hooray, reactions__rocket FROM issues'
    ) as cursor:
        # calling `df` on a cursor, returns the data as a pandas DataFrame
        reactions = cursor.df()
counts = reactions.sum(0).sort_values(0, ascending=False)
```

## カーソルでサポートされているメソッド

- `fetchall()`: すべての行をタプルのリストとして返します。
- `fetchone()`: 1行をタプルのリストとして返します。
- `fetchmany(size=None)`: 複数の行をタプルのリストとして返します。サイズが指定されていない場合は、すべての行が返されます。
- `df(chunk_size=None, **kwargs)`: データをPandas DataFrameとして返します。`chunk_size`が指定されている場合は、指定されたサイズのチャンクでデータが取得されます。
- `arrow(chunk_size=None, **kwargs)`: データをArrowテーブルとして返します。`chunk_size`が指定されている場合は、指定されたサイズのチャンクでデータが取得されます。
- `iter_fetch(chunk_size: int)`: 指定されたサイズのチャンク単位で、タプルのリストとしてデータを反復処理します。
- `iter_df(chunk_size: int)`: 指定されたサイズのチャンク単位で、Pandas DataFrame としてデータを反復処理します。
- `iter_arrow(chunk_size: int)`: 指定されたサイズのチャンク単位で、Arrow テーブルとしてデータを反復処理します。

:::info
どの取得方法を使用するかは、ユースケースと使用する出力先によって大きく異なります。ベンダーが提供する出力先用のドライバーの中には、Arrow または Pandas DataFrame をネイティブにサポートしているものがあります。その場合は、そのインターフェースを使用します。サポートしていない場合は、`dlt` がタプルのリストをこれらの形式に変換します。
:::

## ファイルシステム SQL クライアント

ファイルシステム デスティネーションは、SQL クライアントの特別なバージョンを実装しています。通常のパイプライン実行中は、ファイルシステムは SQL クライアントを使用せず、ロードされたファイルを指定されたフォルダまたはバケットにコピーしますが、このクライアントを介して SQL を使用してこのデータをクエリできます。これを機能させるために、`dlt` はインメモリの `DuckDB` データベースインスタンスを使用し、ファイルシステムテーブルをこのデータベースのビューとして利用できるようにします。ファイルシステム SQL クライアントは、ほとんどの場合、他の SQL クライアントと同様に使用できます。`dlt` は sqlglot を使用してアクセス対象のテーブルを検出し、前述のように `DuckDB` を使用してクエリ可能にします。

以下のコードは、ファイルシステム SQL クライアントを使用してデータをクエリする方法を示しています。

```py
pipeline = dlt.pipeline(destination="filesystem", dataset_name="my_dataset")
with pipeline.sql_client() as client:
    with client.execute_query("SELECT * FROM my_table") as cursor:
        print(cursor.fetchall())
```

ファイルシステム SQL クライアントを使用する際に知っておくべきこと、または留意すべき点がいくつかあります:

- 実際にクエリを実行する SQL データベースはメモリ内データベースであるため、変更を伴うクエリを実行しても、フォルダやバケットには保存されません。
- You must have loaded your data as `JSONL`, `Parquet`, `CSV` files or `delta`/`iceberg` tables for this SQL client to work. For optimal performance, you should use `Parquet` files or open table formats, as `DuckDB` is able to only read the bytes needed to execute your query from a folder or bucket in this case.
- SQL クライアントでフィルタリング、並べ替え、またはテーブル全体のロードを実行する場合、テーブルが大きい場合は、メモリ内 `DuckDB` インスタンスがバケットまたはフォルダから大量のデータをダウンロードしてクエリを実行する必要があることに注意してください。
- バケット上のデータにアクセスする場合、`dlt` はバケットに接続できるように、認証情報を `DuckDB` に一時的に保存します。
- 現時点では、バケットとテーブル形式の組み合わせの一部は完全にサポートされていない可能性があります。

### Control data freshness
`sqlclient` creates views in which the data is immutable (each next query will access the same data). Such "snapshots" are created by:
* globbing the table files once - when view is created
* using the newest iceberg metadata to create view

Updating views may be costly (globbing, re-reading iceberg metadata) so your best option is to create new `sql_client` (or `pipeline.dataset()`) instance
when you need fresh data. Alternatively you can enable autorefresh mode which will re-create view on each query:

```py
from dlt.destination import filesystem

pipeline = dlt.pipeline(destination=filesystem(always_refresh_views=True), dataset_name="my_dataset")
with pipeline.sql_client() as client:
    with client.execute_query("SELECT * FROM my_table") as cursor:
        print(cursor.fetchall())
        # pipeline.run() here and get updated data
        print(cursor.fetchall())
```

Note: `delta` tables are by default on autorefresh which is implemented by delta core and seems to be pretty efficient.
