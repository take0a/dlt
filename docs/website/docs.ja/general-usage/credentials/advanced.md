---
title: コード内の構成へのアクセス
description: dlt関数の引数または明示的に設定にアクセスする
keywords: [credentials, secrets.toml, secrets, config, configuration, environment variables, provider]
---


## dlt で装飾された関数の設定へのアクセス

`dlt` は、`@dlt.source`、`@dlt.resource`、`@dlt.destination` で装飾された関数の設定 **spec** を自動生成します。追加コードは不要です。これらの関数は、環境変数や TOML ファイルなどの [標準設定方法](setup.md) を使用して設定できます。これらの関数は通常の Python 関数のように呼び出すことができ、明示的に指定されていない引数には dlt が設定値を挿入します。

### インジェクションルール

1. 明示的に渡された引数は**決してインジェクションされません**。そのため、インジェクションメカニズムはオプションとなります。Pipedriveソースの例：
  ```py
  @dlt.source(name="pipedrive")
  def pipedrive_source(
      pipedrive_api_key: str = dlt.secrets.value,
      since_timestamp: Optional[Union[pendulum.DateTime, str]] = "1970-01-01 00:00:00",
  ) -> Iterator[DltResource]:
    ...

  my_key = os.environ["MY_PIPEDRIVE_KEY"]
  my_source = pipedrive_source(pipedrive_api_key=my_key)
  ```
認証情報の処理に[標準オプション](setup)を使用しない場合は、`pipedrive_api_key`を明示的に指定できます。

2. 必須引数（デフォルト値なし）は**挿入されることはありません**。呼び出し時に明示的に指定する必要があります。例：

  ```py
  @dlt.source
  def slack_data(channels_list: List[str], api_key: str = dlt.secrets.value):
    ...
  ```
  The `channels_list` argument won't be injected and will produce an error if not specified explicitly.

3. デフォルト値を持つ引数は、設定プロバイダに見つかった場合は挿入されます。見つからない場合は、関数シグネチャのデフォルト値が使用されます。例:

  ```py
  @dlt.source
  def slack_source(
    page_size: int = MAX_PAGE_SIZE,
    access_token: str = dlt.secrets.value,
    start_date: Optional[TAnyDateTime] = START_DATE
  ):
    ...
  ```
`dlt` はまず、設定プロバイダ内で `page_size`、`access_token`、`start_date` を [特定の順序](setup) で検索します。これらの値が見つからない場合は、デフォルト値にフォールバックします。

4. 特別なデフォルト値を持つ引数 `dlt.secrets.value` と `dlt.config.value` は**挿入**（または明示的に渡す）必要があります。設定プロバイダ内で見つからない場合、`dlt` は例外を発生させます。

さらに、`dlt.secrets.value` は `dlt` に値がシークレットであることを示します。つまり、その値はセキュアな設定プロバイダからのみ挿入されます。

### ソースとリソースに型指定を追加する

関数シグネチャに型アノテーションを追加することをお勧めします。これにより、最小限の労力で、いくつかの重要なメリットが得られます。

1. コード内で無効なデータ型が返されることがなくなります。
2. `dlt` が自動的に型の解析と変換を行うため、手動での解析が不要になります。
3. `dlt` は、ソースのサンプル構成ファイルとシークレットファイルを自動的に生成できます。
4. [組み込みおよびカスタムの認証情報](complex_types) (接続文字列、AWS/GCP/Azure の認証情報) をリクエストできます。
5. `Union` を使用して、OAuth や API キー認証など、複数の可能な型を指定できます。

例:

```py
@dlt.source
def google_sheets(
    spreadsheet_id: str = dlt.config.value,
    tab_names: List[str] = dlt.config.value,
    credentials: GcpServiceAccountCredentials = dlt.secrets.value,
    only_strings: bool = False
):
    ...
```

