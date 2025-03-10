---
title: 30+ SQL databases (powered by SQLAlchemy)
description: SQLAlchemy destination
keywords: [sql, sqlalchemy, database, destination]
---

# SQLAlchemy の宛先

SQLAlchemy 宛先を使用すると、[SQLAlchemy 方言](https://docs.sqlalchemy.org/en/20/dialects/) が実装されている任意のデータベースを宛先として使用できます。

現在、MySQL と SQLite は完全にサポートされていると考えられており、`dlt` CI スイートの一部としてテストされています。他の方言はテストされていませんが、通常は動作するはずです。

## SQLAlchemyでdltをインストールする

`sqlalchemy` の追加依存関係を使用して dlt をインストールする:

```sh
pip install "dlt[sqlalchemy]"
```

データベースドライバは含まれていないので、使用する予定のデータベースに合わせて別途インストールする必要があることに注意してください。たとえば、MySQLの場合:

```sh
pip install mysqlclient
```

サポートされているデータベースに必要なクライアント ライブラリの詳細については、[方言に関する SQLAlchemy のドキュメント](https://docs.sqlalchemy.org/en/20/dialects/)を参照してください。

### パイプラインを作成する

**1. MS SQLにロードするパイプラインでプロジェクトを初期化するために、以下を実行します:**

```sh
dlt init chess sqlalchemy
```

**2. SQLAlchemyに必要な依存関係をインストールするには、以下を実行します:**

```sh
pip install -r requirements.txt
```

または、以下を実行します:

```sh
pip install "dlt[sqlalchemy]"
```

**3. データベース クライアント ライブラリをインストールします。**

例えば、MySQLの場合:

```sh
pip install mysqlclient
```

**4. `.dlt/secrets.toml` に資格情報を入力します。**

たとえば、データベース接続情報に置き換えます:

```toml
[destination.sqlalchemy.credentials]
database = "dlt_data"
username = "loader"
password = "<password>"
host = "localhost"
port = 3306
driver_name = "mysql"
```

あるいは、`secrets.toml` 内または環境変数として、有効な SQLAlchemy データベース URL を使用することもできます。たとえば

```toml
[destination.sqlalchemy]
credentials = "mysql://loader:<password>@localhost:3306/dlt_data"
```

または

```sh
export DESTINATION__SQLALCHEMY__CREDENTIALS="mysql://loader:<password>@localhost:3306/dlt_data"
```

SQLAlchemyの`Engine`は、宛先のインスタンスを作成することによって直接渡すこともできます:

```py
import sqlalchemy as sa
import dlt

engine = sa.create_engine('sqlite:///chess_data.db')

pipeline = dlt.pipeline(
    pipeline_name='chess',
    destination=dlt.destinations.sqlalchemy(engine),
    dataset_name='main'
)
```

## SQLite に関する注意事項

### データセットファイル

SQLite データベース ファイルを使用する場合、SQLite は単一のデータベース ファイルで複数のスキーマをサポートしていないため、各データセットは別々のファイルに保存されます。
内部的には、[`ATTACH DATABASE`](https://www.sqlite.org/lang_attach.html) が使用されます。

ファイルは、メイン データベース ファイル (データベース URL によって提供される) と同じディレクトリに保存されます。

たとえば、SQLite URL が `sqlite:////home/me/data/chess_data.db` で、`dataset_name` が `games` の場合、データは `/home/me/data/chess_data__games.db` に保存されます。

**注記**: データセット名が `main` の場合、これはデフォルトの SQLite データベースであるため、追加のファイルは作成されません。

### インメモリデータベース

インメモリ データベースでは、接続が閉じられるとデータベースが破棄されるため、永続的な接続が必要です。
通常、接続は各ロードジョブおよびパイプライン実行中の他のステージで開かれたり閉じられたりします。
パイプラインの実行中もデータベースが維持されるようにするには、資格情報ではなく SQLAlchemy の `Engine` オブジェクトを渡す必要があります。
このエンジンは `dlt` によって自動的に破棄されません。例:

```py
import dlt
import sqlalchemy as sa

# Create the SQLite engine
engine = sa.create_engine('sqlite:///:memory:')

# Configure the destination instance and create pipeline
pipeline = dlt.pipeline('my_pipeline', destination=dlt.destinations.sqlalchemy(engine), dataset_name='main')

# Run the pipeline with some data
pipeline.run([1,2,3], table_name='my_table')

# The engine is still open and you can query the database
with engine.connect() as conn:
    result = conn.execute(sa.text('SELECT * FROM my_table'))
    print(result.fetchall())
```

## 他の方言に関する注記

この宛先は **mysql** および **sqlite** 方言でテストしました。以下は、他の方言を有効にするのに役立つ可能性のあるいくつかの注意事項です:

1. `dlt` は、データベース例外が存在しないエンティティ (テーブルやスキーマなど) に関連している場合にそれを認識できる必要があります。私たちは、一般的な方言のほとんどでそれを認識できるように取り組んでいます (`db_api_client.py` を参照してください)
2. 特定の方言で問題が発生するのを避けるため、主キーと一意制約はデフォルトでは作成されません。
3. `merge` 書き込み処理では、できるだけ多くの方言を有効にするために `DELETE` および `INSERT` 操作のみを使用します。

特定の方言に関する問題を報告してください。問題が解決するように努力します。

## 書き込み処理

以下の書き込み処理がサポートされています:

- `append`
- `replace` は `truncate-and-insert` および `insert-from-staging` 置換戦略で使用します。`staging-optimized` は `insert-from-staging` にフォールバックします。
- `merge`　は `delete-insert` および `scd2` マージ戦略を使用します。

## データのロード

データは、SQLAlchemy のコア API によって生成された `insert` ステートメントを使用して、方言に依存しない方法でロードされます。
基礎となるデータベース ドライバーがサポートしている限り、行はバッチで挿入されます。デフォルトでは、バッチ サイズは 10,000 行です。

## `dlt` の状態の同期

この宛先は、[dlt state sync](../../general-usage/state#syncing-state-with-destination)を完全にサポートします。

### データ型

すべての `dlt` データ型がサポートされていますが、データベースにどのように格納されるかは SQLAlchemy 方言によって異なります。
たとえば、SQLite には `DATETIME` 型や `TIMESTAMP` 型がないため、`timestamp` 列は ISO 8601 形式の `TEXT` として保存されます。

## サポートされているファイル形式

* [typed-jsonl](../file-formats/jsonl.md) がデフォルトで使用されます。型付け情報を含む JSON エンコードされたデータ。
* [Parquet](../file-formats/parquet.md) は、サポートされています。

## サポートされている列のヒント

テーブルにインデックスや制約は作成されません。宛先設定で以下を有効にすることができます。

```toml
[destination.sqlalchemy]
create_unique_indexes=true
create_primary_keys=true
```

* `unique` ヒントは、SQLAlchemy を介して `UNIQUE` 制約に変換されます。
* `primary_key` ヒントは、SQLAlchemy を介して `PRIMARY KEY` 制約に変換されます。
