---
title: Pipeline tutorial
description: Build a data pipeline with dlt from scratch
keywords: [getting started, quick start, basics]
---

# `dlt` によるデータパイプラインの構築。基礎から応用まで

この詳細部の概要では、`dlt` によるパイプラインの主要な領域について説明します。[クイックスタート](./intro.md)をお探しの場合は、リンク先のページにアクセスしてください。

## なぜ `dlt` でパイプラインを構築するのでしょう？

`dlt` は、抽出とロードのプロセス全体をサポートする機能を提供します。ハイレベルの図を見てみましょう:

![dlt source resource pipe diagram](/img/dlt-high-level.png)

まず、データからスキーマを推測し、データを宛先にロードできる `pipeline` 関数があります。
このパイプラインは、JSON データ、データフレーム、ジェネレーター関数のような反復可能なオブジェクトにも使用することができます。

このパイプラインは、スキーマの検出、バージョン管理、進化エンジンを通して、手間のかからないローディングを提供し、行と列のレベルの系統で "そのままロード" できるようにします。

`dlt パイプライン`を利用することで、データの進化に合わせて簡単に適応でき、構造化もできるので、メンテナンスと開発にかかる時間が削減できます。

これによって、データチームは、変更へのタイムリーな通知による効果的なガバナンスを確保しつつ、データの活用と価値の向上に注力できるのです。

抽出では、`dlt` は、`source` と `resource` のデコレーターを提供するので、マイクロバッチと並列処理による適切でスケーラブルな抽出をサポートしつつ、抽出されたデータがロードされるべき定義が可能となります。

## 最もシンプルなパイプライン：スキーマの進化を伴うデータをロードするワンライナー

```py
import dlt

dlt.pipeline(destination='duckdb', dataset_name='mydata').run([{'id': 1, 'name': 'John'}], table_name="users")
```

`dlt` ライブラリの pipeline は、１回の関数呼び出しで、Python コードから宛先にデータ移動できる強力なツールです。パイプラインを定義することで、データ スキーマを簡単に読み込み、正規化、進化させることができ、シームレスなデータ統合と分析が可能になります。

例えば、オブジェクトのリストを「three」という名前の DuckDB テーブルにロードするシナリオを考えてみましょう。`dlt` なら、ほんの数行のコードで、パイプラインを作成して、実行できます:

1. [宛先](dlt-ecosystem/destinations)への [pipeline を作る](./walkthroughs/create-a-pipeline.md)
1. このパイプラインにデータを与えて、[実行する](./walkthroughs/run-a-pipeline.md)

```py
import dlt

pipeline = dlt.pipeline(destination="duckdb", dataset_name="country_data")

data = [
    {'country': 'USA', 'population': 331449281, 'capital': 'Washington, D.C.'},
    {'country': 'Canada', 'population': 38005238, 'capital': 'Ottawa'},
    {'country': 'Germany', 'population': 83019200, 'capital': 'Berlin'}
]

info = pipeline.run(data, table_name="countries")

print(info)
```

この例では、`pipeline` 関数を使用して、指定された宛先 (DuckDB) とデータセット名 (「country_data」) を持つパイプラインを作成します。次に、`run` メソッドが呼び出され、オブジェクトのリストから「countries」という名前のテーブルにデータがロードされます。`info` 変数には、パッケージ ID やジョブ メタデータなど、ロードされたデータに関する情報が格納されます。

渡すことができるデータは反復可能である必要があります。行のリスト、ジェネレーター、または `dlt` ソースであれば問題ありません。

データのロード方法を構成する場合は、pipeline 関数で `replace`、`append`、`merge` などの `write_disposition` を選択できます。

これは、データ内の id 列を　`upserting` または `merging` して、duckdb にデータをロードする例です。
この例では、dbt パッケージも実行し、ロードジョブの結果をそれぞれのテーブルにロードします。
これにより、スキーマの変更が発生したときにログに記録し、ロードされたデータと照合して系統化できるため、列と行レベルの両方の系統化が可能になります。
また、プロデューサーとコンシューマーがサブスクライブしている Slack チャネルにスキーマの変更を通知します。

