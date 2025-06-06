---
title: "Secure data access and sharing"
description: Provide secure data access to your organization
keywords: ["data access", "security", "contracts", "data sharing"]
---

# 安全なデータアクセスと共有

dlt+ は、データサイエンティストやアナリストなどのエンドユーザーが、安全かつ Python フレンドリーな方法で高品質な本番データに簡単にアクセスできるようにします。
[dlt+ プロジェクト](../core-concepts/project.md) は、標準の Python API を公開し、「access」[プロファイル](../core-concepts/profiles.md) を使用して本番データに接続します。
このプロファイルは、ユーザーがデータをどのように操作できるかを指定するように構成できます。例えば、変更が許可されていないデータセットに制限を適用するなどです。

## プロジェクトのパッケージ化

dlt+ プロジェクトは Python パッケージとして配布できます。これにより、エンドユーザーは独自の Python ワークフロー内でデータを簡単に操作できます。
既存の dlt+ プロジェクトをパッケージ化するには、以下の手順が必要です。

1. プロジェクトのルートに `__init__.py` ファイルを追加します。

<details>

<summary>__init__.py example</summary>

```py
"""
A demonstration package that sends GitHub events to Delta Lake, aggregates, and shares via Snowflake

>>> import dlt_package_template
>>>
>>> print(dlt_package_template.catalog())  # list datasets
>>> print(dlt_package_template.catalog().dataset_name) # lists tables in dataset
>>> df_ = dlt_package_template.catalog().dataset_name.table_name.df()  # reads table
"""

import os
import dlt as dlt
from dlt_plus.project import Catalog, EntityFactory, ProjectRunContext, Project, PipelineManager

def access_profile() -> str:
    """Implement this function to select profile assigned to users that import this Python package
    into their own scripts or other modules.
    """
    return "access"


def context() -> ProjectRunContext:
    """Returns the context of this package, including run directory,
    data directory and project config
    """
    from dlt_plus.project.run_context import ensure_project
    return ensure_project(run_dir=os.path.dirname(__file__), profile=access_profile())


def config() -> Project:
    """Returns project configuration and getters of entities like sources, destinations
    and pipelines"""
    return context().project


def entities() -> EntityFactory:
    """Returns methods to create entities in this package likes sources, pipelines etc."""
    return EntityFactory(config())


def runner() -> PipelineManager:
    return PipelineManager(config())


def catalog() -> Catalog:
    """Returns a catalogue with available datasets, which can be read and written to"""
    return Catalog(context())
```
</details>

