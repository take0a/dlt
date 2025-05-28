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

## `sql_database` ソースの引数

`sql_database` ソースでは次の引数を使用できます。
    
    `credentials` (Union[ConnectionStringCredentials, Engine, str]): データベース資格情報または `sqlalchemy.Engine` インスタンス。
    
    `schema` (Optional[str]): ロードするデータベーススキーマ名（デフォルトと異なる場合）。

    `metadata` (Optional[MetaData]): オプションの `sqlalchemy.MetaData` インスタンス。これを使用する場合、`schema` 引数は無視されます。

    `table_names` (Optional[List[str]]): ロードするテーブル名のリスト。デフォルトでは、スキーマ内のすべてのテーブルがロードされます。

    `chunk_size` (int): 1回のバッチで生成される行数。SQL Alchemy はチャンクサイズの2倍のサイズの追加内部行バッファを作成します。
    
    `backend` (TableBackend): テーブルデータを生成するバックエンドの種類。"sqlalchemy"、"pyarrow"、"pandas"、"connectorx" のいずれかです。

        - "sqlalchemy" はバッチを Python 辞書のリストとして生成します。"pyarrow" と "connectorx" はバッチをアローテーブルとして生成します。"pandas" は panda frame として生成します。

        - "sqlalchemy" はデフォルトであり、追加の依存関係は必要ありません。

        - "pyarrow" は正しいデータ型で安定した出力先スキーマを作成します。

        - "connectorx" は通常最も高速ですが、"chunk_size" を無視するため、大きなテーブルを扱う場合は自分で処理する必要があります。
    
    `detect_precision_hints` (bool): 非推奨です。`reflection_level` を使用してください。ソーステーブルの列に基づいて、ターゲットスキーマでサポートされているデータ型の列精度とスケールヒントを設定します。これはデフォルトで無効になっています。
    
    `reflection_level`: (ReflectionLevel): ソースデータベーススキーマからどの程度の情報を反映するかを指定します。

        - "minimal": テーブル名、NULL値許容、主キーのみが反映されます。データ型はデータから推測されます。これがデフォルトのオプションです。

        - "full": データ型は "minimal" に加算されて反映されます。`dlt` は必要に応じて、データを反映された型に変換します。

        - "full_with_precision": サポートされているデータ型（例：decimal、text、binary）の精度とスケールを設定します。big integer型とregular integer型を作成します。
    
    `defer_table_reflect` (bool): データ出力時にのみテーブルスキーマに接続し、反映します。table_names を明示的に渡す必要があります。
    Airflow で実行する場合は、このオプションを有効にしてください。dlt 0.4.4 以降で利用可能です。

    `table_adapter_callback`: (呼び出し可能): 反映される各テーブルを受け取ります。選択される列のリストを変更するために使用できます。

    `backend_kwargs` (**kwargs): テーブルバックエンドに渡されるキーワード。例えば、"conn" は connectorx に特殊な接続文字列を渡すために使用されます。

    `include_views` (bool): テーブルだけでなくビューも反映します。`table_names` に含まれるビュー名は、この設定に関わらず常に含まれることに注意してください。デフォルトでは false に設定されています。

    `type_adapter_callback`(Optional[Callable]): 列を反映する際の型推論をオーバーライドするために呼び出し可能。
    引数は単一の sqlalchemy データ型（`TypeEngine` インスタンス）であり、別の sqlalchemy データ型を返すか、`None`（型はデータから推測されます）を返す必要があります。

    `query_adapter_callback`(Optional[Callable[Select, Table], Select]): テーブルからデータを取得するために使用される SELECT クエリをオーバーライドするための呼び出し可能オブジェクトです。コールバックは sqlalchemy の `Select` と、対応する `Table`、'Incremental`、および `Engine` オブジェクトを受け取り、変更された `Select` または `Text` を返す必要があります。

    `resolve_foreign_keys` (bool): 同じスキーマ内の外部キーを `references` テーブルヒントに変換します。
    参照されているすべてのテーブルが反映されるため、追加のデータベース呼び出しが発生する可能性があります。

    `engine_adapter_callback` (Callable[[Engine], Engine]): 接続を開くために使用される Engine インスタンスを設定、変更するためのコールバックです。トランザクション分離レベルを設定します。
