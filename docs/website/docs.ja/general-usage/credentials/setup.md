---
title: 概要と例
description: 構成がどこに保存され、どのように記述されるかを学びます
keywords: [credentials, secrets.toml, secrets, config, configuration, environment variables, provider]
---

`dlt` は、環境変数、専用ファイル、セキュアボールトなど、複数の [場所](#choose-where-to-store-configuration) から設定とシークレットを取得します。
[設定セクション](#select-a-configuration-layout) のシンプルなレイアウトと詳細なレイアウトの両方を理解します。
一般的な外部システムの [組み込み](#use-built-in-credential-types) 認証情報のいずれかを使用できます。
`@dlt.source`、`@dlt.resource`、または `@dlt.destination` で修飾された関数は、追加コードを記述せずに設定できます。`dlt` は、呼び出されたときに、不足している引数（パスワードや API キーなど）を自動的に [挿入](advanced/#injection-rules) します。

## 設定を保存する場所を選択する {#choose-where-to-store-configuration}

:::tip dlt+
YAML ファイルを使用して宣言的に構成 (ソース、宛先、パイプライン、パラメーターを含む) を定義するには、[dlt+](../../plus/features/projects.md) を参照してください。
:::

`dlt` は、パイプライン実行時にクエリされる **config プロバイダ** を通じて、さまざまな場所（環境変数、toml ファイル、またはセキュアボールト）にある設定とシークレットを検索します。
単一の場所を選択することも、複数の場所を組み合わせることもできます。たとえば、シークレット `api_key` を環境変数で定義し、`api_url` を TOML ファイルで定義することもできます。
プロバイダは次の順序でクエリされます。

1. [環境変数](#environment-variables): 環境変数に値が見つかった場合、`dlt` はその値を使用し、優先度の低いプロバイダはチェックしません。

2. [secrets.toml ファイルと config.toml ファイル](#secretstoml-and-configtoml): これらのファイルには、設定値とシークレットが保存されます。`secrets.toml` には機密情報が含まれ、`config.toml` には機密でない設定が保持されます。

3. [Vaults](#vaults): Google Secrets Manager、Azure Key Vault、AWS Secrets Manager などの安全な Vault に保存された認証情報。

4. [カスタムプロバイダー](#custom-providers) (`register_provider` で追加): 独自の構成形式を使用したり、特殊な前処理を実行したりするために作成できるカスタム実装です。

5. [デフォルトの引数値](./advanced#injection-rules): 関数シグネチャで指定された値。

:::tip
パイプライン名には、英数字、ハイフン（`-`）、アンダースコア（`_`）のみを使用してください。すべての構成プロバイダーとの互換性を確保するため、空白文字やその他の句読点は使用しないでください。
:::

## 設定レイアウトを選択 {#select-a-configuration-layout}

プロジェクトの複雑さに応じて、さまざまな方法で設定を定義できます。ソースと宛先が1つだけのシンプルなパイプラインの場合、設定はシンプルになります。

最もシンプルな**ソース**設定：
<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
]}>
  <TabItem value="toml">

```toml
api_key="some_value"
```
  </TabItem>
  <TabItem value="env">

```sh
export API_KEY="some_value"
```
  </TabItem>
</Tabs>

**destination** の場合、通常は複数の関連するキーをグループ化する [credentials](#use-built-in-credential-types) を構成する必要があります。`dlt` はこれらを `credentials` セクションに配置します。

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
]}>
  <TabItem value="toml">

```toml
[credentials]
user="dlthub"
password="some_value"
```
  </TabItem>
  <TabItem value="env">

```sh
export CREDENTIALS__USER="dlthub"
export CREDENTIALS__PASSWORD="some_value"
```
  </TabItem>
</Tabs>

### 推奨されるセクションレイアウト {#recommended-section-layout}

引数名が競合する可能性のある複数のソースを使用する場合、または複数の宛先で別々の認証情報が必要な場合は、**セクション** を使用して設定キーを整理できます。

以下は、このドキュメントで最も頻繁に使用され、`dlt init` コマンドによって生成される**推奨セクションレイアウト**です。

* 最上位セクションの `sources` と `destination` を使用して、それぞれの設定を分離します。
* ソース関数が定義されている Python モジュール名を使用して、異なるモジュールで定義されたソースの設定を分離します。
* 宛先タイプを使用して、宛先を分離します。

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
]}>
  <TabItem value="toml">

```toml
# source defined in notion.py
[sources.notion]
api_key="some_value"
```
  </TabItem>
  <TabItem value="env">

```sh
export SOURCES__NOTION__API_KEY="some_value"
```
  </TabItem>
</Tabs>

Destination:

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
]}>
  <TabItem value="toml">

```toml
# use postgres destination
[destination.postgres.credentials]
user="dlthub"
password="some_value"

```
  </TabItem>
  <TabItem value="env">

```sh
export DESTINATION__POSTGRES__CREDENTIALS__USER="dltHub"
export DESTINATION__POSTGRES__CREDENTIALS__PASSWORD="some_value"
```
  </TabItem>
</Tabs>

特定のソースと宛先を構成する方法の詳細な例とヒントについては、[資格情報の追加](../../walkthroughs/add_credentials.md)ガイドを参照してください。

### dlt が値を探す方法

`dlt` は、すべての可能なセクションを対象に特定の値の検索を開始し、値が見つからない場合は右端のセクションを削除して再試行します。

例えば、ソース関数がモジュール `notion.py` 内にある場合:

```py
# module: notion.py

@dlt.source
def notion_databases(api_key: str = dlt.secrets.value):
    pass
```

`dlt` は以下のキーを以下の順序で検索します。

1. `sources.notion.notion_databases.api_key`
2. `sources.notion.api_key`
3. `sources.api_key`
4. `api_key`

出力先の認証情報も同様です。この場合、`credentials` セクションは必須のグループとみなされ、削除されません。

1. `destination.postgres.credentials.password`
2. `destination.credentials.password`
3. `credentials.password`

:::tip
構成の構成の詳細については、[構成とシークレットの構造](advanced.md#organize-configuration-and-secrets-with-sections)を参照してください。
:::

:::tip
パイプライン名を使用して、プロジェクト内のパイプラインごとに個別の設定を作成できます。
設定値は、最初にパイプライン名のプレフィックス付きで検索され、次にプレフィックスなしで検索されます:

```toml
[pipeline_name_1.sources.google_sheets.credentials]
client_email = "<client_email_1>"
private_key = "<private_key_1>"
project_id = "<project_id_1>"

[pipeline_name_2.sources.google_sheets.credentials]
client_email = "<client_email_2>"
private_key = "<private_key_2>"
project_id = "<project_id_2>"
```
:::

### 組み込みの認証情報タイプを使用する {#use-built-in-credential-types}

認証情報とは、外部システムにアクセスするためにまとめて定義される構成情報とシークレットのグループです。
`dlt` は、AWS、Azure、Google Cloud などの一般的なシステムにアクセスするために、複数の [組み込みの認証情報タイプ](./complex_types) を実装しています。

一部の認証情報タイプでは、指定方法が異なります。
たとえば、`sql_database` ソースに接続するには、接続文字列を使用するか、次の接続文字列を使用します。

```toml
[sources.sql_database]
credentials="snowflake://user:password@service-account/database?warehouse=warehouse_name&role=role"
```

または、接続パラメータを個別に設定します:

```toml
[sources.sql_database.credentials]
drivername="snowflake"
username="user"
password="password"
database="database"
host="service-account"
warehouse="warehouse_name"
role="role"
```

:::tip
`dlt` はすべての主要なクラウド プロバイダーの **デフォルトの認証情報** を検出できます。つまり、ランタイム環境にすでに存在するものを使用できます。つまり、Colab または Google VM で実行しているときはクラウド認証情報にアクセスでき、構成で何も指定されていない場合は代わりにそれらを使用します。
:::

## 環境変数 {#environment-variables}

環境変数は、特にデプロイメント環境において、設定やシークレットを指定するための便利な手段となります。環境変数を使用する場合は、名前を大文字にし、セクションは二重のアンダースコア (`__`) で区切ります。

例えば、Facebook 広告のアクセストークンを設定するには、次のようにします:

```sh
export SOURCES__FACEBOOK_ADS__ACCESS_TOKEN="<access_token>"
```

環境変数を使用して資格情報を設定する方法の詳細については、[例のセクション](#examples)を参照してください。

:::tip
ローカル開発の場合、[python-dotenv](https://pypi.org/project/python-dotenv/) を使用して `.env` ファイルから変数を自動的に読み込むことができ、資格情報の管理がより簡単かつ安全になります。
:::

:::tip
環境変数は `/run/secrets/<secret-name>` からシークレット値を取得して、**Kubernetes/Docker シークレット** とシームレスに連携することもできます。

これらのシークレットに対して、`dlt` は小文字を使用し、ダッシュ (`-`) を区切り文字として使い、アンダースコアをダッシュ​​に変換した代替名形式を使用します。たとえば、上記の環境変数では `sources--facebook-ads--access-token` がチェックされます。

この方法でチェックされるのは、シークレットとしてマークされた値 (`dlt.secrets.value` でマークされている値、または `TSecretStrValue` などの型を使用) のみです。Kubernetes リソースまたは Docker Compose ファイルでは、シークレットに適切な名前を付けることを忘れないでください。
:::

## Vaults

`dlt` は、認証情報を保存するための専用サービスであるセキュア Vault から構成を読み取る場合があります。

* Google Cloud Secrets Manager については、[サンプルチュートリアル](../../walkthroughs/add_credentials.md#retrieving-credentials-from-google-cloud-secret-manager)をご覧ください。

* AWS Secrets Manager や Azure Key Vault などのその他の Vault 統合については、[営業チーム](https://dlthub.com/contact-sales) までお問い合わせいただき、[データプラットフォーム チーム向けのセキュアな構成要素](https://dlthub.com/product/data-platform-teams#secure) についてご確認ください。

## secrets.toml と config.toml {#secretstoml-and-configtoml}

TOML 構成プロバイダーは、2 つの別々のファイルを使用します。

**config.toml**:
- パイプラインの動作を定義する、機密性のない構成データが含まれます。
- ファイルパス、データベースホスト、タイムアウト、API URL、パフォーマンスオプションなどの設定が含まれます。
- 値は、`dlt.config` ディクショナリを介してコードからアクセスできます。
- バージョン管理に安全にコミットできます。

**secrets.toml**:
- 機密性を維持する必要がある機密情報が含まれます。
- パスワード、API キー、秘密鍵などの認証情報が含まれます。
- 値は、`dlt.secrets` ディクショナリを介してコードからアクセスできます。
- バージョン管理にコミットしないでください。

デフォルトでは、プロジェクトの `.gitignore` ファイルによって `secrets.toml` がバージョン管理に追加されるのがブロックされますが、`config.toml` は自由に含めることができます。

### ファイルの場所

TOMLプロバイダーは、**現在の作業ディレクトリを基準とした** `.dlt` フォルダからファイルを読み込みます。

例えば、作業ディレクトリが `my_dlt_project` で、次のような構造になっている場合:

```text
my_dlt_project:
  |
  pipelines/
    |---- .dlt/secrets.toml
    |---- google_sheets.py
```

実行すると:
```sh
python pipelines/google_sheets.py
```

`dlt` は `my_dlt_project/.dlt/secrets.toml` 内のシークレットを検索し、`my_dlt_project/pipelines/.dlt/secrets.toml` は無視します。

作業ディレクトリを `pipelines` に変更して次のコマンドを実行します。
```sh
python google_sheets.py
```

`dlt` は代わりに `my_dlt_project/pipelines/.dlt/secrets.toml` を検索します。

### 特別な場所

TOML プロバイダーは、ランタイム環境に応じて特別な場所から設定を読み取ります。

1. **ホームディレクトリ**: `dlt` は、`~/.dlt/` で `config.toml` と `secrets.toml` を検索します。これらの値はプロジェクト固有の設定とマージされ、プロジェクトの値が優先されます。これは、マシン上のすべてのパイプラインでグローバル設定（テレメトリの設定など）を共有する場合に便利です。

2. **Google Colab**: Colab で実行する場合、`secrets.toml` および `config.toml` という名前の Colab Secret を使用できます。プロバイダーは、これらを TOML ファイルのように読み取ります。`.dlt` フォルダにファイルが存在する場合、この機能は無効になります。

3. **Streamlit**: Streamlit で実行する場合、ローカルの `.dlt/secrets.toml` が存在しないため、プロバイダーは Streamlit Secret を使用します。 `dlt` シークレットを Streamlit シークレットに直接追加できます。

## カスタムプロバイダー {#custom-providers}

独自の設定プロバイダーを作成して登録することで、`dlt` が設定値にアクセスする方法をカスタマイズできます。最も簡単な方法は、セクション名と引数名をキーとするネストされた辞書を返す関数を作成することです。

以下の例は、JSON ファイルから設定を読み込むカスタムプロバイダーの作成方法を示しています。

```py
import dlt
from dlt.common import json
from dlt.common.configuration.providers import CustomLoaderDocProvider

# Create a function that loads a dictionary
def load_config():
    with open("config.json", "rb") as f:
        return json.load(f)

# Create the custom provider
provider = CustomLoaderDocProvider(
    "my_json_provider", 
    load_config, 
    supports_secrets=False
)

# Register the provider with dlt
dlt.config.register_provider(provider)
```

:::tip
切り替え可能な構成プロファイルをサポートする [サンプル YAML プロバイダー](../../examples/custom_config_provider) を確認してください。
:::

## 例

### 設定とシークレットの両方を設定します

この例では、[Notion](../../dlt-ecosystem/verified-sources/notion) ソースと [filesystem](../../dlt-ecosystem/destinations/filesystem) 宛先を使用して、[推奨セクションレイアウト](#recommended-section-layout) を用いて TOML ファイル内の設定を整理する方法を示します。

Notion のソースは `notion.py` というファイルで定義されているため、設定ではそのモジュール名を使用します。設定では `api_key` を設定し、データベース ID のリストはコードで明示的に渡します。ファイルシステムの宛先については、設定を `config.toml` (`bucket_url` 用) と `secrets.toml` (AWS 認証情報用) に分割します。

```py
import dlt

@dlt.source
def notion_databases(
    database_ids = None,
    api_key: str = dlt.secrets.value,  # mark argument to be injected as secret
):
   ...

# Pass database_id in code, let `dlt` inject api_key
sales_database = notion_databases(  # type: ignore
  database_ids=[
            {
                "id": "a94223535c674d33a24e313e7921ce15",
                "use_name": "sales_alias",
            }
        ]
)
```

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
    {"label": "In the code", "value": "code"},
]}>

  <TabItem value="toml">

**config.toml**

```toml
[runtime]
log_level="INFO"

# Do not compress files sent to the filesystem bucket
[normalize.data_writer]
disable_compression=true

# Recommended sections for the destination (destination.module)
[destination.filesystem]
bucket_url = "s3://[your_bucket_name]"
```

**secrets.toml**

```toml
# Recommended sections for sources (sources.module)
[sources.notion]
api_key = "your-notion-api-key"  # Will be injected to api_key argument

# Recommended sections for destination credentials
[destination.filesystem.credentials]
aws_access_key_id = "ABCDEFGHIJKLMNOPQRST" 
aws_secret_access_key = "1234567890_access_key" 
```

  </TabItem>

  <TabItem value="env">

```sh
# Environment variables for both config and secrets follow the same format
export RUNTIME__LOG_LEVEL="INFO"
export DESTINATION__FILESYSTEM__BUCKET_URL="s3://[your_bucket_name]"
export NORMALIZE__DATA_WRITER__DISABLE_COMPRESSION="true"
export SOURCES__NOTION__API_KEY="your-notion-api-key"
export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID="ABCDEFGHIJKLMNOPQRST"
export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY="1234567890_access_key"
```

  </TabItem>

  <TabItem value="code">

```py
import os
import dlt
import botocore.session
from dlt.common.credentials import AwsCredentials

# Set configuration values directly in code
# Via environment variables
os.environ["RUNTIME__LOG_LEVEL"] = "INFO"
os.environ["DESTINATION__FILESYSTEM__BUCKET_URL"] = "s3://[your_bucket_name]"
os.environ["NORMALIZE__DATA_WRITER__DISABLE_COMPRESSION"] = "true"

# Or directly through dlt.config
dlt.config["runtime.log_level"] = "INFO"
dlt.config["destination.filesystem.bucket_url"] = "s3://[your_bucket_name]"
dlt.config["normalize.data_writer.disable_compression"] = "true"

# For secrets, avoid hardcoding - use existing environment variables
os.environ["SOURCES__NOTION__API_KEY"] = os.environ.get("NOTION_KEY")

# Or use credentials from third-party providers
credentials = AwsCredentials()
session = botocore.session.get_session()
credentials.parse_native_representation(session)
dlt.secrets["destination.filesystem.credentials"] = credentials
```

  </TabItem>

</Tabs>

:::caution
利便性のため、すべての構成と認証情報を `secrets.toml` に置くことができますが、機密情報は `config.toml` やその他の安全でない場所に置かないでください。`dlt` は、不適切な場所に秘密情報が存在することを検出すると例外を発生させます。
:::


### ソースと宛先に異なる Google 認証情報を使用する

この例は、Google ベースのソースと宛先に異なる認証情報を設定する方法を示しています。

#### オプション 1: ソースとターゲット間で認証情報を共有する

BigQuery のターゲットと Google スプレッドシートのソースの両方で同じ認証情報を使用する場合:

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
    {"label": "In the code", "value": "code"},
]}>

  <TabItem value="toml">

```toml
[credentials]
client_email = "<client_email_for_both>"
private_key = "<private_key_for_both>"
project_id = "<project_id_for_both>"
```

  </TabItem>

  <TabItem value="env">

```sh
export CREDENTIALS__CLIENT_EMAIL="<client_email_for_both>"
export CREDENTIALS__PRIVATE_KEY="<private_key_for_both>"
export CREDENTIALS__PROJECT_ID="<project_id_for_both>"
```

  </TabItem>

 <TabItem value="code">

```py
import os

# Avoid setting secrets directly in code
# Instead, use existing environment variables
os.environ["CREDENTIALS__CLIENT_EMAIL"] = os.environ.get("GOOGLE_CLIENT_EMAIL")
os.environ["CREDENTIALS__PRIVATE_KEY"] = os.environ.get("GOOGLE_PRIVATE_KEY")
os.environ["CREDENTIALS__PROJECT_ID"] = os.environ.get("GOOGLE_PROJECT_ID")
```

  </TabItem>

</Tabs>

#### オプション2: ソースと宛先に別々の認証情報を使用する

ソースと宛先の認証情報を別々にするには:

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
    {"label": "In the code", "value": "code"},
]}>

  <TabItem value="toml">

```toml
# Google Sheets credentials
[sources.credentials]
client_email = "<sheets_client_email>"
private_key = "<sheets_private_key>"
project_id = "<sheets_project_id>"

# BigQuery credentials
[destination.credentials]
client_email = "<bigquery_client_email>"
private_key = "<bigquery_private_key>"
project_id = "<bigquery_project_id>"
```

  </TabItem>

  <TabItem value="env">

```sh
# Google Sheets credentials
export SOURCES__CREDENTIALS__CLIENT_EMAIL="<sheets_client_email>"
export SOURCES__CREDENTIALS__PRIVATE_KEY="<sheets_private_key>"
export SOURCES__CREDENTIALS__PROJECT_ID="<sheets_project_id>"

# BigQuery credentials
export DESTINATION__CREDENTIALS__CLIENT_EMAIL="<bigquery_client_email>"
export DESTINATION__CREDENTIALS__PRIVATE_KEY="<bigquery_private_key>"
export DESTINATION__CREDENTIALS__PROJECT_ID="<bigquery_project_id>"
```

  </TabItem>

 <TabItem value="code">

```py
import dlt
import os

# For destination credentials, use existing environment variables
os.environ["DESTINATION__CREDENTIALS__CLIENT_EMAIL"] = os.environ.get("BIGQUERY_CLIENT_EMAIL")
os.environ["DESTINATION__CREDENTIALS__PRIVATE_KEY"] = os.environ.get("BIGQUERY_PRIVATE_KEY")
os.environ["DESTINATION__CREDENTIALS__PROJECT_ID"] = os.environ.get("BIGQUERY_PROJECT_ID")

# For source credentials, set values in dlt.secrets
dlt.secrets["sources.credentials.client_email"] = os.environ.get("SHEETS_CLIENT_EMAIL")
dlt.secrets["sources.credentials.private_key"] = os.environ.get("SHEETS_PRIVATE_KEY")
dlt.secrets["sources.credentials.project_id"] = os.environ.get("SHEETS_PROJECT_ID")
```

  </TabItem>

</Tabs>

この設定では、`dlt` は次の順序で宛先の資格情報を検索します。
```sh
destination.bigquery.credentials --> Not found
destination.credentials --> Found
```

ソースの資格情報の場合:
```sh
sources.google_sheets_module.google_sheets_function.credentials --> Not found
sources.google_sheets_function.credentials --> Not found
sources.credentials --> Found
```

### 複数のソースと宛先の認証情報を設定する

複数の Google ベースのソースと宛先を扱う場合は、推奨セクションレイアウトを使用できます。

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
    {"label": "In the code", "value": "code"},
]}>

  <TabItem value="toml">

