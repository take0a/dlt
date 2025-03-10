# クラウドストレージとファイルシステム

ファイルシステムの宛先は、**AWS S3**、**Google Cloud Storage**、**Azure Blob Storage** などのリモート ファイルシステムやクラウド ストレージ サービスにデータを格納します。その下層では、[fsspec](https://github.com/fsspec/filesystem_spec) を使用してファイル操作を抽象化します。その主な役割は、他の宛先のステージング領域として使用することですが、これを使用してデータ レイクをすばやく構築することもできます。

:::tip
データファイルのレイアウトに関する注意事項をお読みください。現在、フィードバックを受け付けています。Slack (ページ上部のアイコン) に参加して、最適なレイアウトを見つけるお手伝いをお願いします。
:::

## ファイルシステムと dlt をインストールする

ファイルシステムと依存関係を持つ dlt ライブラリをインストールする:

```sh
pip install "dlt[filesystem]"
```

これにより、`s3fs` パッケージと `botocore` パッケージがインストールされます。

:::caution

依存関係を個別にインストールすることもできます:

```sh
pip install dlt
pip install s3fs
```

そうすれば、pip はバックトラックで失敗しません。
:::

## dlt プロジェクトを初期化する

まず、新しい dlt プロジェクトを次のように初期化します:

```sh
dlt init chess filesystem
```

:::note
このコマンドは、チェスをソース、AWS S3 を宛先としてパイプラインを初期化します。
:::

## 宛先と資格情報を設定する

### AWS S3

上記のコマンドは、AWS S3バケットのサンプルの`secrets.toml`と要件ファイルを作成します。これらの依存関係は、次のコマンドを実行してインストールできます。:

```sh
pip install -r requirements.txt
```

秘密情報を含む dlt 認証情報ファイルを編集するには、次のようになっている`.dlt/secrets.toml`を開きます:

```toml
[destination.filesystem]
bucket_url = "s3://[your_bucket_name]" # replace with your bucket name,

[destination.filesystem.credentials]
aws_access_key_id = "please set me up!" # copy the access key here
aws_secret_access_key = "please set me up!" # copy the secret access key here
```

認証情報が `~/.aws/credentials` に保存されている場合は、上記の **[destination.filesystem.credentials]** セクションを削除するだけで、dlt はローカル認証情報の **default** プロファイルに戻ります。プロファイルを切り替える場合は、次のようにプロファイル名を渡します (ここでは `dlt-ci-user`):

```toml
[destination.filesystem.credentials]
profile_name="dlt-ci-user"
```

AWSリージョンを指定することもできます:

```toml
[destination.filesystem.credentials]
region_name="eu-central-1"
```

S3 バケットと、そのバケットにアクセスできるユーザーを作成する必要があります。dlt はバケットを自動的に作成しません。

1. S3 で「バケットの作成」をクリックし、バケットに適切な名前と権限を割り当てることで、AWS コンソールで S3 バケットを作成できます。
2. バケットが作成されると、バケットURLが取得されます。たとえば、バケット名が`dlt-ci-test-bucket`の場合、バケットURLは次のようになります:

   ```text
   s3://dlt-ci-test-bucket
   ```

3. S3 バケットへのアクセスに使用するユーザーに権限を付与するには、「IAM」>「ユーザー」に移動し、「権限の追加」をクリックします。
4. 以下に、上記で作成したバケットに dlt に必要な最小限の権限を付与するサンプル ポリシーを示します。このポリシーには、バケット内のファイルのリスト、オブジェクトの取得、配置、削除を行う権限が含まれています。**ポリシーのリソース セクションにバケット名を忘れずに入力してください。**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DltBucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:GetObjectAttributes",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::dlt-ci-test-bucket/*",
                "arn:aws:s3:::dlt-ci-test-bucket"
            ]
        }
    ]
}
```

5. ユーザーのアクセス キーとシークレット キーを取得するには、[IAM] > [ユーザー] に移動し、[セキュリティ認証情報] で [アクセス キーの作成] をクリックし、できれば [コマンド ライン インターフェイス] を選択してアクセス キーを作成します。
6. 「secrets.toml」で使用するために作成された「アクセスキー」と「シークレットアクセスキー」を取得します。

#### S3互換ストレージの使用

[MinIO](https://min.io/)、[Cloudflare R2](https://www.cloudflare.com/en-ca/developer-platform/r2/)、[Google Cloud Storage](https://cloud.google.com/storage/docs/interoperability) など、AWS S3 以外の S3 互換ストレージを使用する場合は、構成で `endpoint_url` を指定できます。これは、AWS 認証情報とともに設定する必要があります:

```toml
[destination.filesystem]
bucket_url = "s3://[your_bucket_name]" # replace with your bucket name,

