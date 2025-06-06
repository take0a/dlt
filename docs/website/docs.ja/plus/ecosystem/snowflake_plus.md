---
title: "Destination: Snowflake+ Iceberg / Open Catalog"
description: Snowflake destination with Iceberg and Open Catalog
keywords: [Snowflake, Iceberg, destination]
---

# Snowflake+ Iceberg / Open Catalog

Snowflake+は、[OSS Snowflake destination](../../dlt-ecosystem/destinations/snowflake.md)の代替として提供され、[Apache Icebergテーブル](https://docs.snowflake.com/en/user-guide/tables-iceberg)の作成と関連機能を追加します。

Snowflakeを使用してIcebergデータを管理します。テーブルが作成され、データはSnowflake SQL経由でコピーされ、他の（ネイティブ）テーブルと同様にSnowflake（HORIZON）カタログに自動的に表示されます。
さらに、Snowflakeはテーブルのメンテナンス（圧縮、スナップショットの削除など）も提供します。

**Snowflake Open Catalog** (Polaris)は、`CATALOG SYNC`オプションを介して[完全にサポート](#syncing-snowflake-managed-iceberg-tables-to-snowflake-open-catalog)されています。
`dlt` によって実行される新しいデータとすべてのスキーマ移行は、追加のコードや設定なしで参照できます。

`dlt` が `pipeline.dataset()` 経由でサポートするすべての [データアクセス](../../general-usage/dataset-access/) メソッド (pandas、arrow、Ibis、SQL など) が利用可能です。

:::tip
`dlt` [Iceberg](iceberg.md) の宛先で使用される任意のカタログ (Lakekeeper、Glue、S3Tables、または Open Catalog/Polaris) を Snowflake データベースに [リンク](https://docs.snowflake.com/LIMITEDACCESS/iceberg/tables-iceberg-externally-managed-writes#label-tables-iceberg-external-writes-create-cld) できます。
:::

このデスティネーションは、dlt+ バージョン 0.9.0 以降で利用可能です。
Snowflake の標準デスティネーションの全機能に加え、以下の機能もサポートしています。

1. `config.toml` ファイルまたは `dlt.yml` ファイルで `iceberg_mode` を設定することで、Snowflake で Iceberg テーブルを作成できます。
2. 以下の設定により、Snowflake で Iceberg テーブルを追加できます。
    - `external_volume`: Iceberg データが保存される外部ボリューム名。
    - `catalog`: Iceberg テーブルが作成されるカタログ名。デフォルトは `"SNOWFLAKE"` です。
    - `base_location`: Snowflake がテーブルデータを外部ストレージに保存するために使用するベースパスのテンプレート文字列。プレースホルダーをサポートします。
    - `extra_placeholders`: `base_location` テンプレートで使用できる追加の値。
    - `catalog_sync`: [Snowflake Open Catalog](https://other-docs.snowflake.com/en/opencatalog/overview) 用に設定された [カタログ統合](https://docs.snowflake.com/en/user-guide/tables-iceberg#catalog-integration) の名前。
    指定すると、Snowflake はデータベース内の Snowflake 管理の Iceberg テーブルを、Snowflake Open Catalog アカウント内の外部カタログと同期します。

## インストール

`snowflake` エクストラを含む `dlt-plus` パッケージをインストールします。

```sh
pip install "dlt-plus[snowflake]"
```

`snowflake` エクストラがインストールされると、`snowflake` 宛先を使用する場合とまったく同じ方法で `snowflake_plus` を使用するようにパイプラインを構成できます。

## セットアップ

1. [Snowflake の認証情報を設定します](../../dlt-ecosystem/destinations/snowflake.md#setup-guide)
2. [データベースユーザーと権限を設定します](../../dlt-ecosystem/destinations/snowflake.md#set-up-the-database-user-and-permissions)
3. [Snowflake で外部ボリュームを設定します](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume)
4. データのロードに使用するロールに外部ボリュームの使用権限を付与します。

```sql
GRANT USAGE ON EXTERNAL VOLUME <external_volume_name> TO ROLE <role_name>;
```

5. `snowflake_plus` の出力先を設定します。dlt+ プロジェクト（`dlt.yml` 内）または Python スクリプト（`config.toml` 内）の場合は、以下の手順に従います。

<Tabs
  groupId="config-format"
  defaultValue="dlt-yml"
  values={[
    {"label": "dlt.yml", "value": "dlt-yml"},
    {"label": "config.toml", "value": "config-toml"},
]}>
  <TabItem value="dlt-yml">

dlt+プロジェクトがまだない場合は、現在の作業ディレクトリでプロジェクトを初期化してください。`sql_database`を任意のソースコードに置き換えてください:

```sh
dlt project init sql_database snowflake_plus
```

これにより、`dlt.yml` ファイルに Snowflake Plus の宛先が作成されます:

```yaml
destinations:
  snowflake:
    type: snowflake_plus
```

Iceberg テーブルの作成を有効にするには、`iceberg_mode` オプションを設定し、`external_volume` を手順 3 で作成した外部ボリュームの名前に設定します。

```yaml
destinations:
  snowflake:
    type: snowflake_plus
    external_volume: "<external_volume_name>"
    iceberg_mode: "all"
```

  </TabItem>
  <TabItem value="config-toml">

`config.toml` ファイルに設定を追加します:

```toml
[destination.snowflake]
external_volume = "<external_volume_name>"
iceberg_mode = "all"
```

パイプラインで `snowflake_plus` 宛先を使用します:

```py
import dlt

pipeline = dlt.pipeline(
    pipeline_name="my_snowflake_plus_pipeline",
    destination="snowflake_plus",
    dataset_name="my_dataset"
)

@dlt.resource
def my_iceberg_table():
    ...
```

  </TabItem>
</Tabs>

## 設定

`snowflake_plus` 宛先は、Snowflake の標準設定に以下の追加オプションを追加して拡張します。

### `iceberg_mode`
Icebergテーブルとして作成するテーブルを制御します。
- 指定可能な値:
- `"all"`: DLTシステムテーブルを含むすべてのテーブルがIcebergテーブルとして作成されます。
- `"data_tables"`: データテーブル（DLTシステムテーブル以外）のみがIcebergテーブルとして作成されます。
- `"none"`: Icebergテーブルとして作成されるテーブルはありません。
- 必須: いいえ
- デフォルト: `"none"`

### `external_volume`
Icebergメタデータを保存する外部ボリューム。
- 必須: はい
- デフォルト: なし

### `catalog`
Icebergテーブルに使用するカタログ。
- 必須: いいえ
- デフォルト: `"SNOWFLAKE"`。これにより、Icebergテーブルに[Snowflakeをカタログとして使用](https://docs.snowflake.com/en/user-guide/tables-iceberg#label-tables-iceberg-snowflake-as-catalog)します。

### `base_location`
Icebergデータが外部ボリュームに保存されるベースロケーションのテンプレート文字列。`{dataset_name}`や`{table_name}`などのプレースホルダーをサポートします。
- 必須: いいえ
- デフォルト: `"{dataset_name}/{table_name}"`

### `extra_placeholders`
`base_location` テンプレートで使用できる追加の値の辞書です。
値は、静的な文字列、またはデータセット名とテーブル名を引数として受け取り、文字列を返す関数にすることができます。
- 必須: いいえ
- デフォルト: なし

### `catalog_sync`
Icebergテーブルを[Snowflake Open Catalog](https://other-docs.snowflake.com/en/opencatalog/overview)内の外部カタログに同期するための[カタログ統合](https://docs.snowflake.com/en/user-guide/tables-iceberg#catalog-integration)の名前。
- 必須: いいえ
- デフォルト: なし

これらのオプションは、`config.toml`ファイルの`[destination.snowflake]`セクション、または`dlt.yml`ファイルの`destinations.snowflake_plus`セクションで設定します。

## ベースロケーションのテンプレート化

`base_location` パラメーターは、Snowflake が Iceberg テーブルのデータとメタデータを外部ボリュームのどこに保存するかを制御します。
これは、以下の組み込みプレースホルダーをサポートするテンプレート文字列です。

- `{dataset_name}`: データセットの名前
- `{table_name}`: テーブルの名前

柔軟性を高めるために、`extra_placeholders` オプションを使用してカスタムプレースホルダーを定義することもできます。

### 例

1. デフォルトのパターン `{dataset_name}/{table_name}` は、外部ボリュームに「my_dataset/customers」のようなパスを作成します。

2. カスタムの静的パス:
   ```yaml
   base_location: "custom/static/path"
   ```
   これにより、すべてのテーブルが同じディレクトリ `custom/static/path` 内に作成されます。

3. カスタムプレースホルダの使用:
   ```yaml
   base_location: "{env}/{dataset_name}/{table_name}"
   extra_placeholders:
     env: "prod"
   ```
   これにより、`prod/my_dataset/customers` のようなパスが作成されます。

### Snowflake がベースロケーションを使用する方法

`base_location` を指定すると、Snowflake はそれを使用して、外部クラウドストレージ内のデータとメタデータを保存するパスを作成します。
Snowflake が実際に作成するディレクトリ構造は、次のパターンに従います。

```text
STORAGE_BASE_URL/BASE_LOCATION.<randomId>/[data | metadata]/
```

ここで、`<randomId>` は、Snowflake が生成したランダムな 8 文字の文字列で、一意のディレクトリを作成するために追加されます。

Snowflake が外部ストレージで Iceberg テーブルファイルをどのように整理するかの詳細については、[データおよびメタデータディレクトリに関する Snowflake のドキュメント](https://docs.snowflake.com/en/user-guide/tables-iceberg-storage#data-and-metadata-directories) を参照してください。

## 個々のテーブルのテーブル形式

個々の `dlt` リソースに対して、テーブル形式（Iceberg/Native）を指定できます。
例:

  ```py
  @dlt.resource(
    table_format="native"
  )
  def my_resource():
      ...

  pipeline = dlt.pipeline("loads_native", destination="snowflake_plus")
  ```

  [iceberg_mode](#iceberg_mode) を **all** または **data_tables** に設定した場合も、ネイティブ (アイスバーグではない) **my_resource** テーブルが作成されます。

## 書き込み処理

すべての標準的な書き込み処理（`append`、`replace`、`merge`）は、通常のSnowflakeテーブルとIcebergテーブルの両方でサポートされています。

## データ型

Snowflake Plus の宛先は、すべての標準的な Snowflake の宛先データ型をサポートし、Iceberg テーブル用の追加の型マッピングもサポートします。

| dlt Type | Iceberg Type |
|----------|--------------|
| `text` | `string` |
| `bigint` | `long`, `int` |
| `double` | `double` |
| `bool` | `boolean` |
| `timestamp` | `timestamp` |
| `date` | `date` |
| `time` | `time` |
| `decimal` | `decimal` |
| `binary` | `binary` |
| `json` | `string` |

## Snowflake が管理する Iceberg テーブルを Snowflake Open Catalog に同期する

サードパーティ製エンジン（Apache Spark など）から外部カタログ（Snowflake Open Catalog）経由で Snowflake が管理する Iceberg テーブルへのクエリを有効にするには、`catalog_sync` 構成オプションを使用します。
この設定は、Iceberg テーブルを外部カタログに同期する [カタログ統合](https://docs.snowflake.com/en/user-guide/tables-iceberg#catalog-integration) を指定します。

### セットアップ

1. [Snowflake Open Catalog で外部カタログを作成](https://other-docs.snowflake.com/en/opencatalog/create-catalog)。

2. Snowflake でカタログ統合を作成。
例:

```sql
  CREATE OR REPLACE CATALOG INTEGRATION my_open_catalog_int
    CATALOG_SOURCE = POLARIS
    TABLE_FORMAT = ICEBERG
    REST_CONFIG = (
      CATALOG_URI = 'https://<orgname>-<my-snowflake-open-catalog-account-name>.snowflakecomputing.com/polaris/api/catalog'
      CATALOG_NAME = 'myOpenCatalogExternalCatalogName'
    )
    REST_AUTHENTICATION = (
      TYPE = OAUTH
      OAUTH_CLIENT_ID = 'myClientId'
      OAUTH_CLIENT_SECRET = 'myClientSecret'
      OAUTH_ALLOWED_SCOPES = ('PRINCIPAL_ROLE:ALL')
    )
    ENABLED = TRUE;
```

詳細な設定手順については、[Snowflake のドキュメント](https://docs.snowflake.com/en/user-guide/tables-iceberg-open-catalog-sync#step-4-create-a-catalog-integration-for-open-catalog) を参照してください。

3. `catalog_sync` オプションを設定します。

<Tabs
  groupId="config-format"
  defaultValue="config-toml"
  values={[
    {"label": "dlt.yml", "value": "dlt-yml"},
    {"label": "config.toml", "value": "config-toml"},
]}>
  <TabItem value="dlt-yml">

```yaml
destinations:
  snowflake:
    type: snowflake_plus
    # ... other configuration
    catalog_sync: "my_open_catalog_int"
```

  </TabItem>
  <TabItem value="config-toml">

```toml
[destination.snowflake]
# ... other configuration
catalog_sync = "my_open_catalog_int"
```

  </TabItem>
</Tabs>

## 追加リソース

Snowflakeの基本的なデスティネーション機能の詳細については、[Snowflakeデスティネーションドキュメント](../../dlt-ecosystem/destinations/snowflake.md)を参照してください。
