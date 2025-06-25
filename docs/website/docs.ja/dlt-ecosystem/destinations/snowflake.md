---
title: Snowflake
description: Snowflake `dlt` destination
keywords: [Snowflake, destination, data warehouse]
---

# Snowflake

## Snowflake で `dlt` をインストールする
**Snowflake の依存関係を持つ `dlt` ライブラリをインストールするには、次のコマンドを実行します。**
```sh
pip install "dlt[snowflake]"
```

## セットアップガイド

**1. 以下のコマンドを実行して、Snowflake にロードするパイプラインを含むプロジェクトを初期化します。**
```sh
dlt init chess snowflake
```

**2. 次のコマンドを実行して、Snowflake に必要な依存関係をインストールします。**
```sh
pip install -r requirements.txt
```
これにより、Snowflake Python dbapi クライアントを含む `snowflake` エクストラを含む `dlt` がインストールされます。

**3. 新しいデータベースとユーザーを作成し、`dlt` にアクセス権を付与します。**

次の章をお読みください。

**4. `.dlt/secrets.toml` に認証情報を入力します。**
以下のようになります:
```toml
[destination.snowflake.credentials]
database = "dlt_data"
password = "<password>"
username = "loader"
host = "kgiotue-wn98412"
warehouse = "COMPUTE_WH"
role = "DLT_LOADER_ROLE"
```
Snowflakeの場合、**host**は[アカウント識別子](https://docs.snowflake.com/en/user-guide/admin-account-identifier)です。**Admin**/**Accounts**でアカウントURL（https://kgiotue-wn98412.snowflakecomputing.com）をコピーし、ホスト名（**kgiotue-wn98412**）を抽出することで取得できます。

ユーザーにデフォルトを割り当てる場合、**warehouse** と **role** はオプションです。以下の例ではデフォルトを割り当てていないため、明示的に設定しています。

### データベースユーザーと権限の設定
以下の手順は、Snowflakeアカウント作成後にデフォルトで設定されるアカウント設定を使用することを前提としています。**COMPUTE_WH** という名前のデフォルトのウェアハウスとSnowflakeアカウントが必要です。以下では、新しいデータベースとユーザーを作成し、権限を割り当てます。権限は非常に豊富に設定されています。経験豊富なユーザーであれば、`dlt`権限をデータベース内の1つのスキーマだけに簡単に減らすことができます。
```sql
-- create database with standard settings
CREATE DATABASE dlt_data;
-- create new user - set your password here
CREATE USER loader WITH PASSWORD='<password>';
-- we assign all permissions to a role
CREATE ROLE DLT_LOADER_ROLE;
GRANT ROLE DLT_LOADER_ROLE TO USER loader;
-- give database access to new role
GRANT USAGE ON DATABASE dlt_data TO DLT_LOADER_ROLE;
-- allow `dlt` to create new schemas
GRANT CREATE SCHEMA ON DATABASE dlt_data TO ROLE DLT_LOADER_ROLE;
-- allow access to a warehouse named COMPUTE_WH
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO DLT_LOADER_ROLE;
-- grant access to all future schemas and tables in the database
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE dlt_data TO DLT_LOADER_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN DATABASE dlt_data TO DLT_LOADER_ROLE;
```

これで、「LOADER」というユーザーを使用してデータベース「DLT_DATA」にアクセスし、指定したパスワードでログインできるようになります。

また、ウェアハウスの一時停止時間を1分に短縮することもできます（Snowflake UIの**Admin**/**Warehouses**）。

### 認証タイプ

Snowflake の宛先は、以下の 3 種類の認証タイプを受け入れます。
- パスワード認証
- [キーペア認証](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- OAuth 認証

**パスワード認証** は、Postgres や Redshift などの他のデータベースと変わりません。`dlt` は [SQLAlchemy 方言](https://docs.snowflake.com/en/developer-guide/python-connector/sqlalchemy#required-parameters) と同じ構文に従います。

認証情報は、データベース接続文字列として渡すこともできます。例:
```toml
# Keep it at the top of your TOML file, before any section starts
destination.snowflake.credentials="snowflake://loader:<password>@kgiotue-wn98412/dlt_data?warehouse=COMPUTE_WH&role=DLT_LOADER_ROLE"

```

**キーペア認証**では、秘密鍵と公開鍵のペアを使用して認証を行います。`dlt` は以下のキー形式をサポートしています。

1. Base64 エンコードされた DER 形式（[dbt では、Snowflake 接続には Base64 エンコードされた秘密鍵も推奨されています](https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup#key-pair-authentication)）。
2. プレーンテキストまたは Base64 エンコードされた PEM 形式。

秘密鍵は暗号化されている場合もあります。その場合は、秘密鍵とともにパスフレーズも提供する必要があります。

```toml
[destination.snowflake.credentials]
database = "dlt_data"
username = "loader"
host = "kgiotue-wn98412"
private_key = "LS0tLS1CRUdJTiBFTkNSWVBURUQgUFJJ....Qo="
private_key_passphrase="passphrase"
```

> ターミナルで `base64 -i <秘密鍵ファイルのパス>.der` を実行すると、秘密鍵のBase64エンコードされた値を簡単に取得できます。

接続文字列にパスフレーズまたは秘密鍵を渡す場合は、**URLエンコードしてください**。そうしないと、クエリ文字列をデコードした後に鍵が壊れてしまいます。

```toml
# Keep it at the top of your TOML file, before any section starts
destination.snowflake.credentials="snowflake://loader:<password>@kgiotue-wn98412/dlt_data?private_key=<url encoded base64 pem|der>&amp;private_key_passphrase=<url encoded passphrase>"
```

秘密鍵ファイルへのパス（上記のいずれかの形式、バイナリ形式はサポートされていません）のみを渡したい場合は、`toml`、クエリ文字列（**URLエンコードしてください**）、または環境変数で、`private_key` の代わりに `private_key_path` を使用できます。例:

`DESTINATION__SNOWFLAKE__PRIVATE_KEY_PATH=path_to_pem.pem`


**OAuth認証**では、Snowflake、Okta、または外部ブラウザなどのOAuthプロバイダーを使用して認証できます。Snowflake OAuthの場合は、以下のように「認証子」と「トークン」の更新を渡します:
```toml
[destination.snowflake.credentials]
database = "dlt_data"
username = "loader"
authenticator="oauth"
token="..."
```
または、接続文字列にクエリパラメータとして指定します。

外部認証の場合は、OAuth プロバイダーのドキュメントをご確認ください。詳細については、Snowflake [OAuth](https://docs.snowflake.com/en/user-guide/oauth-intro) をご覧ください。

### 追加の接続オプション

すべてのクエリパラメータをSnowflake Pythonコネクタの`connect`関数に渡します。例:

```toml
[destination.snowflake.credentials]
database = "dlt_data"
authenticator="oauth"
[destination.snowflake.credentials.query]
timezone="UTC"
# keep session alive beyond 4 hours
client_session_keep_alive=true
```

これにより、タイムゾーンとセッションキープアライブが設定されます。TOMLを使用する場合は、設定が型指定されることに注意してください。別の方法として、
`"snowflake://loader/dlt_data?authenticator=oauth&timezone=UTC&client_session_keep_alive=true"`
は、`client_session_keep_alive` を文字列として connect メソッドに渡します（動作確認はしていません）。

### 書き込み処理

すべての書き込み処理がサポートされています。

[`replace` 戦略](../../general-usage/full-loading.md) を `staging-optimized` に設定すると、宛先テーブルは削除され、[clone コマンド](https://docs.snowflake.com/en/sql-reference/sql/create-clone) を使用してステージングテーブルから再作成されます。

### データのロード

データはSnowflakeの内部ステージを使用してロードされます。デフォルトでは、`PUT`コマンドとテーブルごとの組み込みステージを使用します。`keep_staged_files`パラメータで特に指定しない限り、ステージファイルはデフォルトで保持されます。

```toml
[destination.snowflake]
keep_staged_files = false
```

:::note
`dlt` は、アカウントおよびユーザー レベルの自動コミット設定をオーバーライドします。トランザクション外では `TRUE` が明示的に設定されます。
:::

### データ型
`snowflake` は様々なタイムスタンプ型をサポートしており、`dlt.resource` デコレータまたは `pipeline.run` メソッドの列フラグ `timezone` および `precision` を使用して設定できます。

- **Precision**: 秒の小数点以下の桁数を 0～9 の範囲で指定できます。`timezone` フラグと組み合わせて使用​​できます。
- **Timezone**:
- `timezone=False` に設定すると、`TIMESTAMP_NTZ` にマッピングされます。
- `timezone=True` に設定すると（またはフラグを省略すると、デフォルトで `True` になります）、`TIMESTAMP_TZ` にマッピングされます。

#### 精度とタイムゾーンの例: TIMESTAMP_NTZ(3)
```py
@dlt.resource(
    columns={"event_tstamp": {"data_type": "timestamp", "precision": 3, "timezone": False}},
    primary_key="event_id",
)
def events():
    yield [{"event_id": 1, "event_tstamp": "2024-07-30T10:00:00.123"}]

pipeline = dlt.pipeline(destination="snowflake")
pipeline.run(events())
```

## サポートされているファイル形式
* デフォルトでは [insert-values](../file-formats/insert-format.md) が使用されます。
* [Parquet](../file-formats/parquet.md) がサポートされています。
* [JSONL](../file-formats/jsonl.md) がサポートされています。
* [CSV](../file-formats/csv.md) がサポートされています。

ステージングが有効な場合：
* デフォルトでは [JSONL](../file-formats/jsonl.md) が使用されます。
* [Parquet](../file-formats/parquet.md) がサポートされています。
* [CSV](../file-formats/csv.md) がサポートされています。

:::caution
Parquetからロードする場合、Snowflakeは`json`型（JSON）を`VARIANT`に文字列として保存します。代わりにJSONL形式を使用するか、ロード後に`PARSE_JSON`を使用して`VARIANT`フィールドを更新してください。
:::

Parquet 形式を使用する場合、**ベクトル化スキャナー** を有効にしてパフォーマンスを向上させることができます。デフォルトでは、この機能は `dlt` の `ON_ERROR=ABORT_STATEMENT` 設定を使用し、エラーが発生した場合に実行を停止します。
ベクトル化スキャナーを有効にするには、以下の設定を追加してください。

```toml
[destination.snowflake]
use_vectorized_scanner=true
```
:::note
**ベクトル化スキャナ**は、出力に明示的に `NULL` 値を表示し、特定の特性を持っています。詳しくはSnowflakeの公式ドキュメントをご覧ください。
:::

### カスタムCSV形式
デフォルトでは、[ライターが生成](../file-formats/csv.md#default-settings) のCSV形式をサポートしています。これは、カンマ区切りでヘッダーが付き、オプションで引用符で囲むことができます。

外部の `csv` ファイルを[インポート](../../general-usage/resource.md#import-external-files)する際に、独自のフォーマットを設定することもできます。
```toml
[destination.snowflake.csv_format]
delimiter="|"
include_header=false
on_error_continue=true
```
これは、ヘッダーなしで `|` で区切られたファイルを読み取り、エラーがあっても続行します。

欠落している列は無視され、 `ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE` NULL が挿入されることに注意してください。

## サポートされている列ヒント
Snowflakeは、以下の[列ヒント](../../general-usage/schema#tables-and-columns)をサポートしています。
* `cluster` - クラスター列を作成します。テーブルごとに複数の列がサポートされており、新しいテーブルを作成する場合にのみ使用できます。
* `unique` - Snowflake列にUNIQUEヒントを作成します。複数の列に追加できます。([オプション](#additional-destination-options))
* `primary_key` - 選択した列にPRIMARY KEYを作成します。複合キーも可能です。([オプション](#additional-destination-options))

`unique`と`primary_key`は強制されず、`dlt`はクエリプランニング時にSnowflakeにこれらを`RELY`するように指示しません。


## テーブルと列の識別子
Snowflakeは、大文字と小文字を区別する識別子と区別しない識別子の両方をサポートしています。引用符で囲まれていない大文字の識別子は、SQL文では大文字と小文字を区別せずに解決されます。デフォルトの**snake_case**のような、大文字と小文字を区別しない[命名規則](../../general-usage/naming-convention.md#case-sensitive-and-insensitive-destinations)では、大文字と小文字を区別しない識別子が生成されます。大文字と小文字を区別する（**sql_cs_v1**など）では、大文字と小文字を区別する識別子が生成されますが、SQL文では引用符で囲む必要があります。

:::note
[スキーマ](../../general-usage/schema.md) 内のテーブル名と列名は、他のすべての出力先と同様に小文字で保持されます。これは、`dbt` などの他のツールで確認されたパターンです。ただし、`dlt` の場合は、大文字の[命名規則](../../general-usage/schema.md#naming-convention) を独自に定義するのは簡単です。
:::

## ステージングのサポート

Snowflakeは、ファイルのステージング先としてS3とGCSをサポートしています。`dlt`は、Parquet形式のファイルをバケットプロバイダーにアップロードし、Snowflakeにそのデータを直接データベースにコピーするよう指示します。

Parquetファイルの代わりに、ステージングファイル形式としてjsonlを指定することもできます。これを行うには、パイプラインの`run`コマンドの`loader_file_format`引数を`jsonl`に設定します。

### Snowflake と Amazon S3

bucket_url と認証情報を使用してバケットを設定する方法については、[S3 ドキュメント](./filesystem.md#aws-s3) を参照してください。S3 の場合、`dlt` Redshift ローダーは、特に指定がない限り、S3 に提供された AWS 認証情報を使用して S3 バケットにアクセスします（以下の構成オプションを参照）。または、[Snowflake S3 ドキュメント](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration) に記載されている手順に従って、S3 バケットのステージを作成することもできます。
基本的な手順は次のとおりです。

* GCS と適切なバケットにリンクされたストレージ統合を作成します。
* Snowflake へのデータのロードに使用している Snowflake ロールに、このストレージ統合へのアクセスを許可します。
* このストレージ統合から、PUBLIC 名前空間、またはデータのスキーマの名前空間にステージを作成します。
* また、Snowflake へのデータロードに使用しているロールに、このステージへのアクセスを許可します。
* `dlt` に、以下のようにステージ名（名前空間を含む）を指定します。

`dlt` がすべてのコマンドで S3 バケットの認証情報を転送しないようにし、S3 ステージを設定するには、以下の設定を変更します。

```toml
[destination]
stage_name="PUBLIC.my_s3_stage"
```

S3 をステージング先として Snowflake を実行するには:

```py
# Create a `dlt` pipeline that will load
# chess player data to the Snowflake destination
# via staging on S3
pipeline = dlt.pipeline(
    pipeline_name='chess_pipeline',
    destination='snowflake',
    staging='filesystem', # add this to activate the staging location
    dataset_name='player_data'
)
```

### Snowflake と Google Cloud Storage

bucket_url と認証情報を使用してバケットを設定する方法については、[Google Storage ファイルシステムのドキュメント](./filesystem.md#google-storage) を参照してください。GCS の場合は、Snowflake でステージを定義し、構成でステージ識別子を指定できます（以下の構成オプションを参照）。[GCS バケットのステージの作成方法](https://docs.snowflake.com/en/user-guide/data-load-gcs-config) については、Snowflake のドキュメントを参照してください。基本的な手順は次のとおりです。

* GCS と適切なバケットにリンクされたストレージ統合を作成します。
* Snowflake へのデータのロードに使用している Snowflake ロールに、このストレージ統合へのアクセスを許可します。
* このストレージ統合から、PUBLIC 名前空間、またはデータのスキーマの名前空間にステージを作成します。
* また、Snowflake へのデータのロードに使用しているロールに、このステージへのアクセスを許可します。
* 次のように、ステージの名前 (名前空間を含む) を `dlt` に指定します。

```toml
[destination]
stage_name="PUBLIC.my_gcs_stage"
```

GCS をステージング先として Snowflake を実行するには:

```py
# Create a `dlt` pipeline that will load
# chess player data to the Snowflake destination
# via staging on GCS
pipeline = dlt.pipeline(
    pipeline_name='chess_pipeline',
    destination='snowflake',
    staging='filesystem', # add this to activate the staging location
    dataset_name='player_data'
)
```

### Snowflake と Azure Blob Storage

bucket_url と認証情報を使用してバケットを設定する方法については、[Azure Blob Storage ファイルシステムのドキュメント](./filesystem.md#azure-blob-storage) を参照してください。Azure の場合、Snowflake ローダーは、特に指定がない限り、Azure Blob Storage コンテナーのファイルシステム認証情報を使用します（以下の構成オプションを参照）。または、Snowflake で外部ステージを定義し、ステージ ID を指定することもできます。[Azure Blob Storage コンテナーのステージの作成方法](https://docs.snowflake.com/en/user-guide/data-load-azure) については、Snowflake ドキュメントを参照してください。基本的な手順は次のとおりです。

* Azure Blob Storage と適切なコンテナーにリンクされたストレージ統合を作成します。
* Snowflake へのデータのロードに使用している Snowflake ロールに、このストレージ統合へのアクセスを許可します。
* このストレージ統合から、PUBLIC 名前空間、またはデータのスキーマの名前空間にステージを作成します。
* また、Snowflake にデータをロードするために使用しているロールに、このステージへのアクセスを許可します。
* 次のように、ステージ名（名前空間を含む）を `dlt` に指定します。

```toml
[destination]
stage_name="PUBLIC.my_azure_stage"
```

Azure をステージング先として Snowflake を実行するには:

```py
# Create a `dlt` pipeline that will load
# chess player data to the Snowflake destination
# via staging on Azure
pipeline = dlt.pipeline(
    pipeline_name='chess_pipeline',
    destination='snowflake',
    staging='filesystem', # add this to activate the staging location
    dataset_name='player_data'
)
```

## 追加の出力先オプション

ファイルをPUTするための独自のステージを定義し、ロード後にステージングされたファイルの削除を無効にすることができます。
[インデックスの作成](#supported-column-hints)を選択することもできます。

```toml
[destination.snowflake]
# Use an existing named stage instead of the default. Default uses the implicit table stage per table
stage_name="DLT_STAGE"
# Whether to keep or delete the staged files after COPY INTO succeeds
keep_staged_files=true
# Add UNIQUE and PRIMARY KEY hints to tables
create_indexes=true
# Enable vectorized scanner when using the Parquet format
use_vectorized_scanner=true
```

### CSV形式の設定

設定ファイルまたは明示的に[デフォルト以外の](../file-formats/csv.md#default-settings) CSV設定を指定できます。

```toml
[destination.snowflake.csv_format]
delimiter="|"
include_header=false
on_error_continue=true
```
or
```py
from dlt.destinations import snowflake
from dlt.common.data_writers.configuration import CsvFormatConfiguration

csv_format = CsvFormatConfiguration(delimiter="|", include_header=False, on_error_continue=True)

dest_ = snowflake(csv_format=csv_format)
```
上記では、ヘッダーなしの CSV ファイル形式を設定し、区切り文字として **|** を使用し、エラーのある行を無視するように要求しています。

:::tip
これらの設定は、[外部ファイルをインポート](../../general-usage/resource.md#import-external-files)するときに必要になります。
:::

### クエリのタグ付け

`dlt` [タグセッション](https://docs.snowflake.com/en/sql-reference/parameters#query-tag) は、以下のジョブプロパティを持つロードジョブを実行します。
* **source** - ソース名（`dlt` スキーマ名と同じ）
* **resource** - リソース名（既知の場合はリソース名、そうでない場合は空文字列）
* **table** - ジョブによってロードされるテーブル名
* **load_id** - ジョブのロードID
* **pipeline_name** - アクティブなパイプライン名（見つからない場合は空文字列）

Snowflake 認証情報でクエリタグのプレースホルダーを定義することで、クエリタグを定義できます。

```toml
[destination.snowflake]
query_tag='{{"source":"{source}", "resource":"{resource}", "table": "{table}", "load_id":"{load_id}", "pipeline_name":"{pipeline_name}"}}'
```
タグ名に対応する Python の名前付きフォーマッタが含まれています。つまり、 `{source}` は dlt ソースの名前を想定します。

:::note
1. クエリのタグ付けはデフォルトでオフになっています。`query_tag` 設定フィールドはデフォルトで `None` に設定されており、タグ付けを有効にするには設定する必要があります。
2. ジョブに関連付けられたセッションのみがタグ付けされます。スキーマを移行するセッションはタグ付けされません。
3. テーブルチェーンを処理するジョブ（SQL マージジョブなど）は、最上位テーブルを **table** として使用します。
:::

### dbt サポート
このデスティネーションは、[dbt-snowflake](https://github.com/dbt-labs/dbt-snowflake) を介して [dbt と統合](../transformations/dbt/dbt.md) します。パスワード認証とキーペア認証の両方がサポートされており、dbt ランナーと共有されます。

### `dlt` 状態の同期
この宛先は [dlt 状態同期](../../general-usage/state#syncing-state-with-destination) を完全にサポートしています。

### Snowflake接続識別子
Snowflakeが「dlt」によって作成された接続を識別できるようにします。Snowflakeはこの識別子を使用して、「dlt」統合に関連する使用パターンをより適切に把握します。接続識別子は「dltHub_dlt」です。

<!--@@@DLT_TUBA snowflake-->