[destination.filesystem.credentials]
aws_access_key_id = "please set me up!" # copy the access key here
aws_secret_access_key = "please set me up!" # copy the secret access key here
endpoint_url = "https://<account_id>.r2.cloudflarestorage.com" # copy your endpoint URL here
```

#### 構成を追加する

`fsspec` に追加の引数を渡すには、toml 設定で `kwargs` と `client_kwargs` を指定します。

```toml
[destination.filesystem.kwargs]
use_ssl=true
auto_mkdir=true

[destination.filesystem.client_kwargs]
verify="public.crt"
```

追加の引数を環境変数経由で渡すには、**文字列化された辞書** を使用します:
`DESTINATION__FILESYSTEM__KWARGS='{"use_ssl": true, "auto_mkdir": true}`


### Google storage

`pip install "dlt[gs]"` を実行すると、`gcfs` パッケージがインストールされます。
シークレット情報を含む `dlt` 認証情報ファイルを編集するには、`.dlt/secrets.toml` を開きます。
デフォルトでは AWS 認証情報が表示されます。
[BigQuery の宛先](bigquery.md) からわかる Google クラウド認証情報を使用します。

```toml
[destination.filesystem]
bucket_url = "gs://[your_bucket_name]" # replace with your bucket name,

[destination.filesystem.credentials]
project_id = "project_id" # please set me up!
private_key = "private_key" # please set me up!
client_email = "client_email" # please set me up!
```
:::note
BigQuery と同じ認証情報を共有できることに注意してください。`[destination.filesystem.credentials]` セクションを、両方の宛先に適用されるより具体的なものではない `[destination.credentials]` に置き換えます。
:::

環境内（つまり、クラウド関数上）にデフォルトの Google Cloud 認証情報がある場合は、上記の認証情報セクションを削除すると、`dlt` は利用可能なデフォルトにフォールバックします。

**Cloud Storage** 管理者を使用して新しいバケットを作成します。次に、**Storage Object Admin** ロールをサービス アカウントに割り当てます。

### Azure Blob Storage

`pip install "dlt[az]"` を実行すると、Azure Blob Storage とインターフェイスするための `adlfs` パッケージがインストールされます。

`.dlt/secrets.toml` の資格情報を編集すると、デフォルトで AWS 資格情報が表示されるので、それを Azure 資格情報に置き換えます。

#### サポートされているスキーム

`dlt` は両方の形式の BLOB ストレージ URL をサポートします:

```toml
[destination.filesystem]
bucket_url = "az://<container_name>/path" # replace with your container name and path
```

と

```toml
[destination.filesystem]
bucket_url = "abfss://<container_name>@<storage_account_name>.dfs.core.windows.net/path"
```

`az`、`abfss`、`azure`、`abfs` URL スキームを使用できます。

ストレージアカウントにカスタムホストを使用する必要がある場合は、以下のように設定できます:

```toml
[destination.filesystem.credentials]
# The storage account name is always required
azure_account_host = "<storage_account_name>.<host_base>"
```

ベースホストに `storage_account_name` を含めることを忘れないでください。つまり、`dlt_ci.blob.core.usgovcloudapi.net` です。
`dlt` は、変更なしでこのホストを使用して Azure BLOB ストレージに接続します:

