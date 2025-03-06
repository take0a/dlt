---
title: Pipeline
description: Explanation of what a dlt pipeline is
keywords: [pipeline, source, full refresh, dev mode]
---

# パイプライン

[パイプライン](glossary.md#pipeline)は、Python コードから[宛先](glossary.md#destination)にデータを移動する接続です。パイプラインは、`dlt` [ソース](source.md)または[リソース](resource.md)のほか、ジェネレーター、非同期ジェネレーター、リスト、および任意の反復可能オブジェクトを受け入れます。
パイプラインが実行されると、すべてのリソースが評価され、データが宛先に読み込まれます。

例:

このパイプラインは、オブジェクトのリストを「 three 」という名前の DuckDB テーブルにロードします:

```py
import dlt

pipeline = dlt.pipeline(destination="duckdb", dataset_name="sequence")

info = pipeline.run([{'id':1}, {'id':2}, {'id':3}], table_name="three")

print(info)
```

パイプラインをインスタンス化するには、次の引数で`dlt.pipeline`関数を呼び出します:

- `pipeline_name`: トレースおよび監視イベントでパイプラインを識別し、後続の実行時に状態とデータ スキーマを復元するために使用されるパイプラインの名前。指定されていない場合、`dlt` は現在実行中の Python モジュールのファイル名からパイプライン名を作成します。
- `destination`: dlt がデータをロードする [destination](../dlt-ecosystem/destinations) の名前。`pipeline` の `run` メソッドに指定することもできます。
- `dataset_name`: データがロードされるデータセットの名前。データセットはテーブルの論理グループ、つまりリレーショナルデータベースの `schema` または多くのファイルをグループ化したフォルダーです。また、後でパイプラインの `run` または `load` メソッドに指定することもできます。指定しない場合は、データセットを必要とする宛先 (ほとんどのウェアハウス) ではデフォルトで `{pipeline_name}_dataset` になります。
テーブルをデータセット(またはデータベーススキーマ)に分割しない宛先(ベクターデータベースまたは Clickhouse) では空のままになります。

データをロードするには、`run` メソッドを呼び出し、`data` 引数にデータを渡します。

引数:

- `data` (最初の引数) は、dlt ソース、リソース、ジェネレーター関数、または任意の Iterator または Iterable (つまり、リストまたは `map` 関数の結果) になります。
- `write_disposition` は、テーブルにデータを書き込む方法を制御します。デフォルトは「append」です。
  - `append` は常にテーブルの末尾に新しいデータを追加します。
  - `replace` は既存のデータを新しいデータに置き換えます。
  - `skip` はデータの読み込みを防止します。
  - `merge` は、`primary_key` と `merge_key` のヒントに基づいてデータの重複を排除し、マージします。
- `table_name` は、テーブル名を推測できない場合、つまりリソー​​スやジェネレータ関数の名前から推測できない場合に指定します。

例: このパイプラインは、ジェネレーター「generate_rows(10)」が生成したデータをロードします:

```py
import dlt

def generate_rows(nr):
    for i in range(nr):
        yield {'id':1}

pipeline = dlt.pipeline(destination='bigquery', dataset_name='sql_database_data')

info = pipeline.run(generate_rows(10))

print(info)
```

## パイプライン作業ディレクトリ

`dlt` で作成した各パイプラインは、抽出されたファイル、ロード パッケージ、推論されたスキーマ、実行トレース、[パイプラインの状態](state.md) をローカル ファイル システムのフォルダーに保存します。このようなフォルダーのデフォルトの場所は、ユーザーのホーム ディレクトリ内です: `~/.dlt/pipelines/<pipeline_name>`。

保存された成果物は、コマンド[dlt pipeline info](../reference/command-line-interface.md#dlt-pipeline)使用したり、[プログラム的に](../walkthroughs/run-a-pipeline.md#4-inspect-a-load-process)検査できます。

> 💡 指定された名前のパイプラインは、上記の場所で作業ディレクトリを検索します。そのため、同じ名前のパイプラインを作成する 2 つのパイプライン スクリプトがある場合、それらは同じ作業フォルダーを参照し、すべての可能な状態を共有します。パイプラインを作成するときに、`pipelines_dir` 引数を使用してデフォルトの場所を上書きできます。

> 💡 `dlt.attach` を使用して新しいパイプラインを作成せずに、既存の作業フォルダーに `Pipeline` インスタンスをアタッチできます。

### `pipelines_dir` で作業環境を分離する

たとえば、開発環境、ステージング環境、または本番環境をターゲットにするために、同じ名前で異なる構成の複数のパイプラインを実行できます。
すべての作業フォルダを特定の場所に保存するには、`pipelines_dir`引数を設定します。例えば:

```py
import dlt
from dlt.common.pipeline import get_dlt_pipelines_dir

dev_pipelines_dir = os.path.join(get_dlt_pipelines_dir(), "dev")
pipeline = dlt.pipeline(destination="duckdb", dataset_name="sequence", pipelines_dir=dev_pipelines_dir)
```

このコードは、パイプラインの作業フォルダーを `~/.dlt/pipelines/dev/<pipeline_name>` に保存します。パイプラインの情報/トレースを取得するには、この `~/.dlt/pipelines/dev/` をすべての CLI コマンドに渡す必要があることに注意してください。

## 開発モードで実験する

[新しいパイプライン スクリプトを作成](../walkthroughs/create-a-pipeline.md)すると、さまざまな実験を行うことになります。パイプラインが毎回状態をリセットして新しいデータセットにデータをロードするようにしたい場合は、`dlt.pipeline` メソッドの `dev_mode` 引数を True に設定します。パイプラインが作成されるたびに、`dlt` はデータセット名に日時ベースのサフィックスを追加します。

## パイプラインデータと状態を更新する

`dlt.pipeline` の `refresh` 引数、またはパイプラインの `run` または `extract` メソッドを使用して、ソースの一部またはすべてをリセットできます。
つまり、パイプラインを実行すると、処理中のソース/リソースの状態がリセットされ、使用されている更新モードに応じて、テーブルが削除または切り捨てられます。

`refresh` オプションは、すべてのリレーショナルまたは SQL の宛先、クラウド ストレージ、およびファイル (`filesystem`) で機能します。ベクターデータベース (現在対応中) およびカスタムの宛先では機能しません。

`refresh`引数には、リフレッシュモードを決定するために、次の文字列値のいずれかを指定する必要があります:

### `drop_sources` を使用してソースのテーブルとパイプライン状態を削除します

`pipeline.run` または `pipeline.extract` で処理されているすべてのソースが更新されます。
つまり、スキーマにリストされているすべてのテーブルが削除され、それらのソースに属する状態とすべてのリソースが完全に消去されます。
テーブルは、パイプラインのスキーマと宛先データベースの両方から削除されます。

ソースが 1 つしかない場合、またはすべてのソースを一緒に実行する場合、これは実質的にパイプラインを初めて再度実行するのと同じです。

:::caution
これにより、選択したソースのスキーマ履歴が消去され、最新バージョンのみが保存されます。
:::

```py
import dlt

pipeline = dlt.pipeline("airtable_demo", destination="duckdb")
pipeline.run(airtable_emojis(), refresh="drop_sources")
```

上記の例では、`dlt` に `airtable_emojis` ソースに属するパイプライン状態を消去し、データがロードされた `duckdb` 内のすべてのデータベース テーブルを削除するように指示しています。`airtable_emojis` ソースには、テーブル "_schedule" と "_budget" にロードされる "📆 Schedule" と "💰 Budget" という 2 つのリソースがありました。`dlt` が実行する処理をステップごとに説明します:

1. 宛先に作成されたスキーマ内のすべてのテーブルを検索して、削除するテーブルのリストを収集します。
2. `airtable_emojis` ソースに関連付けられている既存のパイプラインの状態を削除します。
3. `airtable_emojis` ソースに関連付けられたスキーマをリセットします。
4. `extract` および `normalize` ステップを実行します。これにより、新しいパイプライン状態とスキーマが作成されます。
5. `load` ステップを実行する前に、収集されたテーブルはステージング データセットと通常のデータセットから削除されます。
6. スキーマ `airtable_emojis` (ソースに関連付けられている) は `_dlt_version` テーブルから削除されます。
7. 通常どおり `load` ステップを実行し、テーブルが再作成され、新しいスキーマとパイプラインの状態が保存されます。

### `drop_resources` を使用してテーブルとリソースの状態を選択的に削除する

`pipeline.run` または `pipeline.extract` で処理されているリソースに更新を制限します (例: `source.with_resources(...)` を使用)。
これらのリソースに属するテーブルは削除され、リソースの状態 (増分状態を含む) が消去されます。
テーブルは、パイプラインのスキーマと宛先データベースの両方から削除されます。

このモードではソース レベルの状態キーは削除されません (つまり、`dlt.state()[<'my_key>'] = '<my_value>'`)

:::caution
これにより、影響を受けるすべてのソースのスキーマ履歴が消去され、最新のスキーマ バージョンのみが保存されます。
:::

```py
import dlt

pipeline = dlt.pipeline("airtable_demo", destination="duckdb")
pipeline.run(airtable_emojis().with_resources("📆 Schedule"), refresh="drop_resources")
```

上記では、「📆 Schedule」リソースに関連付けられた状態をリセットし、それによって生成されたテーブル (「_schedule」) を削除するように要求しています。他のリソース、テーブル、状態は影響を受けません。`dlt` が内部で何を行うかについての詳細な説明については、`drop_sources` を確認してください。

### `drop_data` を使用してテーブルを選択的に切り捨て、リソースの状態をリセットする

`drop_resources` と同じですが、スキーマからテーブルを削除する代わりに、テーブルからデータのみが削除されます (つまり、SQL 宛先では `TRUNCATE <table_name>` によって)。選択したリソースのリソース状態も消去されます。[インクリメンタルリソース](incremental-loading.md#incremental-loading-with-a-cursor-field) の場合、これによりカーソル状態がリセットされ、`initial_value` からデータが完全に再ロードされます。

この場合、スキーマは変更されません。

```py
import dlt

pipeline = dlt.pipeline("airtable_demo", destination="duckdb")
pipeline.run(airtable_emojis().with_resources("📆 Schedule"), refresh="drop_data")
```

上記では、`extract` ステップの前に "📆 Schedule" の増分状態がリセットされ、データが完全に再取得されます。`load` ステップが開始する直前に、"_schedule" が切り捨てられ、新しい (完全な) テーブル データが挿入/コピーされます。

## ローディングの進行状況を表示する

パイプラインに進行状況モニターを追加できます。通常、その役割は、パイプラインの実行が進行中であることをユーザーに視覚的に確認することです。dltは、すぐに使用できる4つの進行状況モニターをサポートしています:

- [enlighten](https://github.com/Rockhopper-Technologies/enlighten) - ログ記録も可能な進行状況バー付きのステータスバー。
- [tqdm](https://github.com/tqdm/tqdm) - 最も人気のある Python のプログレスバーライブラリ。ノートブックで動作することが確認されています。
- [alive_progress](https://github.com/rsalmei/alive-progress) - 最も派手なアニメーション付き。
- **log** - 進行状況情報をログ、コンソール、またはテキストストリームにダンプします。**本番環境では最も便利な**オプションでメモリと CPU 使用率の統計を追加します。

> 💡 必要なプログレス バー ライブラリを自分でインストールする必要があります。

パイプラインの`progress`引数に進捗モニターを渡します。次の例のように、上記のリストから名前を使用できます:

```py
# create a pipeline loading chess data that dumps
# progress to stdout every 10 seconds (the default)
pipeline = dlt.pipeline(
    pipeline_name="chess_pipeline",
    destination='duckdb',
    dataset_name="chess_players_games_data",
    progress="log"
)
```

進捗モニターを完全に構成できます。以下の2つの例を参照してください:

```py
from airflow.operators.python import get_current_context  # noqa

# log each minute to Airflow task logger
ti = get_current_context()["ti"]
pipeline = dlt.pipeline(
    pipeline_name="chess_pipeline",
    destination='duckdb',
    dataset_name="chess_players_games_data",
    progress=dlt.progress.log(60, ti.log)
)
```

```py
# set tqdm bar color to yellow
pipeline = dlt.pipeline(
    pipeline_name="chess_pipeline",
    destination='duckdb',
    dataset_name="chess_players_games_data",
    progress=dlt.progress.tqdm(colour="yellow")
)
```

`progress` 引数の値は [構成可能](../walkthroughs/run-a-pipeline.md#2-see-the-progress-during-loading) であることに注意してください。
