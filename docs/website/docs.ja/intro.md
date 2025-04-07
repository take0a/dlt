---
title: Introduction
description: Introduction to dlt
keywords: [introduction, who, what, how]
---

import snippets from '!!raw-loader!./intro-snippets.py';

# Getting started

![dlt pacman](/img/dlt-pacman.gif)

## dlt とは?

dlt は、オープンソースの Python ライブラリで、いろいろな、時には整っていないデータソースから、構造化された本番のデータセットにデータをロードします。[REST APIs](./tutorial/rest-api)、[SQL databases](./tutorial/sql-database)、[cloud storage](./tutorial/filesystem)、[Python data structures](./tutorial/load-data-from-an-api) 、[その他のデータソース](./dlt-ecosystem/verified-sources)からデータを抽出するための軽量なインターフェースです。

dlt は使いやすく、柔軟性と拡張性があるように設計されています:

- dlt は、[スキーマ](./general-usage/schema) と[データ型](./general-usage/schema/#data-types)を推論し、[データを正規化して](./general-usage/schema/#data-normalizer), ネストしたデータ構造を扱います。
- dlt は、様々な[人気のある宛先](./dlt-ecosystem/destinations/)をサポートします。また、リバースETLパイプラインを作るための[カスタマイズした宛先](./dlt-ecosystem/destinations/destination)を追加するインターフェースがあります。
- dlt は、Python が実行される、どんな場所にもデプロイできますから、[Airflow](./walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer) 上にも、[serverless functions](./walkthroughs/deploy-a-pipeline/deploy-with-google-cloud-functions) にも、その他の任意のクラウド上にもデプロイできます。
- dlt は、[インクリメンタルローディング](./general-usage/incremental-loading)、[スキーマの進化](./general-usage/schema-evolution)と[スキーマとデータの制約](./general-usage/schema-contracts)によって、パイプラインのメンテナンスを自動化します。

dlt を使い始めるには、pip を使ってライブラリをインストールします:

```sh
pip install dlt
```
:::tip
実験にはクリーンな仮想環境を使用することをお勧めします！設定方法については、[詳細な手順](./reference/installation)をお読みください。
:::

## dlt でデータをロードします

<Tabs
  groupId="source-type"
  defaultValue="rest-api"
  values={[
    {"label": "REST APIs", "value": "rest-api"},
    {"label": "SQL databases", "value": "sql-database"},
    {"label": "Cloud storages or files", "value": "filesystem"},
    {"label": "Python data structures", "value": "python-data"},
]}>
  <TabItem value="rest-api">

dlt の [REST API ソース](./tutorial/rest-api) を使用して、任意の REST API からデータを抽出します。データの取得元となる API エンドポイント、ページネーション方法、認証を定義すると、dlt が残りの処理を行います:

```py
import dlt
from dlt.sources.rest_api import rest_api_source

source = rest_api_source({
    "client": {
        "base_url": "https://api.example.com/",
        "auth": {
            "token": dlt.secrets["your_api_token"],
        },
        "paginator": {
            "type": "json_link",
            "next_url_path": "paging.next",
        },
    },
    "resources": ["posts", "comments"],
})

pipeline = dlt.pipeline(
    pipeline_name="rest_api_example",
    destination="duckdb",
    dataset_name="rest_api_data",
)

load_info = pipeline.run(source)

# print load info and posts table as dataframe
print(load_info)
print(pipeline.dataset().posts.df())
```

ソースの構成とページネーションの方法の詳細については、[REST API ソースのチュートリアル](./tutorial/rest-api)に従ってください。 
  </TabItem>
  <TabItem value="sql-database">

[SQL ソース](./tutorial/sql-database)を使用して、PostgreSQL、MySQL、SQLite、Oracle などのデータベースからデータを抽出します。

```py
from dlt.sources.sql_database import sql_database

source = sql_database(
    "mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam"
)

pipeline = dlt.pipeline(
    pipeline_name="sql_database_example",
    destination="duckdb",
    dataset_name="sql_data",
)

load_info = pipeline.run(source)

# print load info and the "family" table as dataframe
print(load_info)
print(pipeline.dataset().family.df())
```

ソースの構成とサポート対象のデータベースの詳細については、[SQL ソースのチュートリアル](./tutorial/sql-database)に従ってください。

  </TabItem>
  <TabItem value="filesystem">

[ファイルシステム](./tutorial/filesystem)ソースは、 AWS S3、Google Cloud Storage、Google Drive、Azure またはローカルのファイルシステムからデータを抽出します。

```py
from dlt.sources.filesystem import filesystem

resource = filesystem(
    bucket_url="s3://example-bucket",
    file_glob="*.csv"
)

pipeline = dlt.pipeline(
    pipeline_name="filesystem_example",
    destination="duckdb",
    dataset_name="filesystem_data",
)

load_info = pipeline.run(resource)

# print load info and the "example" table as dataframe
print(load_info)
print(pipeline.dataset().example.df())
```

ソースの構成とサポート対象のストレージサービスの詳細については、[ファイルシステムソースのチュートリアル](./tutorial/filesystem)に従ってください。

  </TabItem>
  <TabItem value="python-data">

dlt は Python のジェネレータや Python のデータ構造から直接データをロードできます:

```py
import dlt

@dlt.resource(table_name="foo_data")
def foo():
    for i in range(10):
        yield {"id": i, "name": f"This is item {i}"}

pipeline = dlt.pipeline(
    pipeline_name="python_data_example",
    destination="duckdb",
)

load_info = pipeline.run(foo)

# print load info and the "foo_data" table as dataframe
print(load_info)
print(pipeline.dataset().foo_data.df())
```

dlt の基礎、高度な利用のシナリオについて学ぶには、[Python データ構造のチュートリアル](./tutorial/load-data-from-an-api)を御覧ください。 

  </TabItem>

</Tabs>

:::tip
dlt をマシンにインストールすることなく、試してみない場合は、[Google Colab のデモ](https://colab.research.google.com/drive/1NfSB1DpwbbHX9_t5vlalBTf13utwpMGx?usp=sharing)を御覧ください。
:::

## dlt コミュニティに参加する

1. ライブラリに⭐をつけて、[GitHub](https://github.com/dlt-hub/dlt) でコードを確認しましょう。
1. [Slack](https://dlthub.com/community) で質問したり、ライブラリの使用方法を共有しましょう。
1. 問題の報告や機能のリクエストは、[ここ](https://github.com/dlt-hub/dlt/issues/new/choose)から。

