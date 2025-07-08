---
title: 組み込みの資格情報
description: AWS、Azure、Google Cloudなどのシステムへのアクセスを構成する
keywords: [credentials, secrets.toml, secrets, config, configuration, environment
      variables, specs]
---

## 概要

`dlt` は、一般的な外部システムとのシームレスな統合を可能にする組み込みの認証情報 (**specs**) を提供します。これらの specs は、[概要](setup.md) ドキュメントに記載されている方法を使用して設定できます。AWS、Azure、Google Cloud などの主要なクラウドプロバイダーの場合、`dlt` はクライアント固有のコードを呼び出してユーザーを認証し、実行環境からデフォルトの認証情報を自動的に取得することもできます。さらに、`dlt` は接続文字列やサービス JSON などの認証情報の一般的な文字列表現を理解するため、一般的な辞書表現以外のさまざまな認証情報形式を簡単に扱うことができます。

:::tip
[RESTClient セクション](../http/rest-client.md#authentication)で、`dlt` RestAPI クライアントでサポートされている認証方法について詳しく学習してください。
:::


## ConnectionStringCredentials の例

`ConnectionStringCredentials` はデータベース接続文字列を処理します。

```py
from dlt.sources.credentials import ConnectionStringCredentials

@dlt.source
def query(sql: str, dsn: ConnectionStringCredentials = dlt.secrets.value):
  ...
```

上記のソースは、`dsn` で定義されたデータベースに対して `sql` を実行します。`ConnectionStringCredentials` は、正しい型で正しい値を取得し、資格情報の適切なネイティブ形式を認識します。

以下は、`secrets.toml` ファイルと `config.toml` ファイルで資格情報を設定する方法の例です。

### 辞書形式

```toml
[dsn]
database="dlt_data"
password="loader"
username="loader"
host="localhost"
```

### ネイティブ形式

```toml
dsn="postgres://loader:loader@localhost:5432/dlt_data"
```

### 混合形式

パスワード以外のすべての資格情報がコード内で明示的に提供されている場合、`dlt` は `secrets.toml` でパスワードを検索します。

```toml
dsn.password="loader"
```

さまざまな形式で資格情報を明示的に提供できます:

```py
query("SELECT * FROM customers", "postgres://loader@localhost:5432/dlt_data") # type: ignore[arg-type]
# or
query("SELECT * FROM customers", {"database": "dlt_data", "username": "loader"}) # type: ignore[arg-type]
```

## 組み込みの認証情報 {#built-in-credentials}

`dlt` は、再利用できる既製の認証情報を提供します。

```py
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.credentials import OAuth2Credentials
from dlt.sources.credentials import GcpServiceAccountCredentials, GcpOAuthCredentials
from dlt.sources.credentials import AwsCredentials
from dlt.sources.credentials import AzureCredentials
```

### ConnectionStringCredentials

`ConnectionStringCredentials` クラスは、SQL データベース接続用の接続文字列認証情報を処理します。ドライバー名、データベース名、ユーザー名、パスワード、ホスト、ポート、その他のクエリパラメータなどの属性が含まれます。このクラスは、接続文字列を解析および生成するためのメソッドを提供します。

#### 使用方法
```py
credentials = ConnectionStringCredentials()

# Set the necessary attributes
credentials.drivername = "postgresql"
credentials.database = "my_database"
credentials.username = "my_user"
credentials.password = "my_password"  # type: ignore
credentials.host = "localhost"
credentials.port = 5432

# Convert credentials to a connection string
connection_string = credentials.to_native_representation()

# Parse a connection string and update credentials
native_value = "postgresql://my_user:my_password@localhost:5432/my_database"
credentials.parse_native_representation(native_value)

# Get a URL representation of the connection
url_representation = credentials.to_url()
```
上記は、ソースと TOML ファイルでこの仕様を使用する方法の例です。

### OAuth2Credentials

`OAuth2Credentials` クラスは、クライアント ID、クライアントシークレット、リフレッシュトークン、アクセストークンなどの OAuth 2.0 認証情報を処理します。また、スコープの追加やクライアント認証のためのメソッドも提供します。

使用方法:
```py
oauth_credentials = OAuth2Credentials(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",  # type: ignore
    refresh_token="REFRESH_TOKEN",  # type: ignore
    scopes=["scope1", "scope2"]
)

# Authorize the client
oauth_credentials.auth()

# Add additional scopes
oauth_credentials.add_scopes(["scope3", "scope4"])
```

`OAuth2Credentials` は実際の OAuth を実装するための基本クラスです。たとえば、[GcpOAuthCredentials](#gcpoauthcredentials) の基本クラスです。

### GCP 認証情報

#### 例
* [Google Analytics 検証済みソース](https://github.com/dlt-hub/verified-sources/blob/master/sources/google_analytics/__init__.py): GCP 認証情報の使用方法の例。
* [Google Analytics の例](https://github.com/dlt-hub/verified-sources/blob/master/sources/google_analytics/setup_script_gcp_oauth.py): `dlt.secrets.value` を使用してリフレッシュトークンを取得する方法。

#### Types

* [GcpServiceAccountCredentials](#gcpserviceaccountcredentials).
* [GcpOAuthCredentials](#gcpoauthcredentials).

#### GcpServiceAccountCredentials

`GcpServiceAccountCredentials` クラスは、GCP サービスアカウントの認証情報を管理します。このクラスは、Google クライアントのネイティブ認証情報を取得するためのメソッドを提供します。

##### 使用方法

- `service.json` を文字列または辞書として渡すこともできます（コード内および構成プロバイダー経由）。
- または、デフォルトの認証情報が使用されます。

```py
gcp_credentials = GcpServiceAccountCredentials()
# Parse a native value (ServiceAccountCredentials)
# Accepts a native value, which can be either an instance of ServiceAccountCredentials
# or a serialized services.json.
# Parses the native value and updates the credentials.
gcp_native_value = {"private_key": ".."} # or "path/to/services.json"
gcp_credentials.parse_native_representation(gcp_native_value)
```
またはより好ましい使用法:
```py
import dlt
from dlt.sources.credentials import GcpServiceAccountCredentials
from google.analytics import BetaAnalyticsDataClient

@dlt.source
def google_analytics(
    property_id: str = dlt.config.value,
    credentials: GcpServiceAccountCredentials = dlt.secrets.value,
):
    # Retrieve native credentials for Google clients
    # For example, build the service object for Google Analytics PI.
    client = BetaAnalyticsDataClient(credentials=credentials.to_native_credentials())

    # Get a string representation of the credentials
    # Returns a string representation of the credentials in the format client_email@project_id.
    credentials_str = str(credentials)
    ...
```
一方、`secrets.toml` は次のようになります。
```toml
[sources.google_analytics.credentials]
client_id = "client_id" # please set me up!
client_secret = "client_secret" # please set me up!
refresh_token = "refresh_token" # please set me up!
project_id = "project_id" # please set me up!
```
そして `config.toml`:
```toml
[sources.google_analytics]
property_id = "213025502"
```

#### GcpOAuthCredentials

`GcpOAuthCredentials` クラスは、Google Cloud Platform (GCP) のデスクトップ アプリケーションの OAuth2 認証情報を処理します。ネイティブ値を `GoogleOAuth2Credentials` またはシリアル化された OAuth クライアント シークレット JSON として解析できます。このクラスは、認証とアクセス トークンの取得のためのメソッドを提供します。

##### 使用方法

```py
oauth_credentials = GcpOAuthCredentials()

# Accepts a native value, which can be either an instance of GoogleOAuth2Credentials
# or serialized OAuth client secrets JSON.
# Parses the native value and updates the credentials.
native_value_oauth = {"client_secret": ...}
oauth_credentials.parse_native_representation(native_value_oauth)
```
Or more preferred use:
```py
import dlt
from dlt.sources.credentials import GcpOAuthCredentials

@dlt.source
def google_analytics(
    property_id: str = dlt.config.value,
    credentials: GcpOAuthCredentials = dlt.secrets.value,
):
    # Authenticate and get access token
    credentials.auth(scopes=["scope1", "scope2"])

    # Retrieve native credentials for Google clients
    # For example, build the service object for Google Analytics API.
    client = BetaAnalyticsDataClient(credentials=credentials.to_native_credentials())

    # Get a string representation of the credentials
    # Returns a string representation of the credentials in the format client_id@project_id.
    credentials_str = str(credentials)
    ...
```
一方、`secrets.toml` は次のようになります。
```toml
[sources.google_analytics.credentials]
client_id = "client_id" # please set me up!
client_secret = "client_secret" # please set me up!
refresh_token = "refresh_token" # please set me up!
project_id = "project_id" # please set me up!
```
そして `config.toml`:
```toml
[sources.google_analytics]
property_id = "213025502"
```

`auth()` メソッドを成功させるには、次の条件を満たす必要があります。

- 最新の **アクセストークン** を取得し、OAuth で認証するには、有効な `client_id`、`client_secret`、`refresh_token`、`project_id` を指定する必要があります。`refresh_token` には、アクセスに必要なすべてのスコープが含まれている必要があることに注意してください。
- `refresh_token` が指定されておらず、コンソールまたはノートブックからパイプラインを実行する場合、`dlt` は InstalledAppFlow を使用してデスクトップ認証フローを実行します。

#### デフォルト

設定値が欠落している場合、`dlt` はデフォルトの Google 認証情報（`default()` から取得）を使用します（利用可能な場合）。[Google のデフォルト](https://googleapis.dev/python/google-auth/latest/user-guide.html#application-default-credentials) の詳細については、こちらをご覧ください。

- `dlt` はデフォルトの認証情報から `project_id` を取得しようとします。プロジェクト ID が欠落している場合は、シークレットから `project_id` を検索します。そのため、通常は認証情報の一部（`project_id` のみ）を渡し、残りはデフォルトから取得します。

### AwsCredentials

`AwsCredentials`クラスは、アクセスキー、セッショントークン、プロファイル名、リージョン名、エンドポイントURLなどのAWS認証情報の処理を担当します。デフォルトの認証情報を管理する機能を継承し、部分的な認証情報の処理や認証情報をbotocoreセッションに変換するメソッドを追加して拡張しています。

#### 使用方法
```py
aws_credentials = AwsCredentials()
# Set the necessary attributes
aws_credentials.aws_access_key_id = "ACCESS_KEY_ID"
aws_credentials.aws_secret_access_key = "SECRET_ACCESS_KEY"
aws_credentials.region_name = "us-east-1"
```
or
```py
# Imports an external botocore session and sets the credentials properties accordingly.
import botocore.session

aws_credentials = AwsCredentials()
session = botocore.session.get_session()
aws_credentials.parse_native_representation(session)
print(aws_credentials.aws_access_key_id)
```
or more preferred use:
```py
@dlt.source
def aws_readers(
    bucket_url: str = dlt.config.value,
    credentials: AwsCredentials = dlt.secrets.value,
):
    ...
    # Convert credentials to s3fs format
    s3fs_credentials = credentials.to_s3fs_credentials()
    print(s3fs_credentials["key"])

    # Get AWS credentials from botocore session
    aws_credentials = credentials.to_native_credentials()
    print(aws_credentials.access_key)
    ...
```
一方、`secrets.toml` は次のようになります。
```toml
[sources.aws_readers.credentials]
aws_access_key_id = "key_id"
aws_secret_access_key = "access_key"
region_name = "region"
```
そして `config.toml`:
```toml
[sources.aws_readers]
bucket_url = "bucket_url"
```

#### デフォルト

設定が指定されていない場合、`dlt` はマシン上に存在するデフォルトの AWS 認証情報（`.aws/credentials` から取得）を使用します。

- botocore セッションのインスタンスを作成することで動作します。
- `profile_name` が指定されている場合は、そのプロファイルの認証情報が使用されます。指定されていない場合は、デフォルトのプロファイルが使用されます。

### AzureCredentials

`AzureCredentials` クラスは、アカウント名、アカウントキー、Shared Access Signature (SAS) トークン、SAS トークンのアクセス許可など、Azure Blob Storage の資格情報の処理を担当します。このクラスは、デフォルトの資格情報を管理する機能を継承し、部分的な資格情報の処理や、adlfs ライブラリを使用して Azure Blob Storage とのやり取りに適した形式への資格情報変換を行うメソッドを追加して拡張しています。

#### 使用方法
```py
az_credentials = AzureCredentials()
# Set the necessary attributes
az_credentials.azure_storage_account_name = "ACCOUNT_NAME"
az_credentials.azure_storage_account_key = "ACCOUNT_KEY"
```
or more preferred use:
```py
@dlt.source
def azure_readers(
    bucket_url: str = dlt.config.value,
    credentials: AzureCredentials = dlt.secrets.value,
):
    ...
    # Generate a SAS token
    credentials.create_sas_token()
    print(credentials.azure_storage_sas_token)

    # Convert credentials to adlfs format
    adlfs_credentials = credentials.to_adlfs_credentials()
    print(adlfs_credentials["account_name"])

    # to_native_credentials() is not yet implemented
    ...
```
一方、`secrets.toml` は次のようになります。
```toml
[sources.azure_readers.credentials]
azure_storage_account_name = "account_name"
azure_storage_account_key = "account_key"
```
そして `config.toml`:
```toml
[sources.azure_readers]
bucket_url = "bucket_url"
```

#### デフォルト

設定が指定されていない場合、`dlt` は `DefaultAzureCredential` を使用してデフォルトの資格情報を使用します。

## 認証情報の代替（ユニオン型）の使用

ソース/リソースが複数の認証方法をサポートしている場合、ユーザーはそれらをシームレスに利用できます。ユーザーは適切な認証情報を渡すだけで、`dlt` が適切な型をデコレートされた関数に挿入します。

例:

```py
@dlt.source
def zen_source(credentials: Union[ZenApiKeyCredentials, ZenEmailCredentials, str] = dlt.secrets.value, some_option: bool = False):
  # Depending on what the user provides in config, ZenApiKeyCredentials or ZenEmailCredentials will be injected into the `credentials` argument. Both classes implement `auth` so you can always call it.
  credentials.auth() # type: ignore[union-attr]
  return dlt.resource([credentials], name="credentials")

# Pass native value
os.environ["CREDENTIALS"] = "email:mx:pwd"
assert list(zen_source())[0].email == "mx"

# Pass explicit native value
assert list(zen_source("secret:🔑:secret"))[0].api_secret == "secret"
# Pass explicit dict
assert list(zen_source(credentials={"email": "emx", "password": "pass"}))[0].email == "emx"
```

:::info
これは資格情報だけでなく、[すべての仕様](advanced.md#write-custom-specs)に適用されます。
:::

:::tip
共通クラスから派生した資格情報の結合を作成し、コード内でシームレスに処理する方法については、[完全な例](https://github.com/dlt-hub/dlt/blob/devel/tests/common/configuration/test_spec_union.py)を参照してください。
:::
