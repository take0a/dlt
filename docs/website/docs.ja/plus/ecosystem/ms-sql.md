---
title: "Source: MS SQL replication"
description: MS SQL replication
keywords: [MSSQL, CDC, Change Tracking, MSSQL replication]
---

# MS SQL レプリケーション

dlt+ は、CDC に類似したソリューションである [変更追跡](https://learn.microsoft.com/en-us/sql/relational-databases/track-changes/about-change-tracking-sql-server) を使用して、MS SQL Server テーブルを同期するための包括的なソリューションを提供します。
SQL Server のネイティブな変更追跡機能を活用することで、挿入、更新、削除などの増分データ変更を効率的に同期先に読み込むことができます。

## 前提条件

変更追跡は明示的に有効化する必要があるため、開始する前に、データベースと追跡対象のテーブルの両方で変更追跡が有効になっていることを確認してください。

### データベースで変更追跡を有効にする

データベースで変更追跡を有効にするには、次のSQLコマンドを実行します。

```sql
ALTER DATABASE [YourDatabaseName]
SET CHANGE_TRACKING = ON
(CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);
```

- `[YourDatabaseName]`: 実際のデータベース名に置き換えます。
- `CHANGE_RETENTION`: 変更追跡情報の保持期間を指定します。この例では7日間に設定されています。
- `AUTO_CLEANUP`: ONに設定すると、保持期間を過ぎた変更追跡情報は自動的に削除されます。

### テーブルの変更追跡を有効にする

追跡するテーブルごとに、以下のコマンドを実行します:

```sql
ALTER TABLE [YourSchemaName].[YourTableName]
ENABLE CHANGE_TRACKING
WITH (TRACK_COLUMNS_UPDATED = ON);
```

- `[YourSchemaName].[YourTableName]`: スキーマ名とテーブル名に置き換えてください。
- `TRACK_COLUMNS_UPDATED`: ONに設定すると、行内で更新された列を確認できます。
このレベルの詳細が必要ない場合はOFFに設定してください。

### dlt+ とドライバーのセットアップ

* [インストールガイド](../getting-started/installation.md) に従って dlt+ がインストールされていることを確認してください。

* 公式の [手順](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16) に従って、Microsoft ODBC Driver for SQL Server をインストールしてください。

必要に応じて、[Python ライブラリの代替](https://www.pymssql.org/) もご利用いただけます。

* [sql_database ソースの手順](../../dlt-ecosystem/verified-sources/sql_database/setup) に従って、SQL Server 接続の資格情報を指定してください。


## パイプラインの設定

このプロセスは主に2つのステップで構成されます。

1. **初期フルロード**: `sql_table` 関数を使用して、テーブルデータの完全なバックフィルを実行します。
2. **増分ロード**: `create_change_tracking_table` 関数を使用して、SQL Server の変更追跡機能を利用した増分変更をロードします。

このアプローチにより、初期ロードから完全なデータセットが確保され、その後の変更に合わせて効率的に更新されます。

### 初期フルロード

**初期ロードを実行する前に**、変更追跡バージョンを取得して、ロード中に発生する可能性のある更新を見逃さないようにしてください。
これにより、ロード中に発生したいくつかの変更が「再現」される可能性がありますが、`merge`書き込み処理のため、宛先データには影響しません。

```py
from dlt_plus.sources.mssql import get_current_change_tracking_version
from sqlalchemy import create_engine

connection_url = "mssql+pyodbc://username:password@your_server:port/YourDatabaseName?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(connection_url)

tracking_version = get_current_change_tracking_version(engine)
```

重複を完全に回避するには、初期ロード中にテーブルを完全にロックします。

これで、`sql_table` リソースを使用して初期バックフィルを実行できます:

```py
import dlt
from dlt.sources.sql_database import sql_table

# Initial full load
initial_resource = sql_table(
    credentials=engine,
    schema=schema_name,
    table=table_name,
    reflection_level="full",
    write_disposition="merge",
)

pipeline = dlt.pipeline(
    pipeline_name='sql_server_sync_pipeline',
    destination='your_destination',
    dataset_name='destination_dataset',
)

# Run the pipeline for initial load
pipeline.run(initial_resource)
```

デフォルトでは、`_DLT_DELETED` 列または `_DLT_SYS_CHANGE_VERSION` 列は、変更があった場合にのみ増分変更追跡リソースによって作成されます。
これらの列を初期ロード中に作成する場合は、パイプラインを実行する前に次のように `apply_hints` を使用して設定できます:

```py
initial_resource.apply_hints(
        columns=[
            {"name": "_dlt_sys_change_version", "data_type": "bigint"},
            {"name": "_dlt_deleted", "data_type": "text", "precision": 10},
        ]
    )
```

次に、`create_change_tracking_table` 関数を使用して初回実行用の増分リソースを設定し、**1 回** 実行します。

```py
from dlt_plus.sources.mssql import create_change_tracking_table

# Optional: Configure engine isolation level
# use it if you create an Engine implicitly
def configure_engine_isolation_level(engine):
    return engine.execution_options(isolation_level="SERIALIZABLE")

incremental_resource = create_change_tracking_table(
    credentials=engine,
    table=table_name,
    schema=schema_name,
    initial_tracking_version=tracking_version,
    engine_adapter_callback=configure_engine_isolation_level,
)

pipeline.run(incremental_resource)
```

初めて実行する際は、`initial_tracking_version` 引数に `tracking_version` を渡す必要があります。
これにより、増分読み込みが初期化され、更新されたトラッキングバージョンが dlt 状態に保持されます。
以降の実行では、初期値を指定する必要はありません。

### 増分ロード

初期ロード後、SQL Server の `CHANGETABLE` 関数を使用して、スケジュールに従って `create_change_tracking_table` リソースを実行し、最後の追跡バージョン以降の変更のみをロードできます。
`initial_tracking_version` は自動的に dlt 状態に保存されるため、渡す必要はありません。

```py
from dlt_plus.sources.mssql import create_change_tracking_table

incremental_resource = create_change_tracking_table(
    credentials=engine,
    table=table_name,
    schema=schema_name,
)
pipeline.run(incremental_resource)
```

:::note
`write_disposition` はデフォルトで `merge` に設定されており、主キーに基づいて upsert を処理します。
これは、新しいデータがロードされる際、特に重複、更新、削除に関して、動作を決定します。
:::

## 完全なコード例

<details>

<summary>完全なコード例を表示</summary>

```py
import dlt

from sqlalchemy import create_engine

from dlt.sources.sql_database import sql_table
from dlt_plus.sources.mssql import (
    create_change_tracking_table,
    get_current_change_tracking_version,
)


def single_table_initial_load(connection_url: str, schema_name: str, table_name: str) -> None:
    """Performs an initial full load and sets up tracking version and incremental loads"""
    # Create a new pipeline
    pipeline = dlt.pipeline(
        pipeline_name=f"{schema_name}_{table_name}_sync",
        destination="duckdb",
        dataset_name=schema_name,
    )

    # Explicit database connection
    engine = create_engine(connection_url, isolation_level="SNAPSHOT")

    # Initial full load
    initial_resource = sql_table(
        credentials=engine,
        schema=schema_name,
        table=table_name,
        reflection_level="full",
        write_disposition="merge",
    )

    # Get the current tracking version before you run the pipeline to make sure
    # you do not miss any records
    tracking_version = get_current_change_tracking_version(engine)
    print(f"will track from: {tracking_version}")  # noqa

    # Apply hints to create _DLT_DELETED and _DLT_SYS_CHANGE_VERSION columns on the initial load
    # This is an optional step
    initial_resource.apply_hints(
        columns=[
            {"name": "_dlt_sys_change_version", "data_type": "bigint"},
            {"name": "_dlt_deleted", "data_type": "text", "precision": 10},
        ]
    )

    # Run the pipeline for the initial load
    # NOTE: we always drop data and state from the destination on initial load
    print(pipeline.run(initial_resource, refresh="drop_resources"))  # noqa

    # Incremental loading resource
    incremental_resource = create_change_tracking_table(
        credentials=engine,
        table=table_name,
        schema=schema_name,
        initial_tracking_version=tracking_version,
    )

    # Run the pipeline for incremental load
    print(pipeline.run(incremental_resource))  # noqa


def single_table_incremental_load(connection_url: str, schema_name: str, table_name: str) -> None:
    """Continues loading incrementally"""
    # Make sure you use the same pipeline and dataset names in order to continue incremental
    # loading.
    pipeline = dlt.pipeline(
        pipeline_name=f"{schema_name}_{table_name}_sync",
        destination="duckdb",
        dataset_name=schema_name,
    )

    engine = create_engine(connection_url, isolation_level="SNAPSHOT")
    # We do not need to pass the tracking version anymore
    incremental_resource = create_change_tracking_table(
        credentials=engine,
        table=table_name,
        schema=schema_name,
    )
    print(pipeline.run(incremental_resource))  # noqa


if __name__ == "__main__":
    # Change Tracking already enabled here
    test_db = "my_database83ed099d2d98a3ccfa4beae006eea44c"
    # A test run with a local mssql instance
    connection_url = (
        f"mssql+pyodbc://sa:Strong%21Passw0rd@localhost:1433/{test_db}"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    single_table_initial_load(
        connection_url,
        "my_dlt_source",
        "app_user",
    )
    single_table_incremental_load(
        connection_url,
        "my_dlt_source",
        "app_user",
    )
```

</details>



## 変更追跡クエリについて

増分読み込みプロセスでは、CHANGETABLE関数とソーステーブルを結合して最新の変更を取得するSQLクエリを使用します。
クエリの簡略版を以下に示します:

```sql
SELECT
    [Columns],
    ct.SYS_CHANGE_VERSION AS _dlt_sys_change_version,
    CASE WHEN ct.SYS_CHANGE_OPERATION = 'D' THEN 'DELETE' ELSE NULL END AS _dlt_deleted
FROM
    CHANGETABLE(CHANGES [YourSchemaName].[YourTableName], @last_version) AS ct
    LEFT JOIN [YourSchemaName].[YourTableName] AS t
        ON ct.[PrimaryKey] = t.[PrimaryKey]
WHERE
    ct.SYS_CHANGE_VERSION > @last_version
ORDER BY
    ct.SYS_CHANGE_VERSION ASC
```

- *CHANGETABLE*: 指定されたテーブルにおける、最後の追跡バージョン以降の変更を取得します。
- **ソーステーブルとの結合**: 結合により、変更された行の現在のデータが取得されます。
- *SYS_CHANGE_VERSION*: 変更の追跡と順序付けに使用されます。
- *_dlt_deleted*: 行が削除されたかどうかを示します。

:::note
クエリは本番環境のテーブルと結合するため、ロックやパフォーマンスに影響が出る可能性があります。
データベースが追加の負荷を処理できることを確認し、必要に応じて分離レベルを検討してください。
:::


## Full refresh

:::warning
完全更新を実行すると、宛先テーブルがドロップされ、つまり宛先からデータが削除され、追跡バージョンを保持している状態がリセットされます。
:::

フル ロードを再度実行し、run メソッドに `drop_resources` を渡すことで、完全な更新をトリガーできます ([パイプライン構成](../../general-usage/pipeline#selectively-drop-tables-and-resource-state-with-drop_resources) で説明されているとおり)。

```py
pipeline.run(initial_resource, refresh="drop_resources")
```


## 削除の処理

削除の処理方法を設定するために、`create_change_tracking_table` に渡すことができるオプションパラメータがあります。

```py
from dlt_plus.sources.mssql import create_change_tracking_table

incremental_resource = create_change_tracking_table(
    credentials=engine,
    table=table_name,
    schema=schema_name,
    hard_delete=True,
)
pipeline.run(incremental_resource)
```

### ハード削除

デフォルトでは、`hard_delete` は `True` に設定されており、ハード削除が実行されます。つまり、ソースで削除された行は、ターゲットからも完全に削除されます。

レプリケートされたデータでは、レコードが削除された際に、NULL 値が許可されない列に NULL が許容されます。
削除された行を保持するテーブルの追加や追加のマージ手順を回避するため、dlt はステージングデータセットにのみ保存されるプレースホルダ値を出力します。

### ソフト削除

`hard_delete` が `False` に設定されている場合、ソフト削除が実行されます。つまり、ソースで削除された行は削除済みとしてマークされますが、デスティネーションからは物理的に削除されません。

この場合、デスティネーションスキーマはレプリケートされた列に対して NULL を受け入れる必要があるため、`sql_table` リソースに `remove_nullability_adapter` アダプタを必ず渡してください。

```py
from dlt_plus.sources.mssql import remove_nullability_adapter

table = sql_table(
    table_adapter_callback=remove_nullability_adapter,
)
```

