---
title: Native Ibis integration
description: Accessing your data with native Ibis backends
keywords: [data, dataset, ibis]
---

# Ibis

Ibis は、強力なポータブル Python データフレームライブラリです。[公式ドキュメント](https://ibis-project.org/) で、Ibis の概要と使用方法について詳しく学んでください。

`dlt` を使用すると、読み込んだデータセットを Ibis バックエンド接続に簡単に渡すことができます。

:::tip
`dlt` でサポートされているすべての出力先に、同等の Ibis バックエンドがあるわけではありません。ネイティブでサポートされている出力先としては、DuckDB（Motherduck を含む）、Postgres（Redshift は Ibis バージョン 10.4.0 未満では Postgres バックエンド経由でサポートされます）、Snowflake、Clickhouse、MSSQL（Synapse を含む）、BigQuery などがあります。ファイルシステムの出力先は、[ファイルシステム SQL クライアント](./sql-client#the-filesystem-sql-client) 経由でサポートされます。Ibis を使用するには、DuckDB バックエンドをインストールしてください。ファイルシステム上のデータを Ibis で変更しても、永続化されたファイルに実際の変更は反映されません。
:::

## 前提条件

Ibis バックエンドを使用するには、適切な Ibis エクストラがインストールされている `ibis-framework` パッケージが必要です。以下の例では、DuckDB バックエンドをインストールします。

```sh
pip install ibis-framework[duckdb]
```

## データセットからIbis接続を取得します

`dlt`データセットには、データセットが存在する宛先へのIbis接続を返すヘルパーメソッドがあります。返されるオブジェクトは、宛先へのネイティブIbis接続であり、データの読み取りや変換に使用できます。Ibisでできることについて詳しくは、[Ibisドキュメント](https://ibis-project.org)をご覧ください。

```py
# get the dataset from the pipeline
dataset = pipeline.dataset()
dataset_name = pipeline.dataset_name

# get the native ibis connection from the dataset
ibis_connection = dataset.ibis()

# list all tables in the dataset
# NOTE: You need to provide the dataset name to ibis, in ibis datasets are named databases
print(ibis_connection.list_tables(database=dataset_name))

# get the items table
table = ibis_connection.table("items", database=dataset_name)

# print the first 10 rows
print(table.limit(10).execute())

# Visit the ibis docs to learn more about the available methods
```
