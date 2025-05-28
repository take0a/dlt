---
title: Add incremental configuration to SQL resources
description: Incremental SQL data loading strategies
keywords: [how to, load data incrementally from SQL]
slug: sql-incremental-configuration
---

# SQL リソースに増分設定を追加する

増分読み込みとは、新規または変更されたデータのみを読み込み、既に読み込まれている古いレコードは読み込まない操作です。
例えば、銀行は最新の取引のみを読み込み、企業は新規または変更されたユーザー情報でデータベースを更新します。
この記事では、いくつかの増分読み込み戦略について説明します。

:::important
データを段階的に、またはバッチで処理すると、効率が向上し、コストが削減され、待ち時間が短縮され、スケーラビリティが向上し、リソースの使用率が最適化されます。
:::

### 増分ロード戦略

このガイドでは、`dlt` を使用したさまざまな増分ロード手法について説明します。具体的には以下のとおりです:

| S.No. | Strategy | Description |
| --- | --- | --- |
| 1. | Full load (replace) |既存のデータを新しい/更新されたデータセットで完全に上書きします。|
| 2. | Append new records based on Incremental ID |増分 ID に基づいて新しいレコードのみをテーブルに追加します。 |
| 3. | Append new records based on date ("created_at") | 日付フィールドに基づいて、新しいレコードのみをテーブルに追加します。 |
| 4. | Merge (Update/Insert) records based on timestamp ("last_modified_at") and ID | 複合IDキーとタイムスタンプフィールドに基づいてレコードをマージします。必要に応じて既存のレコードを更新し、新しいレコードを挿入します。 |

## Code examples



### 1. Full load (replace)

フルロード戦略では、既存のデータが新しいデータセットで完全に上書きされます。これは、テーブル全体を最新のデータで更新したい場合に便利です。

:::note
この戦略は技術的には新しいデータのみをロードするのではなく、古いデータと新しいデータをすべて再ロードします。
:::

以下に手順を説明します。

1. SQL ソース内の「contact」という名前の初期テーブルは次のようになります:

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 |
    | 2 | Bob | 2024-07-02 |

2. このPythonコードは、`dlt`パイプラインを使用してSQLソースからBigQueryにデータをロードするプロセスを示しています。以下で使用されている`write_disposition = "replace"`にご注意ください。

    ```py
    def load_full_table_resource() -> None:
        """Load a full table, replacing existing data."""
        pipeline = dlt.pipeline(
            pipeline_name="mysql_database",
            destination='bigquery',
            dataset_name="dlt_contacts"
        )

        # Load the full table "contact"
        source = sql_database().with_resources("contact")

        # Run the pipeline
        info = pipeline.run(source, write_disposition="replace")

        # Print the info
        print(info)

    load_full_table_resource()
    ```

3. `dlt` パイプラインを実行すると、BigQuery の「contact」テーブルにロードされたデータは次のようになります:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 | 1721878309.021546 | tgyMM73iMz0cQg |
    | 2 | 2 | Bob | 2024-07-02 | 1721878309.021546 | 88P0bD796pXo/Q |

4. 次に、SQLソースの「contact」テーブルが更新されます。2つの新しい行が追加され、 `id = 2` の行が削除されます。
更新されたデータソース（「contact」テーブル）は次のようになります:

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 |
    | 3 | Charlie | 2024-07-03 |
    | 4 | Dave | 2024-07-04 |

5. パイプラインを再度実行した後、BigQuery に作成された「contact」テーブル:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 | 1721878309.021546 | S5ye6fMhYECZA |
    | 2 | 3 | Charlie | 2024-07-03 | 1721878309.021546 | eT0zheRx9ONWuQ |
    | 3 | 4 | Dave | 2024-07-04 | 1721878309.021546 | gtflF8BdL2NO/Q |

**何が起こったか？**

パイプラインを実行すると、「contact」テーブルの元のデータ（AliceとBob）が、新しい更新されたテーブルに完全に置き換えられます。このテーブルには「Charlie」と「Dave」のデータが追加され、「Bob」のデータは削除されています。この戦略は、データセット全体を最新の情報に更新または置き換える必要があるシナリオで役立ちます。

### 2. 増分IDに基づいて新しいレコードを追加する

この戦略では、増分IDに基づいて、新しいレコードのみをテーブルに追加します。
これは、新しいレコードごとに一意の増分IDが割り当てられているシナリオで役立ちます。

手順は以下のとおりです:

