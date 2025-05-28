---
title: Transforming data with SQL
description: Transforming the data loaded by a dlt pipeline with the dlt SQL client
keywords: [transform, sql]
---

# `dlt` SQL クライアントを使用したデータ変換

dbt のシンプルな代替方法として、`dlt` SQL クライアントを使用してデータをクエリし、Python の SQL 文を使用して変換を実行する方法があります。
`execute_sql` メソッドを使用すると、データベース スキーマやテーブル内のデータを変更する文も含め、任意の SQL 文を実行できます。
以下の例では、`customers` テーブルに行を挿入します。
構文は標準的な `dbapi` 接続と同じであることに注意してください。

:::info
* この方法は、`dlt` でサポートされているすべての SQL 出力先で機能しますが、ファイルシステム出力先では機能しません。
* SQL クライアントを使用してデータにアクセスする方法の詳細については、[SQL クライアントのドキュメント](../../ general-usage/dataset-access/dataset) を参照してください。
* 単にデータを読み取るだけの場合は、代わりに強力な [データセット インターフェース](../../general-usage/dataset-access/dataset) を使用する必要があります。
:::


通常、このタイプの変換は、Python 環境からデータを挿入することなく、既存のテーブルから直接テーブルを作成または更新できる場合に使用します。

以下の例では、カテゴリと地域ごとに合計売上と平均売上を含む新しいテーブル `aggregated_sales` を作成します。


```py
pipeline = dlt.pipeline(destination="duckdb", dataset_name="crm")

# NOTE: this is the duckdb sql dialect, other destinations may use different expressions
with pipeline.sql_client() as client:
    client.execute_sql(
        """ CREATE OR REPLACE TABLE aggregated_sales AS
            SELECT 
                category,
                region,
                SUM(amount) AS total_sales,
                AVG(amount) AS average_sales
            FROM 
                sales
            GROUP BY 
                category, 
                region;
    """)
```

`execute_sql` メソッドを使用して選択クエリを実行することもできます。
データは行のリストとして返され、行の要素は選択された列に対応します。
より便利なデータ抽出方法は、DLTデータセットを使用することです。

```py
try:
    with pipeline.sql_client() as client:
        res = client.execute_sql(
            "SELECT id, name, email FROM customers WHERE id = %s",
            10
        )
        # Prints column values of the first row
        print(res[0])
except Exception:
    ...
```

## その他の変換ツール

ロード前にデータを変換する場合は、Python を使用できます。
ロード後にデータを変換する場合は、SQL または次のいずれかを使用できます。

1. [dbt](dbt/dbt.md) (recommended).
2. [Python with DataFrames or Arrow tables](python.md).

