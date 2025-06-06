---
title: Load data from a SQL database
description: How to extract data from a SQL Database using dlt's SQL Database core source
keywords: [sql connector, sql database pipeline, sql database]
---

このチュートリアルでは、dlt を使用して SQL データベース (PostgreSQL、MySQL、Microsoft SQL Server、Oracle、IBM DB2 など) から任意の dlt が対応する宛先 (Postgres、BigQuery、Snowflake、DuckDB など) にデータをロードする方法を説明します。

再現を容易にするために、[パブリックな MySQL の RFam データベース](https://docs.rfam.org/en/latest/database.html) からローカル DuckDB インスタンスにデータをロードします。

## 学ぶ内容

- 基本的なSQLデータベースパイプラインの設定方法
- 「追加」、「置換」、「マージ」ロード戦略を実装する方法
- データをインクリメンタルにロードする方法

## 0. 前提条件

- Python 3.9 以上がインストールされている
- 仮想環境がセットアップされている
- dlt がインストールされている。[インストールガイド](../reference/installation)の指示に従って、新しい仮想環境を作成し、`dlt` パッケージをインストールしてください。

## 1. 新しい dlt プロジェクトを作成する

`dlt init`コマンドを使用して、現在の作業ディレクトリに新しい dlt プロジェクトを初期化します:

```sh
dlt init sql_database duckdb
```

これは、SQL データベースから DuckDB パイプラインに必要なファイルとフォルダーを作成する便利な CLI コマンドです。`duckdb` を他の [サポートされている宛先](../dlt-ecosystem/destinations) に簡単に置き換えることができます。

このコマンドを実行すると、プロジェクトは次の構造になります。:

```text
├── .dlt
│   ├── config.toml
│   └── secrets.toml
├── sql_database_pipeline.py
└── requirements.txt
```

各ファイルの機能は次のとおりです:

- `sql_database_pipeline.py`: これは、データパイプラインを定義するメインスクリプトです。SQL データベースのパイプラインを構成する方法を示すさまざまな例が含まれています。
- `requirements.txt`: このファイルには、プロジェクトに必要なすべての Python 依存関係がリストされます。
- `.dlt/`: このディレクトリには、プロジェクトの[構成ファイル](../general-usage/credentials/)が含まれています。:
    - `secrets.toml`: このファイルには、資格情報、API キー、トークン、その他の機密情報が保存されます。
    - `config.toml`: このファイルには、`dlt` プロジェクトの構成設定が含まれています。

:::note
パイプラインを本番環境にデプロイする場合、すべての構成を TOML ファイルで管理するのは不便な場合があります。この場合、代わりに dlt で利用可能な環境変数またはその他の [構成プロバイダー](../general-usage/credentials/setup) を使用してシークレットと構成を保存することを強くお勧めします。
:::

## 2. パイプラインスクリプトを構成する

必要なファイルが準備できたら、パイプライン スクリプトの作成を開始できます。既存のファイル `sql_database_pipeline.py` には、さまざまなデータ読み込みシナリオを開始するのに役立つ、事前設定されたサンプル関数が多数含まれています。ただし、このチュートリアルでは、新しい関数を最初から作成します。

:::note
スクリプトをそのまま実行すると、関数 `load_standalone_table_resource()` が実行されるので、メイン ブロック内からの関数呼び出しをコメント アウトすることを忘れないでください。
:::


次の関数は、テーブル `family` と `genome` をロードします。

```py
import dlt
from dlt.sources.sql_database import sql_database

def load_tables_family_and_genome():

    # Create a dlt source that will load tables "family" and "genome"
    source = sql_database().with_resources("family", "genome")

    # Create a dlt pipeline object
    pipeline = dlt.pipeline(
        pipeline_name="sql_to_duckdb_pipeline", # Custom name for the pipeline
        destination="duckdb", # dlt destination to which the data will be loaded
        dataset_name="sql_to_duckdb_pipeline_data" # Custom name for the dataset created in the destination
    )

    # Run the pipeline
    load_info = pipeline.run(source)

    # Pretty print load information
    print(load_info)

if __name__ == '__main__':
    load_tables_family_and_genome()

```

説明:
- `sql_database` ソースには `sql_database()` と `sql_table()` という 2 つの組み込みヘルパー関数があります。:
    - `sql_database()` は、`with_resource()` メソッド内で渡されたテーブル (この例では、`"family"` と `"genome"`) を反復的にロードする [dlt ソース関数](../general-usage/source) です。
    - `sql_table()` は、スタンドアロン テーブルをロードする [dlt リソース関数](../general-usage/resource) です。たとえば、テーブル `"family"` のみをロードしたい場合は、`sql_table(table="family")` を使用して実行できます。
- `dlt.pipeline()` は、宛先が DuckDB となる `"sql_to_duckdb_pipeline"` という名前の `dlt` パイプラインを作成します。
- `pipeline.run()` メソッドはデータを宛先にロードします。

## 3. 資格情報を追加する

SQL データベースに正常に接続するには、パイプラインに資格情報を渡す必要があります。dlt は、生成された TOML ファイル内でこの情報を自動的に検索します。

次のように、[接続の詳細](https://docs.rfam.org/en/latest/database.html)を `secrets.toml` 内に貼り付けるだけです。:
```toml
[sources.sql_database.credentials]
drivername = "mysql+pymysql" # database+dialect
database = "Rfam"
password = ""
username = "rfamro"
host = "mysql-rfam-public.ebi.ac.uk"
port = 4497
```

あるいは、資格情報を接続文字列として貼り付けることもできます:
```toml
sources.sql_database.credentials="mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam"
```

資格情報の形式とその他の接続方法の詳細については、[SQL データベースへの接続の構成](../dlt-ecosystem/verified-sources/sql_database#credentials-format) のセクションを参照してください。


## 4. 依存関係をインストールする

パイプラインを実行する前に、必要な依存関係をすべてインストールしてください:
1. **一般的な依存関係**: これらは、`sql_database` ソースに必要な一般的な依存関係です。
    ```sh
    pip install -r requirements.txt
    ```
2. **データベース特有の依存関係**: 一般的な依存関係に加えて、このチュートリアルでは MySQL データベースに接続するために `pymysql` もインストールする必要があります:
    ```sh
    pip install pymysql
    ```

    説明: dlt は SQLAlchemy を使用してソース データベースに接続するため、`pymysql` (MySQL)、`psycopg2` (Postgres)、`pymssql` (MSSQL)、`snowflake-sqlalchemy` (Snowflake) などのデータベース固有の SQLAlchemy 方言も必要です。使用可能な方言の完全なリストについては、[SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/en/20/dialects/#external-dialects) を参照してください。

## 5. パイプラインを実行する

手順1～4を実行した後、次のコマンドを実行することでパイプラインを正常に実行できるはずです:

```sh
python sql_database_pipeline.py
```
実行すると、dlt プロジェクトのディレクトリに `sql_to_duckdb_pipeline.duckdb` ファイルが作成され、そこにロードされたデータが含まれます。

## 6. データを探索する

dlt には、ロードされたデータを操作できる組み込みのブラウザアプリケーションが付属しています。これを有効にするには、次のコマンドを実行します:

```sh
pip install streamlit
```

次に、以下のコマンドを実行してデータブラウザアプリを起動します。:

```sh
dlt pipeline sql_to_duckdb_pipeline show
```

読み込まれたデータを調べたり、クエリを実行したり、パイプライン実行の詳細を確認したりできます。

![streamlit-screenshot](https://storage.googleapis.com/dlt-blog-images/docs-sql-database-tutorial-streamlit-screenshot.png)

## 7. 読み込んだデータを追加、置換、または結合する

`python sql_database_pipeline.py` でパイプラインを再度実行してみてください。すべてのテーブルにデータが重複していることがわかります。これは、dlt がデフォルトでロードごとに宛先テーブルにデータを追加するためです。この動作は、`pipeline.run()` メソッド内の `write_disposition` パラメータを設定することで調整できます。設定可能な値は次のとおりです。:

- `append`: データを宛先テーブルに追加します。これがデフォルトです。
- `replace`: 宛先テーブル内のデータを新しいデータに置き換えます。
- `merge`: 主キーに基づいて、新しいデータを宛先テーブル内の既存のデータとマージします。

### 置換するロード

各行でデータが重複するのを防ぐには、`write_disposition` を `replace` に設定します:

```py
import dlt
from dlt.sources.sql_database import sql_database

def load_tables_family_and_genome():

    source = sql_database().with_resources("family", "genome")

    pipeline = dlt.pipeline(
        pipeline_name="sql_to_duckdb_pipeline",
        destination="duckdb",
        dataset_name="sql_to_duckdb_pipeline_data"
    )

    load_info = pipeline.run(source, write_disposition="replace") # Set write_disposition to load the data with "replace"

    print(load_info)

if __name__ == '__main__':
    load_tables_family_and_genome()

```

`sql_database_pipeline.py` を使用してパイプラインを再度実行します。今回は、宛先テーブルでデータが追加されるのではなく、置き換えられます。

### マージするロード

新しいデータがロードされるときに既存のデータを更新する場合は、`merge` 書き込み処理を使用できます。これには、テーブルの主キーを指定する必要があります。主キーは、新しいデータを宛先テーブルの既存のデータと一致させるために使用されます。

前の例では、`pipeline.run()` 内で `write_disposition="replace"` を設定し、すべてのテーブルが `replace` でロードされるようにしました。ただし、`apply_hints` メソッドを使用して、各テーブルごとに `write_disposition` 戦略を個別に定義することもできます。以下の例では、各テーブルで `apply_hints` を使用して、マージに異なる主キーを指定しています。:

```py
import dlt
from dlt.sources.sql_database import sql_database

def load_tables_family_and_genome():

    source = sql_database().with_resources("family", "genome")

    # specify different loading strategy for each resource using apply_hints
    source.family.apply_hints(write_disposition="merge", primary_key="rfam_id") # merge table "family" on column "rfam_id"
    source.genome.apply_hints(write_disposition="merge", primary_key="upid") # merge table "genome" on column "upid"

    pipeline = dlt.pipeline(
        pipeline_name="sql_to_duckdb_pipeline",
        destination="duckdb",
        dataset_name="sql_to_duckdb_pipeline_data"
    )

    load_info = pipeline.run(source)

    print(load_info)

if __name__ == '__main__':
    load_tables_family_and_genome()
```

## 8. インクリメンタルにデータをロードする

多くの場合、各ロードでデータセット全体をロードするのではなく、新しいデータまたは変更されたデータのみをロードします。dlt は、[インクリメンタルなロード](../general-usage/incremental-loading) によりこれを簡単にします。

以下の例では、テーブル「family」を列「updated」に基づいて増分ロードするように設定しています:

```py
import dlt
from dlt.sources.sql_database import sql_database

def load_tables_family_and_genome():

    source = sql_database().with_resources("family", "genome")

    # only load rows whose "updated" value is greater than the last pipeline run
    source.family.apply_hints(incremental=dlt.sources.incremental("updated"))

    pipeline = dlt.pipeline(
        pipeline_name="sql_to_duckdb_pipeline",
        destination="duckdb",
        dataset_name="sql_to_duckdb_pipeline_data"
    )

    load_info = pipeline.run(source)

    print(load_info)



if __name__ == '__main__':
    load_tables_family_and_genome()
```

パイプライン `python sql_database_pipeline.py` の最初の実行では、テーブル `"family"` 全体がロードされます。その後の実行では、新しく更新された行 (列 `"updated"` によって追跡される) のみがロードされます。

## 次は？

チュートリアルの完了おめでとうございます。dlt で SQL データベース ソースを設定し、データ パイプラインを実行してデータを DuckDB にロードする方法を学びました。

dlt についてもっと知りたいですか？いくつか提案があります:
- SQL データベースソース構成の詳細については、[SQL データベースソースのリファレンス](../dlt-ecosystem/verified-sources/sql_database) を参照してください。
- [単一のテーブルを抽出し、高速な `arrow` および `connectorx` バックエンドを使用する](../dlt-ecosystem/verified-sources/sql_database/configuration.md) 方法を学びます
- [テーブル スキーマとクエリを書き換える](../dlt-ecosystem/verified-sources/sql_database/usage.md) 方法を学びます
- 上級チュートリアルで[カスタムソースを作成する](./load-data-from-an-api.md)方法を学びます