2つの形式のAzure資格情報がサポートされています:

#### SAS トークン資格情報

ストレージアカウント名と SAS トークンまたはストレージアカウントキーを入力します。

```toml
[destination.filesystem.credentials]
# The storage account name is always required
azure_storage_account_name = "account_name" # please set me up!
# You can set either account_key or sas_token, only one is needed
azure_storage_account_key = "account_key" # please set me up!
azure_storage_sas_token = "sas_token" # please set me up!
```

マシンに正しい Azure 資格情報が設定されていれば (Azure CLI 経由など)、
`azure_storage_account_key` と `azure_storage_sas_token` の両方を省略でき、`dlt` は利用可能なデフォルトに戻ります。
`azure_storage_account_name` は環境から推測できないため、引き続き必要であることに注意してください。

#### サービスプリンシパルの資格情報

コンテナへのアクセスを許可されたサービス プリンシパルのクライアント ID、クライアントシークレット、テナント ID を指定します。

```toml
[destination.filesystem.credentials]
azure_storage_account_name = "account_name" # please set me up!
azure_client_id = "client_id" # please set me up!
azure_client_secret = "client_secret"
azure_tenant_id = "tenant_id" # please set me up!
```

:::caution
**同時 BLOB アップロード**
`dlt` は、アップロードされた単一の BLOB の同時接続数を 1 に制限します。デフォルトでは、使用する `adlfs` は BLOB を 4 MB のチャンクに分割して同時にアップロードするため、大量のロード パッケージではメモリがギガバイト単位で使用され、接続が数千に上ります。最大同時接続数は次のように増やすことができます:

```toml
[destination.filesystem.kwargs]
max_concurrency=3
```
:::

### ローカルファイルシステム

何らかの理由でこれらのファイルをローカル フォルダーに保存したい場合は、次のように `bucket_url` を設定します (シークレットは必要ないため、`config.toml` を自由に使用できます):

```toml
[destination.filesystem]
bucket_url = "file:///absolute/path"  # three / for an absolute path
```

:::tip
深くネストされたレイアウトを処理するには、ローカルファイルシステムの宛先の自動ディレクトリ作成を有効にすることを検討してください。これは、`secrets.toml` で `kwargs` を設定することで実行できます:

```toml
[destination.filesystem]
kwargs = '{"auto_mkdir": true}'
```

または環境変数を設定することで:

```sh
export DESTINATION__FILESYSTEM__KWARGS = '{"auto_mkdir": true/false}'
```
:::

`dlt` はネイティブのローカルファイルパスを正しく処理します。実際、`file://` スキーマの使用は、特に Windows ユーザーにとっては直感的ではない可能性があります。

```toml
[destination.unc_destination]
bucket_url = 'C:\a\b\c'
```

