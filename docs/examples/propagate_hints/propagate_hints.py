"""
---
title: primary_key をルートからネストされたテーブルに伝播する
description: Learn how to propagate any column to nested tables
keywords: [root table, nested reference, parent key]
---

親レコードの特定のフィールド（主キー、外部キーなど）を各子レコードに伝播する方法を学習します。

この例では、以下の手順を説明します。

- `add_parent_id` 関数を使用して、各子レコードに `parent_id` を追加する
- [`add_map` 関数](https://dlthub.com/docs/api_reference/extract/resource#add_map) を使用して、
このカスタムロジックをデータセット内のすべてのレコードに適用する

:::note important
`_dlt_id` および `_dlt_load_id` を含む dlt メタデータは引き続きテーブルにロードされることに注意してください。
:::
"""

from typing import List, Dict, Any, Generator
import dlt


# Define a dlt resource with write disposition to 'merge'
@dlt.resource(name="parent_with_children", write_disposition={"disposition": "merge"})
def data_source() -> Generator[List[Dict[str, Any]], None, None]:
    # Example data
    data = [
        {
            "parent_id": 1,
            "parent_name": "Alice",
            "children": [
                {"child_id": 1, "child_name": "Child 1"},
                {"child_id": 2, "child_name": "Child 2"},
            ],
        },
        {
            "parent_id": 2,
            "parent_name": "Bob",
            "children": [{"child_id": 3, "child_name": "Child 3"}],
        },
    ]

    yield data


# Function to add parent_id to each child record within a parent record
def add_parent_id(record: Dict[str, Any]) -> Dict[str, Any]:
    parent_id_key = "parent_id"
    for child in record["children"]:
        child[parent_id_key] = record[parent_id_key]
    return record


if __name__ == "__main__":
    # Create and configure the dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="generic_pipeline",
        destination="duckdb",
        dataset_name="dataset",
    )

    # Run the pipeline
    load_info = pipeline.run(data_source().add_map(add_parent_id), primary_key="parent_id")
    # Output the load information after pipeline execution
    print(load_info)
