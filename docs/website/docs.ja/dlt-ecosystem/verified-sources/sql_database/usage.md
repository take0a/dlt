---
title: Usage
description: basic usage of the sql_database source
keywords: [sql connector, sql database pipeline, sql database]
---

import Header from '../_source-info-header.md';

# 使用法

<Header/>

## 取り込まれるデータに列方向のフィルタリングを適用する

デフォルトでは、既存のソース関数とリソース関数である `sql_database` と `sql_table` は、ソース テーブルからすべてのレコードを取り込みます。ただし、`query_adapter_callback` を使用すると、[SQLAlchemy 構文](https://docs.sqlalchemy.org/en/14/core/selectable.html#) を使用して、基になる `SELECT` ステートメント内に `WHERE` 句を渡すことができます。これにより、抽出前に特定の列に基づいてデータをフィルタリングできます。

以下の例では、`query_adapter_callback` を使用して、テーブル `orders` の列 `customer_id` でフィルタリングします:

```py
from dlt.sources.sql_database import sql_database

def query_adapter_callback(query, table):
    if table.name == "orders":
        # Only select rows where the column customer_id has value 1
        return query.where(table.c.customer_id==1)
    # Use the original query for other tables
    return query

source = sql_database(
    query_adapter_callback=query_adapter_callback
).with_resources("orders")
```

## カスタム SQL カスタムクエリを書く

ソース データベースに SQL VIEW を作成し、そこからデータを抽出することをお勧めします。その場合、`dlt` はすべての列タイプを推測し、それ以上のカスタマイズを行わずに、ビューで定義した形式でデータを読み取ります。

ビューの作成が不可能な場合は、`query_adapter_callback` の拡張バージョンを使用して、自動生成されたクエリを完全に書き換えることができます:

```py
import sqlalchemy as sa

def query_adapter_callback(
      query, table, incremental=None, engine=None
  ) -> TextClause:

      if incremental and incremental.start_value is not None:
          t_query = sa.text(
              f"SELECT *, 1 as add_int, 'const' as add_text FROM {table.fullname} WHERE"
              f" {incremental.cursor_path} > :start_value"
          ).bindparams(**{"start_value": incremental.start_value})
      else:
          t_query = sa.text(f"SELECT *, 1 as add_int, 'const' as add_text FROM {table.fullname}")

      return t_query
```

上記のスニペットでは、いくつか興味深いことを行っています:

1. `sa.text`でテキストクエリを作成します
2. 増分列を選択する条件をデフォルトの`ge`から`greater`に変更します。<!-- (f" {incremental.cursor_path} > :start_value") -->
3. 追加の計算列を追加します: `1 as add_int, 'const' as add_text`。ここで他のテーブルを結合することもできます。

`table_adapter_callback` で追加した列を明示的に入力することをお勧めします:

```py
from sqlalchemy.sql import sqltypes

def add_new_columns(table) -> None:
    required_columns = [
        ("add_int", sqltypes.BigInteger, {"nullable": True}),
        ("add_text", sqltypes.Text, {"default": None, "nullable": True}),
    ]
    for col_name, col_type, col_kwargs in required_columns:
        if col_name not in table.c:
            table.append_column(sa.Column(col_name, col_type, **col_kwargs))
```

そうでない場合、`dlt` は抽出されたデータから型を推測しようとします。

これらのアダプタを使用して `sql_table` を呼び出す方法は次のとおりです。

```py
import dlt
from dlt.sources.sql_database import sql_table

table = sql_table(
  table="chat_channel",
  table_adapter_callback=add_new_columns,
  query_adapter_callback=query_adapter_callback,
  incremental=dlt.sources.incremental("updated_at"),
)
```

## 計算列とカスタム増分句を追加する

計算列をサブクエリに変換することで、テーブル定義に追加できます:

```py
def add_max_timestamp(table):
    computed_max_timestamp = sa.sql.type_coerce(
        sa.func.greatest(table.c.created_at, table.c.updated_at),
        sqltypes.DateTime,
    ).label("max_timestamp")
    subquery = sa.select(*table.c, computed_max_timestamp).subquery()
    return subquery
```

`created_at` 列と `updated_at` 列の最大値である新しい `max_timestamp` 列を追加し、それをサブクエリに変換します。これは、これに `WHERE` 句を付加する増分ロードに使用するためです。

```py
import dlt
from dlt.sources.sql_database import sql_table

read_table = sql_table(
    table="chat_message",
    table_adapter_callback=add_max_timestamp,
    incremental=dlt.sources.incremental("max_timestamp"),
)
```

`dlt` は、増分クエリを生成するために、元の `chat_message` テーブルの代わりにサブクエリを使用します。上記の例のように、クエリ アダプタを使用してサブクエリをさらにカスタマイズできることに注意してください。

## ロード前にデータを変換する

抽出されたデータには、リソース オブジェクト (`sql_table()` または `sql_database().with_resource())`) を通じて直接アクセスできます。各オブジェクトは単一の SQL テーブルを表します。これらのオブジェクトは、テーブルの個々の行を生成するジェネレーターであり、カスタム Python 関数を使用して変更できます。これらの関数は、`add_map` を使用してリソースに適用できます。

:::note
PyArrow バックエンドは個々の行を生成するのではなく、データのチャンクを `ndarray` として読み込みます。この場合、`add_map` に入る変換関数は `ndarray` 入力を期待するように構成する必要があります。
:::

例:

1. データを宛先にロードする前に、個人を特定できる情報 (PII) を隠すためにデータを仮名化します。(`dlt` を使用したデータの仮名化の詳細については、[こちら](../../../general-usage/customising-pipelines/pseudonymizing_columns)を参照してください。)

    ```py
    import dlt
    import hashlib
    from dlt.sources.sql_database import sql_database

    def pseudonymize_name(doc):
        '''
        Pseudonymization is a deterministic type of PII-obscuring.
        Its role is to allow identifying users by their hash,
        without revealing the underlying info.
        '''
        # add a constant salt to generate
        salt = 'WI@N57%zZrmk#88c'
        salted_string = doc['rfam_acc'] + salt
        sh = hashlib.sha256()
        sh.update(salted_string.encode())
        hashed_string = sh.digest().hex()
        doc['rfam_acc'] = hashed_string
        return doc

    pipeline = dlt.pipeline(
        # Configure the pipeline
    )
    # using sql_database source to load family table and pseudonymize the column "rfam_acc"
    source = sql_database().with_resources("family")
    # modify this source instance's resource
    source.family.add_map(pseudonymize_name)
    # Run the pipeline. For a large db this may take a while
    info = pipeline.run(source, write_disposition="replace")
    print(info)
    ```

2. ロード前に不要な列を除外する

    ```py
    import dlt
    from dlt.sources.sql_database import sql_database

    def remove_columns(doc):
        del doc["rfam_id"]
        return doc

    pipeline = dlt.pipeline(
        # Configure the pipeline
    )
    # using sql_database source to load family table and remove the column "rfam_id"
    source = sql_database().with_resources("family")
    # modify this source instance's resource
    source.family.add_map(remove_columns)
    # Run the pipeline. For a large db this may take a while
    info = pipeline.run(source, write_disposition="replace")
    print(info)
    ```

## sql_database パイプラインのデプロイ

`sql_database` パイプラインは、[GitHub Actions](../../../walkthroughs/deploy-a-pipeline/deploy-with-github-actions)、[Airflow](../../../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer)、[Dagster](../../../walkthroughs/deploy-a-pipeline/deploy-with-dagster) などの `dlt` デプロイメント方法のいずれかを使用してデプロイできます。デプロイメント方法の完全なリストについては、[こちら](../../../walkthroughs/deploy-a-pipeline) を参照してください。

### Airflow で実行する

Airflowで実行する場合:

1. `dlt` [Airflow Helper](../../../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer.md#2-modify-dag-file) を使用して、`sql_database` ソースからタスクを作成します。(テーブル抽出を並列で実行する場合は、ソースから DAG への変換時に `decompose = "parallel-isolated"` を設定することで実行できます。コード例については、[こちら](../../../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer#2-modify-dag-file) を参照してください。)
2. `defer_table_reflect` 引数を使用して実行時にテーブルを反映します。
3. [Airflow intervals](../../../general-usage/incremental/cursor.md#using-airflow-schedule-for-backfill-and-incremental-loading) を使用してデータをロードするには、`allow_external_schedulers` を設定します。