```py
import dlt

# have data? dlt likes data
data = [{'id': 1, 'name': 'John'}]

# open connection
pipeline = dlt.pipeline(
    destination='duckdb',
    dataset_name='raw_data'
)

# Upsert/merge: Update old records, insert new
load_info = pipeline.run(
    data,
    write_disposition="merge",
    primary_key="id",
    table_name="users"
)
```
dbt ランナーを追加します。オプションで venv も:
```py
venv = dlt.dbt.get_venv(pipeline)
dbt = dlt.dbt.package(
    pipeline,
    "https://github.com/dbt-labs/jaffle_shop.git",
    venv=venv
)
models_info = dbt.run_all()

# Load metadata for monitoring and load package lineage.
# This allows for both row and column level lineage,
# as it contains schema update info linked to the loaded data
pipeline.run([load_info], table_name="loading_status", write_disposition='append')
pipeline.run([models_info], table_name="transform_status", write_disposition='append')
```

スキーマの変更を通知しましょう:
```py
from dlt.common.runtime.slack import send_slack_message

slack_hook = "https://hooks.slack.com/services/xxx/xxx/xxx"

for package in load_info.load_packages:
    for table_name, table in package.schema_update.items():
        for column_name, column in table["columns"].items():
            send_slack_message(
                slack_hook,
                message=f"\tTable updated: {table_name}: Column changed: {column_name}: {column['data_type']}"
            )
```

## `dlt` によるデータ抽出

`dlt` を使用したデータの抽出は簡単です。データ生成関数をロードまたは増分抽出メタデータで装飾するだけで、`dlt` はカスタム ロジックによって抽出およびロードできるようになります。

技術的には、2つの重要な側面が `dlt` の有効性に貢献しています:

- イテレータ、チャンク化、並列化によるスケーラビリティ。
- データの拡充や変換のための効率的な API 呼び出しを可能にする暗黙的な抽出 DAG の利用。

### イテレータ、チャンク化、並列化によるスケーラビリティ

`dlt` は、イテレータ、チャンク化、並列化技術を活用してスケーラブルなデータ抽出を提供します。このアプローチにより、大規模なデータセットを管理しやすいチャンクに分割して効率的に処理できます。

たとえば、数百万件のレコードを含む大規模なデータベースからデータを抽出する必要があるシナリオを考えてみましょう。データセット全体を一度に読み込む代わりに、`dlt` を使用すると、反復子を使用して、より小さく管理しやすい部分でデータを取得できます。この手法により、増分処理と読み込みが可能になり、メモリ リソースが限られている場合に特に役立ちます。

さらに、`dlt` は抽出プロセス中の並列化を容易にします。`dlt` は複数のデータ チャンクを同時に処理することで並列処理機能を活用し、抽出時間を大幅に短縮します。この並列化により、特に大量のデータ ソースを処理する場合にパフォーマンスが向上します。

### 暗黙的な抽出 DAG

`dlt` には、データ ソースとその変換間の依存関係を自動的に処理するための暗黙的な抽出 DAG の概念が組み込まれています。DAG はサイクルのない有向グラフを表し、各ノードはデータ ソースまたは変換ステップを表します。

`dlt` を使用すると、ツールはデータ ソースとその変換の間で識別された依存関係に基づいて、抽出 DAG を自動的に生成します。この抽出 DAG は、データの一貫性と整合性を確保するために、リソースを抽出する最適な順序を決定します。

たとえば、複数の API エンドポイントからデータを抽出し、追加の呼び出しによって特定の変換またはエンリッチメントを行ってからデータベースにロードする必要があるパイプラインを想像してください。`dlt` は、API エンドポイントと変換間の依存関係を分析し、それに応じて抽出 DAG を生成します。抽出 DAG は、依存関係と変換を考慮して、データが正しい順序で抽出されることを保証します。