メリット:
1. `tab_names` として、適切に型指定された文字列のリストが返されます。
2. 適切に構成された Google 認証情報（[GCP 認証情報の構成](complex_types#gcp-credentials) を参照）が返されます。ユーザーはこの認証情報をさまざまな形式で提供できます。
    * `service.json` を文字列または辞書として（コード内または構成プロバイダ経由）
    * 接続文字列（SQL Alchemy で使用）
    * 何も渡されない場合のデフォルトの認証情報（Cloud Function ランナーで利用可能なものなど）

## セクションを使用して構成とシークレットを整理する

`dlt` は、構成とシークレットのセクションを、[インジェクションメカニズム](#injection-rules) と統合された **構成レイアウト** に整理します。この構造は、TOML ファイル、環境変数、その他のソースを含むすべての [構成プロバイダ](setup) に適用されます。

この階層構造は、単純なケースを効率的に処理するだけでなく、異なる認証情報を持つ複数のソースや、同じプロジェクト内で複数のパイプラインが構成を共有するなど、より複雑なシナリオもサポートします。

```text
pipeline_name
    |
    |-sources
        |-<source 1 module name>
            |-<source function 1 name>
                |- {all source and resource options and secrets}
            |-<source function 2 name>
                |- {all source and resource options and secrets}
        |-<source 2 module>
            |...

        |-extract
            |- extract options for resources i.e., parallelism settings, maybe retries
    |-destination
        |- <destination name>
            |- {destination options}
                |-credentials
                    |-{credentials options}
    |-schema
        |-<schema name>
            |-schema settings: not implemented but I'll let people set nesting level, name convention, normalizer, etc. here
    |-load
    |-normalize
```

TOMLファイルを使用する場合、この構造はドットで区切られたキーを持つネストされたセクションとして表現されます。環境変数やその他の設定プロバイダの場合、レイアウトは二重のアンダースコアを使用してフラット化されます（例：`PIPELINE_NAME__SOURCES__MODULE_NAME__FUNCTION_NAME__OPTION`）。

## コード内で構成情報とシークレットにアクセス

`dlt` は認証情報を自動的に処理しますが、コード内で直接アクセスすることもできます。`dlt.secrets` オブジェクトと `dlt.config` オブジェクトは、構成値とシークレットへの辞書的なアクセスを提供し、必要に応じてカスタムの前処理を可能にします。また、同じ構成ファイルにカスタム設定を保存することもできます。

```py
# Use `dlt.secrets` and `dlt.config` to explicitly retrieve values from providers
source_instance = google_sheets(
    dlt.config["sheet_id"],
    dlt.config["my_section.tabs"],
    dlt.secrets["my_section.gcp_credentials"]
)

source_instance.run(destination="bigquery")
```

`dlt.config` と `dlt.secrets` は辞書として機能します。`dlt` はすべての [config プロバイダ](setup)（環境変数、TOML ファイルなど）を調べて、これらの辞書に値を入力します。`dlt.config.get()` または `dlt.secrets.get()` を使用して値を取得し、特定の型に変換することもできます。

```py
credentials = dlt.secrets.get("my_section.gcp_credentials", GcpServiceAccountCredentials)
```
これにより、`my_section.gcp_credentials` キーの下に保存されている値から `GcpServiceAccountCredentials` インスタンスが作成されます。

## 設定とシークレットをコードで記述する

`dlt.config` と `dlt.secrets` を使用して、プログラムで値を設定することもできます。
```py
dlt.config["sheet_id"] = "23029402349032049"
dlt.secrets["destination.postgres.credentials"] = BaseHook.get_connection('postgres_dsn').extra
```

これにより、指定した値を使用して TOML プロバイダーを効果的にモックします。

## コードで宛先認証情報を設定する

必要に応じて、プログラムで宛先認証情報を設定できます。次の例は、[GcpServiceAccountCredentials](complex_types#gcp-credentials) **仕様** を BigQuery の宛先で使用する方法を示しています。

```py
import os

import dlt
from dlt.sources.credentials import GcpServiceAccountCredentials
from dlt.destinations import bigquery

# Retrieve credentials from environment variable
creds_dict = os.getenv('BIGQUERY_CREDENTIALS')

# Create and initialize credentials instance
gcp_credentials = GcpServiceAccountCredentials()
gcp_credentials.parse_native_representation(creds_dict)

# Pass credentials to the BigQuery destination
pipeline = dlt.pipeline(destination=bigquery(credentials=gcp_credentials))
pipeline.run([{"key1": "value1"}], table_name="temp")
```

### Google スプレッドシートのソース例

この例は、Google スプレッドシートから選択されたタブを読み取る `google_sheets` ソース関数を示しています。

```py
@dlt.source
def google_sheets(
    spreadsheet_id=dlt.config.value,
    tab_names=dlt.config.value,
    credentials=dlt.secrets.value,
    only_strings=False
):
    # Handle credentials as either dictionary or string
    if isinstance(credentials, str):
        credentials = json.loads(credentials)
    # Handle tabs as either list or comma-separated string
    if isinstance(tab_names, str):
      tab_names = tab_names.split(",")
    sheets = build('sheets', 'v4', credentials=ServiceAccountCredentials.from_service_account_info(credentials))
    tabs = []
    for tab_name in tab_names:
        data = _get_sheet(sheets, spreadsheet_id, tab_name)
        tabs.append(dlt.resource(data, name=tab_name))
    return tabs
```

`@dlt.source` デコレータは、関数内のすべての引数を設定可能にします。特別なデフォルト値である `dlt.secrets.value` と `dlt.config.value` は、`dlt` に対してこれらの引数が必須であり、明示的に渡すか、設定ファイル内に存在する必要があることを示します。さらに、`dlt.secrets.value` は引数をシークレットとして指定します。

この例では、次のようになります。
- `spreadsheet_id` は **必須の設定** 引数です。
- `tab_names` は **必須の設定** 引数です。
- `credentials` は **必須のシークレット** 引数です（Google スプレッドシートの認証情報を辞書として格納）。
- `only_strings` はデフォルト値を持つ **オプションの設定** 引数です。

:::tip
`dlt.resource` も同様に機能するため、[スタンドアロン リソース](../resource.md#declare-a-standalone-resource) (**ソース** の内部関数として定義されていない) は同じ注入ルールに従います。
:::

## カスタム仕様の作成

**カスタム仕様** を使用すると、関数の引数を完全に制御できます。以下のことが可能です。

- 注入する値、型、デフォルト値を制御できます。
- 省略可能フィールドと最終フィールドを指定できます。
- 階層的な設定（仕様の中に仕様を記述する）を作成できます。
- `on_partial`（設定キーが見つからない場合に失敗する前に呼び出される）または `on_resolved` 用の独自のハンドラーを定義できます。
- 独自のネイティブ値パーサーを定義できます。
- 独自のデフォルト認証情報ロジックを定義できます。
- Python データクラス機能を利用できます。
- Python の `dict` 機能を利用できます（`specs` インスタンスは辞書から作成でき、辞書からシリアル化できます）。

実際、`dlt` はデコレートされた関数ごとに固有の仕様を生成します。例えば、`google_sheets` の場合、次のクラスが作成されます。

```py
from dlt.sources.config import configspec, with_config

@configspec
class GoogleSheetsConfiguration(BaseConfiguration):
  tab_names: List[str] = None  # mandatory
  credentials: GcpServiceAccountCredentials = None # mandatory secret
  only_strings: Optional[bool] = False
```

### すべての仕様は [BaseConfiguration](https://github.com/dlt-hub/dlt/blob/devel/dlt/common/configuration/specs/base_configuration.py#L170) から派生しています。
このクラスは、特定の特性を持つ設定オブジェクトを作成するための基盤として機能します。

- 設定を解析し、ネイティブ形式で表現するためのメソッド (`parse_native_representation` および `to_native_representation`) を提供します。

- 設定フィールドにアクセスし、操作するためのメソッドを定義します。

- データクラス上に辞書互換のインターフェースを実装します。これにより、このクラスのインスタンスを辞書のように扱うことができます。

- 特定の属性が存在するかどうか、フィールドが有効かどうか、メソッド解決順序 (MRO) に従ってメソッドを呼び出すためのヘルパー関数を定義します。

このクラスの詳細については、クラスのドキュメント文字列を参照してください。

### すべての認証情報は [CredentialsConfiguration](https://github.com/dlt-hub/dlt/blob/devel/dlt/common/configuration/specs/base_configuration.py#L307) から派生します。

このクラスは `BaseConfiguration` のサブクラスであり、様々な種類の認証情報を扱うための基本クラスとして機能します。認証情報の初期化、ネイティブ表現への変換、そして機密情報の適切な取り扱いを確保しながら文字列表現を生成するためのメソッドを定義します。

このクラスの詳細については、クラスのドキュメント文字列をご覧ください。