1. SQL ソース内の「contact」という名前の初期テーブルは次のようになります:

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 |
    | 2 | Bob | 2024-07-02 |

2. この Python コードは、増分変数 `id` を使用して SQL ソースから BigQuery にデータをロードする方法を示しています。
この変数は、`dlt` パイプライン内の新規または更新されたレコードを追跡します。以下で使用されている `write_disposition = "append"` に注意してください。

    ```py
    def load_incremental_id_table_resource() -> None:
        """Load a table incrementally based on an ID."""
        pipeline = dlt.pipeline(
            pipeline_name="mysql_database",
            destination='bigquery',
            dataset_name="dlt_contacts",
        )

        # Load table "contact" incrementally based on ID
        source = sql_database().with_resources("contact")
        source.contact.apply_hints(incremental=dlt.sources.incremental("id"))

        # Run the pipeline with append write disposition
        info = pipeline.run(source, write_disposition="append")

        # Print the info
        print(info)
    ```

3. `dlt` パイプラインを実行すると、BigQuery の「contact」テーブルにロードされたデータは次のようになります:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 | 1721878309.021546 | YQfmAu8xysqWmA |
    | 2 | 2 | Bob | 2024-07-02 | 1721878309.021546 | Vcb5KKah/RpmQw |

4. 次に、SQLソースの「contact」テーブルが更新されます。2つの新しい行が追加され、`id = 2` の行が削除されます。更新されたデータソースは次のようになります。

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 |
    | 3 | Charlie | 2024-07-03 |
    | 4 | Dave | 2024-07-04 |

5. パイプラインを再度実行した後、BigQuery に作成された「contact」テーブル:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 | 1721878309.021546 | OW9ZyAzkXg4D4w |
    | 2 | 2 | Bob | 2024-07-02 | 1721878309.021546 | skVYZ/ppQuztUg |
    | 3 | 3 | Charlie | 2024-07-03 | 1721878309.021546 | y+T4Q2JDnR33jg |
    | 4 | 4 | Dave | 2024-07-04 | 1721878309.021546 | MAXrGhNNADXAiQ |

**何が起こったか？**

このシナリオでは、パイプラインは既存のエントリに影響を与えることなく、既存のデータ（Alice と Bob）に新しいレコード（Charlie と Dave）を追加します。この戦略は、履歴データを保持しながら新しいデータのみを追加する必要がある場合に最適です。

### タイムスタンプ（"created_at"）に基づいて新しいレコードを追加する

この戦略では、日付/タイムスタンプフィールドに基づいて、新しいレコードのみをテーブルに追加します。これは、レコードがタイムスタンプ付きで作成され、特定の日付以降に作成されたレコードのみをロードしたい場合に便利です。

手順は以下のとおりです:

1. SQLソース内の「contact」という名前の初期データセットは次のようになります:

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 00:00:00 |
    | 2 | Bob | 2024-07-02 00:00:00 |

2. Pythonコードは、`dlt`パイプラインを使用してSQLソースからBigQueryにデータをロードするプロセスを示しています。`write_disposition = "append"`と、増分パラメータとして`created_at`が使用されていることに注意してください。

    ```py
    def load_incremental_timestamp_table_resource() -> None:
        """Load a table incrementally based on created_at timestamp."""
        pipeline = dlt.pipeline(
            pipeline_name="mysql_databasecdc",
            destination='bigquery',
            dataset_name="dlt_contacts",
        )

        # Load table "contact", incrementally starting at a given timestamp
        source = sql_database().with_resources("contact")
        source.contact.apply_hints(incremental=dlt.sources.incremental(
            "created_at", initial_value=datetime.datetime(2024, 4, 1, 0, 0, 0)))

        # Run the pipeline
        info = pipeline.run(source, write_disposition="append")

        # Print the info
        print(info)

    load_incremental_timestamp_table_resource()
    ```

3. `dlt` パイプラインを実行すると、BigQuery の「contact」テーブルにロードされたデータは次のようになります:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 00:00:00 UTC | 1721878309.021546 | 5H8ca6C89umxHA |
    | 2 | 2 | Bob | 2024-07-02 00:00:00 UTC | 1721878309.021546 | M61j4aOSqs4k2w |

4. 次に、SQLソースの「contact」テーブルが更新されます。2つの新しい行が追加され、`id = 2` の行が削除されます。更新されたデータソースは次のようになります:

    | id | name | created_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 00:00:00 |
    | 3 | Charlie | 2024-07-03 00:00:00 |
    | 4 | Dave | 2024-07-04 00:00:00 |