```toml
# Google Sheets credentials
[sources.google_sheets.credentials]
client_email = "<sheets_client_email>"
private_key = "<sheets_private_key>"
project_id = "<sheets_project_id>"

# Google Analytics credentials
[sources.google_analytics.credentials]
client_email = "<analytics_client_email>"
private_key = "<analytics_private_key>"
project_id = "<analytics_project_id>"

# BigQuery credentials
[destination.bigquery.credentials]
client_email = "<bigquery_client_email>"
private_key = "<bigquery_private_key>"
project_id = "<bigquery_project_id>"
```

  </TabItem>

  <TabItem value="env">

```sh
# Google Sheets credentials
export SOURCES__GOOGLE_SHEETS__CREDENTIALS__CLIENT_EMAIL="<sheets_client_email>"
export SOURCES__GOOGLE_SHEETS__CREDENTIALS__PRIVATE_KEY="<sheets_private_key>"
export SOURCES__GOOGLE_SHEETS__CREDENTIALS__PROJECT_ID="<sheets_project_id>"

# Google Analytics credentials
export SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__CLIENT_EMAIL="<analytics_client_email>"
export SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__PRIVATE_KEY="<analytics_private_key>"
export SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__PROJECT_ID="<analytics_project_id>"

# BigQuery credentials
export DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL="<bigquery_client_email>"
export DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY="<bigquery_private_key>"
export DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID="<bigquery_project_id>"
```

  </TabItem>

 <TabItem value="code">