Airflow にデプロイすると、一貫性を確保し、きめ細かい読み込みを可能にするために、内部 DAG が Airflow タスクに展開されます。

## 増分ロードの定義

[増分ロード](general-usage/incremental-loading.md)は、データ パイプラインの重要な概念であり、データセット全体を再読み込みするのではなく、新しいデータまたは変更されたデータのみを読み込みます。このアプローチには、低レイテンシのデータ転送やコスト削減など、いくつかの利点があります。

### 宣言的ローディング

宣言的ロードでは、ターゲットの宛先にあるデータの望ましい状態を指定できるため、効率的な増分更新が可能になります。`dlt` では、`write_disposition` パラメータを使用して増分ロードの動作を定義できます。3 つのオプションがあります。

1. Full load: このオプションは、宛先データセット全体を、現在の実行でソースによって生成されたデータに置き換えます。これを実現するには、リソースで `write_disposition='replace'` を設定します。これは、ページ ビューなどの記録されたイベントなど、変更されないステートレス データに適しています。
2. Append: 追記 オプションは、既存の宛先データセットに新しいデータを追加します。
`write_disposition='append'` を使用すると、新しいレコードのみがロードされることを保証できます。これは、競合なしで簡単に追加できるステートレス データに適しています。
3. Merge: マージ オプションは、重複排除やアップサートを処理しながら、新しいデータを既存の宛先データセットとマージする場合に使用します。特定のレコードを識別して更新するには、`merge_key` や `primary_key` を使用する必要があります。`write_disposition='merge'` を設定すると、マージベースの増分読み込みを実行できます。

たとえば、GitHub イベントをロードして宛先で更新し、各イベントのインスタンスが 1 つだけ存在するようにするとします。

マージ書き込み処理は次のように使用できます:

```py
@dlt.resource(primary_key="id", write_disposition="merge")
def github_repo_events():
    yield from _get_event_pages()
```

この例では、`github_repo_events` リソースは、`primary_key="id"` を使用したマージ書き込み処理を使用します。これにより、一意の ID で識別される各イベントのコピーが 1 つだけ `github_repo_events` テーブルに存在することが保証されます。`dlt` は、データを段階的に読み込み、重複を排除し、必要なマージ操作を実行します。

### 高度な状態管理

`dlt` の高度な状態管理により、パイプラインの実行中に値を保存および取得できます。保存先で値を永続化しながら、コード内の辞書で値にアクセスします。これにより、増分読み込みを効果的に追跡および管理できます。パイプラインの状態を活用することで、最後の値、チェックポイント、列名の変更などの情報を保持し、パイプラインで後で利用できます。

## データ変換

データ変換は、データ読み込みプロセスにおいて重要な役割を果たします。データの読み込み前と読み込み後に変換を実行できます。その方法は次のとおりです。:

### ロード前

データをロードする前に、Python を使用して柔軟に変換を実行できます。Python の広範なライブラリと関数を活用して、必要に応じてデータを操作および前処理できます。
データをロードする前に[カラムを仮名化する](general-usage/customising-pipelines/pseudonymizing_columns.md)例です。

上記の例では、`pseudonymize_name` 関数は、SHA256 を使用して決定論的ハッシュを生成することで、`name` 列を仮名化します。一貫したマッピングを確保するために、列の値にソルトを追加します。`dummy_source` は、`id` 列と `name` 列を持つダミー データを生成し、`add_map` 関数は各レコードに `pseudonymize_name` 変換を適用します。

### ロード後

データをロードした後の変換には、いくつかのオプションがあります:

#### [dbt の使用](dlt-ecosystem/transformations/dbt/dbt.md)