5. パイプラインを再度実行した後、BigQuery に作成された「contact」テーブル:

    | Row | id | name | created_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 00:00:00 UTC | 1721878309.021546 | Petj6R+B/63sWA |
    | 2 | 2 | Bob | 2024-07-02 00:00:00 UTC | 1721878309.021546 | 3Rr3VmY+av+Amw |
    | 3 | 3 | Charlie | 2024-07-03 00:00:00 UTC | 1721878309.021546 | L/MnhG19xeMrvQ |
    | 4 | 4 | Dave | 2024-07-04 00:00:00 UTC | 1721878309.021546 | W6ZdfvTzfRXlsA |

**何が起こったか？**

パイプラインは、既存のデータ（AliceとBob）を保持しながら、指定された初期値以降の「created_at」タイムスタンプを持つ新しいレコード（CharlieとDave）を追加します。このアプローチは、データの作成日時に基づいて段階的にロードする場合に便利です。

### 4. タイムスタンプ（"last_modified_at"）とIDに基づいてレコードをマージ（更新/挿入）する

この戦略では、IDとタイムスタンプフィールドの複合キーに基づいてレコードをマージします。既存のレコードを更新し、必要に応じて新しいレコードを挿入します。

手順は以下のとおりです:

1. SQLソース内の「contact」という名前の初期データセットは次のようになります:

    | id | name | last_modified_at |
    | --- | --- | --- |
    | 1 | Alice | 2024-07-01 00:00:00 |
    | 2 | Bob | 2024-07-02 00:00:00 |

2. このPythonコードは、`dlt`パイプラインを使用してSQLソースからBigQueryにデータをロードするプロセスを示しています。`write_disposition = "merge"`と、`last_modified_at`が増分パラメータとして使用されている点にご注意ください。

    ```py
    def load_merge_table_resource() -> None:
        """Merge (update/insert) records based on last_modified_at timestamp and ID."""
        pipeline = dlt.pipeline(
            pipeline_name="mysql_database",
            destination='bigquery',
            dataset_name="dlt_contacts",
        )

        # Merge records, 'contact' table, based on ID and last_modified_at timestamp
        source = sql_database().with_resources("contact")
        source.contact.apply_hints(incremental=dlt.sources.incremental(
            "last_modified_at", initial_value=datetime.datetime(2024, 4, 1, 0, 0, 0)),
            primary_key="id")

        # Run the pipeline
        info = pipeline.run(source, write_disposition="merge")

        # Print the info
        print(info)

    load_merge_table_resource()
    ```

3. `dlt` パイプラインを実行すると、BigQuery の「contact」テーブルにロードされたデータは次のようになります。

    | Row | id | name | last_modified_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 1 | Alice | 2024-07-01 00:00:00 UTC | 1721878309.021546 | ObbVlxcly3VknQ |
    | 2 | 2 | Bob | 2024-07-02 00:00:00 UTC | 1721878309.021546 | Vrlkus/haaKlEg |

4. 次に、SQL ソースの "contact" テーブルが更新されます。「Alice」が「Alice Updated」に更新され、新しい行「Hank」が追加されます。

    | id | name | last_modified_at |
    | --- | --- | --- |
    | 1 | Alice Updated | 2024-07-08 00:00:00 |
    | 3 | Hank | 2024-07-08 00:00:00 |

5. パイプラインを再度実行した後、BigQuery に作成された「contact」テーブル:

    | Row | id | name | last_modified_at | _dlt_load_id | _dlt_id |
    | --- | --- | --- | --- | --- | --- |
    | 1 | 2 | Bob | 2024-07-02 00:00:00 UTC | 1721878309.021546 | Cm+AcDZLqXSDHQ |
    | 2 | 1 | Alice Updated | 2024-07-08 00:00:00 UTC | 1721878309.021546 | OeMLIPw7rwFG7g |
    | 3 | 3 | Hank | 2024-07-08 00:00:00 UTC | 1721878309.021546 | Ttp6AI2JxqffpA |

**何が起こったか？**

パイプラインは、更新された `last_modified_at` タイムスタンプを含む新しいデータで Alice のレコードを更新し、Hank の新しいレコードを追加します。この方法は、特定のタイムスタンプと ID に基づいてレコードの更新と挿入の両方を確実に行う必要がある場合に役立ちます。

提供されている例では、`dlt` を使用してさまざまな増分ロードシナリオを実現する方法を説明し、各パイプラインの実行前後の変更点を強調表示しています。

