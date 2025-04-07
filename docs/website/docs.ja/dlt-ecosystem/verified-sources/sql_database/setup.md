---
title: Setup
description: basic steps for setting up a dlt pipeline for SQL Database
keywords: [sql connector, sql database pipeline, sql database]
---

import Header from '../_source-info-header.md';

# Setup

<Header/>

`dlt` を使用してSQLデータベースに接続するには、次の手順に従います:

1. 次のコマンドを実行して、現在の作業ディレクトリで `dlt` プロジェクトを初期化します:

    ```sh 
    dlt init sql_database duckdb
    ```

    これにより、SQL データベースをソースとし、[DuckDB](../../destinations/duckdb.md) を宛先とする `dlt` パイプラインに必要なファイルと構成が追加されます。

:::tip
別の保存先を使用する場合は、`duckdb` を希望する [宛先](../../destinations) の名前に置き換えてください。
:::

2. SQL データベースの資格情報を追加する

    SQL データベースに接続するには、`dlt` は必要な資格情報を使用して認証する必要があります。これを有効にするには、`.dlt/` フォルダ内に作成された `secrets.toml` ファイルに次の形式で資格情報を貼り付けます:

    ```toml
    [sources.sql_database.credentials]
    drivername = "mysql+pymysql" # driver name for the database
    database = "Rfam" # database name
    username = "rfamro" # username associated with the database
    host = "mysql-rfam-public.ebi.ac.uk" # host address
    port = "4497" # port required for connection
    ```

    あるいは、接続文字列を使用して認証することもできます:

    ```toml
    [sources.sql_database.credentials]
    credentials="mysql+pymysql://rfamro@mysql-rfam-public.ebi.ac.uk:4497/Rfam"
    ```

    `sql_database` パイプラインに資格情報を追加する方法の詳細については、[こちら](./configuration#configuring-the-connection)を参照してください。

3. 宛先の資格情報を追加する（必要な場合）

    ロード先の [宛先](../../destinations) によっては、宛先の資格情報も追加する必要がある可能性があります。詳細については、[一般的な使用方法: 資格情報](../../../general-usage/credentials)を参照してください。

4. 必要な依存関係をインストールする

    ```sh
    pip install -r requirements.txt
    ```

    :::note
    To [load data more efficiently using pyarrow](./configuration#pyarrow), you'll also need to install `pyarrow`, `numpy`, and `pandas`. 

    ```sh
    pip install pyarrow numpy pandas
    ```
    :::

5. パイプラインを実行する

    ```sh
    python sql_database_pipeline.py
    ```

    このコマンドを実行すると、手順 1 で作成したサンプル スクリプト `sql_database_pipeline.py` が実行されます。これを正常に実行するには、ロードするデータベースやテーブルの名前を渡す必要があります。詳細については、[sql_database ソースの構成に関するセクション](./configuration#configuring-the-sql-database-source)を参照してください。


6. すべてが期待通りにロードされていることを確認してください

    ```sh
    dlt pipeline <pipeline_name> show
    ```

   :::note
   上記の例の pipeline_name は `rfam` ですが、代わりに任意のカスタム名を使用することもできます。 
   :::  

