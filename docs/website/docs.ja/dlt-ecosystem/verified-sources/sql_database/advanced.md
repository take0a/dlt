---
title: Advanced usage
description: advance configuration and usage of the sql_database source
keywords: [sql connector, sql database pipeline, sql database]
---

import Header from '../_source-info-header.md';

# 高度な使い方

<Header/>

## インクリメンタルローディング
### 包括的、排他的フィルタリング

デフォルトでは、増分フィルタリングは開始値側も含まれるため、カーソルが前回の実行のカーソルと等しい行がデータベースから再度取得されます。

生成される SQL クエリは次のようになります (`last_value_func` が `max` であると仮定):

```sql
SELECT * FROM family
WHERE last_modified >= :start_value
ORDER BY last_modified ASC
```

つまり、前回のロードと重複する一部の行がデータベースから取得されます。その後、重複は主キーまたは行の内容のハッシュを使用して dlt によってフィルタリングされます。

これにより、抽出されたシーケンスにギャップがなくなることが保証されます。ただし、重複排除処理とデータベースから冗長レコードを取得するコストの両方により、パフォーマンスのオーバーヘッドが発生します。

これは必ずしも必要ではありません。データに重複するカーソル値が含まれていないことがわかっている場合は、`range_start="open"` を incremental に渡すことで抽出を最適化できます。

これにより、重複排除プロセスが無効になり、SQL `WHERE` 句で使用される演算子が `>=` (以上)から `>` (より大きい)に変更されるため、重複する行は取得されません。

例えば

```py
table = sql_table(
    table='family',
    incremental=dlt.sources.incremental(
        'last_modified',  # Cursor column name
        initial_value=pendulum.DateTime(2024, 1, 1, 0, 0, 0),  # Initial cursor value
        range_start="open",  # exclude the start value
    )
)
```

次の場合に適したオプションです:

* カーソルが自動的に増加するIDである
* カーソルが高精度のタイムスタンプであり、2つのレコードがまったく同時に作成されることがない。
* パイプラインの実行が、ロード中に新しいデータが生成されないようにタイミングが調整されている

## 並列化された抽出

各テーブルを個別のスレッドで抽出できます (この時点ではマルチプロセスではありません)。これにより、クエリの実行に時間がかかったり、ネットワークの待ち時間や速度が遅い場合に、読み込み時間が短縮されます。これを有効にするには、ソース/リソースを次のように宣言します:

```py
from dlt.sources.sql_database import sql_database, sql_table

database = sql_database().parallelize()
table = sql_table().parallelize()
```

## 列のリフレクション

列のリフレクションは、列名、制約、データ型などの列メタデータを自動的に検出して取得することです。列とそのデータ型は SQLAlchemy で反映されます。その後、SQL 型が `dlt` 型にマップされます。選択したバックエンドによっては、一部の型で追加の処理が必要になる場合があります。

`reflection_level` 引数は、どの程度の情報が反映されるかを制御します:

- `reflection_level = "minimal"`: 列名と NULL 値可能性のみが検出されます。データ型はデータから推測されます。
- `reflection_level = "full"`: 列名、NULL 値可能性、およびデータ型が検出されます。小数点型の場合、常に精度とスケールが追加されます。**これがデフォルトです。**
- `reflection_level = "full_with_precision"`: 列名、NULL 値可能性、データ型、精度/スケールが検出されます。また、テキストやバイナリなどの型についても検出されます。整数サイズは、他のすべての型では bigint と int に設定されます。

If the SQL type is unknown or not supported by `dlt`, then we'll try to infer it from the data.
* `sqlalchemy` follows standard `dlt` inference rules from Python objects. This often means that some types are coerced to strings and `dataclass` based values from sqlalchemy are inferred as `json` (JSON in most destinations).
* `pyarrow` backend will try to infer types from the data using rules built-in in arrow (we just past an array of Python objects and ask for a type). Variant columns are not created by this backend so columns with inconsistent types cannot be loaded by this backend.

:::tip
リフレクションレベル **full** / **full_with_precision** を使用すると、sqlalchemy または pyarrow バックエンドによって返されるデータがリフレクションされたデータ型と一致しない状況が発生する可能性があります。最も一般的な症状は次のとおりです:

1. 宛先は、特定の列に対して 1 つの型を別の型にキャストできないというエラーを出力します。たとえば、`connector-x` ナノ秒単位で TIME を返しますが、BigQuery はそれを bigint として認識し、読み込みに失敗します。
2. `normalize` ステップで、`SchemaCorruptedException` や他の強制エラーが発生します。
この場合、返されたデータからすべてのデータ型が推測される **最小限の** リフレクションレベルを試せます。経験上、これにより強制エラーの問題のほとんどを回避できます。
:::

### 必要に応じてリフレクションタイプを調整します

`type_adapter_callback` 関数を渡すことで SQL 型をオーバーライドすることもできます。この関数は、入力として `SQLAlchemy` データ型を受け取り、出力として新しい型 (または、データから推測される列を強制する `None` ) を返します。

これは、たとえば次のような場合に役立ちます:

- 宛先でサポートされていないデータ型をロードする (たとえば、JSON 型の列を文字列に強制変換する必要があります)。
- 標準の sqlalchemy タイプを継承しないカスタムタイプを使用する sqlalchemy 方言を使用している。
- 特定の型については、データからデータ型を推測する `dlt` を使用するように、`None` を返すことをお勧めします。

