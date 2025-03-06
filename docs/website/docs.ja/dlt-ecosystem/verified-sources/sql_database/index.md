---
title: 30+ SQL Databases
description: PostgreSQL, MySQL, MS SQL, BigQuery, Redshift, and more
keywords: [sql connector, sql database pipeline, sql database]
---
import Header from '../_source-info-header.md';

# 30 以上の SQL データベース

<Header/>

SQL データベースは、構造化された形式でデータを保存する管理システム (DBMS) であり、効率的で信頼性の高いデータ取得によく使用されます。

SQL データベース検証済みソースは、SQLAlchemy、PyArrow、pandas、または ConnectorX のいずれかのバックエンドを使用して、指定された宛先にデータを読み込みます。

この検証済みソースを使用してロードできるソースとリソースは:

| 名前         | 説明                                                                  |
| ------------ | -------------------------------------------------------------------- |
| sql_database | SQLデータベースのテーブルとビューを反映し、データを取得します             |
| sql_table    | 特定のSQLデータベーステーブルからデータを取得します                      |
|              |                                                                      |

:::tip
チュートリアルをスキップしてすぐにコード例を確認したい場合は、[こちら](https://github.com/dlt-hub/verified-sources/blob/master/sources/sql_database_pipeline.py) のパイプライン例を確認してください。
:::

### サポートされているデータベース

:::tip dlt+
Microsoft SQL Server の変更追跡のサポートについては、[dlt+](../../../plus/ecosystem/ms-sql.md) を参照してください。
:::

私たちはすべての[SQLAlchemy方言](https://docs.sqlalchemy.org/en/20/dialects/)をサポートしています。これには以下のデータベースエンジンが含まれますが、これらに限定されません。:


* [PostgreSQL](./troubleshooting#postgres--mssql)
* [MySQL](./troubleshooting#mysql)
* SQLite
* [Oracle](./troubleshooting#oracle)
* [Microsoft SQL Server](./troubleshooting#postgres--mssql)
* MariaDB
* [IBM DB2 and Informix](./troubleshooting#db2)
* Google BigQuery
* Snowflake
* Redshift
* Apache Hive and Presto
* SAP Hana
* CockroachDB
* Firebird
* Teradata Vantage

:::note
[DuckDB](https://duckdb.org/) など、非公式の方言が多数存在することに注意してください。
:::

