"""
---
title: Backfilling in chunks
description: Learn how to backfill in chunks of defined size
keywords: [incremental loading, backfilling, chunks,example]
---

この例では、sql_database ソースから定義済みのサイズのチャンク単位でロードする Python スクリプトを示します。これは、複数のパイプライン実行でバックフィルを行う場合に便利です。1 回の非常に大きなパイプライン実行でバックフィルを行うと、一時ストレージのメモリ問題により失敗したり、完了までに非常に長い時間がかかったりして、出力先に進捗状況が表示されなかったりする可能性があります。

ここでは、以下の方法を学習します。

- sql_database ソースを使用して MySQL データベースに接続する
- ロードするテーブルを 1 つ選択し、増分ロードのヒントと主キーを適用する
- チャンクサイズを設定し、1 回のパイプライン実行でロードするチャンク数を制限する
- パイプラインを作成し、定義済みのチャンク単位でテーブルをバックフィルする
- データセット アクセサーを使用して、ロードの進行状況を検査およびアサートする
"""

import pandas as pd

import dlt
from dlt.sources.sql_database import sql_database


if __name__ == "__main__":
    # NOTE: this is a live table in the rfam database, so the number of final rows may change
    TOTAL_TABLE_ROWS = 4178
    RFAM_CONNECTION_STRING = "mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam"

    # create sql database source that only loads the family table in chunks of 1000 rows
    source = sql_database(RFAM_CONNECTION_STRING, table_names=["family"], chunk_size=1000)

    # we apply some hints to the table, we know the rfam_id is unique and that we can order
    # and load incrementally on the created datetime column
    source.family.apply_hints(
        primary_key="rfam_id",
        incremental=dlt.sources.incremental(
            cursor_path="created", initial_value=None, row_order="asc"
        ),
    )

    # with limit we can limit the number of chunks to load, with a chunk size of 1000 and a limit of 1
    # we will load 1000 rows per pipeline run
    source.add_limit(1)

    # create pipeline
    pipeline = dlt.pipeline(
        pipeline_name="rfam", destination="duckdb", dataset_name="rfam_data", dev_mode=True
    )

    def _assert_unique_row_count(df: pd.DataFrame, num_rows: int) -> None:
        """Assert that a dataframe has the correct number of unique rows"""
        # NOTE: this check is dependent on reading the full table back from the destination into memory,
        # so it is only useful for testing before you do a large backfill.
        assert len(df) == num_rows
        assert len(set(df.rfam_id.tolist())) == num_rows

    # after the first run, the family table in the destination should contain the first 1000 rows
    pipeline.run(source)
    _assert_unique_row_count(pipeline.dataset().family.df(), 1000)

    # after the second run, the family table in the destination should contain 1999 rows
    # there is some overlap on the incremental to prevent skipping rows
    pipeline.run(source)
    _assert_unique_row_count(pipeline.dataset().family.df(), 1999)

    # ...
    pipeline.run(source)
    _assert_unique_row_count(pipeline.dataset().family.df(), 2998)

    # ...
    pipeline.run(source)
    _assert_unique_row_count(pipeline.dataset().family.df(), 3997)

    # the final run will load all the rows until the end of the table
    pipeline.run(source)
    _assert_unique_row_count(pipeline.dataset().family.df(), TOTAL_TABLE_ROWS)

    # NOTE: in a production environment you will likely:
    # * be using much larger chunk sizes and limits
    # * run the pipeline in a loop to load all the rows
    # * and programmatically check if the table is fully loaded and abort the loop if this is the case.
