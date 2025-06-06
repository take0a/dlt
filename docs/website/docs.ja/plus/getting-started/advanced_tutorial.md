---
title: Packaging a dlt+ Project tutorial
description: Using the dlt+ cli commands to package a dlt+ Project and enable secure access to data
keywords: [command line interface, cli, dlt init, dlt+, project]
---

dlt+ プロジェクトをパッケージ化すると、プロジェクトの内部コードに直接アクセスすることなく、データアナリストやデータサイエンスチームなどのチームや関係者間での配布が簡素化されます。
パッケージをインストールすると、標準化された Python インターフェースを介してパイプラインを実行し、本番環境のデータにアクセスできるようになります。

このチュートリアルでは、dlt+ プロジェクトを再利用および配布用にパッケージ化し、pip でインストールできるようにする方法を学習します。


## 前提条件

始める前に、以下の要件を満たしていることを確認してください。

- dlt+ が [インストールガイド](./installation.md) に従ってインストールおよび設定されていること
- [dlt の中核概念](../../reference/explainers/how-dlt-works.md) を理解していること
- [基本プロジェクトチュートリアル](./tutorial.md) を完了していること

さらに、必要な Python パッケージをインストールしてください。

```sh
pip install pandas numpy pyarrow streamlit dlt[duckdb] uv
```


## プロジェクトのパッケージ化

`dlt+` は、配布用にプロジェクトをパッケージ化するためのツールを提供します。
これにより、プロジェクトは `pip` 経由でインストールできるようになり、組織内での共有が容易になります。

パッケージに必要なプロジェクト構造を作成するには、初期化時に `--package` オプションを追加します。

```sh
dlt project init arrow duckdb --package my_dlt_project
```

これは[基本チュートリアル](./tutorial.md)と同じ基本プロジェクトを作成しますが、`my_dlt_project`というモジュール内に配置され、PEP標準に準拠した基本的な`pyproject.toml`ファイルが含まれます。
また、インストール後にパッケージを使用できるようにするためのデフォルトの`__init__.py`ファイルも取得されます。

```sh
.
├── my_dlt_project/       # Your project module
│   ├── __init__.py       # Package entry point
│   ├── dlt.yml           # dlt+ project manifest
│   └── ...               # Other project files
├── .gitignore
└── pyproject.toml        # the main project manifest
```

`dlt.yml` は、パッケージ化されていないプロジェクトと全く同じように動作します。
主な違いは、モジュール構造と `pyproject.toml` ファイルの存在です。
このファイルには、dlt+ がプロジェクトを検出できるようにするための特別なエントリポイント設定が含まれています。

```toml
[project.entry-points.dlt_package]
dlt-project = "my_project"
```

ルート フォルダーから CLI コマンドを使用して、通常どおりパイプラインを実行することもできます:

```sh
dlt pipeline my_pipeline run
```

プロジェクトモジュール内の `__init__.py` ファイルを開くと、パッケージのユーザーが操作する完全なインターフェースが表示されます。
このインターフェースは、フラット（パッケージ化されていない）プロジェクトで使用される [`current`](../features/projects.md#python-api-to-interact-with-dlt-plus-project) インターフェースと非常によく似ています。
主な違いは、デフォルトで `access` プロファイルが自動的に使用されることです。
`__init__.py` ファイルは、プロジェクトのニーズに合わせてカスタマイズできます。

### パッケージ化されたプロジェクトの使用

パッケージ化されたプロジェクトの使用方法を説明するために、データサイエンティストが別のPython環境にプロジェクトをインストールして実行するという実際のシナリオをシミュレートしてみましょう。
この例では、[**uv** パッケージマネージャー](https://github.com/astral-sh/uv) を使用しますが、**poetry** または **pip** を使用する場合も同じ手順が適用されます。インストール手順は [こちら](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) で確認できます。
パッケージ化された dlt+ プロジェクトが `/Volumes/my_drive/my_folder/pyproject.toml` にあると仮定します。
新しいディレクトリに移動し、プロジェクトを初期化します。

```sh
uv init
```

パッケージ化されたプロジェクトをローカル パスから直接インストールします:

```sh
uv pip install /Volumes/my_drive/my_folder
```

これで、dlt+ プロジェクトをこの環境で使用できるようになりました。

例として、`test_project.py` という名前の新しい Python ファイルを作成し、パッケージ化されたプロジェクトを使用して、必要な環境変数を定義します。

```py
# import the packaged project
import my_dlt_project
import os
import pandas as pd

os.environ["MY_PIPELINE__SOURCES__ARROW__ARROW__ROW_COUNT"] = "0"
os.environ["MY_PIPELINE__SOURCES__ARROW__ARROW__SOME_SECRET"] = "0"

if __name__ == "__main__":
    # should print "access" as defined in your dlt package
    print(my_dlt_project.config().current_profile)
    # Run the pipeline from the packaged project
    my_dlt_project.runner().run_pipeline("my_pipeline")
    # should list the defined destinations  
    print(my_dlt_project.config().destinations)
    # get a dataset from the catalog
    dataset = my_dlt_project.catalog().dataset("my_pipeline_dataset")
    # Write a DataFrame to the "my_table" table in the dataset
    dataset.save(pd.DataFrame({"name": ["John", "Jane", "Jim"], "age": [30, 25, 35]}), table_name="my_table")
    # get the row counts of all tables in the dataset as a dataframe
    print(dataset.row_counts().df())
```

uv 仮想環境内でスクリプトを実行します:

```sh
uv run python test_project.py
```

パイプラインを実行すると、dlt+ が提供するさまざまなアクセス方法を使用して、読み込んだデータを探索および共有できます。
[詳細については、「安全なデータアクセスと共有」をご覧ください。](../features/data-access#data-access-and-sharing)

:::info
実際の環境では、データサイエンティストはローカルパスからパッケージをインストールすることはありません。通常は、プライベートな PyPI リポジトリまたは Git URL からパッケージを取得します。
:::


## Next steps

