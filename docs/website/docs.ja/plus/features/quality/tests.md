---
title: Test utils
description: dlt+ Test utils
keywords: ["dlt+", "data tests", "test"]
---

## はじめに

dlt+ は、dlt+ プロジェクトのテストを簡素化する強力なフィクスチャとユーティリティを備えた `pytest` プラグインを提供します。これらのテストユーティリティは `dlt-plus-tests` に個別にパッケージ化されているため、開発依存関係として簡単にインストールできます。パッケージのインストール方法については、[インストールガイド](#installation) をご覧ください。

`dlt-plus-tests` パッケージには以下が含まれます。

- [定義済みのフィクスチャとユーティリティ](#predefined-fixtures-and-utils)
- [追加の `pytest.ini` オプション](#pytestini-options)
- [`pytest_config` セットアップ](#pytest-config-setup) により、テストが正しいコンテキストで実行され、`tests` プロファイルに切り替わります。


## インストール

現在、`dlt-plus-tests` は dltHub PyPI レジストリで利用可能です。
ただし、まもなく `pypi.org` に移行される予定です。

```sh
pip install --index-url https://pypi.dlthub.com --no-deps  dlt-plus-tests
```

## 定義済みのフィクスチャとユーティリティ

dlt-plus-tests パッケージは、定義済みのフィクスチャとユーティリティ関数のセットを提供します。

* フィクスチャは `dlt_plus_tests.fixtures` で利用できます。
* ユーティリティ関数は `dlt_plus_tests.utils` で見つかります。

### フィクスチャ

必須フィクスチャを有効にするには、`conftest.py` に以下のインポートを追加します。

```py
from dlt_plus_tests.fixtures import (
    auto_preserve_environ as auto_preserve_environ,
    drop_pipeline as drop_pipeline,
    autouse_test_storage as autouse_test_storage,
)
```

これらのフィクスチャを有効にするには、明示的にインポートする必要があります。フィクスチャの簡単な説明は以下をご覧ください:

| Fixture Name                     | Description                                                                   | Fixture Settings                 |
| -------------------------------- | ----------------------------------------------------------------------------- | -------------------------------- |
| `auto_preserve_environ`          | テスト前に環境変数を保存し、テスト後に復元します。 | `autouse=True`                   |
| `auto_drop_pipeline`             | 'no_load' でマークされていない限り、テスト実行後にアクティブなパイプライン データを削除します。 | `autouse=True`                   |
| `autouse_test_storage`           | プロジェクト コンテキストのテスト ストレージをクリーンアップして提供します。 | `autouse=True`                   |
| `auto_unload_modules`            | これらのテストで検査されたすべてのモジュールをアンロードします。  | `autouse=True`                   |
| `auto_preserve_run_context`      | テストが完了したら、初期実行コンテキストを復元します。 | `autouse=True`                   |
| `auto_preserve_sources_registry` | テストのソース レジストリを保存および復元します。 | `autouse=True, scope="function"` |
| `auto_cwd_to_local_dir`          | テスト実行のために作業ディレクトリを一時ディレクトリに変更します。 | `autouse=True`                   |
| `auto_test_access_profile`       | 返されるプロファイル名に 'tests-' をプレフィックスとして追加して、アクセス プロファイルをモックします。  | `autouse=True`                   |
|                                  |                                                                               |                                  |

### テスト実行

設定により、テスト対象プロジェクトの `dlt.yml` で実行コンテキストが有効化されます。`tests` プロファイルが有効化されます（必ず存在する必要があります）。

テストプロジェクトの実行コンテキストでは、以下のようになります。
- `run_dir` はテスト対象プロジェクトを指します。
- `data_dir` は `_data/tests/` を指します。

:::note
`autouse_test_storage` フィクスチャ:
* `data_dir` (通常は `_data/tests`) フォルダをクリーンアップします (プロジェクトのルートディレクトリを基準とします)
* `local_dir` (通常は `_data/tests/local`) フォルダをクリーンアップします (プロジェクトのルートディレクトリを基準とします)
:::

### ユーティリティ

負荷の検証、テーブル数の確認、メトリクスの検査などを行うための便利なユーティリティを `utils.py` からインポートできます。

| Name                        | Type     | Description                                                                                                                                                                               |
| --------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IsInstanceMockMatch`       | Class    |比較をモックするためのヘルパー: 比較対象のオブジェクトが指定されたクラスのインスタンスである場合、`__eq__` メソッドは `True` を返します。|
| `get_test_project_context`  | Function | `dlt_plus` から現在の `ProjectRunContext` を取得します。|
| `get_local_dir`             | Function | 現在のプロジェクトの構成からローカル ディレクトリへのパスを取得します。|
| `clean_test_storage`        | Function | 既存のデータディレクトリを削除して再作成し、プロジェクトの一時ディレクトリに `FileStorage` を設定します。オプションで `tests/.dlt` から設定ファイルをコピーします。|
| `delete_test_storage`       | Function |テスト ストレージで使用されるフォルダーが存在する場合は削除します。 |
| `drop_active_pipeline_data` | Function | 現在アクティブなパイプラインのすべてのデータセットを削除し、その作業フォルダーを削除しようとしてから、パイプライン コンテキストを非アクティブ化します。 |
| `assert_load_info`          | Function | 指定された数のロードパッケージが正常にロードされ、失敗したジョブがないことを確認します。失敗したジョブが存在する場合はエラーが発生します。 |
| `load_table_counts`         | Function | パイプラインの SQL クライアントをクエリして、指定されたテーブル名の行数の辞書を返します。 |
| `load_tables_to_dicts`      | Function | 指定されたテーブルの内容を辞書のリストとしてパイプラインから取得します。オプションでシステム列 (`_dlt*`) を除外し、結果を指定されたキーで並べ替えることができます。 |
| `assert_records_as_set`     | Function | 2 つの辞書リストをそれぞれキーと値のペアのセットに変換して比較し、順序に関係なく一致することを確認します。 |


## pytest.ini オプション

このプラグインは、2 つの追加の `pytest.ini` オプションを導入します。これらは自動的に設定され、通常は変更する必要はありません。

```toml
[tool.pytest.ini_options]
dlt_tests_project_path="..."
dlt_tests_project_profile="..."
```

## Pytest の設定

以下は、UV 用の pyproject.toml 設定の例です。

```toml
[project]
name = "dlt-portable-data-lake-demo"

dependencies = [
    "dlt[duckdb,parquet,deltalake,filesystem,snowflake]>=1.4.1a0",
    "dlt-plus>=0.2.6",
    "enlighten",
    "duckdb<=1.1.2"
]

[tool.uv]
dev-dependencies = [
    "dlt-plus-tests>=0.1.2",
]

[[tool.uv.index]]
name = "dlt-hub"
url = "https://pypi.dlthub.com"
explicit=true

[tool.uv.sources]
dlt-plus = { index = "dlt-hub" }
dlt-plus-tests = { index = "dlt-hub" }
```

## テストの作成

テストを作成する際は、dlt プロジェクト API を使用してプロジェクトエンティティをリクエストし、実行することができます。例:

```py
from dlt_plus.project import Project
from dlt_plus.project.entity_factory import EntityFactory
from dlt_plus.project.pipeline_manager import PipelineManager
from dlt_plus_tests.fixtures import auto_test_access_profile as auto_test_access_profile
from dlt_plus_tests.utils import assert_load_info, load_table_counts

def test_events_to_data_lake(dpt_project_config: Project) -> None:
    """Make sure we dispatch the events to tables properly"""
    factory = EntityFactory(dpt_project_config)
    github_events = factory.get_source("events")
    events_to_lake = factory.get_pipeline("events_to_lake")
    info = events_to_lake.run(github_events())
    assert_load_info(info)

    # Did I load my test data?
    assert load_table_counts(
        events_to_lake, *events_to_lake.default_schema.data_table_names()
    ) == {
        "issues_event": 604,
    }

def test_t_layer(dpt_project_config: Project) -> None:
    """Make sure that our generated dbt package creates expected reports in the data warehouse"""
    pipeline_manager = PipelineManager(dpt_project_config)
    info = pipeline_manager.run_pipeline("events_to_lake")
    assert_load_info(info)
```

ここでは、`dpt_project_config` フィクスチャを介して現在のプロジェクトを取得し、`EntityFactory` と `PipelineManager` を使用してエンティティのインスタンスを取得して実行します。
テストプラグインは、各テストがクリーンな状態で開始され、`test` プロファイルがアクティブになり、パイプラインによって作成されたデータセット（リモートの宛先でも）が削除されることを保証します。

