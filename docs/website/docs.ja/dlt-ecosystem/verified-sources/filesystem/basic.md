---
title: ファイルシステムソース
description: Learn how to set up and configure
keywords: [readers source and filesystem, files, filesystem, readers source, cloud storage, object storage, local file system]
---
import Header from '../_source-info-header.md';
<Header/>

ファイルシステムソースを使用すると、リモートの場所 (AWS S3、Google Cloud Storage、Google Drive、Azure Blob Storage、SFTP サーバー) またはローカルファイルシステムからファイルをシームレスに読み込むことができます。ファイルシステムソースは、[CSV](../../file-formats/csv.md)、[Parquet](../../file-formats/parquet.md)、[JSONL](../../file-formats/jsonl.md) ファイルをネイティブにサポートし、あらゆる種類の構造化ファイルを読み込むためのカスタマイズが可能です。

非構造化データ (PDF、プレーンテキスト、電子メール) を読み込むには、[非構造化データソース](https://github.com/dlt-hub/verified-sources/tree/master/sources/unstructured_data)を参照してください。

## ファイルシステムソースはどのように動くのか

ファイルシステムソースは、リモートファイルとローカルファイルの両方からデータを簡単にロードできるだけでなく、特定のニーズに合わせてロードプロセスをカスタマイズできる強力なツールセットも備えています。

ファイルシステム ソースは、次の 2 つの手順でデータを読み込みます:

1. 実際にコンテンツを読み取ることなく、リモートまたはローカルのファイルストレージ内の[ファイルにアクセスします](#1-initialize-a-filesystem-resource)。この時点で、[メタデータまたは名前でファイルをフィルター](#6-filter-files)できます。また、[インクリメンタルローディング](#5-incremental-loading)を設定して、新しいファイルのみを読み込むこともできます。
2. [トランスフォーマー](#2-choose-the-right-transformer-resource)はファイルの内容を読み取り、レコードを生成します。このステップでは、実際のデータをフィルター処理したり、ファイルのメタデータを使用してレコードを充実させたり、ファイルの内容に基づいて[インクリメンタルローディングを実行](#load-new-records-based-on-a-specific-column)したりできます。

## 簡単な例

```py
import dlt
from dlt.sources.filesystem import filesystem, read_parquet

filesystem_resource = filesystem(
  bucket_url="file://Users/admin/Documents/parquet_files",
  file_glob="**/*.parquet"
)
filesystem_pipe = filesystem_resource | read_parquet()
filesystem_pipe.apply_hints(incremental=dlt.sources.incremental("modification_date"))

# We load the data into the table_name table
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe.with_name("table_name"))
print(load_info)
print(pipeline.last_trace.last_normalize_info)
```

## セットアップ

### 前提条件

`dlt` ライブラリがインストールされていることを確認してください。[インストールガイド](../../../intro)を参照してください。

### ファイルシステムソースの初期化

データ パイプラインを開始するには、次の手順に従います:

1. 次のコマンドを入力します:

   ```sh
   dlt init filesystem duckdb
   ```

   [dlt init コマンド](../../../reference/command-line-interface)は、ファイルシステムをソースとして、[duckdb](../../destinations/duckdb.md) を宛先として[パイプラインの例](https://github.com/dlt-hub/verified-sources/blob/master/sources/filesystem_pipeline.py)を初期化します。

2. 別の宛先を使用する場合は、希望する[宛先](../../destinations)の名前で、`duckdb` を置き換えてください。

3. このコマンドを実行すると、開始するために必要なファイルと構成設定を含む新しいディレクトリが作成されます。

## 構成

### 資格情報の取得

<Tabs
  groupId="filesystem-type"
  defaultValue="aws"
  values={[
    {"label": "AWS S3", "value": "aws"},
    {"label": "GCS/GDrive", "value": "gcp"},
    {"label": "Azure", "value": "azure"},
    {"label": "SFTP", "value": "sftp"},
    {"label": "Local filesystem", "value": "local"},
]}>

<TabItem value="aws">

S3 アクセス用の AWS キーを取得するには:

1. AWS コンソールで IAM にアクセスします。
2. 「ユーザー」メニューから、ユーザーを選択して、「セキュリティ資格情報」を開きます。
3. 「アクセスキーの作成」をクリックして、AWS ID とシークレットキーを取得します。

詳細については、[AWS 公式ドキュメント](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)を参照してください。

</TabItem>

<TabItem value="gcp">

GCS/GDrive にアクセスするには:

1. [console.cloud.google.com](http://console.cloud.google.com/) にログインします。
2. [service account](https://cloud.google.com/iam/docs/service-accounts-create#creating)を作成します。
3. 「Cloud Storage API」/「Google Drive API」を有効にします。
   [Google のガイド](https://support.google.com/googleapi/answer/6158841?hl=en)を参照してください。
4. 「IAM と管理」>「サービス アカウント」でアカウントを見つけ、3 つのドットのメニュー >「キーの管理」>「キーの追加」>「作成」をクリックして、JSON 認証情報ファイルを取得します。
5. サービスアカウントにクラウドストレージアクセスの適切な権限を付与します。

詳細については、[サービスアカウントの作成](https://support.google.com/a/answer/7378726?hl=en)方法をご覧ください。

</TabItem>

<TabItem value="azure">

Azure BLOB ストレージにアクセスするには:

1. Azure ポータル (portal.azure.com) にアクセスします。
2. 「ストレージ アカウント」 > ストレージを選択します。
3. 「設定」>「アクセスキー」をクリックします。
4. アカウント名と 2 つのキー (プライマリ/セカンダリ) を表示します。キーは秘密にしておいてください。

詳細については、[Azure の公式ドキュメント](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-keys-manage?tabs=azure-portal)を参照してください。

</TabItem>

<TabItem value="sftp">

dlt はいくつかの認証方法をサポートしています:

1. キーベースの認証
2. SSH エージェントベースの認証
3. ユーザー名/パスワード認証
4. GSS-API 認証

SFTP 認証オプションの詳細については、[SFTP のセクション](../../destinations/filesystem#sftp)を参照してください。資格情報を取得するには、サーバー管理者に問い合わせてください。
</TabItem>

<TabItem value="local">
ローカルファイルシステムの資格情報は必要ありません。
</TabItem>

</Tabs>

### dlt パイプラインに資格情報を追加する

ファイルシステムソースに資格情報を提供するには、 dlt で[可能な任意の方法](../../../general-usage/credentials/setup#available-config-providers) を使用できます。
最も簡単な方法の 1 つは、構成ファイルを使用することです。作業ディレクトリの `.dlt` フォルダーには、`config.toml` と `secrets.toml` の2 つのファイルが含まれています。パスワードやアクセストークンなどの機密情報は `secrets.toml` にのみ入れる必要がありますが、バケットへのパスなどのその他の構成は `config.toml` に指定できます。

<Tabs
  groupId="filesystem-type"
  defaultValue="aws"
  values={[
    {"label": "AWS S3", "value": "aws"},
    {"label": "GCS/GDrive", "value": "gcp"},
    {"label": "Azure", "value": "azure"},
    {"label": "SFTP", "value": "sftp"},
    {"label": "Local filesystem", "value": "local"},
]}>

<TabItem value="aws">

```toml
# secrets.toml
[sources.filesystem.credentials]
aws_access_key_id="Please set me up!"
aws_secret_access_key="Please set me up!"

# config.toml
[sources.filesystem]
bucket_url="s3://<bucket_name>/<path_to_files>/"
```
</TabItem>

<TabItem value="azure">

```toml
# secrets.toml
[sources.filesystem.credentials]
azure_storage_account_name="Please set me up!"
azure_storage_account_key="Please set me up!"

# config.toml
[sources.filesystem] # use [sources.readers.credentials] for the "readers" source
bucket_url="az://<container_name>/<path_to_files>/"
```
</TabItem>

<TabItem value="gcp">

```toml
# secrets.toml
[sources.filesystem.credentials]
client_email="Please set me up!"
private_key="Please set me up!"
project_id="Please set me up!"

# config.toml
# gdrive
[gdrive_pipeline_name.sources.filesystem]
bucket_url="gdrive://<folder_name>/<subfolder_or_file_path>/"

# config.toml
# Google storage
[gstorage_pipeline_name.sources.filesystem]
bucket_url="gs://<bucket_name>/<path_to_files>/"
```
</TabItem>

<TabItem value="sftp">

[SFTP のセクション](../../destinations/filesystem#sftp)で、各認証方法の SFTP 資格情報を設定する方法を学びます。たとえば、キーベースの認証の場合は、次のようにソースを構成できます:

```toml
# secrets.toml
[sources.filesystem.credentials]
sftp_username = "foo"
sftp_key_filename = "/path/to/id_rsa"     # Replace with the path to your private key file
sftp_key_passphrase = "your_passphrase"   # Optional: passphrase for your private key

# config.toml
[sources.filesystem] # use [sources.readers.credentials] for the "readers" source
bucket_url = "sftp://[hostname]/[path]"
```
</TabItem>

<TabItem value="local">

ネイティブのローカルファイルシステムパスと `file://` URI の両方を使用できます。絶対パス、相対パス、および UNC Windows パスがサポートされています。

絶対ファイルパスを指定することもできます:

```toml
# config.toml
[sources.filesystem]
bucket_url='file://Users/admin/Documents/csv_files'
```

または、スキーマをスキップして、オペレーティングシステムに固有の形式でローカルパスを指定します。たとえば、Windows の場合:

```toml
[sources.filesystem]
bucket_url='~\Documents\csv_files\'
```

</TabItem>

</Tabs>

環境変数を使用して資格情報を指定することもできます。対応する環境変数の名前は、TOML ファイル内の対応する名前とは少し異なります。ドット `.` を二重アンダースコア `__` に置き換えるだけです:

```sh
export SOURCES__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID = "Please set me up!"
export SOURCES__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY = "Please set me up!"
```

:::tip
dlt は、ID ベースやデフォルトの認証情報など、クラウドストレージを使用した認証のさまざまな方法をサポートしています。パイプラインに認証情報を追加する方法の詳細については、[構成とシークレットのセクション](../../../general-usage/credentials/complex_types#gcp-credentials)
:::

## 使用方法

ファイルシステムソースは、ファイルからデータをロードするための構成要素を提供するという点で非常にユニークです。まず、ストレージ内のファイルを反復処理し、各ファイルを処理してレコードを生成します。通常、次の 2 つのリソースが必要です:

1. `filesystem` リソースは、glob パターンを使用して選択したバケット内のファイルを列挙し、カスタマイズ可能なページサイズなどの詳細を `FileItem` として返します。
2. 特定の変換関数で各ファイルを処理し、レコードを生成するために使用できるトランスフォーマー リソースの 1 つ。

### 1. `filesystem` リソースを初期化する

:::note
`filesystem` リソースだけの使用で、glob パラメータに基づいてストレージ内のファイルがリストされ、ファイルの[メタデータ](advanced#fileitem-fields)が生成されます。`filesystem` リソース自体はファイルを読み取ったりコピーしたりしません。
:::

リソースのすべてのパラメータはコード内で直接指定できます:

```py
from dlt.sources.filesystem import filesystem

filesystem_source = filesystem(
  bucket_url="file://Users/admin/Documents/csv_files",
  file_glob="*.csv"
)
```

または設定から​​取得して:

* python コード:

  ```py
  from dlt.sources.filesystem import filesystem

  filesystem_source = filesystem()
  ```

* 設定ファイル:
  ```toml
  [sources.filesystem]
  bucket_url="file://Users/admin/Documents/csv_files"
  file_glob="*.csv"
  ```

`filesystem` リソースの全パラメータのリスト:

* `bucket_url` - バケットの完全な URL (ローカル ファイル システムの場合は相対パスになる場合があります)。
* `credentials` - `AbstractFilesystem` インスタンスのクラウドストレージ資格情報(ローカルファイルシステムの場合は空にする必要があります)。このパラメーターをコード内で指定するのではなく、シークレットファイルに配置することをお勧めします。
* `file_glob` -  glob 形式のファイルフィルター。デフォルトでは、バケット URL 内のすべての非再帰ファイルがリストされます。
* `files_per_page` - 一度に処理されるファイルの数。デフォルト値は `100` です。
* `extract_content` - true の場合、ファイルの内容が読み取られ、リソースに返されます。デフォルト値は `False` です。

### 2. 適切なトランスフォーマーリソースの選択

ファイルシステムソースの現在の実装では、CSV、Parquet、JSONL の 3 つのファイルタイプがネイティブにサポートされています。上記のいずれかを適用するか、[独自のトランスフォーマーを作成する](advanced#create-your-own-transformer)ことができます。選択したトランスフォーマー リソースを適用するには、パイプ表記 `|` を使用します:

```py
from dlt.sources.filesystem import filesystem, read_csv

filesystem_pipe = filesystem(
  bucket_url="file://Users/admin/Documents/csv_files",
  file_glob="*.csv"
) | read_csv()
```

#### 利用可能なトランスフォーマー

- `read_csv()` - [Pandas](https://pandas.pydata.org/) を使用して CSV ファイルを処理します。
- `read_jsonl()` - JSONL ファイルをチャンクごとに処理します。
- `read_parquet()` - [PyArrow](https://arrow.apache.org/docs/python/)を使用して Parquet ファイルを処理します。
- `read_csv_duckdb()` - このトランスフォーマーは、通常 pandas よりも優れたパフォーマンスを発揮する DuckDB を使用して CSV ファイルを処理します。

:::tip
`pipeline.run` でロードする前に、各リソースに[特定の名前](../../../general-usage/resource#duplicate-and-rename-resources)を付けることをお勧めします。これにより、データが希望の名前のテーブルに送信され、各パイプラインが[インクリメンタルロードに個別の状態](../../../general-usage/state#read-and-write-pipeline-state-in-a-resource)を使用するようになります。
:::

### 3. パイプラインの作成と実行

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

filesystem_pipe = filesystem(bucket_url="file://Users/admin/Documents/csv_files", file_glob="*.csv") | read_csv()
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
info = pipeline.run(filesystem_pipe)
print(info)
```

パイプラインを作成して実行する方法の詳細については、[ウォークスルー:パイプラインを実行する](../../../walkthroughs/run-a-pipeline)を参照してください。

### 4. ヒントの適用

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

filesystem_pipe = filesystem(bucket_url="file://Users/admin/Documents/csv_files", file_glob="*.csv") | read_csv()
# Tell dlt to merge on date
filesystem_pipe.apply_hints(write_disposition="merge", merge_key="date")

# We load the data into the table_name table
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe.with_name("table_name"))
print(load_info)
```

### 5. インクリメンタルローディング

データを段階的にロードする簡単な方法をいくつか紹介します:

1. [変更日に基づいてファイルをロードします](#load-files-based-on-modification-date)。最後に `dlt` 処理されてから更新されたファイルのみをロードします。`dlt` は、ファイルのメタデータ (変更日など) をチェックし、変更されていないファイルをスキップします。
2. [特定の列に基づいて新しいレコードをロードします](#load-new-records-based-on-a-specific-column)。 `updated_at` などの特定の列を調べることで、新しいレコードまたは更新されたレコードのみをロードできます。 最初の方法とは異なり、このアプローチでは毎回すべてのファイルを読み取り、更新されたレコードをフィルター処理します。
3. [更新されたファイルと更新されたレコードのみの読み込みを組み合わせます](#combine-loading-only-updated-files-and-records)。最後に、両方の方法を組み合わせることができます。既存のファイルに新しいレコードを追加できる場合は便利なので、変更されたファイルだけでなく、変更されたレコードもフィルターする必要があります。

#### 変更日に基づくファイルのロード

For example, to load only new CSV files with 例えば、[インクリメンタルローディング](../../../general-usage/incremental-loading)で新しい CSV ファイルだけをロードするには、`apply_hints` メソッドが使用できます。

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

# This configuration will only consider new CSV files
new_files = filesystem(bucket_url="s3://bucket_name", file_glob="directory/*.csv")
# Add incremental on modification time
new_files.apply_hints(incremental=dlt.sources.incremental("modification_date"))

pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run((new_files | read_csv()).with_name("csv_files"))
print(load_info)
```

#### 特定カラムに戻づく新しいレコードのロード

この例では、`update_at` というフィールドに基づいて新しいレコードのみをロードします。この方法は、たとえば、新しいレコードが表示されるたびにすべてのファイルが変更されるため、変更日でファイルをフィルタリングできない場合に役立ちます。

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

# We consider all CSV files
all_files = filesystem(bucket_url="s3://bucket_name", file_glob="directory/*.csv")

# But filter out only updated records
filesystem_pipe = (all_files | read_csv())
filesystem_pipe.apply_hints(incremental=dlt.sources.incremental("updated_at"))
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe)
print(load_info)
```

#### 更新されたファイルの更新されたレコードだけを組み合わせたロード

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

# This configuration will only consider modified CSV files
new_files = filesystem(bucket_url="s3://bucket_name", file_glob="directory/*.csv")
new_files.apply_hints(incremental=dlt.sources.incremental("modification_date"))

# And in each modified file, we filter out only updated records
filesystem_pipe = (new_files | read_csv())
filesystem_pipe.apply_hints(incremental=dlt.sources.incremental("updated_at"))
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe)
print(load_info)
```

### 6. ファイルをフィルタする

メタデータに基づいてファイルをフィルタリングする必要がある場合は、`add_filter` メソッドを使用して簡単に行うことができます。フィルタリング関数内では、`FileItem` 表現の[任意のフィールド](advanced#fileitem-fields)にアクセスできます。

#### 名前でフィルタリング

名前に `London` と `Berlin` が含まれるファイルのみをフィルタリングするには、次のようにします:

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

# Filter files accessing file_name field
filtered_files = filesystem(bucket_url="s3://bucket_name", file_glob="directory/*.csv")
filtered_files.add_filter(lambda item: ("London" in item["file_name"]) or ("Berlin" in item["file_name"]))

filesystem_pipe = (filtered_files | read_csv())
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe)
print(load_info)
```

:::tip
`file_glob` を使ってファイル名でフィルタリングすることもできます。拡張子でフィルタリングするなど、単純なケースでは非常にうまく機能します:

```py
from dlt.sources.filesystem import filesystem

filtered_files = filesystem(bucket_url="s3://bucket_name", file_glob="**/*.json")
```
:::

#### サイズでフィルタリング

何らかの理由で小さなファイルだけをロードしたい場合は、それも可能です:

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

MAX_SIZE_IN_BYTES = 10

# Filter files accessing size_in_bytes field
filtered_files = filesystem(bucket_url="s3://bucket_name", file_glob="directory/*.csv")
filtered_files.add_filter(lambda item: item["size_in_bytes"] < MAX_SIZE_IN_BYTES)

filesystem_pipe = (filtered_files | read_csv())
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(filesystem_pipe)
print(load_info)
```

## トラブルシューティング

### 非常に長いファイルパスにアクセスする

Windows は最大 255 文字のパスをサポートします。255 文字を超えるパスにアクセスすると、`FileNotFound` 例外が表示されます。

この制限を超えるには、[拡張パス](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry)を使用できます。
**Python glob は拡張 UNC パスでは動作しない** ので、使用できないことに注意してください。

```toml
[sources.filesystem]
bucket_url = '\\?\C:\a\b\c'
```

### 空のファイルリストが得られた場合

ファイルシステム ソースを使用して dlt パイプラインを実行していて、レコードがゼロの場合、`bucket_url` および `file_glob` パラメータの構成を確認することをお勧めします。

たとえば、Azure Blob Storage では、アカウント名をコンテナー名と間違えることがあります。URL が `"az://<コンテナー名>/"` として設定されていることを確認してください。

また、リソースを正しく構成するには、[glob](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.glob) 関数を参照してください。再帰ファイルを含めるには `**` を使用します。ローカルファイルシステムは完全な Python [glob](https://docs.python.org/3/library/glob.html#glob.glob) 機能をサポートしていますが、クラウドストレージは制限された `fsspec` [version](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.glob) のサポートになります。

<!--@@@DLT_TUBA filesystem-->

