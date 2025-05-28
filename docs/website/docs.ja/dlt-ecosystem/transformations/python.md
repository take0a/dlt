---
title: Transforming data in Python with Arrow tables or DataFrames
description: Transforming data loaded by a dlt pipeline with pandas dataframes or arrow tables
keywords: [transform, pandas]
---

# PythonでArrowテーブルまたはDataFramesを使ってデータを変換する

Pythonでは、Pandas DataFramesまたはArrowテーブルを使ってデータを変換できます。まずは[データセットのドキュメント](../../general-usage/dataset-access/dataset)をご覧ください。


## Python でデータをインタラクティブに変換する

[データセットのドキュメント](../../general-usage/dataset-access/dataset)で説明されている方法を使用することで、ローカル Python プロセスで出力先から DataFrame または Arrow テーブルにデータを取得し、インタラクティブに操作できます。これはファイルシステムの出力先でも機能します。

以下の例では、GitHub の反応データを `issues` テーブルから読み取り、反応の種類をカウントします。

```py
pipeline = dlt.pipeline(
    pipeline_name="github_pipeline",
    destination="duckdb",
    dataset_name="github_reactions",
    dev_mode=True
)

# get a dataframe of all reactions from the dataset
reactions = pipeline.dataset().issues.select("reactions__+1", "reactions__-1", "reactions__laugh", "reactions__hooray", "reactions__rocket").df()

# calculate and print out the sum of all reactions
counts = reactions.sum(0).sort_values(0, ascending=False)
print(counts)

# alternatively, you can fetch the data as an arrow table
reactions = pipeline.dataset().issues.select("reactions__+1", "reactions__-1", "reactions__laugh", "reactions__hooray", "reactions__rocket").arrow()
# ... do transformations on the arrow table
```

## 変換されたデータの永続化

dlt はリソースから DataFrame と Arrow テーブルを直接サポートしているため、同じパイプラインを使用して変換されたデータを出力先にロードできます。


### 簡単な例

既存のユーザーテーブルから、個人情報を含まない列のみを含む新しいテーブルを作成する簡単な例です。リレーションの `iter_arrow()` メソッドを使用して、矢印テーブルを一度にすべて取得するのではなく、反復処理していることに注意してください。

```py
pipeline = dlt.pipeline(
    pipeline_name="users_pipeline",
    destination="duckdb",
    dataset_name="users_raw",
    dev_mode=True
)

# get user relation with only a few columns selected, but omitting email and name
users = pipeline.dataset().users.select("age", "amount_spent", "country")

# load the data into a new table called users_clean in the same dataset
pipeline.run(users.iter_arrow(chunk_size=1000), table_name="users_clean")
```

### より複雑な例

上記の例はSQLで簡単に実行できます。PythonでArrow変換を実際に実行したいとしましょう。そのためには、変更されたArrowテーブルを生成するためのリソースを作成します。DataFramesでも同様です。

```py
import pyarrow.compute as pc

pipeline = dlt.pipeline(
    pipeline_name="users_pipeline",
    destination="duckdb",
    dataset_name="users_raw",
    dev_mode=True
)

# NOTE: this resource will work like a regular resource and support write_disposition, primary_key, etc.
# NOTE: For selecting only users above 18, we could also use the filter method on the relation with ibis expressions
@dlt.resource(table_name="users_clean")
def users_clean():
    users = pipeline.dataset().users
    for arrow_table in users.iter_arrow(chunk_size=1000):

        # we want to filter out users under 18
        age_filter = pc.greater_equal(arrow_table["age"], 18)
        arrow_table = arrow_table.filter(age_filter)

        # we want to hash the email column
        arrow_table = arrow_table.append_column("email_hash", pc.sha256(arrow_table["email"]))

        # we want to remove the email column and name column
        arrow_table = arrow_table.drop(["email", "name"])

        # yield the transformed arrow table
        yield arrow_table


pipeline.run(users_clean())
```

## その他の変換ツール

ロード前にデータを変換したい場合は、Python を使用できます。
ロード後にデータを変換したい場合は、Pandas または次のいずれかを使用できます。

1. [dbt.](dbt/dbt.md) (recommended)
2. [`dlt` SQL client.](sql.md)

