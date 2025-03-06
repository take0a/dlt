---
title: Source
description: Explanation of what a dlt source is
keywords: [source, api, dlt.source]
---

# ソース

[ソース](glossary.md#source)は、リソース、つまり単一の API のエンドポイントの論理的なグループです。最も一般的なアプローチは、別の Python モジュールで定義することです。

- ソースは、1 つ以上のリソースを返す `@dlt.source` で装飾された関数です。
- ソースでは、オプションでテーブル、列、パフォーマンス ヒントなどを含む [スキーマ](schema.md) を定義できます。
- ソース Python モジュールには通常、オプションのカスタマイズとデータ変換が含まれています。
- ソース Python モジュールには通常、特定の API の認証およびページネーション コードが含まれています。

## ソースを宣言する

ソースを宣言するには、1 つ以上のリソースを返すか生成する (オプションで非同期の) 関数を `@dlt.source` で装飾します。[パイプラインを作成する](../walkthroughs/create-a-pipeline.md) ハウツー ガイドで、その方法を説明しています。

### リソースを動的に作成する

`dlt.resource` を関数として使用してリソースを作成できます。以下の例では、単一のジェネレーター関数を再利用して、複数の Hubspot エンドポイントのリソースのリストを作成します。

```py
@dlt.source
def hubspot(api_key=dlt.secrets.value):

    endpoints = ["companies", "deals", "products"]

    def get_resource(endpoint):
        yield requests.get(url + "/" + endpoint).json()

    for endpoint in endpoints:
        # calling get_resource creates a generator,
        # the actual code of the function will be executed in pipeline.run
        yield dlt.resource(get_resource(endpoint), name=endpoint)
```

### スキーマをアタッチ、構成する

ソースをロードするときに使用される [スキーマを作成、アタッチ、および構成](schema.md#attaching-schemas-to-sources) できます。

### source 関数での長時間の操作を避ける

sorce 関数でデータを抽出しないでください。可能であれば、そのタスクはリソースに任せてください。ソース関数は、呼び出されるとすぐに実行されます (Python ジェネレーターなどの実行を遅らせるリソースとは異なります)。`pipeline.run` または `pipeline.extract` 内でデータを抽出すると、いくつかの利点 (エラー処理、実行メトリック、並列化) が得られます。

これが現実的でない場合（たとえば、データベースを反映してテーブルのリソースを作成する場合）、source 関数を頻繁に呼び出さないようにしてください。[Airflow にデプロイする予定の場合は、この注記を参照してください](../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer.md#2-modify-dag-file)

## ソースをカスタマイズする

### ロードするリソースにアクセスして選択する

ソース内に存在するリソースにアクセスし、読み込むリソースを選択できます。上記の `hubspot` リソースの場合、「companies」、「deals」、「products」のリソースを選択して読み込むことができます:

```py
from hubspot import hubspot

source = hubspot()
# "resources" is a dictionary with all resources available, the key is the resource name
print(source.resources.keys())  # print names of all resources
# print resources that are selected to load
print(source.resources.selected.keys())
# load only "companies" and "deals" using the "with_resources" convenience method
pipeline.run(source.with_resources("companies", "deals"))
```

リソースは個別にアクセスして選択できます:

```py
# resources are accessible as attributes of a source
for c in source.companies:  # enumerate all data in the companies resource
    print(c)

# check if deals are selected to load
print(source.deals.selected)
# deselect the deals
source.deals.selected = False
```

### データのフィルタリング、変換、ピボット

リソース内のデータを変更したりフィルタリングしたりすることができます。たとえば、特定の日付以降の取引のみを保持したい場合などです:

```py
source.deals.add_filter(lambda deal: deal["created_at"] > yesterday)
```

変換の詳細については、[こちら](resource.md#filter-transform-and-pivot-data)を参照してください。

### データを部分的に読み込む

ソースで `add_limit` メソッドを呼び出すことで、各リソースによって生成されるアイテムの数を制限できます。これは、テスト、デバッグ、および実験用のサンプルデータセットの生成に役立ちます。テストデータセットを数分で簡単に取得できます。そうでなければ、完全な読み込みが完了するまで何時間も待つ必要があります。以下では、`pipedrive` ソースを各エンドポイントから **10 ページ** のデータのみを取得するように制限しています。トランスフォーマーは完全に評価されることに注意してください:

```py
from pipedrive import pipedrive_source

pipeline = dlt.pipeline(pipeline_name='pipedrive', destination='duckdb', dataset_name='pipedrive_data')
load_info = pipeline.run(pipedrive_source().add_limit(10))
print(load_info)
```

ソースに時間制限を適用することもできます:

```py
pipeline.run(pipedrive_source().add_limit(max_time=10))
```

または件数と時間の両方で制限し、最初に到達した制限で抽出を停止します:

```py
pipeline.run(pipedrive_source().add_limit(max_items=10, max_time=10))
```

:::note
`add_limit` は **レコード数を制限するのではなく**、「yield の数」を制限することに注意してください。`dlt` は、制限に達した後にデータを生成するイテレータ/ジェネレータを閉じます。リソース ページで `add_limit` の詳細をお読みください。
:::

データのサンプリングの詳細については、[こちら](resource.md#sample-from-large-data)を参照してください。

### ソースの名前を変更する

`dlt` を使用すると、ソースの名前を変更したり、ソース構成をカスタムセクションに配置したり、ソースのインスタンスを複数並べて作成したりできます。たとえば、:

```py
from dlt.sources.sql_database import sql_database

my_db = sql_database.clone(name="my_db", section="my_db")(table_names=["table_1"])
print(my_db.name)
```

ここでは、`sql_database`の名前を変更したバージョンを作成し、それをインスタンス化します。このようなソースは、以下から資格情報を読み取ります:

```toml
[sources.my_db.my_db.credentials]
password="..."
```

### 既存のソースにリソースを追加する

ソースを作成した後で、カスタムリソースをソースに追加できます。すべての取引を Keras モデルでスコアリングして、取引が詐欺であるかどうかを判断したいとします。そのためには、新しい `deals` リソースから[データを取得するトランスフォーマー](resource.md#feeding-data-from-one-resource-into-another) を宣言し、ソースに追加します。

```py
import dlt
from hubspot import hubspot

# source contains `deals` resource
source = hubspot()

@dlt.transformer
def deal_scores(deal_item):
    # obtain the score, deal_items contains data yielded by source.deals
    score = model.predict(featurize(deal_item))
    yield {"deal_id": deal_item, "score": score}

# connect the data from `deals` resource into `deal_scores` and add to the source
source.resources.add(source.deals | deal_scores)
# load the data: you'll see the new table `deal_scores` in your destination!
pipeline.run(source)
```

ソース内のリソースを次のように設定することもできます:

```py
source.deal_scores = source.deals | deal_scores
```

もしくは

```py
source.resources["deal_scores"] = source.deals | deal_scores
```
:::note
ソースにリソースを追加しても、`dlt` はリソースを複製するため、既存のインスタンスには影響しません。
:::

### 生成されたテーブルのネストレベルを減らす

ネストされたテーブルを生成し、辞書を列に平坦化するときに、`dlt` がどこまで深く進むかを制限できます。デフォルトでは、ライブラリは辞書からネストされたすべてのリストと列を制限なく降下してネストされたテーブルを生成します。

```py
@dlt.source(max_table_nesting=1)
def mongo_db():
    ...
```

上記の例では、ネストされたテーブルを 1 レベルだけ生成します (つまり、ネストされたテーブルのネストされたテーブルは存在しません)。一般的な設定は:

- `max_table_nesting=0` ネストされたテーブルは生成されず、辞書は列にフラット化されません。ネストされたデータはすべて JSON として表現されます。
- `max_table_nesting=1` ルートテーブルのネストされたテーブルのみが生成されます。ネストされたテーブル内のすべてのネストされたデータは JSON として表されます。

ソースインスタンスを作成した後でも同じ効果が得られます:

```py
from mongo_db import mongo_db

source = mongo_db()
source.max_table_nesting = 0
```

いくつかのデータ ソースには、MongoDB データベースなど、非常に深いネストを持つ半構造化ドキュメントが含まれる傾向があります。実際の経験では、`max_nesting_level` を 2 または 3 に設定すると、最も明確で人間が判読できるスキーマが生成されます。

:::tip
ソース レベルの `max_table_nesting` パラメータは、直接アクセスした場合 (例: `source.resources["resource_1"]` を使用)、個々のリソースに自動的には適用されません。確実に機能させるには、`source.with_resources("resource_1")` を使用するか、リソースに直接パラメータを設定します。
:::

リソースレベルで`max_table_nesting`パラメータを直接設定することができます。:

```py
@dlt.resource(max_table_nesting=0)
def my_resource():
    ...
```

もしくは

```py
source.my_resource.max_table_nesting = 0
```

### スキーマの変更

スキーマは、ソースの `schema` プロパティを介して利用できます。[データがロードされる前に、このスキーマを操作できます。つまり、テーブルの追加、列定義の変更などを行うことができます。](schema.md#schema-is-modified-in-the-source-function-body)

ソースには他に2つの便利なプロパティがあります:

1. `max_table_nesting` は、ネストされたテーブルとフラット化された列の最大ネストレベルを設定します。
1. `root_key` は、`_dlt_id` をルートテーブルからすべてのネストされたテーブルに伝播します。

## ソースをロードする

個々のソースまたはソースのリストを `dlt.pipeline` オブジェクトに渡すことができます。デフォルトでは、すべてのソースが 1 つのデータセットにロードされます。

1つのソースを複数のソースに分解することもできます。たとえば、50テーブルのコピージョブを、データをより速くロードするために、高並列処理のAirflow DAGに分割したい場合があります。これを行うには、次のようにリソースのリストを取得します:

```py
# get a list of resources' names
resource_list = sql_source().resources.keys()

# now we are able to make a pipeline for each resource
for res in resource_list:
    pipeline.run(sql_source().with_resources(res))
```

### 完全にリフレッシュする

ソース内のすべての（または選択した）リソースの「 write disposition 」を一時的に `replace` に変更して、完全な更新を強制することができます:

```py
p.run(merge_source(), write_disposition="replace")
```

選択したリソースに対して:

```py
p.run(tables.with_resources("users"), write_disposition="replace")
```
