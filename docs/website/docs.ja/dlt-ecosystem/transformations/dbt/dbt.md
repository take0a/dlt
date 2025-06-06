---
title: Transform data with dbt
description: Transforming the data loaded by a dlt pipeline with dbt
keywords: [transform, dbt, runner]
---

# dbt によるデータの変換

:::tip dlt+
dbt モデルを自動的に生成したい場合は、[dlt+](../../../plus/features/transformations/dbt-transformations.md) を参照してください。
:::

[dbt](https://github.com/dbt-labs/dbt-core)は、DAGへの変換を簡単に構造化できるフレームワークです。dbtを使用する利点は次のとおりです:

- dlt→dbt パイプラインのエンドツーエンドでクロス DB な互換性。
- 学習曲線が低く、SQL アナリストにとって使いやすい。
- 使用時の柔軟性と構成可能性が高く、テンプレートをサポートし、バックフィルなどを実行できます。
- テストと迅速なトラブルシューティングのサポート。

## dlt の dbt ランナー

dbt ランナーを使用すると、`dlt` で dbt を実行できます。

dbtランナーは:

- dbt の仮想環境を即座に作成できます。
- オンラインソース (GitHub など) またはローカルファイルから dbt パッケージを実行できます。
- 構成と資格情報を dbt に渡すため、`dlt` と別に処理する必要がなく、dbt をその場で構成できるようになります。

## dbtランナーの使い方

dbt ランナーの使用方法の例については、[jaffle shop の例](https://github.com/dlt-hub/dlt/blob/devel/docs/examples/archive/dbt_run_jaffle.py) を参照してください。
以下は、`dlt` パイプラインを実行し、次に `dlt` 経由で dbt パッケージを実行する別の例です:

> 💡 Docstring は IDE で読み取ることができます。

```py
# Load all Pipedrive endpoints to the pipedrive_raw dataset
pipeline = dlt.pipeline(
    pipeline_name='pipedrive',
    destination='bigquery',
    dataset_name='pipedrive_raw'
)

load_info = pipeline.run(pipedrive_source())
print(load_info)

# Create a transformation on a new dataset called 'pipedrive_dbt'
# We created a local dbt package
# and added pipedrive_raw to its sources.yml
# The destination for the transformation is passed in the pipeline
pipeline = dlt.pipeline(
    pipeline_name='pipedrive',
    destination='bigquery',
    dataset_name='pipedrive_dbt'
)

# Make or restore venv for dbt, using the latest dbt version
# NOTE: If you have dbt installed in your current environment, just skip this line
#       and the `venv` argument to dlt.dbt.package()
venv = dlt.dbt.get_venv(pipeline)

# Get runner, optionally pass the venv
dbt = dlt.dbt.package(
    pipeline,
    "pipedrive/dbt_pipedrive/pipedrive",
    venv=venv
)

# Run the models and collect any info
# If running fails, the error will be raised with a full stack trace
models = dbt.run_all()

# On success, print the outcome
for m in models:
    print(
        f"Model {m.model_name} materialized" +
        f" in {m.time}" +
        f" with status {m.status}" +
        f" and message {m.message}"
    )
```

## パイプラインなしで dbt ランナーを実行する方法

dbt ランナーは dlt パイプラインなしでも使用できます。以下の例では、指定した dbt プロファイルを使用して **jaffle shop** を複製して実行します。
これは、dbt が現在の Python 環境にインストールされており、`profile.yml` が Python スクリプトと同じフォルダーにあることを前提としています。
<!--@@@DLT_SNIPPET ./dbt-snippets.py::run_dbt_standalone-->

**duckdb** プロファイルの例を以下に示します:

```yaml
config:
  # Do not track usage, do not create .user.yml
  send_anonymous_usage_stats: False

duckdb_dlt_dbt_test:
  target: analytics
  outputs:
    analytics:
      type: duckdb
      # Schema: "{{ var('destination_dataset_name', var('source_dataset_name')) }}"
      path: "duckdb_dlt_dbt_test.duckdb"
      extensions:
        - httpfs
        - parquet
```

dbt デバッグログを使用してサンプルを実行できます: `RUNTIME__LOG_LEVEL=DEBUG python dbt_standalone.py`

## その他の変換ツール

ロード前にデータを変換したい場合は、Python を使用できます。ロード後にデータを変換したい場合は、dbt または次のいずれかを使用できます:

1. [`dlt` SQL client.](../sql.md)
2. [Python でデータフレームまたは arrow テーブルを処理](../python.md)

