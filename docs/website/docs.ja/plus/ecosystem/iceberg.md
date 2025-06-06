---
title: "Destination: Iceberg"
description: Iceberg destination
keywords: [Iceberg, pyiceberg]
---

# Iceberg

Apache Iceberg は、大規模データセットの高性能分析向けに設計されたオープンテーブル形式です。
ACID トランザクション、スキーマ進化、タイムトラベルをサポートしています。

dlt の Iceberg 出力先を使用すると、[pyiceberg](https://py.iceberg.apache.org/) ライブラリを使用して Iceberg テーブルにデータをロードできます。
複数のカタログタイプと、ローカルおよびクラウドストレージバックエンドの両方をサポートしています。

## 機能

* SQLおよびRESTカタログ（Lakekeeper、Polaris）と互換性があります
* 自動スキーマ進化とテーブル作成
* あらゆる書き込み処理をサポート
* ローカルファイルシステムとクラウドストレージ（S3、Azure、GCS）で動作します
* `pipeline.dataset()` を使用してDuckDBビュー経由でデータを公開
* パーティショニングをサポート

##  前提条件

必要な依存関係がインストールされていることを確認してください。

```sh
pip install dlt[filesystem,pyiceberg]>=1.9.1
pip install dlt-plus>=0.9.1
```

## 構成

### 概要

Iceberg の宛先を設定するには、カタログを選択して設定する必要があります。
Iceberg カタログの役割は次のとおりです。

* メタデータを保存し、トランザクションを調整する（必須）
* 認証情報を生成し、pyiceberg クライアントに渡す（認証情報ベンダー）
* 新しく生成されたテーブルの場所を生成し、渡す（REST カタログ）

現在、Iceberg の宛先は 2 種類のカタログをサポートしています。
* SQL ベースのカタログ。ローカル開発に最適で、メタデータを SQLite または PostgreSQL に保存します。
* REST カタログ。Lakekeeper や Polaris などのシステムで本番環境で使用されます。

### SQL カタログ

SQL カタログは開発とテストに最適です。
認証情報や位置情報の自動提供は提供されないため、手動で設定する必要があります。
ファイルベースの SQLite データベースなどのローカルストレージパスをサポートしており、通常はローカルファイルシステムの操作に使用されます。

SQL カタログを設定するには、次のパラメータを指定します。

<Tabs
  groupId="filesystem-type"
  defaultValue="yml"
  values={[
    {"label": "dlt.yml", "value": "yml"},
    {"label": "TOML files", "value": "toml"},
    {"label": "Environment variables", "value": "env"}
]}>

<TabItem value="yml">

```yaml
# we recommend to put sensitive parameters to secrets.toml
destinations:
  iceberg_lake:
    type: iceberg
    catalog_type: sql
    credentials: "sqlite:///catalog.db"  # connection string for accessing the database
    filesystem:
      bucket_url: "path_to_data" # table location
      # credentials section below is only needed if you're using the cloud storage (not local disk)
      # we recommend to put sensitive parameters to secrets.toml
      credentials:
        aws_access_key_id: "please set me up!" # only if needed
        aws_secret_access_key: "please set me up!" # only if needed
    capabilities:
      # will register tables if found in storage but not found in the catalog (backward compatibility)
      register_new_tables: True
      table_location_layout: "{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="toml">

```toml
[destination.iceberg]
catalog_type="sql"
credentials="sqlite:///catalog.db" # connection string for accessing the database

[destination.iceberg.filesystem]
bucket_url="path_to_data" # table location

# credentials section below is only needed if you're using the cloud storage (not local disk)
[destination.iceberg.filesystem.credentials]
aws_access_key_id = "please set me up!"
aws_secret_access_key = "please set me up!"

[destination.iceberg.capabilities]
# will register tables if found in storage but not found in the catalog (backward compatibility)
register_new_tables=true
table_location_layout="{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="env">

```sh
export DESTINATION__ICEBERG__CATALOG_TYPE=sql
export DESTINATION__ICEBERG__CREDENTIALS=sqlite:///catalog.db
export DESTINATION__ICEBERG__FILESYSTEM__BUCKET_URL=path_to_data
# credentials section below is only needed if you're using the cloud storage (not local disk)
export DESTINATION__ICEBERG__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID="please set me up!"
export DESTINATION__ICEBERG__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY="please set me up!"

export DESTINATION__ICEBERG__CAPABILITIES__REGISTER_NEW_TABLE=True
export DESTINATION__ICEBERG__CAPABILITIES__TABLE_LOCATION_LAYOUT={dataset_name}/{table_name}
```
</TabItem>

</Tabs>

* `catalog_type=sql` - これは、SQLベースのカタログを使用することを示します。
* `credentials=dialect+database_type://username:password@server:port/database_name` - カタログデータベースへの接続文字列。
SQLiteやPostgreSQLなど、SQLAlchemy互換のデータベースであればどれでも構いません。
ローカル開発の場合は、`sqlite:///catalog.db`のようなシンプルなSQLiteファイルで十分です。
もし存在しない場合は、dltが自動的に作成します。
* `filesystem.bucket_url` - Icebergテーブルデータが保存される物理的な場所。
これは、ローカルディレクトリ、または[ファイルシステムの保存先](../../dlt-ecosystem/destinations/filesystem.md)でサポートされているクラウドストレージであればどれでも構いません。
クラウドストレージを使用している場合は、[認証情報設定ガイド](../../dlt-ecosystem/destinations/filesystem.md#set-up-the-destination-and-credentials) に記載されている適切な認証情報を必ず含めてください。
ローカルファイルシステムの場合、追加の認証情報は必要ありません。
* `capabilities.register_new_tables=true` - ストレージには存在するがカタログには存在しないテーブルの自動登録を有効にします。
* `capabilities.table_location_layout` - Iceberg テーブルファイルのディレクトリ構造を制御します。
次の 2 つのモードをサポートしています。
  * 絶対 - カタログのウェアハウスパスに一致する完全な URI を指定します。オプションでより深いサブパスを含めることもできます。
  * 相対 - カタログのウェアハウスルートに追加されるパス。これは、Lakekeeper などのカタログで特に便利です。

SQL カタログには、次のスキーマの 1 つのテーブルが格納されます:

| catalog_name | table_namespace     | table_name  | metadata_location                                 | previous_metadata_location                                                          |
|--------------|---------------------|-------------|---------------------------------------------------|---------------------------------------------------------------------------------------|
| default      | jaffle_shop_dataset | orders | path/to/files                                     | path/to/files |
| default      | jaffle_shop_dataset | _dlt_loads  | path/to/files  | path/to/files |

### Lakekeeper カタログ

[Lakekeeper](https://docs.lakekeeper.io/) は、オープンソースで本番環境レベルの Iceberg カタログです。
セットアップが簡単で、あらゆるクラウドストレージと連携し、高負荷なインフラストラクチャを構築することなく、本格的なデータプラットフォームを構築できます。
Lakeleeper は、認証情報のベンダー化（クレデンシャルベンダー）もサポートしているため、長期間有効なシークレットを DLT に直接渡す必要がなくなります。

Lakekeeper を構成するには、カタログとストレージの両方のパラメータを指定する必要があります。
カタログはメタデータと認証情報のベンダー化を処理し、`bucket_url` は Lakekeeper で構成されたウェアハウスと一致する必要があります。

<Tabs
  groupId="filesystem-type"
  defaultValue="yml"
  values={[
    {"label": "dlt.yml", "value": "yml"},
    {"label": "TOML files", "value": "toml"},
    {"label": "Environment variables", "value": "env"}
]}>

<TabItem value="yml">

```yaml
# we recommend to put sensitive configurations to secrets.toml
destinations:
  iceberg_lake:
    type: iceberg
    catalog_type: rest
    credentials:
      # we recommend to put sensitive configurations to secrets.toml
      credential: my_lakekeeper_key
      uri: https://lakekeeper.path.to.host/catalog
      warehouse: warehouse
      properties:
        scope: lakekeeper
        oauth2-server-uri: https://keycloak.path.to.host/realms/master/protocol/openid-connect/token
    filesystem:
      # bucket for s3 tables - must match Lakekeeper warehouse if defined
      bucket_url: "s3://warehouse/"
    capabilities:
      table_root_layout: "lakekeeper-warehouse/dlt_plus_demo/lakekeeper_demo/{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="toml">

```toml
[destination.iceberg]
catalog_type="rest"

[destination.iceberg.credentials]
credential="my_lakekeeper_key"
uri="https://lakekeeper.path.to.host/catalog"
warehouse="warehouse"

[destination.iceberg.credentials.properties]
scope="lakekeeper"
oauth2-server-uri="https://keycloak.path.to.host/realms/master/protocol/openid-connect/token"

[destination.iceberg.filesystem]
bucket_url="s3://warehouse/"

[destination.iceberg.capabilities]
table_location_layout="lakekeeper-warehouse/dlt_plus_demo/lakekeeper_demo/{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="env">

```sh
export DESTINATION__ICEBERG__CATALOG_TYPE=rest
export DESTINATION__ICEBERG__CREDENTIALS__CREDENTIAL=my_lakekeeper_key
export DESTINATION__ICEBERG__CREDENTIALS__URI=https://lakekeeper.path.to.host/catalog
export DESTINATION__ICEBERG__CREDENTIALS__WAREHOUSE=warehouse
export DESTINATION__ICEBERG__CREDENTIALS__PROPERTIES__SCOPE=lakekeeper
export DESTINATION__ICEBERG__CREDENTIALS__PROPERTIES__OAUTH2-SERVER-URI=https://keycloak.path.to.host/realms/master/protocol/openid-connect/token
export DESTINATION__ICEBERG__FILESYSTEM__BUCKET_URL=s3://warehouse/
export DESTINATION__ICEBERG__CAPABILITIES__TABLE_LOCATION_LAYOUT=lakekeeper-warehouse/dlt_plus_demo/lakekeeper_demo/{dataset_name}/{table_name}
```
</TabItem>

</Tabs>

* `catalog_type=rest` - REST ベースのカタログ実装を使用していることを指定します。
* `credentials.credential` - カタログ認証に使用する Lakekeeper キーまたはトークン。
* `credentials.uri` - Lakekeeper カタログエンドポイントの URL。
* `credentials.warehouse` - Lakekeeper で構成されたウェアハウスの名前。すべてのデータテーブルのルートの場所を定義します。
* `credentials.properties.scope=lakekeeper` - 認証に必要なスコープ。
* `credentials.properties.oauth2-server-uri` - Lakekeeper 認証に使用する OAuth2 トークンエンドポイントの URL。
* `filesystem.bucket_url` - Iceberg テーブルファイルの物理的な保存場所。[ファイルシステムの保存先](../../dlt-ecosystem/destinations/filesystem.md) にリストされている、サポートされている任意のクラウドストレージバックエンドを指定できます。

:::warning
現在、以下のバケットと認証情報の組み合わせが十分にテストされています。

* S3: STS と署名者、S3 Express
* Azure: アクセスキーとテナント ID（プリンシパル）ベースの認証の両方
* Google ストレージ
:::

* `capabilities.table_location_layout` -- Iceberg テーブルファイルのディレクトリ構造を制御します。
2 つのモードをサポートします。
  * 絶対パス - カタログのウェアハウスパスに一致する完全な URI を指定します。オプションで、より深いサブパスも含めることができます。
  * 相対パス - カタログのウェアハウスルートに付加されるパスです。これは、Lakekeeper のようなカタログで特に便利です。

### Polaris catalog

[Polaris](https://polaris.apache.org/) は、Iceberg 用のオープンソースでフル機能のカタログです。
設定は Lakekeeper に似ていますが、認証情報のスコープと URI に若干の違いがあります。

<Tabs
  groupId="filesystem-type"
  defaultValue="yml"
  values={[
    {"label": "dlt.yml", "value": "yml"},
    {"label": "TOML files", "value": "toml"},
    {"label": "Environment variables", "value": "env"}
]}>

<TabItem value="yml">

```yaml
# we recommend to put sensitive configurations to secrets.toml
destinations:
  iceberg_lake:
    type: iceberg
    catalog_type: rest
    credentials:
      # we recommend to put sensitive configurations to secrets.toml
      credential: my_polaris_key
      uri: https://account.snowflakecomputing.com/polaris/api/catalog
      warehouse: warehouse
      properties:
        scope: PRINCIPAL_ROLE:ALL
    filesystem:
      # bucket for s3 tables - must match Lakekeeper warehouse if defined
      bucket_url: "s3://warehouse"
    capabilities:
      table_root_layout: "{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="toml">

```toml
[destination.iceberg]
catalog_type="rest"

[destination.iceberg.credentials]
credential="my_polaris_key"
uri="https://account.snowflakecomputing.com/polaris/api/catalog"
warehouse="warehouse"

[destination.iceberg.credentials.properties]
scope="PRINCIPAL_ROLE:ALL"

[destination.iceberg.filesystem]
bucket_url="s3://warehouse"

[destination.iceberg.capabilities]
table_location_layout="{dataset_name}/{table_name}"
```
</TabItem>

<TabItem value="env">

```sh
export DESTINATION__ICEBERG__CATALOG_TYPE=rest
export DESTINATION__ICEBERG__CREDENTIALS__CREDENTIAL=my_polaris_key
export DESTINATION__ICEBERG__CREDENTIALS__URI=https://account.snowflakecomputing.com/polaris/api/catalog
export DESTINATION__ICEBERG__CREDENTIALS__WAREHOUSE=warehouse
export DESTINATION__ICEBERG__CREDENTIALS__PROPERTIES__SCOPE=PRINCIPAL_ROLE:ALL
export DESTINATION__ICEBERG__FILESYSTEM__BUCKET_URL=s3://warehouse/
export DESTINATION__ICEBERG__CAPABILITIES__TABLE_LOCATION_LAYOUT={dataset_name}/{table_name}
```
</TabItem>

</Tabs>

詳細については、[上記の Lakekeeper セクション](#lakekeeper-catalog) を参照してください。

## 書き込み処理

すべての[書き込み処理](../../general-usage/incremental-loading.md)がサポートされています。

## データアクセス

Iceberg 宛先は `pipeline.dataset()` と統合され、ユーザーがデータにクエリ可能なアクセスを提供します。
呼び出されると、Iceberg テーブルを参照するビューを含むインメモリ DuckDB データベースが作成されます。

作成されたビューは、利用可能な最新のスナップショットを反映します。
開発中に最新のデータを確保するには、`always_refresh_views` オプションを使用してください。
ビューは、クエリの使用状況に基づいて、必要に応じてのみ生成されます。

## データアクセスのための認証情報

デフォルトでは、データにアクセスするための認証情報はカタログによって提供され、テーブルごとにシークレットが自動的に作成されます。
これは、STS 認証情報を使用する AWS S3 などのクラウドストレージプロバイダーで最も効果的に機能します。
ただし、一時的な認証情報ではパフォーマンスが制限される可能性があるため、`dataset()` または dlt+ 変換を使用する場合は、ファイルシステムを明示的に定義することをお勧めします。
このアプローチにより、ネイティブの DuckDB ファイルシステムアクセス、永続的なシークレット、および高速なデータアクセスが可能になります。
たとえば、Iceberg テーブルの保存場所として AWS S3 を使用する場合、`filesystem` セクションの宛先設定で明示的な認証情報を提供できます。

```toml
[destination.iceberg.filesystem.credentials]
aws_access_key_id = "please set me up!"
aws_secret_access_key = "please set me up!"
```

## パーティショニング

Apache Iceberg は、クエリパフォーマンスを最適化するために [テーブルパーティショニング](https://iceberg.apache.org/docs/latest/partitioning/) をサポートしています。

dlt+ Iceberg の宛先でパーティショニングを構成する方法は 2 つあります。
* [`iceberg_adapter`](#using-the-iceberg_adapter-function) 関数を使用する
* 列レベルの [`partition`](#using-column-level-partition-property) プロパティを使用する

### `iceberg_adapter` 関数の使用

`iceberg_adapter` 関数を使用すると、Iceberg テーブルのパーティション分割を設定できます。
このアダプタは、データ列に適用できるさまざまなパーティション変換をサポートしています。


```py
import dlt
from dlt_plus.destinations.impl.iceberg.iceberg_adapter import iceberg_adapter, iceberg_partition

@dlt.resource
def my_data():
    yield [{"id": 1, "created_at": "2024-01-01", "category": "A"}]

# Apply partitioning to the resource
iceberg_adapter(
    my_data,
    partition=["category"]  # Simple identity partition
)
```

### パーティション変換

Iceberg は、パーティション分割のためのいくつかの変換関数をサポートしています。
パーティション仕様を作成するには、`iceberg_partition` ヘルパークラスを使用します。

#### ID パーティショニング

列の正確な値でパーティション分割します（文字列列の場合は、名前で指定した場合のデフォルト）。

```py
# These are equivalent:
iceberg_adapter(resource, partition=["region"])
iceberg_adapter(resource, partition=[iceberg_partition.identity("region")])
```

#### 時間変換

日付/日時列から時間要素を抽出します。

* `iceberg_partition.year(column_name)`: Partition by year
* `iceberg_partition.month(column_name)`: Partition by month
* `iceberg_partition.day(column_name)`: Partition by day
* `iceberg_partition.hour(column_name)`: Partition by hour

```py
import dlt
from dlt_plus.destinations.impl.iceberg.iceberg_adapter import iceberg_adapter, iceberg_partition

@dlt.resource
def events():
    yield [{"id": 1, "event_time": datetime.datetime(2024, 3, 15, 10, 30), "data": "..."}]

iceberg_adapter(
    events,
    partition=[iceberg_partition.month("event_time")]
)
```

#### バケット分割

ハッシュ関数を使用して、一定数のバケットにデータを分散します:

```py
iceberg_adapter(
    resource,
    partition=[iceberg_partition.bucket(16, "user_id")]
)
```

#### 切り捨てパーティション分割

文字列値を固定プレフィックス長でパーティション分割します:

```py
iceberg_adapter(
    resource,
    partition=[iceberg_partition.truncate(3, "category")]  # Groups "ELECTRONICS" → "ELE"
)
```

### 高度なパーティション分割の例

#### 複数列のパーティション分割

複数のパーティション戦略を組み合わせる:

```py
import dlt
from dlt_plus.destinations.impl.iceberg.iceberg_adapter import iceberg_adapter, iceberg_partition

@dlt.resource
def sales_data():
    yield [
        {
            "id": 1,
            "timestamp": datetime.datetime(2024, 1, 15, 10, 30),
            "region": "US",
            "category": "Electronics",
            "amount": 1250.00
        },
        {
            "id": 2,
            "timestamp": datetime.datetime(2024, 1, 16, 14, 20),
            "region": "EU",
            "category": "Clothing",
            "amount": 890.50
        }
    ]

# Partition by month and region
iceberg_adapter(
    sales_data,
    partition=[
        iceberg_partition.month("timestamp"),
        "region"  # Identity partition on region
    ]
)

pipeline = dlt.pipeline("sales_pipeline", destination="iceberg")
pipeline.run(sales_data)
```

#### カスタムパーティションフィールド名

パーティションフィールドにわかりやすいカスタム名を指定します。

```py
import dlt
from dlt_plus.destinations.impl.iceberg.iceberg_adapter import iceberg_adapter, iceberg_partition

@dlt.resource
def user_activity():
    yield [{"user_id": 123, "activity_time": datetime.datetime.now(), "action": "click"}]

iceberg_adapter(
    user_activity,
    partition=[
        iceberg_partition.year("activity_time", "activity_year"),
        iceberg_partition.bucket(8, "user_id", "user_bucket")
    ]
)
```

### 列レベルのパーティションプロパティの使用

列仕様で「"partition": True」プロパティを使用することで、列レベルで直接アイデンティティパーティションを設定できます。
このアプローチでは、アイデンティティ変換（正確な列値によるパーティション分割）が使用されます。

#### 基本的な列レベルのパーティション分割

```py
import dlt

@dlt.resource(columns={"region": {"partition": True}})
def sales_data():
    yield [
        {"id": 1, "region": "US", "amount": 1250.00},
        {"id": 2, "region": "EU", "amount": 890.50},
        {"id": 3, "region": "APAC", "amount": 1100.00}
    ]

pipeline = dlt.pipeline("sales_pipeline", destination="iceberg")
pipeline.run(sales_data)
```

#### 複数列のパーティション分割

各列に「"partition": True」を設定することで、複数の列でパーティション分割できます。

```py
@dlt.resource(columns={
    "region": {"partition": True},
    "category": {"partition": True},
})
def multi_partition_data():
    yield [
        {"id": 1, "region": "US", "category": "Electronics", "amount": 1250.00},
        {"id": 2, "region": "EU", "category": "Clothing", "amount": 890.50}
    ]
```

### DLT ロード ID によるパーティション分割

DLT [ロード ID](../../general-usage/destination-tables.md#load-packages-and-load-ids) は、各ロードパッケージ（DLT によって処理されるデータのバッチ）の一意の識別子です。
パイプラインを実行するたびに、その実行でロードされたすべてのデータを識別する一意のロード ID が生成されます。
`_dlt_load_id` は、`dlt` によってテーブルにロードされる各データ行に自動的に追加されるシステム列です。

DLT ロード ID でパーティション分割するには、列指定で `partition` プロパティを `_dlt_load_id` に設定します。

```py
@dlt.resource(columns={"_dlt_load_id": {"partition": True}})
def load_partitioned_data():
    yield [
        {"id": 1, "data": "example1"},
        {"id": 2, "data": "example2"}
    ]
```
