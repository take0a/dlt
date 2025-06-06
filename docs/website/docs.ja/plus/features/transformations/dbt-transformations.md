---
title: dbt generator
description: Generate dbt models automatically
---

**dbt ジェネレータ** は、DLT によって取り込まれたデータを使用して、DBT プロジェクトのスキャフォールディングを作成します。
パイプライン スキーマを分析し、ステージング スキーマとファクト スキーマを自動生成します。
DLT で構成された出力先と統合することで、コード作成を自動化し、増分ロードをサポートし、取り込みレイヤーと変換レイヤーの両方で新しいレコードのみが処理されるようにします。

DBT ジェネレータは、ローカル変換機能の一部としても、スタンドアロン ツールとしても使用でき、あらゆる DLT パイプライン用の DBT モデルを生成できます。
ここでは、DBT ジェネレータをスタンドアロン機能として説明しますが、ここで説明するすべての情報は、ローカル変換で使用する場合にも適用できます。

DBT ジェネレータの動作は次のとおりです。

- パイプライン スキーマを自動的に検査し、ステージング レイヤーとマート レイヤーを備えたベースライン DBT プロジェクトを生成します。
ジェネレータは、ステージング スキーマ、ディメンション スキーマ、ファクト スキーマを作成できます。

- さらに、dlt dbt ジェネレーターを使用すると、スキーマテーブル間のリレーションシップを定義でき、これを使用してファクトテーブルを自動的に作成できます。

- 生成されたプロジェクトは、パイプラインに既に提供されている資格情報を使用して実行でき、入力データを段階的に処理できます。

## ファクトテーブルへのリレーションシップヒントの追加

ファクトテーブルを生成するには、まずパイプラインにリレーションシップヒントを追加する必要があります。
リレーションシップはこれらのキーに基づいているため、各テーブルに主キーが定義されていることを確認する必要があります。

```py
import dlt


@dlt.resource(name="customers", primary_key="id")
def customers():
    ...

```

リレーションシップのヒントを追加するには、リレーションシップ アダプターを使用します:

```py
import dlt
from dlt_plus.dbt_generator.utils import table_reference_adapter


# Example countries table
@dlt.resource(name="countries", primary_key="id", write_disposition="merge")
def countries():
    yield from [
        {"id": 1, "name": "USA"},
        {"id": 2, "name": "Germany"},
    ]


# Example companies table
@dlt.resource(name="companies", primary_key="id", write_disposition="merge")
def companies():
    yield from [
        {"id": 1, "name": "GiggleTech", "country_id": 2},
        {"id": 2, "name": "HappyHacks", "country_id": 1},
    ]


# Example customers table which references company
@dlt.resource(name="customers", primary_key="id", write_disposition="merge")
def customers():
    yield from [
        {"id": 1, "name": "Andrea", "company_id": 1},
        {"id": 2, "name": "Violetta", "company_id": 2},
        {"id": 3, "name": "Marcin", "company_id": 1},
    ]


# Example orders table which references customer
@dlt.resource(name="orders", primary_key="id", write_disposition="merge")
def orders():
    yield from [
        {"id": 1, "date": "1-2-2020", "customer_id": 1},
        {"id": 2, "date": "14-2-2020", "customer_id": 2},
        {"id": 3, "date": "18-2-2020", "customer_id": 1},
        {"id": 4, "date": "1-3-2020", "customer_id": 3},
        {"id": 5, "date": "2-3-2020", "customer_id": 3},
    ]

# Run your pipeline
p = dlt.pipeline(pipeline_name="example_shop", destination="duckdb")
p.run([customers(), companies(), orders(), countries()])

# Define relationships in your schema
table_reference_adapter(
    p,
    "companies",
    references=[
        {
            "referenced_table": "countries",
            "columns": ["country_id"],
            "referenced_columns": ["id"],
        }
    ],
)

table_reference_adapter(
    p,
    "customers",
    references=[
        {
            "referenced_table": "companies",
            "columns": ["company_id"],
            "referenced_columns": ["id"],
        }
    ],
)

table_reference_adapter(
    p,
    "orders",
    references=[
        {
            "referenced_table": "customers",
            "columns": ["customer_id"],
            "referenced_columns": ["id"],
        }
    ],
)

```

:::note
パイプラインが認識していない関係のみをアダプタに明示的に渡す必要があります。つまり、正規化段階で dlt によって作成された親子関係は既に認識されているため、定義する必要はありません。
:::

## ベースライン・プロジェクトの生成

DLTパイプラインがローカルで少なくとも1回実行されているか、または宛先から復元されていることを確認してください。
次に、パイプラインが配置されているディレクトリに移動し、その名前を使用して次のコマンドを実行し、既存のすべてのパイプライン・テーブルに対応するディメンション・テーブルを含むベースラインDBTプロジェクトを作成します。

```sh
dlt dbt generate <pipeline-name>
```