```py
import os
import dlt

# For Analytics credentials
os.environ["SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__CLIENT_EMAIL"] = os.environ.get("ANALYTICS_CLIENT_EMAIL")
os.environ["SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__PRIVATE_KEY"] = os.environ.get("ANALYTICS_PRIVATE_KEY")
os.environ["SOURCES__GOOGLE_ANALYTICS__CREDENTIALS__PROJECT_ID"] = os.environ.get("ANALYTICS_PROJECT_ID")

# For BigQuery credentials
os.environ["DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL"] = os.environ.get("BIGQUERY_CLIENT_EMAIL")
os.environ["DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY"] = os.environ.get("BIGQUERY_PRIVATE_KEY")
os.environ["DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID"] = os.environ.get("BIGQUERY_PROJECT_ID")

# For Google Sheets credentials
dlt.secrets["sources.google_sheets.credentials.client_email"] = os.environ.get("SHEETS_CLIENT_EMAIL")
dlt.secrets["sources.google_sheets.credentials.private_key"] = os.environ.get("SHEETS_PRIVATE_KEY")
dlt.secrets["sources.google_sheets.credentials.project_id"] = os.environ.get("SHEETS_PROJECT_ID")
```

  </TabItem>

</Tabs>

### 同じソースの複数のインスタンスを設定する

