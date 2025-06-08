"""
---
title: Load mysql table with ConnectorX & Arrow
description: Load data from sql queries fast with connector x and arrow tables
keywords: [connector x, pyarrow, zero copy]
---

以下のサンプルスクリプトは、パブリック **mysql** インスタンスからゲノムデータを取得し、それを **duckdb** にロードします。
出力先は parquet ファイルのロードをサポートしている必要があります。
これは、`dlt` が Arrow テーブルを保存するために使用する形式です。
[Connector X](https://github.com/sfu-db/connector-x) を使用すると、いくつかの一般的なデータベースからデータを取得し、
メモリ内に Arrow テーブルを作成します。`dlt` はこれをロードパッケージに保存し、出力先にロードします。

:::tip
データが大きく、負荷を分割する必要がある場合は、複数のテーブルを作成できます。
:::

学習内容：

- [コネクタX](https://github.com/sfu-db/connector-x) からアローテーブルを取得し、それをyieldする方法。
- アローテーブルでマージロードと増分ロードが機能すること。
- 効率的なデータ抽出のために [増分ロード](../general-usage/incremental-loading) を有効にする方法。
- 組み込みのConnectionString認証情報を使用する方法。

"""

import connectorx as cx

import dlt
from dlt.sources.credentials import ConnectionStringCredentials


def read_sql_x(
    conn_str: ConnectionStringCredentials = dlt.secrets.value,
    query: str = dlt.config.value,
):
    yield cx.read_sql(
        conn_str.to_native_representation(),
        query,
        return_type="arrow2",
        protocol="binary",
    )


def genome_resource():
    # create genome resource with merge on `upid` primary key
    genome = dlt.resource(
        name="genome",
        write_disposition="merge",
        primary_key="upid",
    )(read_sql_x)(
        "mysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam",  # type: ignore[arg-type]
        "SELECT * FROM genome ORDER BY created LIMIT 1000",
    )
    # add incremental on created at
    genome.apply_hints(incremental=dlt.sources.incremental("created"))
    return genome


if __name__ == "__main__":
    pipeline = dlt.pipeline(destination="duckdb")
    genome = genome_resource()

    load_info = pipeline.run(genome)
    print(load_info)
    print(pipeline.last_trace.last_normalize_info)
    # NOTE: run pipeline again to see that no more records got loaded thanks to incremental loading

    # check that stuff was loaded
    row_counts = pipeline.last_trace.last_normalize_info.row_counts
    assert row_counts["genome"] == 1000