このコマンドは、次の構造のプロジェクトが含まれる `dbt_<pipeline-name>` という名前の新しいフォルダーを生成します。

```sh
dbt_<pipeline-name>/
├── analysis/
├── macros/
├── models/
│   ├── marts/
│   │   ├── dim_<pipeline-name>__<table1>.sql
│   │   ├── dim_<pipeline-name>__<table2>.sql
│   │   └── dim_<pipeline-name>__<tableN>.sql
│   ├── staging/
│   │   ├── sources.yml
│   │   ├── stg_<pipeline-name>__<table1>.sql
│   │   ├── stg_<pipeline-name>__<table2>.sql
│   │   └── stg_<pipeline-name>__<tableN>.sql
│   ├── <pipeline-name>_dlt_active_load_ids.sql # Used for incremental processing of data
│   └── <pipeline-name>_dlt_processed_load.sql # Used for incremental processing of data
├── tests/
├── dbt_project.yml
└── requirements.txt
```

さらに、ジェネレーターを実行したディレクトリには、`run_<pipeline-name>_dbt.py` という名前の新しい Python ファイルがあり、これを実行してプロジェクトを実行できます。


## ファクトテーブルの生成

ディメンションテーブルを含むベースプロジェクトを作成したら、次のコマンドを実行して、以前に追加したリレーションシップヒントを使用するファクトテーブルを作成できます。

```sh
dlt dbt generate <pipeline-name> --fact <fact_table_name>
```

指定する `<fact_table_name>` は、リレーションシップが見つかるベーステーブルの名前である必要があります。
このファクトテーブルは、DLT で定義された親子関係を通じて検出されたすべての関連テーブル ID と、アダプタを通じて手動で追加されたリレーションシップ ID を自動的に結合します。
その後、生成されたモデルで追加のフィールドを選択して追加できます。

上記の例では、`orders` テーブルに対してこれを実行できます。

```sh
dlt dbt generate example_shop --fact orders
```

これにより、dbt プロジェクトの `marts` フォルダーに `fact_<pipeline-name>__orders.sql` モデルが生成されます。

```sh
dbt_<pipeline-name>/
├── analysis/
├── macros/
├── models/
│   ├── marts/
│   │   ├── dim_<pipeline-name>__<table1>.sql
│   │   ├── dim_<pipeline-name>__<table2>.sql
│   │   └── dim_<pipeline-name>__<tableN>.sql
│   │   └── fact_<pipeline-name>__orders.sql # <-- This is the fact table model
│   ├── staging/
│   │   ├── sources.yml
│   │   ├── stg_<pipeline-name>__<table1>.sql
│   │   ├── stg_<pipeline-name>__<table2>.sql
│   │   └── stg_<pipeline-name>__<tableN>.sql
│   ├── <pipeline-name>_dlt_active_load_ids.sql  # Used for incremental processing of data
│   └── <pipeline-name>_dlt_processed_load.sql  # Used for incremental processing of data
├── tests/
├── dbt_project.yml
└── requirements.txt
```

## dbt プロジェクトの実行

`dlt dbt generate <パイプライン名>` によって生成された前述のスクリプトを使用して、dbt プロジェクトを実行できます。

```sh
python run_<pipeline_name>_dbt.py
```

このスクリプトは、dbt 変換を実行し、結果を `<original-dataset>_transformed` という名前の新しいデータセットに読み込み、dbt テストを実行します。必要に応じて、スクリプト内でデータセット名を直接変更できます。

`dbt run` コマンドの出力を確認するには、ログレベルを上げてください。例:

```sh
RUNTIME__LOG_LEVEL=INFO python run_<pipeline_name>_dbt.py
```

または `config.toml` を設定することによって:

```toml
[runtime]
log_level="INFO"
```

## dbt パッケージを直接実行する

パイプラインインスタンスを使用せずに dbt パッケージを実行する場合は、[dbt ランナーのドキュメント](../../../dlt-ecosystem/transformations/dbt/dbt.md) を参照してください。

## 増分処理について

dlt はロード パッケージに一意の ID を生成し、データセット内のすべてのテーブルの `_dlt_load_id` 列に格納します。
この列は、各行が属する特定のロード パッケージを示します。

生成された dbt プロジェクトは、これらのロード ID を使用してデータを増分処理します。
このプロセスを管理するために、プロジェクトにはロード パッケージのステータスを追跡する 2 つの主要なテーブルが含まれています。

- `<pipeline_name>_dlt_active_load_ids`: 各 dbt 実行の開始時に、このテーブルには、以前の dbt 実行で成功し、まだ処理されていないすべてのロード ID (アクティブ ロード ID) が入力されます。
ステージング テーブルには、これらのアクティブ ロード ID に関連付けられた行のみが入力されます。
- `<pipeline_name>_dlt_processed_load_ids`: 各 dbt 実行の終了時に、アクティブ ロード ID がタイムスタンプとともにこのテーブルに記録されます。
これにより、各ロード ID がいつ処理されたかを追跡できます。

