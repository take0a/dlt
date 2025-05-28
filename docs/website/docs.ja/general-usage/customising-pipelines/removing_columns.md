---
title: Removing columns
description: Removing columns by passing a list of column names
keywords: [deleting, removing, columns, drop]
---

# 列の削除

データベースにデータをロードする前に列を削除することは、機密性の高いフィールドや不要なフィールドを除外するための確実な方法です。例えば、このシナリオでは、「country_id」列を含むソースを作成し、ロード前にデータベースからこの列を除外します。

列を削除するプロセスを示すサンプルパイプラインを作成しましょう。

1. 次のようにダミー データを作成するソース関数を作成します:

   ```py
   import dlt

   # This function creates a dummy data source.
   @dlt.source
   def dummy_source():
       @dlt.resource(write_disposition="replace")
       def dummy_data():
           for i in range(3):
               yield {"id": i, "name": f"Jane Washington {i}", "country_code": 40 + i}

       return dummy_data()
   ```

   この関数は、`id`、`name`、`country_code` の 3 つの列を作成します。

2. 次に、次のように、データをデータベースにロードする前に、データから列をフィルター処理する関数を作成します:

   ```py
   from typing import Dict, List, Optional

   def remove_columns(doc: Dict, remove_columns: Optional[List[str]] = None) -> Dict:
       if remove_columns is None:
           remove_columns = []

       # Iterating over the list of columns to be removed
       for column_name in remove_columns:
           # Removing the column if it exists in the document
           if column_name in doc:
               del doc[column_name]

       return doc
   ```

   `doc`: 列を削除するドキュメント（辞書）。

    `remove_columns`: 削除する列名のリスト。デフォルトは None です。

3. 次に、テーブルから削除する列を宣言し、次のようにソースを変更します:

   ```py
   # Example columns to remove:
   remove_columns_list = ["country_code"]

   # Create an instance of the source so you can edit it.
   source_instance = dummy_source()

   # Modify this source instance's resource
   source_instance.dummy_data.add_map(
       lambda doc: remove_columns(doc, remove_columns_list)
   )
   ```

4. オプションで結果を検査することもできます:

   ```py
   for row in source_instance:
       print(row)
   #{'id': 0, 'name': 'Jane Washington 0'}
   #{'id': 1, 'name': 'Jane Washington 1'}
   #{'id': 2, 'name': 'Jane Washington 2'}
   ```

5. 最後に、パイプラインを作成します:

   ```py
   # Integrating with a dlt pipeline
   pipeline = dlt.pipeline(
       pipeline_name='example',
       destination='bigquery',
       dataset_name='filtered_data'
   )
   # Run the pipeline with the transformed source
   load_info = pipeline.run(data_source)
   print(load_info)
   ```

