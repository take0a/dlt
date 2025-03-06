---
title: How dlt works
description: How data load tool (dlt) works
keywords: [architecture, extract, normalize, load]
---

# `dlt` の仕組み

簡単に言うと、`dlt` は、利用可能なさまざまな[ソース](../../dlt-ecosystem/verified-sources)(API、PostgreSQL データベース、Python データ構造など)からのデータを自動的に、選択した[宛先](../../dlt-ecosystem/destinations)(Google BigQuery、Azure の Deltalake、またはリバース ETL でのデータのプッシュバックなど)に保存されるライブデータセットに変換します。JSON オブジェクト、Python リストと辞書、pandas データフレーム、アローテーブルなど、`dlt` と互換性のある方法でデータを生成する限り、独自のソースを簡単に実装できます。`dlt` は、スキーマを自動的に計算し、データを宛先に移動できます。

![architecture-diagram](/img/dlt-onepager.png)

## 具体的な例

`dlt` の主な構成要素は [パイプライン](../../general-usage/glossary.md#pipeline) であり、`run` メソッドを呼び出すと、ソースから宛先へのデータのロードを 3 つの個別のステップで調整します。意図的に短くした次の例を考えてみましょう:

```py
import dlt

pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
pipeline.run(
    [
        {"id": 1},
        {"id": 2},
        {"id": 3, "nested": [{"id": 1}, {"id": 2}]},
    ],
    table_name="items",
)
```

これは`run`メソッドが実行されたときに起こることです:

1. [Extract](how-dlt-works.md#extract) - ソースからハード ドライブにデータを完全に抽出します。上記の例では、3 つの項目を持つ 1 つのリソースを持つ暗黙的なソースが作成され、抽出されます。
2. [Normalize](how-dlt-works.md#normalize) - データを検査して正規化し、宛先と互換性のあるスキーマを計算します。上記の例では、正規化機能は `items` という名前の 1 つのテーブルで `int` 型の `id` 列を 1 つ検出し、さらにテーブル items 内のネストされたリストを検出して、それを `items__nested` という名前の子テーブルにしてネストを解除します。
3. [Load](how-dlt-works#load) - 必要に応じて宛先でスキーマ移行を実行し、データを宛先にロードします。上記の例では、前の手順で検出された 2 つのテーブルを含む新しいデータセットがローカル duckdb データベースに作成されます。

## ３つのフェーズ

### 抽出

抽出はパイプラインの`extract`コマンドで個別に実行できます。: 

```py
pipeline.extract(data)
```

抽出フェーズでは、`dlt` は[ソース](../../dlt-ecosystem/verified-sources)からハードドライブの新しい [ロードパッケージ](../../general-usage/destination-tables#load-packages-and-load-ids)にデータを完全に抽出します。このパッケージには一意の ID が割り当てられ、ソースから受信した生データが含まれます。さらに、[スキーマヒントを提供](../../general-usage/resource#define-schema)して、一部の列のデータ型を定義したり、主キーや一意のインデックスを追加したりすることもできます。このフェーズは、[インクリメンタルカーソルフィールド](../../general-usage/resource#sample-from-large-data)を使用して 1 回の実行で抽出される項目の数を[制限](../../general-usage/resource#sample-from-large-data)して、[並列化](../../reference/performance#extract)でパフォーマンスを調整することでも制御できます。また、フィルターとマップを適用して個人データを[難読化](../../general-usage/customising-pipelines/pseudonymizing_columns)または[削除](../../general-usage/customising-pipelines/removing_columns)したり、[トランスフォーマー](../../examples/transformers)を使用して派生データを作成したりすることもできます。

### 正規化

正規化は、パイプラインの `normalize` コマンドを使用して個別に実行できます。正規化は抽出フェーズが完了していることに依存しており、抽出されたデータがない場合には何も実行されません。

```py
pipeline.normalize()
```

正規化フェーズでは、`dlt` はデータを検査して正規化し、入力データに対応する[スキーマ](../../general-usage/schema)を計算します。スキーマは、新しい列やテーブルなどの将来のソースデータの変更に対応するために自動的に進化します。また、`dlt` は、検出された値が前回の実行中に計算されたスキーマと一致しない場合は、ネストされたデータ構造を子テーブルにネスト解除し、バリアント列を作成します。正規化フェーズの結果は、宛先が理解できる形式で正規化されたデータを保持する更新されたロードパッケージと、データを宛先に移行するために使用できる完全なスキーマです。正規化フェーズは、たとえば、入力データの [許可されるネストレベルを定義](../../general-usage/source#reduce-the-nesting-level-of-generated-tables) したり、スキーマがどのように進化するか、および適合しない行がどのように処理されるかを制御する [スキーマコントラクトを適用](../../general-usage/schema-contracts)したりすることで制御できます。パフォーマンス設定も [使用可能](../../reference/performance#normalize)です。

### ロード

ロードは、パイプラインの `load` コマンドを使用して個別に実行できます。ロードは、正規化フェーズが完了していることに依存しており、正規化されたデータがない場合には何も実行されません。

```py
pipeline.load()
```
ロードフェーズでは、`dlt` は最初に必要に応じて宛先でスキーマ移行を実行し、次にデータを宛先に読み込みます。`dlt` は、大規模な読み込みを並列化できるように、ロードジョブと呼ばれる小さなチャンクでデータを読み込みます。宛先への接続が失敗した場合は、パイプラインを再実行しても安全であり、`dlt` は現在の読み込みパッケージからすべてのロードジョブの読み込みを続行します。`dlt` は、内部 dlt スキーマ、すべてのロードパッケージに関する情報、およびインクリメンタルに使用されるいくつかの状態情報などを格納する特別なテーブルも作成します。これらの情報は、インクリメンタルに前回の実行から別のマシンへの増分状態を復元できるようにします。ロードフェーズを制御する方法には、異なる [`write_dispositions`](../../general-usage/incremental-loading#choosing-a-write-disposition) を使用して宛先のデータを置き換えたり、単に追加したり、テーブルごとに構成できる特定のマージキーでマージしたりする方法があります。一部の宛先では、バケットプロバイダー上のリモートステージングデータセットを使用できます。また、`dlt` は [deltables や iceberg](../../dlt-ecosystem/destinations/delta-iceberg) などの最新のオープンテーブル形式もサポートしており、[リバース ETL](../../dlt-ecosystem/destinations/destination) も可能です。

## その他の注目すべき `dlt` の機能

* `dlt` は単なる Python パッケージなので、[Python が実行されるあらゆる場所](../../walkthroughs/deploy-a-pipeline) (ローカル、ノートブック、オーケストレーターなど) で実行されます。 
* `dlt` を使用すると、`duckdb` を使用してデータ パイプラインをローカルで構築およびテストし、デプロイメントの宛先を切り替えることができます。 
* `dlt` は、[Python でデータにアクセス](../../general-usage/dataset-access/dataset)するためのユーザーフレンドリーなインターフェースを提供します。[Streamlit アプリ](../../general-usage/dataset-access/streamlit)を使用し、優れた Ibis ライブラリとの [統合](../../general-usage/dataset-access/ibis-backend) を活用します。これらはすべて、バケット ストレージ プロバイダーが提供するデータ レイクでも機能します。
* `dlt` は、移行先でのスキーマ移行を完全に管理します。スキーマを更新するために SQL を使用する方法を知る必要さえありません。また、スキーマがどのように進化するかを制御する [スキーマ コントラクト](../../general-usage/schema-contracts) もサポートしています。 
* `dlt` は、ロード中に何が起こっているかを [監視およびトレース](../../running-in-production/monitoring) するためのさまざまなオプションを提供します。
* `dlt` は、dbt を使用する場合でも、Arrow テーブルと pandas DataFrames を使用して Python を使用する場合でも、ロード後に [データを変換](../../dlt-ecosystem/transformations)する必要がある場合にサポートします。