dbt は、データを変換するための強力なフレームワークです。変換を DAG に構造化して、データベース間の互換性と、テンプレート、バックフィル、テスト、トラブルシューティングなどのさまざまな機能を提供します。`dlt` の dbt ランナーを使用して、dbt をパイプラインにシームレスに統合できます。以下は、データを読み込んだ後に dbt パッケージを実行する例です。

```py
import dlt
from pipedrive import pipedrive_source

# load to raw
pipeline = dlt.pipeline(
    pipeline_name='pipedrive',
    destination='bigquery',
    dataset_name='pipedrive_raw'
)

load_info = pipeline.run(pipedrive_source())
print(load_info)
```
ロードしたデータをdbtデータセットに変換します:
```py
pipeline = dlt.pipeline(
    pipeline_name='pipedrive',
    destination='bigquery',
    dataset_name='pipedrive_dbt'
)

# make venv and install dbt in it.
venv = dlt.dbt.get_venv(pipeline)

# get package from local or GitHub link and run
dbt = dlt.dbt.package(pipeline, "pipedrive/dbt_pipedrive/pipedrive", venv=venv)
models = dbt.run_all()

# show outcome
for m in models:
    print(f"Model {m.model_name} materialized in {m.time} with status {m.status} and message {m.message}")
```

この例では、最初のパイプラインは `pipedrive_source()` を使用してデータをロードします。2 番目のパイプラインは、データを読み込んだ後、`pipedrive` という dbt パッケージを使用して変換を実行します。`dbt.package` 関数は dbt ランナーを設定し、`dbt.run_all()` はパッケージで定義された dbt モデルを実行します。

#### [`dlt` の SQL クライアントの使用](dlt-ecosystem/transformations/sql.md)

もう 1 つのオプションは、`dlt` SQL クライアントを利用して、ロードされたデータをクエリし、SQL ステートメントを使用して変換を実行することです。データベース スキーマを変更したり、テーブル内のデータを操作したりする SQL ステートメントを実行できます。以下は、duckdb で集計された売上データを含む新しいテーブルを作成する例です:

```py
pipeline = dlt.pipeline(destination="duckdb", dataset_name="crm")

with pipeline.sql_client() as client:
    client.execute_sql(
        """ CREATE TABLE aggregated_sales AS
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

この例では、SQL クライアントの `execute_sql` メソッドを使用して SQL ステートメントを実行できます。このステートメントは、値を含む行を `customers` テーブルに挿入します。

#### [Pandas の使用](dlt-ecosystem/transformations/python.md)

クエリ結果をPandasデータフレームとして取得し、Pandasの機能を使用して変換を実行できます。以下は、DuckDBの「issues」テーブルからデータを読み取り、Pandaを使用して反応タイプをカウントする例です:

```py
pipeline = dlt.pipeline(
    pipeline_name="github_pipeline",
    destination="duckdb",
    dataset_name="github_reactions",
    dev_mode=True
)

# get a dataframe of all reactions from the dataset
reactions = pipeline.dataset().issues.select("reactions__+1", "reactions__-1", "reactions__laugh", "reactions__hooray", "reactions__rocket").df()

