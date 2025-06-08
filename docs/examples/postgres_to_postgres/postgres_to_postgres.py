"""
---
title: Load from Postgres to Postgres faster
description: Load data fast from Postgres to Postgres with ConnectorX & Arrow export as Parquet, normalizing and exporting as DuckDB, and attaching it to Postgres for bigger Postgres tables (GBs)
keywords: [connector x, pyarrow, zero copy, duckdb, postgres, initial load]
---

:::info
この例を提供してくれた [Simon Späti](https://github.com/sspaeti) に大いに感謝します。
:::

この例では、ConnectorX と DuckDB を使用して、Postgres から Postgres へデータを高速にエクスポートおよびインポートする方法を示します。
デフォルトのエクスポートでは、正規化フェーズで `Insert_statement` が生成されますが、これは大規模なテーブルでは非常に遅くなります。

これは初期ロードであるため、最初にタイムスタンプ付きの別のスキーマを作成し、その後、既存のスキーマを新しいスキーマに置き換えます。

:::note
このアプローチはテスト済みで、初期ロード (`--replace`) では適切に機能しますが、増分ロード (`--merge`) ではいくつかの調整が必要になる場合があります
 (dlt のロード テーブルのロード、初期ロード後の最初の実行のセットアップなど)。
:::

学習内容：

- [コネクタ X](https://github.com/sfu-db/connector-x) からアローテーブルを取得し、チャンク単位で生成する方法。
- アローテーブルでマージロードと増分ロードが機能すること。
- DuckDB を使用して高速な正規化を行う方法。
- `argparse` を使用してパイプラインスクリプトを CLI に変換する方法。
- `ConnectionStringCredentials` 仕様の使用方法。

`.dlt/secrets.toml` または dlt 環境変数でデータベース認証情報を定義し、テーブル名（"table_1" と "table_2"）を調整する必要があることに注意してください。

`dlt` を `duckdb` とともにインストールし、`connectorx`、Postgres アダプタ、プログレスバーツールもインストールします。

```sh
pip install "dlt[duckdb]" connectorx pyarrow psycopg2-binary alive-progress
```

例を実行します:

```sh
python postgres_to_postgres.py --replace
```

:::warn
注意: ナノ秒を含むTIMEデータ型に問題が発生しました。
詳細は[Slack](https://dlthub-community.slack.com/archives/C04DQA7JJN6/p1711579390028279?thread_ts=1711477727.553279&cid=C04DQA7JJN60)をご覧ください。

DuckDB拡張機能のインストール（[問題はこちら](https://github.com/duckdb/duckdb/issues/8035#issuecomment-2020803032)を参照）に加え、
データをPostgresにロードするために、Dockerfileに`postgres_scanner.duckdb_extension`を手動でインストールしました。
:::
"""

import argparse
import os
from dlt.common import pendulum
from typing import List

import connectorx as cx
import duckdb
import psycopg2

import dlt
from dlt.sources.credentials import ConnectionStringCredentials

CHUNKSIZE = int(
    os.getenv("CHUNKSIZE", 1000000)
)  # 1 mio rows works well with 1GiB RAM memory (if no parallelism)


def read_sql_x_chunked(conn_str: str, query: str, chunk_size: int = CHUNKSIZE):
    offset = 0
    while True:
        chunk_query = f"{query} LIMIT {chunk_size} OFFSET {offset}"
        data_chunk = cx.read_sql(
            conn_str,
            chunk_query,
            return_type="arrow2",
            protocol="binary",
        )
        yield data_chunk
        if data_chunk.num_rows < chunk_size:
            break  # No more data to read
        offset += chunk_size


@dlt.source(max_table_nesting=0)
def pg_resource_chunked(
    table_name: str,
    primary_key: List[str],
    schema_name: str,
    order_date: str,
    load_type: str = "merge",
    columns: str = "*",
    credentials: ConnectionStringCredentials = None,
):
    print(
        f"dlt.resource write_disposition: `{load_type}` -- ",
        "connection string:"
        f" postgresql://{credentials.username}:*****@{credentials.host}:{credentials.host}/{credentials.database}",
    )

    query = (  # Needed to have an idempotent query
        f"SELECT {columns} FROM {schema_name}.{table_name} ORDER BY {order_date}"
    )

    source = dlt.resource(  # type: ignore
        name=table_name,
        table_name=table_name,
        write_disposition=load_type,  # use `replace` for initial load, `merge` for incremental
        primary_key=primary_key,
        parallelized=True,
    )(read_sql_x_chunked)(
        credentials.to_native_representation(),  # Pass the connection string directly
        query,
    )

    if load_type == "merge":
        # Retrieve the last value processed for incremental loading
        source.apply_hints(incremental=dlt.sources.incremental(order_date))

    return source


def table_desc(table_name, pk, schema_name, order_date, columns="*"):
    return {
        "table_name": table_name,
        "pk": pk,
        "schema_name": schema_name,
        "order_date": order_date,
        "columns": columns,
    }


