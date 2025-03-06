---
title: Troubleshooting
description: common troubleshooting use-cases for the sql_database source
keywords: [sql connector, sql database pipeline, sql database]
---

import Header from '../_source-info-header.md';

# トラブルシューティング

<Header/>

## 接続のトラブルシューティング

#### SSL で MySQL に接続する

ここでは、`mysql` および `pymysql` 方言を使用してサーバーへの SSL 接続を設定します。すべての情報は [SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/en/14/dialects/mysql.html#ssl-connections) から取得されています。

1. クライアント証明書なしでクライアントにSSLを強制するには、次のDSNを渡します:

   ```toml
   sources.sql_database.credentials="mysql+pymysql://root:<pass>@<host>:3306/mysql?ssl_ca="
   ```

1. サーバーの公開証明書（パイプラインにバンドルされている可能性があります）を渡して、ホスト名のチェックを無効にすることもできます:

   ```toml
   sources.sql_database.credentials="mysql+pymysql://root:<pass>@<host>:3306/mysql?ssl_ca=server-ca.pem&ssl_check_hostname=false"
   ```

1. クライアント証明書を必要とするサーバーの場合は、クライアントの秘密鍵（秘密値）を指定します。Airflow では、通常、これは変数として保存され、使用前にファイルにエクスポートされます。以下の例では、サーバー証明書は省略されています:

   ```toml
   sources.sql_database.credentials="mysql+pymysql://root:<pass>@35.203.96.191:3306/mysql?ssl_ca=&ssl_cert=client-cert.pem&ssl_key=client-key.pem"
   ```

#### SSQL Server の接続オプション

**Windows 認証を使用して** `mssql` **サーバーに接続するには、** 接続文字列に `trusted_connection=yes` を含めます。

```toml
sources.sql_database.credentials="mssql+pyodbc://loader.database.windows.net/dlt_data?trusted_connection=yes&driver=ODBC+Driver 17+for+SQL+Server"
```

**SSL なしで実行されているローカル SQL Server インスタンスに接続するには、** `encrypt=no` パラメータを渡します:

```toml
sources.sql_database.credentials="mssql+pyodbc://loader:loader@localhost/dlt_data?encrypt=no&driver=ODBC+Driver 17+for+SQL+Server"
```

`証明書の検証に失敗しました。ローカル発行者の証明書を取得できません。` となった時に**自己署名 SSL 証明書を許可するには**:

```toml
sources.sql_database.credentials="mssql+pyodbc://loader:loader@localhost/dlt_data?TrustServerCertificate=yes&driver=ODBC+Driver 17+for+SQL+Server"
```

**長い文字列 (>8k) を使用して照合エラーを回避するには**:

```toml
sources.sql_database.credentials="mssql+pyodbc://loader:loader@localhost/dlt_data?LongAsMax=yes&driver=ODBC+Driver 17+for+SQL+Server"
```

**ConnectorX を使用して MS SQL Server 接続の問題を修正するには**:

一部のユーザーから、MS SQL Server と Connector X に関する問題が報告されています。この問題は dlt が原因ではなく、接続の確立方法に起因しています。解決策を提案してくださった [Mark-James M](https://github.com/markjamesm) に深く感謝いたします。

ConnectorX と MS SQL Server の接続の問題を修正するには、接続文字列に `Encrypt=yes` と `encrypt=true` の両方を含めます:

```toml
sources.sql_database.credentials="mssql://user:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&encrypt=true"
```
このアプローチは、接続関連の問題を解決するのに役立ちます。

## バックエンドのトラブルシューティング

### 特定のデータベースに関する注意事項

#### Oracle

1. `oracledb` 方言を Thin モードで使用すると、プロトコル エラーが発生します。Thick モードまたは `cx_oracle` (古い) クライアントを使用してください。
2. `SQLAlchemy` は Oracle 識別子を小文字に変換することに注意してください。データをロードするときは、デフォルトの `dlt` 命名規則 (`snake_case`) を維持してください。すぐにさらに多くの命名規則をサポートする予定です。
3. 何らかの理由で、`Connectorx` は Oracle では `PyArrow` バックエンドよりも遅くなります。
  
Oracle のセットアップとベンチマークに関する情報とコードについては、[こちら](https://github.com/dlt-hub/sql_database_benchmarking/tree/main/oracledb#installing-and-setting-up-oracle-db) を参照してください。

#### DB2

1. `SQLAlchemy` は DB2 識別子を小文字に変換することに注意してください。データをロードするときは、デフォルトの `dlt` 命名規則 (`snake_case`) を維持してください。すぐにさらに多くの命名規則をサポートする予定です。
2. DB2 型 `DOUBLE` は、Python 型 `float` (デフォルトの精度の `SQLAlchemy` 型 `Numeric` ではなく) に誤ってマップされます。これにより、`dlt` が追加のキャストを実行する必要があります。ただし、キャストのコストは、データベースから行を読み取るコストと比較するとごくわずかです。

DB2 のセットアップとベンチマークに関する情報とコードについては、[こちら](https://github.com/dlt-hub/sql_database_benchmarking/tree/main/db2#installing-and-setting-up-db2) を参照してください。

#### MySQL

1. `SQLAlchemy` 方言は、倍精度数を小数点数に変換します。(これは、コード例 [こちら](./configuration#pyarrow) に示すように、テーブル アダプタ引数によって無効にできます)

#### Postgres / MSSQL

これらのデータベースでは問題は見つかりませんでした。Postgres は、`ConnectorX` で 2 倍の高速化が観測された唯一のバックエンドです (ベンチマーク コードについては、[こちら](https://github.com/dlt-hub/sql_database_benchmarking/tree/main/postgres) を参照してください)。他のデータベース システムでは、`PyArrow` バックエンドと同じ (または場合によってはそれよりも悪い) パフォーマンスになります。

### 特定のデータ型に関する注意事項

#### JSON

`SQLAlchemy` バックエンドでは、JSON データ型は Python オブジェクトとして表現され、`PyArrow` バックエンドでは JSON 文字列として表現されます。現時点では、Python オブジェクトを `str` にキャストする `pandas` および `ConnectorX` では正しく動作せず、宛先に読み込むことができない無効な JSON 文字列が生成されます。

#### UUID  

UUID は、デフォルトでは文字列として表されます。`table_adapter_callback` を使用して特定の列の UUID タイプのプロパティを変更することで、この動作を切り替えることができます。(特定の列のデータ型プロパティを変更する方法については、[こちら](./configuration#pyarrow) のコード例を参照してください。)