同じソースタイプから異なる設定でデータを抽出する必要がある場合は、異なるパイプライン名で実行できます。

<Tabs
  groupId="config-provider-type"
  defaultValue="toml"
  values={[
    {"label": "TOML config provider", "value": "toml"},
    {"label": "Environment variables", "value": "env"},
    {"label": "In the code", "value": "code"},
]}>

  <TabItem value="toml">

```toml
[pipeline_name_1.sources.sql_database]
credentials="snowflake://user1:password1@service-account/database1?warehouse=warehouse_name&role=role1"

[pipeline_name_2.sources.sql_database]
credentials="snowflake://user2:password2@service-account/database2?warehouse=warehouse_name&role=role2"
```

  </TabItem>

  <TabItem value="env">

```sh
export PIPELINE_NAME_1__SOURCES__SQL_DATABASE__CREDENTIALS="snowflake://user1:password1@service-account/database1?warehouse=warehouse_name&role=role1"
export PIPELINE_NAME_2__SOURCES__SQL_DATABASE__CREDENTIALS="snowflake://user2:password2@service-account/database2?warehouse=warehouse_name&role=role2"
```

  </TabItem>

 <TabItem value="code">

```py
import os
import dlt

# Use existing environment variables to set credentials
os.environ["PIPELINE_NAME_1__SOURCES__SQL_DATABASE__CREDENTIALS"] = os.environ.get("SQL_CREDENTIAL_STRING_1")

# Or set values directly in dlt.secrets
dlt.secrets["pipeline_name_2.sources.sql_database.credentials"] = os.environ.get("SQL_CREDENTIAL_STRING_2")
```

  </TabItem>