if __name__ == "__main__":
    # Input Handling
    parser = argparse.ArgumentParser(description="Run specific functions in the script.")
    parser.add_argument("--replace", action="store_true", help="Run initial load")
    parser.add_argument("--merge", action="store_true", help="Run delta load")
    args = parser.parse_args()

    source_schema_name = "example_data_1"
    target_schema_name = "example_data_2"
    pipeline_name = "loading_postgres_to_postgres"

    tables = [
        table_desc("table_1", ["pk"], source_schema_name, "updated_at"),
        table_desc("table_2", ["pk"], source_schema_name, "updated_at"),
    ]

    # default is initial loading (replace)
    load_type = "merge" if args.merge else "replace"
    print(f"LOAD-TYPE: {load_type}")

    resources = []
    for table in tables:
        resources.append(
            pg_resource_chunked(
                table["table_name"],
                table["pk"],
                table["schema_name"],
                table["order_date"],
                load_type=load_type,
                columns=table["columns"],
                credentials=dlt.secrets["sources.postgres.credentials"],
            )
        )

    if load_type == "replace":
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination="duckdb",
            dataset_name=target_schema_name,
            dev_mode=True,
            progress="alive_progress",
        )
    else:
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination="postgres",
            dataset_name=target_schema_name,
            dev_mode=False,
        )  # dev_mode=False

    # start timer
    startTime = pendulum.now()

    # 1. extract
    print("##################################### START EXTRACT ########")
    pipeline.extract(resources, loader_file_format="parquet")
    print(f"--Time elapsed: {pendulum.now() - startTime}")

    # 2. normalize
    print("##################################### START NORMALIZATION ########")
    if load_type == "replace":
        info = pipeline.normalize(
            workers=2,
        )  # https://dlthub.com/docs/blog/dlt-arrow-loading
    else:
        info = pipeline.normalize()

    print(info)
    print(pipeline.last_trace.last_normalize_info)
    print(f"--Time elapsed: {pendulum.now() - startTime}")

    # 3. load
    print("##################################### START LOAD ########")
    load_info = pipeline.load()
    print(load_info)
    print(f"--Time elapsed: {pendulum.now() - startTime}")

    # check that stuff was loaded
    row_counts = pipeline.last_trace.last_normalize_info.row_counts
    assert row_counts["table_1"] == 9
    assert row_counts["table_2"] == 9

    if load_type == "replace":
        # 4. Load DuckDB local database into Postgres
        print("##################################### START DUCKDB LOAD ########")
        # connect to local duckdb dump
        conn = duckdb.connect(f"{load_info.destination_displayable_credentials}".split(":///")[1])
        conn.sql("INSTALL postgres;")
        conn.sql("LOAD postgres;")
        # select generated timestamp schema
        timestamped_schema = conn.sql(
            f"""select distinct table_schema from information_schema.tables
                     where table_schema like '{target_schema_name}%'
                     and table_schema NOT LIKE '%_staging'
                     order by table_schema desc"""
        ).fetchone()[0]
        print(f"timestamped_schema: {timestamped_schema}")

        target_credentials = ConnectionStringCredentials(
            dlt.secrets["destination.postgres.credentials"]
        )
        # connect to destination (timestamped schema)
        conn.sql(
            "ATTACH"
            f" 'dbname={target_credentials.database} user={target_credentials.username} password={target_credentials.password} host={target_credentials.host} port={target_credentials.port}'"
            " AS pg_db (TYPE postgres);"
        )
        conn.sql(f"CREATE SCHEMA IF NOT EXISTS pg_db.{timestamped_schema};")

        for table in tables:
            print(
                f"LOAD DuckDB -> Postgres: table: {timestamped_schema}.{table['table_name']} TO"
                f" Postgres {timestamped_schema}.{table['table_name']}"
            )

            conn.sql(
                f"CREATE OR REPLACE TABLE pg_db.{timestamped_schema}.{table['table_name']} AS"
                f" SELECT * FROM {timestamped_schema}.{table['table_name']};"
            )
            conn.sql(
                f"SELECT count(*) as count FROM pg_db.{timestamped_schema}.{table['table_name']};"
            ).show()

        print(f"--Time elapsed: {pendulum.now() - startTime}")
        print("##################################### FINISHED ########")

        # check that stuff was loaded
        rows = conn.sql(
            f"SELECT count(*) as count FROM pg_db.{timestamped_schema}.{table['table_name']};"
        ).fetchone()[0]
        assert int(rows) == 9

        # 5. Cleanup and rename Schema
        print("##################################### RENAME Schema and CLEANUP ########")
        try:
            con_hd = psycopg2.connect(
                dbname=target_credentials.database,
                user=target_credentials.username,
                password=target_credentials.password,
                host=target_credentials.host,
                port=target_credentials.port,
            )
            con_hd.autocommit = True
            print(
                "Connected to HD-DB: "
                + target_credentials.host
                + ", DB: "
                + target_credentials.username
            )
        except Exception as e:
            print(f"Unable to connect to HD-database! The reason: {e}")

        with con_hd.cursor() as cur:
            # Drop existing target_schema_name
            print(f"Drop existing {target_schema_name}")
            cur.execute(f"DROP SCHEMA IF EXISTS {target_schema_name} CASCADE;")
            # Rename timestamped-target_schema_name to target_schema_name
            print(f"Going to rename schema {timestamped_schema} to {target_schema_name}")
            cur.execute(f"ALTER SCHEMA {timestamped_schema} RENAME TO {target_schema_name};")

        con_hd.close()