2. いずれかの Python パッケージ マネージャー (例: [uv](https://docs.astral.sh/uv/)、[poetry](https://python-poetry.org/)、setuptools) を使用してプロジェクトをパッケージ化します。

<details>

<summary>pyproject.toml example</summary>

```toml
[project]
name = "dlt_example_project"
version = "0.0.1"
description = "Description"
requires-python = ">=3.9,<3.13"

dependencies = [
    "dlt>=1.7.0",
    "dlt-plus==0.7.0"
]

[project.entry-points.dlt_package]
dlt-project = "dlt_example_project"
```
</details>

:::info
dlt+ プロジェクトのパッケージ化のための CLI サポートは現在開発中であり、将来のリリースで利用可能になる予定です。
:::

## データへのアクセスと共有

Python パッケージを作成したら、PyPI（プライベートまたはパブリック）または Git リポジトリ経由で配布できます。
作成された Python パッケージにより、ユーザーは Python ワークフロー内でデータにアクセスできるようになります。
このようなワークフローの例：

1. ローカルの Python 環境（ノートブックなど）に Python パッケージを pip でインストールします。

    ```sh
    pip install -U --index-url https://pypi.dlthub.com dlt_example_project
    ```

2. 他の Python モジュールと同様にプロジェクトをインポートします。

    ```py
    import dlt_example_project as dlt_project
    ```

3. データを探索します。

    プロジェクトで宣言されたデータセットは、利用可能なデータセットとテーブルを探索し、ローカルマシンに実際にデータをロードすることなく、それらのスキーマを発見できるデータカタログを作成します。

    ```py
    my_catalog = dlt_project.catalog() # Access the data catalog created by dlt
    print(my_catalog) # Inspect datasets and available tables
    print(my_catalog.github_events_dataset) # Access the dataset github_events_dataset from the catalog
    ```

    この例では、`print(my_catalog)` はカタログ内の 2 つの使用可能なデータセット (s3 バケット内の `github_events_dataset` と Snowflake ウェアハウス内の `reports_dataset`) を表示します。

    ```sh
    Datasets in project dlt_example_project for profile access:
    github_events_dataset@delta_lake[s3://dlt-ci-test-bucket/dlt_plus_demo/lake_1/]
    reports_dataset@warehouse[snowflake://loader:***@kgiotue-wn98412/dlt_data]
    ```

    また、`print(my_catalog.github_events_dataset)` は、データセット `github_events_dataset` で使用可能なテーブルを表示します。

    ```sh
    Dataset github_events_dataset tables in logical schema events@v2
    pull_request_event
    issues_event
    watch_event
    push_event
    public_event
    pull_request_review_event
    create_event
    issue_comment_event
    delete_event
    fork_event
    release_event
    pull_request_review_comment_event
    gollum_event
    commit_comment_event
    member_event
    gollum_event__payload__pages
    push_event__payload__commits
    ```

4. データにアクセスします。

    カタログから操作したいテーブル（例：`issues_event`）を選択し、それらのテーブルのみをローカル環境にロードします。

    ```py
    df = my_catalog.github_events_dataset.issues_event.df()
    ```

    これらは以下の場所に読み込むことができます。
    * Pandas データフレーム（`.df()` を使用）
    * Arrow テーブル（`.arrow()` を使用）
    * SQL（`.sql()` を使用）


5. データに作業を実行します。

    環境にロードしたら、通常のPythonワークフローと同じようにデータを操作できます。
    以下の例では、カスタムPython関数 `aggregate_issues()` がデータの集計を実行します。

    ```py
    reports_df = aggregate_issues(df)
    ```

6. 結果を共有します。

    `.save()` メソッドを使用すると、データを直接保存先に書き戻すことができます。
    例えば、以下のコードは、ステップ 5 の `reports_df` をデータセット `reports_dataset` の新しいテーブル `aggregated_issues` として書き込みます。

    ```py
    print(my_catalog.reports_dataset.save(reports_df, table_name="aggregated_issues"))
    ```

    これらの行を実行すると、次の出力が得られます:

    ```sh
    Pipeline save_aggregated_issues_pipeline load step completed in 7.85 seconds
    1 load package(s) were loaded to destination warehouse and into dataset reports_dataset
    The warehouse destination used snowflake://loader:***@kgiotue-wn98412/dlt_data location to store data
    Load package 1730314457.4512188 is LOADED and contains no failed jobs
    ```

## セキュリティとコントラクト

エンドユーザーがPython APIを使用してデータを操作する際には、「access」と呼ばれるプロファイルを使用します。
データエンジニアは、`dlt.yml` または toml ファイルでこのプロファイルの設定と認証情報を設定することで、このアクセスを管理できます。
各プロファイルのシークレットと設定の詳細については、[こちら](../core-concepts/profiles.md) をご覧ください。

スキーマとデータコントラクトを通じて、ユーザーがデータを書き込む方法にきめ細かな制限を設定できます。
これらの制限は、プロファイルごと、データセットごとに個別に設定できます。

```yaml
profiles:
    access:
        datasets:
            github_events_dataset:
                # no new tables, no column changes
                contract: freeze

            reports_dataset:
                # allow new tables but no column changes
                contract:
                    tables: evolve
                    columns: freeze
                    data_type: freeze
```

この例では、プロファイル「access」を持つユーザーは、データセット「github_events_dataset」内のテーブルへの書き込みや既存テーブルのスキーマ変更が制限されています。
そのため、[前の例](#data-access-and-sharing)のエンドユーザーが、`reports_dataset`ではなくこのデータセットにテーブルを書き戻そうとした場合、次のようになります:

```py
print(my_catalog.github_events_dataset.save(reports_df, table_name="aggregated_issues"))
```

次のようなエラーが発生します:

```sh
PipelineStepFailed: Pipeline execution failed at stage extract when processing package 1730314603.1941314 with exception:

<class 'dlt.common.schema.exceptions.DataValidationError'>
In schema: events: In Schema: events Table: aggregated_issues. Contract on tables with mode freeze is violated. Trying to add table aggregated_issues but new tables are frozen.
```

`reports_dataset` には、ユーザーがテーブルに書き込むことは許可するが、既存のスキーマの変更は制限するコントラクトも設定されています。
つまり、同じユーザーが `reports_dataset` 内の既存のテーブル `aggregated_issues` に新しい列 `id` を追加しようとした場合、次のようになります。

```py
# Access the aggregated_issues table from the reports_dataset in the catalog
reports_df = my_catalog.reports_dataset.aggregated_issues.df()

# Create a new column "id"
reports_df["id"] = 1

# Push back the modified table
print(my_catalog.reports_dataset.save(reports_df, table_name="aggregated_issues"))
```

次のようなエラーが発生します:

```sh
PipelineStepFailed: Pipeline execution failed at stage extract when processing package 1730314610.4309433 with exception:

<class 'dlt.common.schema.exceptions.DataValidationError'>
In schema: out_source: In Schema: out_source Table: aggregated_issues Column: id. Contract on columns with mode freeze is violated. Trying to add column id to table aggregated_issues but columns are frozen.
```