</Tabs>

:::tip
同じソースの複数のインスタンスを利用するための追加オプションがあります。

1. [sql_database ドキュメント](../../dlt-ecosystem/verified-sources/sql_database/advanced.md#configure-many-sources-side-by-side-with-custom-sections)で説明されているように、`clone()`メソッドを使用します。

2. 同じ宛先タイプを異なる構成で使用するには、[名前付き宛先](../destination.md#configure-multiple-destinations-in-a-pipeline)を作成します。
:::

## 構成エラーのトラブルシューティング

`dlt` が必要な構成値またはシークレットを見つけられない場合、`ConfigFieldMissingException` 例外が発生します。この例外は、検索内容と検索場所に関する詳細情報を提供します。

例えば、パスワードを指定せずに `chess.py` サンプルを実行すると、次のようになります。

```sh
$ CREDENTIALS="postgres://loader@localhost:5432/dlt_data" python chess.py
...
dlt.common.configuration.exceptions.ConfigFieldMissingException: Following fields are missing: ['password'] in configuration with spec PostgresCredentials
        for field "password" config providers and keys were tried in the following order:
                In Environment Variables key CHESS_GAMES__DESTINATION__POSTGRES__CREDENTIALS__PASSWORD was not found.
                In Environment Variables key CHESS_GAMES__DESTINATION__CREDENTIALS__PASSWORD was not found.
                In Environment Variables key CHESS_GAMES__CREDENTIALS__PASSWORD was not found.
                In secrets.toml key chess_games.destination.postgres.credentials.password was not found.
                In secrets.toml key chess_games.destination.credentials.password was not found.
                In secrets.toml key chess_games.credentials.password was not found.
                In Environment Variables key DESTINATION__POSTGRES__CREDENTIALS__PASSWORD was not found.
                In Environment Variables key DESTINATION__CREDENTIALS__PASSWORD was not found.
                In Environment Variables key CREDENTIALS__PASSWORD was not found.
                In secrets.toml key destination.postgres.credentials.password was not found.
                In secrets.toml key destination.credentials.password was not found.
                In secrets.toml key credentials.password was not found.
Please refer to https://dlthub.com/docs/general-usage/credentials/ for more information
```

このエラーメッセージは、以下の点を正確に示しています。

1. どのフィールドが欠落しているか（この場合は「password」）
2. `dlt` がチェックしたすべてのキーと場所（優先度順）
3. 最初にパイプライン名（「chess_games」）のプレフィックス付きで検索し、次にプレフィックスなしで検索した
4. 最初に環境変数を検索し、次に `secrets.toml` を検索した

`config.toml` はシークレットの保存に適していないため、チェックされていないことに注意してください。