上記の例では、[バックスラッシュのエスケープ](https://github.com/toml-lang/toml/blob/main/toml.md#string)を必要としない**TOMLのリテラル文字列**を使用して `bucket_url` を指定しています。

```toml
[destination.unc_destination]
bucket_url = '\\localhost\c$\a\b\c'  # UNC equivalent of C:\a\b\c

[destination.posix_destination]
bucket_url = '/var/local/data'  # absolute POSIX style path

[destination.relative_destination]
bucket_url = '_storage/data'  # relative POSIX style path
```

上記の例では、いくつかの名前付きファイルシステムの宛先を定義しています。:
* **unc_destination**  は、ネイティブ形式の Windows UNC パスを示します。
* **posix_destination** は、ネイティブ POSIX (Linux/Mac) 絶対パスを示します。
* **relative_destination** は、ネイティブ POSIX (Linux/Mac) 相対パスを示します。この場合、ファイルシステムの保存先は $cwd/_storage/data パスにファイルを保存します。ここで、$cwd は現在の作業ディレクトリです。

`dlt` は Windows [file:// スキームを使用した UNC パス](https://en.wikipedia.org/wiki/File_URI_scheme) をサポートしています。これらは **host** を使用して指定することも、純粋に **path** コンポーネントとして指定することもできます。

```toml
[destination.unc_with_host]
bucket_url="file://localhost/c$/a/b/c"

[destination.unc_with_path]
bucket_url="file:////localhost/c$/a/b/c"
```

:::caution
Windows は最大 255 文字のパスをサポートします。255 文字を超えるパスにアクセスすると、`FileNotFound` 例外が表示されます。

この制限を克服するには、[拡張パス](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry) を使用できます。`dlt` は通常のパスと UNC 拡張パスの両方を認識します。

```toml
[destination.regular_extended]
bucket_url = '\\?\C:\a\b\c'

[destination.unc_extended]
bucket_url='\\?\UNC\localhost\c$\a\b\c'
```
:::

### SFTP

`pip install "dlt[sftp]"` を実行すると、`dlt` とともに `paramiko` パッケージがインストールされ、安全な SFTP 転送が可能になります。

`.dlt/secrets.toml` ファイルを編集して、SFTP 認証情報を設定します。デフォルトでは、ファイルには AWS 認証情報のプレースホルダーが含まれています。これらを SFTP 認証情報に置き換える必要があります。

以下はSFTP認証情報設定の可能なフィールドです:

```text
sftp_port             # The port for SFTP, defaults to 22 (standard for SSH/SFTP)
sftp_username         # Your SFTP username, defaults to None
sftp_password         # Your SFTP password (if using password-based auth), defaults to None
sftp_key_filename     # Path to your private key file for key-based authentication, defaults to None
sftp_key_passphrase   # Passphrase for your private key (if applicable), defaults to None
sftp_timeout          # Timeout for establishing a connection, defaults to None
sftp_banner_timeout   # Timeout for receiving the banner during authentication, defaults to None
sftp_auth_timeout     # Authentication timeout, defaults to None
sftp_channel_timeout  # Channel timeout for SFTP operations, defaults to None
sftp_allow_agent      # Use SSH agent for key management (if available), defaults to True
sftp_look_for_keys    # Search for SSH keys in the default SSH directory (~/.ssh/), defaults to True
sftp_compress         # Enable compression (can improve performance over slow networks), defaults to False
sftp_gss_auth         # Use GSS-API for authentication, defaults to False
sftp_gss_kex          # Use GSS-API for key exchange, defaults to False
sftp_gss_deleg_creds  # Delegate credentials with GSS-API, defaults to True
sftp_gss_host         # Host for GSS-API, defaults to None
sftp_gss_trust_dns    # Trust DNS for GSS-API, defaults to True
```

:::info
資格情報パラメータの詳細については: https://docs.paramiko.org/en/3.3/api/client.html#paramiko.client.SSHClient.connect
:::

### 認証方法

SFTP 認証は次の優先順位で試行されます:

1. **キーベースの認証**: 秘密鍵または対応する OpenSSH 公開証明書 (例: `id_rsa` および `id_rsa-cert.pub`) へのパスを含む `key_filename` を指定すると、これらが認証に使用されます。秘密鍵にパスフレーズが必要な場合は、`sftp_key_passphrase` で指定できます。秘密鍵のロック解除にパスフレーズが必要な場合、パスフレーズを指定してあると、そのパスフレーズを使用して鍵のロック解除が試行されます。

2. **SSHエージェントベースの認証**: `allow_agent=True` (デフォルト) の場合、Paramiko はローカル SSH エージェントに保存されている SSH キー (`~/.ssh/` に保存されている `id_rsa`、`id_dsa`、または `id_ecdsa` キーなど) を検索します。

3. **ユーザー名/パスワード認証**: パスワードが指定されている場合 (`sftp_password`)、単純なユーザー名/パスワード認証が試行されます。

4. **GSS-API認証**: GSS-API (Kerberos) が有効になっている場合 (`sftp_gss_auth=True`)、認証には Kerberos プロトコルが使用されます。GSS-API は、キー交換 (`sftp_gss_kex=True`) および資格情報の委任 (`sftp_gss_deleg_creds=True`) にも使用できます。この方法は、Kerberos が設定されている環境 (多くの場合、エンタープライズ ネットワーク) で役立ちます。


#### 1. キーベースの認証

パスワードの代わりに SSH キーを使用する場合は、設定で秘密キーへのパスを指定できます。

```toml
[destination.filesystem]
bucket_url = "sftp://[hostname]/[path]"
file_glob = "*"

[destination.filesystem.credentials]
sftp_username = "foo"
sftp_key_filename = "/path/to/id_rsa"     # Replace with the path to your private key file
sftp_key_passphrase = "your_passphrase"   # Optional: passphrase for your private key
```

#### 2. SSHエージェントベースの認証

読み込まれたキーを使用して SSH エージェントを実行している場合は、Paramiko がこれらのキーを自動的に使用できるようにします。SSH エージェントに依存している場合は、パスワードとキーのフィールドを省略できます。

```toml
[destination.filesystem]
bucket_url = "sftp://[hostname]/[path]"
file_glob = "*"

[destination.filesystem.credentials]
sftp_username = "foo"
sftp_key_passphrase = "your_passphrase"   # Optional: passphrase for your private key
```

ロードされたキーは、~/.ssh/ に保存されている id_rsa、id_dsa、または id_ecdsa のいずれかのタイプである必要があります。

#### 3. ユーザー名/パスワード認証

これは最も単純な認証形式で、ユーザー名とパスワードを直接入力します。

```toml
[destination.filesystem]
bucket_url = "sftp://[hostname]/[path]"  # The hostname of your SFTP server and the remote path
file_glob = "*"                          # Pattern to match the files you want to upload/download

[destination.filesystem.credentials]
sftp_username = "foo"                    # Replace "foo" with your SFTP username
sftp_password = "pass"                   # Replace "pass" with your SFTP password
```


### Notes:
- **キーベースの認証**: 秘密鍵に正しい権限 (`chmod 600`) があることを確認してください。そうでないと、SSH は秘密鍵の使用を拒否します。
- **タイムアウト**: 接続の問題を回避するには、ネットワークの状態に基づいてタイムアウト値を調整することが重要です。

この構成により、パスワード、キー、エージェントのいずれを使用していても柔軟な SFTP 認証が可能になり、ローカル環境と SFTP サーバー間の安全な通信が保証されます。

## 書き込み処理
ファイルシステムの宛先は書き込み処理を次のように処理します。:
- `append` - このようなテーブルに属するファイルはデータセットフォルダに追加されます
- `replace` - そのようなテーブルに属するすべてのファイルはデータセット フォルダーから削除され、現在のファイル セットが追加されます。
- `merge` - `append` にフォールバックする

## ファイル圧縮

dlt ライブラリのファイルシステムの保存先では、効率性を高めるためにデフォルトで `gzip` 圧縮が使用されるため、ファイルが圧縮形式で保存される可能性があります。この形式は、プレーンテキストや JSON ライン (`jsonl`) ファイルとして簡単に読み取れない可能性があります。読み取れないように見えるファイルが見つかった場合は、圧縮されている可能性があります。

圧縮ファイルを扱うには:

- 圧縮を無効にするには、「config.toml」ファイルの `data_writer.disable_compression` 設定を変更します。これは、ファイルを解凍せずに直接ファイルにアクセスしたい場合に便利です。たとえば、:

```toml
[normalize.data_writer]
disable_compression=true
```

- `gzip` ファイルを解凍するには、`gunzip` などのツールを使用できます。これにより、圧縮されたファイルが元の形式に戻され、読み取り可能になります。

ファイル圧縮の管理の詳細については、パフォーマンスの最適化に関するドキュメントをご覧ください: [ファイル圧縮の無効化と有効化](../../reference/performance#disabling-and-enabling-file-compression)。

## ファイルのレイアウト

すべてのファイルは、`pipeline` の `run` または `load` メソッドに渡したデータセットの名前を持つ単一のフォルダーに保存されます。この例のチェス パイプラインでは、**chess_players_games_data** です。

:::note
オブジェクト ストレージは、実際にはキー BLOB ストレージであるため、ファイル名を区切り文字 (`/`) でコンポーネントに分割することでフォルダー構造をエミュレートします。
:::

必要な構成を指定して、ファイルのレイアウトを制御できます。これを行うにはいくつかの方法があります。

### デフォルトのレイアウト

現在のデフォルトレイアウト: `{table_name}/{load_id}.{file_id}.{ext}`

:::note
dlt 0.3.12 では、デフォルトのレイアウト形式が `{schema_name}.{table_name}.{load_id}.{file_id}.{ext}` から `{table_name}/{load_id}.{file_id}.{ext}` に変更されました。手動で設定することで、古いレイアウトに戻すことができます。
:::

### 利用可能なレイアウトプレースホルダー

#### 標準プレースホルダー

* `schema_name` - [スキーマ](../../general-usage/schema.md) の名前
* `table_name` - テーブル名
* `load_id` - ファイルの取得元の[ロードパッケージ](../../general-usage/destination-tables.md#load-packages-and-load-ids)のID
* `file_id` - ファイルのID。1つのテーブルにデータを含むファイルが多数ある場合、それらは異なるファイルIDでコピーされます。
* `ext` - ファイルの形式、つまり `jsonl` または `parquet`

#### 日付と時刻のプレースホルダー

:::tip
すべての値は小文字であることに注意してください。
:::

* `timestamp` - Unix タイムスタンプ形式の現在のタイムスタンプ（秒単位）
* `timestamp_ms` - Unix タイムスタンプ形式の現在のタイムスタンプ（ミリ秒単位）
* `load_package_timestamp` - [ロードパッケージ](../../general-usage/destination-tables.md#load-packages-and-load-ids) からのタイムスタンプ (秒単位に丸められた Unix タイムスタンプ形式)
* `load_package_timestamp_ms` - [ロードパッケージ](../../general-usage/destination-tables.md#load-packages-and-load-ids) からのタイムスタンプ (ミリ秒単位の Unix タイムスタンプ形式)

:::note
`timestamp_ms` と `load_package_timestamp_ms` はどちらもミリ秒単位（例: 12334455233）であり、小数点なしのミリ秒精度を保証するために小数秒ではありません。
:::

* Years
  * `YYYY` - 2024, 2025
  * `Y` - 2024, 2025
* Months
  * `MMMM` - January, February, March
  * `MMM` - Jan, Feb, Mar
  * `MM` - 01, 02, 03
  * `M` - 1, 2, 3
* Days of the month
  * `DD` - 01, 02
  * `D` - 1, 2
* Hours 24h format
  * `HH` - 00, 01, 02...23
  * `H` - 0, 1, 2...23
* Minutes
  * `mm` - 00, 01, 02...59
  * `m` - 0, 1, 2...59
* Seconds
  * `ss` - 00, 01, 02...59
  * `s` - 0, 1, 2...59
* Fractional seconds
  * `SSSS` - 000[0..] 001[0..] ... 998[0..] 999[0..]
  * `SSS` - 000 001 ... 998 999
  * `SS` - 00, 01, 02 ... 98, 99
  * `S` - 0 1 ... 8 9
* Days of the week
  * `dddd` - Monday, Tuesday, Wednesday
  * `ddd` - Mon, Tue, Wed
  * `dd` - Mo, Tu, We
  * `d` - 0-6
* `Q` - quarters 1, 2, 3, 4

次のようにファイルシステムの宛先のレイアウト設定を指定することで、ファイル名の形式を変更できます。:

```toml
[destination.filesystem]
layout="{table_name}/{load_id}.{file_id}.{ext}" # current preconfigured naming scheme

# More examples
# With timestamp
# layout = "{table_name}/{timestamp}/{load_id}.{file_id}.{ext}"

# With timestamp of the load package
# layout = "{table_name}/{load_package_timestamp}/{load_id}.{file_id}.{ext}"

# Parquet-like layout (note: it is not compatible with the internal datetime of the parquet file)
# layout = "{table_name}/year={YYYY}/month={MM}/day={DD}/{load_id}.{file_id}.{ext}"

# Custom placeholders
# extra_placeholders = { "owner" = "admin", "department" = "finance" }
# layout = "{table_name}/{owner}/{department}/{load_id}.{file_id}.{ext}"
```

ファイル名のレイアウトを指定する際に知っておくべきいくつかのこと:

- すべてのファイル名に共通する別のベースパスが必要な場合は、`layout` 設定のプレフィックスではなく、`bucket_url` のサフィックスを付けることができます。
- `{ext}` プレースホルダーを指定しない場合は、区切り文字としてドットが付いたプレースホルダーがレイアウトの最後に自動的に追加されます。
- 各プレースホルダーの間に区切り文字を入れるのがベストプラクティスです。区切り文字にはファイル名の文字として許可されている任意の文字を使用できますが、ドット、ダッシュ、スラッシュが最も一般的です。
- `replace` 処理を使用する場合、`dlt` は新しいデータをロードする前に削除する正しいファイルを判断できなければなりません。これを機能させるには、:
  - レイアウトに `{table_name}` プレースホルダーを含める
  - table_name プレースホルダの前に `{schema_name}` プレースホルダ以外のプレースホルダがないこと
  - table_nameプレースホルダーの後に区切り文字を入れる

ご注意ください:
- `dlt` は、`_dlt_loads` テーブルに対応する `./_dlt_loads` フォルダーに json ファイルを作成して、ロードが完了したことをマークします。たとえば、loads フォルダーに `chess__1685299832.jsonl` ファイルが存在する場合、ロード パッケージ `1685299832` のすべてのファイルが完全にロードされていることを確認できます。

### 高度なレイアウト構成

ファイルシステムの宛先構成は、高度なレイアウトのカスタマイズと追加のプレースホルダーの組み込みをサポートしています。これは、`config.toml` を通じて、またはファクトリ メソッドを介して初期化するときにプログラムによって実行できます。

#### `config.toml` による構成

`config.toml`を使用してレイアウトとプレースホルダーを設定するには、次の形式を使用します。:

```toml
[destination.filesystem]
layout = "{table_name}/{test_placeholder}/{YYYY}-{MM}-{DD}/{ddd}/{mm}/{load_id}.{file_id}.{ext}"
extra_placeholders = { "test_placeholder" = "test_value" }
current_datetime="2024-04-14T00:00:00"
# for automatic directory creation in the local filesystem
kwargs = '{"auto_mkdir": true}'
```

:::note
プレースホルダー名が意図された使用法と一致していることを確認します。たとえば、一貫性を保つために、`{test_placeholer}` は `{test_placeholder}` に修正する必要があります。
:::

#### コード内の動的構成

レイアウトやプレースホルダーなどの構成オプションは、ファイルシステムの宛先を初期化してパイプラインに直接渡すときに動的にオーバーライドできます。

```py
import pendulum

import dlt
from dlt.destinations import filesystem

pipeline = dlt.pipeline(
    pipeline_name="data_things",
    destination=filesystem(
        layout="{table_name}/{test_placeholder}/{timestamp}/{load_id}.{file_id}.{ext}",
        current_datetime=pendulum.now(),
        extra_placeholders={
            "test_placeholder": "test_value",
        }
    )
)
```

さらに:

1. 追加のプレースホルダー機能のためにコールバックを使用して動作をカスタマイズします。各コールバックは次の位置引数を受け入れ、文字列を返す必要があります。
2. `current_datetime` をカスタマイズします。これはコールバック関数でもあり、`pendulum.DateTime` インスタンスを返すことが期待されます。

```py
import pendulum

import dlt
from dlt.destinations import filesystem

def placeholder_callback(schema_name: str, table_name: str, load_id: str, file_id: str, ext: str) -> str:
    # Custom logic here
    return "custom_value"

def get_current_datetime() -> pendulum.DateTime:
    return pendulum.now()

pipeline = dlt.pipeline(
    pipeline_name="data_things",
    destination=filesystem(
        layout="{table_name}/{placeholder_x}/{timestamp}/{load_id}.{file_id}.{ext}",
        current_datetime=get_current_datetime,
        extra_placeholders={
            "placeholder_x": placeholder_callback
        }
    )
)
```

### 推奨レイアウト

現在推奨されているレイアウト構造は単純な:

```toml
layout="{table_name}/{load_id}.{file_id}.{ext}"
```

このレイアウトを採用するといくつかの利点がある:

1. **Efficiency:** 処理は高速かつ簡単です。
2. **Compatibility:** 書き込み処理方法として `replace` をサポートします。
3. **Flexibility:** Athena を含むさまざまな宛先と互換性があります。
4. **Performance:** 深くネストされた構造はファイルナビゲーションを遅くする可能性がありますが、よりシンプルなレイアウトはこの問題を軽減します。

## サポートされているファイル形式

以下のファイル形式を選択できます:

* [JSONL](../file-formats/jsonl.md) is used by default
* [Parquet](../file-formats/parquet.md) is supported
* [CSV](../file-formats/csv.md) is supported

## サポートされている表形式

以下の[表形式](./delta-iceberg.md)を選択できます:

* Delta table
* Iceberg

## dlt の状態の同期

この宛先は、[dlt の状態の同期](../../general-usage/state#syncing-state-with-destination) を完全にサポートします。このため、パイプラインの状態、スキーマ、完了したロードに関する情報を保持する特別なフォルダーとファイルが宛先に作成されます。これらのフォルダーは、レイアウト セクションの設定を尊重しません。ファイルシステムをステージングの宛先として使用する場合、状態とスキーマは構成した最終宛先によって通常の方法で管理されるため、これらのフォルダーがすべて作成されるわけではありません。

また、ルート フォルダーと特別な `dlt` フォルダーに `init` ファイルがあることにも気づくでしょう。BLOB ストレージとディレクトリにはスキーマとテーブルの概念がないため、`dlt` はこれらの特別なファイルを使用して、`filesystem` 宛先の動作を他の実装された宛先と調和させます。

:::note
インクリメンタルロードを使用する場合など、ロードによって新しい状態が生成されると、宛先の `_dlt_pipeline_state` フォルダーに新しい状態ファイルが作成されます。データの蓄積を防ぐために、状態クリーンアップ メカニズムによって古い状態ファイルが自動的に削除され、デフォルトでは最新の 100 個のみが保持されます。このクリーンアップ プロセスは、保持するパイプライン状態ファイルの最大数 (デフォルトは 100) を決定するファイル システム構成 `max_state_files` を使用してカスタマイズまたは無効にできます。この値を 0 または負の数に設定すると、古い状態のクリーンアップが無効になります。
:::

## トラブルシューティング

### ファイル名が長すぎるエラー

パイプラインを実行すると、`[Errno 36] ファイル名が長すぎますエラー` のようなエラーが発生する場合があります。このエラーは、生成されたファイル名がファイルシステムで許可されている最大長を超えているために発生します。

ファイル名の長さエラーを防ぐには、宛先に `max_identifier_length` パラメータを設定します。これにより、すべての識別子 (ファイル名を含む) が指定された最大長に切り捨てられます。
たとえば:

```py
from dlt.destinations import duckdb as duckdb_destination

pipeline = dlt.pipeline(
    pipeline_name="your_pipeline_name",
    destination=duckdb_destination(
        max_identifier_length=200,  # Adjust the length as needed
    ),
)
```

:::note
- `max_identifier_length` はすべての識別子 (テーブル、列) を切り捨てます。衝突を避けるために、長さが一意性を維持するようにしてください。
- データ構造とファイルシステムの制限に基づいて `max_identifier_length` を調整します。
:::

<!--@@@DLT_TUBA filesystem-->