次の例では、Snowflake からタイムスタンプをロードするときに、結果のスキーマで標準のsqlalchemy `timestamp`列に変換されるようにします:

```py
import dlt
import sqlalchemy as sa
from dlt.sources.sql_database import sql_database, sql_table
from snowflake.sqlalchemy import TIMESTAMP_NTZ

def type_adapter_callback(sql_type):
    if isinstance(sql_type, TIMESTAMP_NTZ):  # Snowflake does not inherit from sa.DateTime
        return sa.DateTime(timezone=True)
    return sql_type  # Use default detection for other types

source = sql_database(
    "snowflake://user:password@account/database?&warehouse=WH_123",
    reflection_level="full",
    type_adapter_callback=type_adapter_callback,
    backend="pyarrow"
)

dlt.pipeline("demo").run(source)
```

### NULL可能情報の除去

`dlt` は、**すべてのリフレクションレベル**で、リフレクションされたスキーマ情報に `NULL`/`NOT NULL` 情報を追加します。この情報が不要である場合もあります。たとえば:

* 行を（ソフト）削除するレプリケーション ソースを使用する予定の場合
* ソース テーブルから列が削除されることが予想される場合

このような場合、null 可能情報を削除するテーブルアダプターを使用できます (`dlt` デフォルトでは null 値許容テーブルが作成されます):

```py
from dlt.sources.sql_database import sql_table, remove_nullability_adapter

read_table = sql_table(
    table="chat_message",
    reflection_level="full_with_precision",
    table_adapter_callback=remove_nullability_adapter,
)
print(read_table.compute_table_schema())
```

両方を組み合わせる必要がある場合は、カスタムテーブルアダプターから `remove_nullability_adapter` を呼び出すことができます。

## TOML または環境変数で構成する

`sql_database()` と `sql_table()` の引数のほとんどは、TOML ファイル内で直接設定することも、環境変数として設定することもできます。
`dlt` は、これらの値をパイプラインスクリプトに自動的に挿入します。

これは、`sql_table()` で、各テーブルごとに個別の構成を維持できるため、特に便利です(以下では **secrets.toml** と **config.toml** を示していますが、これらを 1 つに自由に組み合わせることができます)。

以下の例は、TOML ファイル (`secrets.toml` または `config.toml`) のいずれかで引数を設定する方法を示しています:

1. 接続文字列の指定:
    ```toml
    [sources.sql_database]
    credentials="mssql+pyodbc://loader.database.windows.net/dlt_data?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    ```

2. `chat_message` テーブルの `backend`、`chunk_size`、増分列などのパラメータを設定:
    ```toml
    [sources.sql_database.chat_message]
    backend="pandas"
    chunk_size=1000

    [sources.sql_database.chat_message.incremental]
    cursor_path="updated_at"
    ```

    これは、`sql_table()` で、このリソースを複数のテーブルに対して実行する必要がある場合に特に便利です。このようにパラメータを設定すると、テーブルごとに個別の構成をクリーンな方法で維持できるようになります。

3. データベースと個々のテーブルの個別の構成の処理で `sql_database()` ソースを使用する場合でも、データベースと個々のテーブルのパラメータを個別に構成できます。
    
    ```toml
    [sources.sql_database]
    credentials="mssql+pyodbc://loader.database.windows.net/dlt_data?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    schema="data"
    backend="pandas"
    chunk_size=1000

    [sources.sql_database.chat_message.incremental]
    cursor_path="updated_at"
    ```

    以下に作成される結果のソースは、**chunk_size** が 1000 の **pandas** バックエンドを使用してデータを抽出します。テーブル **chat_message** は、**updated_at** 列を使用してデータをインクリメンタルロードします。他のすべてのテーブルではインクリメンタルロードは使用されず、代わりに全データがロードされます。

    ```py
    database = sql_database()
    ```

この方法で(アダプター コールバック関数を除く)すべての引数を構成できます。[標準の dlt ルールが適用されます](../../../general-usage/credentials/setup)。

[構成セクションを使用して](../../../general-usage/credentials/setup#recommended-section-layout)、これらの引数を環境変数として設定することもできます:

```sh
SOURCES__SQL_DATABASE__CREDENTIALS="mssql+pyodbc://loader.database.windows.net/dlt_data?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
SOURCES__SQL_DATABASE__BACKEND=pandas
SOURCES__SQL_DATABASE__CHUNK_SIZE=1000
SOURCES__SQL_DATABASE__CHAT_MESSAGE__INCREMENTAL__CURSOR_PATH=updated_at
```

### カスタムセクションで複数のソースを並べて設定する

`dlt` では、ソースの名前を変更して、ソース構成をカスタムセクションに配置したり、ソースのインスタンスを多数並べて作成したりできます。例:

```py
from dlt.sources.sql_database import sql_database

my_db = sql_database.clone(name="my_db", section="my_db")(table_names=["chat_message"])
print(my_db.name)
```

ここでは、`sql_database` の名前を変更したバージョンを作成し、それをインスタンス化します。このようなソースは、次のように資格情報を読み取ります:

```toml
[sources.my_db]
credentials="mssql+pyodbc://loader.database.windows.net/dlt_data?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
schema="data"
backend="pandas"
chunk_size=1000

[sources.my_db.chat_message.incremental]
cursor_path="updated_at"
```
