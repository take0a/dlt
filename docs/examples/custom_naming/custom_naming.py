"""
---
title: Create and use own naming convention
description: We demonstrate how to create naming conventions that allow UNICODE letters and never generate collisions
keywords: [example]
---

この例では、カスタム命名規則を追加して使用する方法を示します。命名規則は、ソースデータ内の識別子を、有効な識別子のルールが制約されている宛先の識別子に変換します。

カスタム命名規則は、`dlt.common.normalizers.naming` からインポートできる `NamingConvention` から派生したクラスです。次のモジュールレイアウトを推奨します。
1. 各命名規則は、別々の Python モジュール（ファイル）に存在します。
2. クラスの名前は常に `NamingConvention` です。

この例には 2 つの命名規則があります。
1. `sql_ci` の派生版で、各名前に決定論的なタグを追加することで、低い確率（ユーザー定義）で識別子の衝突を生成します。
2. LATIN（ウムラウトなど）文字に対応した `sql_cs` のバリアント

この例では、以下の点を学習します。
* 推奨レイアウトで命名規則モジュールを作成する
* 命名規則を `duckdb` の宛先ファクトリに明示的に渡すことで使用する
* 命名規則を config.toml で設定することで使用する
* `is_case_sensitive` プロパティをオーバーライドすることで、宣言されている大文字と小文字の区別を変更する
* `normalize_identifier` メソッドをオーバーライドすることで、カスタム正規化ロジックを提供する

"""

import dlt

if __name__ == "__main__":
    # sql_cs_latin2 module
    import sql_cs_latin2  # type: ignore[import-not-found]

    # create postgres destination with a custom naming convention. pass sql_cs_latin2 as module
    # NOTE: ql_cs_latin2 is case sensitive and postgres accepts UNICODE letters in identifiers
    dest_ = dlt.destinations.postgres(
        "postgresql://loader:loader@localhost:5432/dlt_data", naming_convention=sql_cs_latin2
    )
    # run a pipeline
    pipeline = dlt.pipeline(
        pipeline_name="sql_cs_latin2_pipeline",
        destination=dest_,
        dataset_name="example_data",
        dev_mode=True,
    )
    # Extract, normalize, and load the data
    load_info = pipeline.run([{"StückId": 1}], table_name="Ausrüstung")
    print(load_info)
    with pipeline.sql_client() as client:
        # NOTE: we quote case sensitive identifers
        with client.execute_query('SELECT "StückId" FROM "Ausrüstung"') as cur:
            print(cur.description)
            print(cur.fetchone())

    # sql_ci_no_collision (configured in config toml)
    # NOTE: pipeline with name `sql_ci_no_collision` will create default schema with the same name
    # so we are free to use it in config.toml to just affect this pipeline and leave the postgres pipeline as it is
    pipeline = dlt.pipeline(
        pipeline_name="sql_ci_no_collision",
        destination="duckdb",
        dataset_name="example_data",
        dev_mode=True,
    )
    # duckdb is case insensitive so tables and columns below would clash but sql_ci_no_collision prevents that
    data_1 = {"ItemID": 1, "itemid": "collides"}
    load_info = pipeline.run([data_1], table_name="BigData")

    data_2 = {"1Data": 1, "_1data": "collides"}
    # use colliding table
    load_info = pipeline.run([data_2], table_name="bigdata")

    with pipeline.sql_client() as client:
        from duckdb import DuckDBPyConnection

        conn: DuckDBPyConnection = client.native_connection
        # tags are deterministic so we can just use the naming convention to get table names to select
        first_table = pipeline.default_schema.naming.normalize_table_identifier("BigData")
        sql = f"DESCRIBE TABLE {first_table}"
        print(sql)
        print(conn.sql(sql))
        second_table = pipeline.default_schema.naming.normalize_table_identifier("bigdata")
        sql = f"DESCRIBE TABLE {second_table}"
        print(sql)
        print(conn.sql(sql))

    # print(pipeline.default_schema.to_pretty_yaml())
