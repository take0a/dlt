---
title: Configuring the SQL Database source
description: configuring the pipeline script, connection, and backend settings in the sql_database source
keywords: [sql connector, sql database pipeline, sql database]
---

import Header from '../_source-info-header.md';

# 構成

<Header/>

## SQL データベースソースの構成

`dlt` ソースは、簡単にカスタマイズできるソース関数とリソース関数で構成された Python スクリプトです。SQL データベース検証済みソースには、次の組み込みソースとリソースがあります:

1. `sql_database`: SQL データベースから複数のテーブルとビューをロードするために使用できる `dlt` ソース。
2. `sql_table`: SQL データベースから単一のテーブルをロードする `dlt` リソース。

ソースとリソースの詳細については、こちらをご覧ください: [一般的な使用法: ソース](../../../general-usage/source.md) および [一般的な使用法: リソース](../../../general-usage/resource.md).

:::note NOTE
To see complete list of source arguments for `sql_database` [refer to the this section](#arguments-for-sql_database-source).
:::

### 使用例:

:::tip
私たちのソースは完全にハッキング可能なものになる予定です。ソースやリソースのソース コードを自由に変更して、ニーズに合わせてカスタマイズしてください。
:::

1. **データベースからすべてのテーブルをロードする**

    `sql_database()` を呼び出すと、データベースからすべてのテーブルがロードされます。

    ```py
    import dlt
    from dlt.sources.sql_database import sql_database

    def load_entire_database() -> None:
        # Define the pipeline
        pipeline = dlt.pipeline(
            pipeline_name="rfam",
            destination='synapse',
            dataset_name="rfam_data"
        )

        # Fetch all the tables from the database
        source = sql_database()

        # Run the pipeline
        info = pipeline.run(source, write_disposition="replace")

        # Print load info
        print(info)
    ```

2. **データベースから選択したテーブルをロードする**

    `sql_database(table_names=["family", "clan"])` または `sql_database().with_resources("family", "clan")` を呼び出すと、データベースからテーブル `"family"` と `"clan"` のみがロードされます。

    ```py
    import dlt
    from dlt.sources.sql_database import sql_database

    def load_select_tables_from_database() -> None:
        # Define the pipeline
        pipeline = dlt.pipeline(
            pipeline_name="rfam",
            destination="postgres",
            dataset_name="rfam_data"
        )

        # Fetch tables "family" and "clan"
        source = sql_database(table_names=['family', 'clan'])
        # or
        # source = sql_database().with_resources("family", "clan")

        # Run the pipeline
        info = pipeline.run(source)

        # Print load info
        print(info)

    ```

    :::note
    `sql_database` ソースを使用する場合、ソース引数でテーブル名を直接指定すると (例: `sql_database(table_names=["family", "clan"])`)、それらのテーブルのみが反映され、リソースに変換されます。対照的に、`.with_resources("family", "clan")` を使用する場合は、最初にスキーマ全体が反映され、指定されたテーブルをフィルタリングする前にすべてのテーブルのリソースが生成されます。大規模なスキーマの場合、`table_names` を指定するとパフォーマンスが向上する可能性があります。
    :::

3. **スタンドアロンテーブルをロードする**

    `sql_table(table="family")` を呼び出すと、テーブル `"family"` のみが取得されます。

    ```py
    import dlt
    from dlt.sources.sql_database import sql_table

    def load_select_tables_from_database() -> None:
        # Define the pipeline
        pipeline = dlt.pipeline(
            pipeline_name="rfam",
            destination="duckdb",
            dataset_name="rfam_data"
        )

        # Fetch the table "family"
        table = sql_table(table="family")

        # Run the pipeline
        info = pipeline.run(table)

        # Print load info
        print(info)

    ```

4. **`config.toml` でテーブルと列の選択を構成する**

   Python スクリプトの外部でテーブルと列の選択を管理するには、`config.toml` ファイルで直接構成することができます。この方法は、複数のテーブルを扱う場合や、構成をコードから分離しておく場合に特に便利です。

   以下は`config.toml`ファイルでテーブルと列の選択を定義する方法の例です。:

   ```toml
   # to select tables names
   [sources.sql_database]
   table_names = [
       "Table_Name_1",  
   ]

   # to select specific columns from table "Table_Name_1"
   [sources.sql_database.Table_Name_1]
   included_columns = [
       "Column_Name_1",
       "Column_Name_2"
   ]
   ```
   :::note
   *大文字と小文字の区別:* 
   
   `config.toml` で指定されたテーブル名と列名は、大文字と小文字が区別されるため、SQL データベース内の対応するものと完全に一致する必要があります。
   :::

## 接続の設定

### 接続文字列の形式

`sql_database` は SQLAlchemy を使用してデータベース接続を作成し、テーブル スキーマを反映します。[データベース URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) を使用して資格情報を渡すことができます。一般的な形式は次のとおりです。

```py
"dialect+database_type://username:password@server:port/database_name"
```

たとえば、`pymysql` 方言を使用して MySQL データベースに接続するには、次の接続文字列を使用できます。

```py
"mysql+pymysql://rfamro:PWD@mysql-rfam-public.ebi.ac.uk:4497/Rfam"
```

データベース固有のドライバーは、クエリ パラメーターを使用して接続文字列に渡すことができます。たとえば、ODBC ドライバーを使用して Microsoft SQL Server に接続するには、次のようにドライバーをクエリ パラメーターとして渡す必要があります:

```py
"mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"
```

### 接続資格情報を `dlt` パイプラインに渡す

`dlt`パイプラインに接続資格情報を追加するにはいくつかのオプションがあります:

#### 1. `secrets.toml` または環境変数として設定する (推奨)

`dlt` でサポートされている [任意の方法](../../../general-usage/credentials/setup#available-config-providers) を使用して資格情報を設定できます。`.dlt/secrets.toml` または環境変数を使用することをお勧めします。`secrets.toml` 内で資格情報を設定する方法については、[セットアップ](./setup) の手順 2 を参照してください。資格情報の受け渡しの詳細については、[こちら](../../../general-usage/credentials/setup) を参照してください。

#### 2. スクリプト内で直接渡す

ソース内で資格情報を明示的に渡すこともできます。例:

```py
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_database

credentials = ConnectionStringCredentials(
    "mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam"
)

source = sql_database(credentials).with_resources("family")
```

:::note
`.dlt/secrets.toml` で資格情報を設定し、パイプライン コードに機密情報を含めないようにすることをお勧めします。
:::

### その他の接続オプション

#### SqlAlchemy エンジンを認証情報として使用する

資格情報の代わりに SqlAlchemy エンジンのインスタンスを渡すこともできます:
```py
from dlt.sources.sql_database import sql_table
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam")
table = sql_table(engine, table="chat_message", schema="data")
```

このエンジンは、`dlt` によってデータベース接続を開くために使用され、複数のスレッドにまたがって動作できるため、dlt ソースおよびリソースの `parallelize` 設定と互換性があります。

## バックエンドの設定

テーブル バックエンドは、データベース テーブルからの行のストリームをさまざまな形式のバッチに変換します。デフォルトのバックエンドである `SQLAlchemy` は、Python 辞書を抽出して正規化する標準の `dlt` 動作に従います。これは、小さなテーブル、初期の開発作業、および最小限の依存関係または純粋な Python 環境が必要な場合に推奨されます。このバックエンドは最も低速でもあります。他のバックエンドは、テーブルの構造化データ形式を利用し、速度を大幅に向上させます。たとえば、`PyArrow` バックエンドは行を `Arrow` テーブルに変換します。これにより、パフォーマンスが向上し、正確なデータ型が保持されます。大きなテーブルには、このバックエンドを使用することをお勧めします。

### SQLAlchemy

`SQLAlchemy` バックエンド (デフォルト) は、テーブル データを Python 辞書のリストとして生成します。このデータは、通常の抽出および正規化の手順を経るため、追加の依存関係をインストールする必要はありません。これは最も堅牢 (任意の宛先で動作し、データ型を正しく表す) ですが、最も低速でもあります。`reflection_level="full_with precision"` を設定すると、正確なデータ型を `dlt` スキーマに渡すことができます。

### PyArrow

`PyArrow` バックエンドは、データを `Arrow` テーブルとして生成します。`SQLAlchemy` を使用して行をバッチで読み取りますが、その後すぐにそれらを `ndarray` に変換し、転置して、`Arrow` テーブルの列として設定します。このバックエンドは常にデータベース テーブルを完全に反映し、元の型を保持します (つまり、**decimal** / **numeric** データは精度を失うことなく抽出されます)。宛先が parquet ファイルを読み込む場合、このバックエンドは `dlt` ノーマライザーをスキップし、2 桁 (20 倍 - 30 倍) の速度向上が得られます。

:::note
To use the `backend="arrow"` configuration, you will need `numpy` installed. You can get another 20-30% speed increase by having `pandas` installed.
The library `numpy` is a required dependency of `pandas` and `pyarrow<18.0.0`. To have all required dependencies, we suggest using this command:

```sh
pip install dlt[sql_database] pyarrow numpy pandas
```
:::

```py
import dlt
import sqlalchemy as sa
from dlt.sources.sql_database import sql_database

pipeline = dlt.pipeline(
    pipeline_name="rfam_cx", destination="postgres", dataset_name="rfam_data_arrow"
)

def _double_as_decimal_adapter(table: sa.Table) -> sa.Table:
    """Emits decimals instead of floats."""
    for column in table.columns.values():
        if isinstance(column.type, sa.Float):
            column.type.asdecimal = False
    return table

sql_alchemy_source = sql_database(
    "mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam?&binary_prefix=true",
    backend="pyarrow",
    backend_kwargs={"tz": "UTC"},
    table_adapter_callback=_double_as_decimal_adapter
).with_resources("family", "genome")

info = pipeline.run(sql_alchemy_source)
print(info)
```

PyArrow でサポートされている `backend_kwargs` 内の `tz` パラメータの詳細については、[公式ドキュメント](https://arrow.apache.org/docs/python/generated/pyarrow.timestamp.html)を参照してください。

### Pandas

`pandas` バックエンドは、`pandas.io.sql` モジュールを使用して、データを DataFrames として生成します。`dlt` は、より安定した型を生成するため、デフォルトで `PyArrow` dtype を使用します。

デフォルト設定では、生成されたデータ フレーム内のいくつかのデータ型が dtype に強制変換されます:

* **decimal** は倍精度にマッピングされるため、精度が失われる可能性があります。
* **date** と **time** 文字列にマッピングされます。
* すべての型はnull可能です

:::note
`dlt` は、宛先テーブルを作成するときに、ソース データベースから反映されたデータ型を引き続き使用します。`pandas` バックエンドから生じる型の違いをどのように調整/解析するかは、宛先によって異なります。ほとんどの宛先では、日付/時刻文字列を解析し、倍精度を小数に変換できます (デフォルト設定では、小数の精度が失われることに注意してください)。 **ただし、ソース テーブルに日付、時刻、または小数点の列が含まれている場合は、** `pandas` **バックエンドを使用しないことを強くお勧めします。**
:::

内部的には、`dlt` は `pandas.io.sql._wrap_result` を使用して `pandas` フレームを生成します。[pandas 固有の設定](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_table.html) を調整するには、それを `backend_kwargs` パラメータに渡します。たとえば、以下では `coerce_float` を `False` に設定します:

```py
import dlt
import sqlalchemy as sa
from dlt.sources.sql_database import sql_database

pipeline = dlt.pipeline(
    pipeline_name="rfam_cx", destination="postgres", dataset_name="rfam_data_pandas_2"
)

def _double_as_decimal_adapter(table: sa.Table) -> sa.Table:
    """Emits decimals instead of floats."""
    for column in table.columns.values():
        if isinstance(column.type, sa.Float):
            column.type.asdecimal = True
    return table

sql_alchemy_source = sql_database(
    "mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam?&binary_prefix=true",
    backend="pandas",
    table_adapter_callback=_double_as_decimal_adapter,
    chunk_size=100000,
    # set coerce_float to False to represent them as string
    backend_kwargs={"coerce_float": False, "dtype_backend": "numpy_nullable"},
).with_resources("family", "genome")

info = pipeline.run(sql_alchemy_source)
print(info)
```

### ConnectorX

[`ConnectorX`](https://sfu-db.github.io/connector-x/intro.html) バックエンドは、テーブル行の読み取り時に `SQLALchemy` を完全にスキップし、Rust で読み取ります。これは、他のどの方法よりも大幅に高速であるとされています (PostgreSQL でのみ検証済み)。デフォルト設定では、`PyArrow` テーブルが出力されますが、`backend_kwargs` で `return_type` を指定することでこれを構成できます。(構成可能なパラメーターの完全なリストについては、[`ConnectorX` ドキュメント](https://sfu-db.github.io/connector-x/api.html) を参照してください。)

このバックエンドを使用する場合、一定の制限があります:

* `chunk_size` は無視されます。`ConnectorX` はバッチでデータを生成できません。
* 多くの場合、`SQLAlchemy` 接続文字列とは異なる接続文字列が必要です。これを設定するには、`backend_kwargs` の `conn` 引数を使用します。
* **decimal** を **double** に変換するため、精度が失われます。
* 列の NULL 可能性は無視されます (常に true)。
* データ型ごとに異なるマッピングを使用します。(詳細については、[こちら](https://sfu-db.github.io/connector-x/databases.html)を参照してください。)
* JSON フィールド (少なくとも PostgreSQL からのもの) は文字列で二重にラップされています。これをラップ解除するには、組み込みの変換関数 `unwrap_json_connector_x` を渡します (たとえば、`add_map` を使用)。

    ```py
    from dlt.sources.sql_database.helpers import unwrap_json_connector_x
    ```

:::note
`dlt` は、宛先テーブルを作成するときに、ソース データベースから反映されたデータ型を引き続き使用します。 型の違いを調整/解析するのは宛先次第です。 デフォルト設定では、小数の精度が失われることに注意してください。
:::

```py
"""This example is taken from the benchmarking tests for ConnectorX performed on the UNSW_Flow dataset (~2mln rows, 25+ columns). Full code here: https://github.com/dlt-hub/sql_database_benchmarking"""
import os
import dlt
from dlt.destinations import filesystem
from dlt.sources.sql_database import sql_table

unsw_table = sql_table(
    "postgresql://loader:loader@localhost:5432/dlt_data",
    "unsw_flow_7",
    "speed_test",
    # this is ignored by connectorx
    chunk_size=100000,
    backend="connectorx",
    # keep source data types
    reflection_level="full_with_precision",
    # just to demonstrate how to set up a separate connection string for connectorx
    backend_kwargs={"conn": "postgresql://loader:loader@localhost:5432/dlt_data"}
)

pipeline = dlt.pipeline(
    pipeline_name="unsw_download",
    destination=filesystem(os.path.abspath("../_storage/unsw")),
    progress="log",
    dev_mode=True,
)

info = pipeline.run(
    unsw_table,
    dataset_name="speed_test",
    table_name="unsw_flow",
    loader_file_format="parquet",
)
print(info)
```

上記のデータセットとローカル PostgreSQL インスタンスを使用すると、`ConnectorX` バックエンドは `PyArrow` バックエンドよりも 2 倍高速になります。

## Arguments for `sql_database` source
The following arguments can be used with the `sql_database` source:
    
    `credentials` (Union[ConnectionStringCredentials, Engine, str]): Database credentials or an `sqlalchemy.Engine` instance.
    
    `schema` (Optional[str]): Name of the database schema to load (if different from default).
    
    `metadata` (Optional[MetaData]): Optional `sqlalchemy.MetaData` instance. `schema` argument is ignored when this is used.
    
    `table_names` (Optional[List[str]]): A list of table names to load. By default, all tables in the schema are loaded.
    
    `chunk_size` (int): Number of rows yielded in one batch. SQL Alchemy will create additional internal rows buffer twice the chunk size.
    
    `backend` (TableBackend): Type of backend to generate table data. One of: "sqlalchemy", "pyarrow", "pandas" and "connectorx".

        - "sqlalchemy" yields batches as lists of Python dictionaries, "pyarrow" and "connectorx" yield batches as arrow tables, "pandas" yields panda frames.

        - "sqlalchemy" is the default and does not require additional dependencies, 

        - "pyarrow" creates stable destination schemas with correct data types,

        - "connectorx" is typically the fastest but ignores the "chunk_size" so you must deal with large tables yourself.
    
    `detect_precision_hints` (bool): Deprecated. Use `reflection_level`. Set column precision and scale hints for supported data types in the target schema based on the columns in the source tables. This is disabled by default.
    
    `reflection_level`: (ReflectionLevel): Specifies how much information should be reflected from the source database schema.

        - "minimal": Only table names, nullability and primary keys are reflected. Data types are inferred from the data. This is the default option.

        - "full": Data types will be reflected on top of "minimal". `dlt` will coerce the data into reflected types if necessary.

        - "full_with_precision": Sets precision and scale on supported data types (ie. decimal, text, binary). Creates big and regular integer types.
    
    `defer_table_reflect` (bool): Will connect and reflect table schema only when yielding data. Requires table_names to be explicitly passed.
        Enable this option when running on Airflow. Available on dlt 0.4.4 and later.
    
    `table_adapter_callback`: (Callable): Receives each reflected table. May be used to modify the list of columns that will be selected.
    
    `backend_kwargs` (**kwargs): kwargs passed to table backend ie. "conn" is used to pass specialized connection string to connectorx.
    
    `include_views` (bool): Reflect views as well as tables. Note view names included in `table_names` are always included regardless of this setting. This is set to false by default.
    
    `type_adapter_callback`(Optional[Callable]): Callable to override type inference when reflecting columns.
        Argument is a single sqlalchemy data type (`TypeEngine` instance) and it should return another sqlalchemy data type, or `None` (type will be inferred from data)
    
    `query_adapter_callback`(Optional[Callable[Select, Table], Select]): Callable to override the SELECT query used to fetch data from the table. The callback receives the sqlalchemy `Select` and corresponding `Table`, 'Incremental` and `Engine` objects and should return the modified `Select` or `Text`.
    
    `resolve_foreign_keys` (bool): Translate foreign keys in the same schema to `references` table hints.
        May incur additional database calls as all referenced tables are reflected.
    
    `engine_adapter_callback` (Callable[[Engine], Engine]): Callback to configure, modify and Engine instance that will be used to open a connection ie. to set transaction isolation level.