counts = reactions.sum(0).sort_values(0, ascending=False)
```

これらの変換オプションを活用することで、データをロードする前またはロードした後にデータを整形および操作できるため、特定の要件を満たし、データの品質と一貫性を確保できます。

## 自動正規化の調整

プロセスを効率化するために、`dlt` では、スキーマを明示的に作成するのではなく、暗黙的にソースにアタッチすることを推奨しています。いくつかのグローバル スキーマ設定を提供して、テーブルと列のスキーマをリソース ヒントとデータ自体から生成することができます。`dlt.source` デコレータは、ソース関数内で作成および変更できるスキーマ インスタンスを受け入れます。さらに、スキーマ ファイルをソース Python モジュールに保存し、自動的にロードしてソースのスキーマとして使用することもできます。

`dlt` の自動正規化プロセスを調整することで、生成されたデータベース スキーマが特定の要件を満たし、優先する命名規則、データ型、その他のカスタマイズ ニーズに一致することを確認できます。

### 正規化プロセスのカスタマイズ

`dlt` の正規化プロセスをカスタマイズすることで、特定の要件に合わせて調整することができます。

テーブル名と列名を調整したり、列のプロパティを構成したり、データ型の自動検出器を定義したり、パフォーマンス ヒントを適用したり、優先データ型を指定したり、解凍プロセスで ID が伝播される方法を変更したりできます。

これらのカスタマイズ オプションを使用すると、希望する命名規則、データ型、および全体的なデータ構造に合わせたスキーマを作成できます。`dlt` を使用すると、独自のニーズに合わせて正規化プロセスを柔軟にカスタマイズし、最適な結果を得ることができます。

[スキーマ生成](general-usage/schema.md)を構成する方法の詳細については、リンク先を御覧ください。

### スキーマファイルのエクスポートとインポート

`dlt` を使用すると、データの処理と読み込みの構造と指示を含むスキーマ ファイルをエクスポートおよびインポートできます。スキーマ ファイルをエクスポートすると、それらを直接変更して、必要に応じてスキーマを調整できます。その後、変更したスキーマ ファイルを `dlt` にインポートして、パイプラインで使用できます。

詳細は: [スキーマの調整](./walkthroughs/adjust-a-schema.md)

## `dlt` パイプラインにおけるガバナンスのサポート

`dlt` パイプラインは、パイプラインメタデータの利用、スキーマの適用とキュレーション、スキーマ変更アラートという 3 つの主要なメカニズムを通じて、強力なガバナンス サポートを提供します。

### パイプラインメタデータ

`dlt` パイプラインはメタデータを活用してガバナンス機能を提供します。このメタデータには、タイムスタンプとパイプライン名で構成されるロード ID が含まれます。ロード ID は、データのロードを追跡し、データのリネージとトレーサビリティを容易にすることで、増分変換とデータ保管を可能にします。

[リネージ](general-usage/destination-tables.md#data-lineage)についてもっと読む

### スキーマの強制とキュレーション

`dlt` を使用すると、ユーザーはスキーマを強制および管理して、データの一貫性と品質を確保できます。スキーマは正規化されたデータの構造を定義し、データの処理と読み込みをガイドします。パイプラインは、定義済みのスキーマに準拠することで、データの整合性を維持し、標準化されたデータ処理方法を促進します。

詳細: [スキーマの調整](./walkthroughs/adjust-a-schema.md)

### スキーマの進化

`dlt` は、スキーマの変更をユーザーに警告することで、積極的なガバナンスを可能にします。テーブルや列の変更など、ソース データのスキーマに変更が発生すると、`dlt` は関係者に通知し、変更の確認と検証、下流プロセスの更新、影響分析の実行など、必要なアクションを実行できるようにします。

`dlt` パイプラインのこれらのガバナンス機能は、データ管理プラクティス、コンプライアンス遵守、および全体的なデータ ガバナンスの向上に貢献し、データ処理ライフサイクル全体にわたってデータの一貫性、追跡可能性、および制御を促進します。

### スケーリングと微調整

`dlt`はパイプラインをスケールアップし微調整するためのいくつかのメカニズムと構成オプションを提供します:

- 抽出、正規化、ロードを並行して実行します。
- スレッド プールと非同期実行を介して並列実行されるソースとリソースを書き込みます。
- メモリバッファー、中間ファイルのサイズ、および圧縮オプションを微調整します。

[パフォーマンス](reference/performance.md)の詳細を御覧ください。

### その他の高度なトピック

`dlt` は、コミュニティが必要とする多くの機能とユースケースをサポートする、継続的に成長しているライブラリです。[Slack](https://dlthub.com/community) に参加して、最新のリリースを見つけたり、`dlt` を使用して構築できるものについて話し合ったりしてください。

