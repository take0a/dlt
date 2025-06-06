---
title: 高度なファイルシステムの使用
description: Use filesystem source as a building block
keywords: [readers source and filesystem, files, filesystem, readers source, cloud storage]
---

ファイルシステム ソースは、ファイルからデータをロードするための構成要素を提供します。このセクションでは、ユースケースに合わせてファイルシステム ソースをカスタマイズする方法について説明します。

## スタンドアロンファイルシステムリソース

[スタンドアロンファイルシステム](../../../general-usage/resource#declare-a-standalone-resource)リソースを使用して、クラウドストレージまたはローカルファイルシステム内のファイルを一覧表示できます。これにより、ファイルリーダーをカスタマイズしたり、[fsspec](https://filesystem-spec.readthedocs.io/en/latest/index.html)を使用してファイルを管理したりできます。

```py
from dlt.sources.filesystem import filesystem

pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
files = filesystem(bucket_url="s3://my_bucket/data", file_glob="csv_folder/*.csv")
pipeline.run(files)
```

ファイルシステムは、バケットタイプ間で一貫したファイル表現を保証し、データにアクセスして読み取る方法を提供します:

- PDFからテキストを抽出する ([非構造化データソース](https://github.com/dlt-hub/verified-sources/tree/master/sources/unstructured_data)).
- 大きなファイルコンテンツをバケットから直接ストリーミングします。
- ファイルをローカルにコピーする ([ファイルをコピーする](#copy-files-locally))

### `FileItem` 表現

- ファイルを生成するすべての dlt ソース/リソースは、[FileItem](https://github.com/dlt-hub/dlt/blob/devel/dlt/common/storages/fsspec_filesystem.py#L40) に従います。
- ファイルコンテンツは通常は読み込まれません (ファイルシステムリソースの `extract_content` パラメータを使用して制御できます)。代わりに、完全なファイル情報とコンテンツにアクセスするためのメソッドが利用できます。
- ユーザーは認証された [fsspec AbstractFileSystem](https://filesystem-spec.readthedocs.io/en/latest/_modules/fsspec/spec.html#AbstractFileSystem) インスタンスをリクエストできます。

#### `FileItem` のフィールド

- `file_url` - ファイルの完全な URL (例: `s3://bucket-name/path/file`)。このフィールドは主キーとして機能します。
- `file_name` - バケット URL からのファイルの名前。
- `relative_path` - `glob` を実行するときに設定され、`bucket_url` 引数への相対パスになります。
- `mime_type` - ファイルの MIME タイプ。バケットプロバイダーから取得されるか、拡張子から推測されます。
- `modification_date` - ファイルの最終変更時刻 (形式: `pendulum.DateTime`)。
- `size_in_bytes` - ファイルのサイズ.
- `file_content` - コンテンツはリクエストに応じて提供されます。

:::info
ネストされたまたは再帰的な glob パターンを使用する場合、`relative_path` には `bucket_url` を基準としたファイルのパスが含まれます。たとえば、リソース `filesystem("az://dlt-ci-test-bucket/standard_source/samples", file_glob="met_csv/A801/*.csv")` を使用すると、`met_csv/A801/A881_20230920.csv` など、`/standard_source/samples` パスを基準としたファイル名が生成されます。ローカル ファイル システムの場合、POSIX パス (区切り文字として "/" を使用) が返されます。
:::

### ファイル操作

[FileItem](https://github.com/dlt-hub/dlt/blob/devel/dlt/common/storages/fsspec_filesystem.py#L40)は、辞書実装に基づいており、これらのヘルパーを提供します:

- `read_bytes()` - ファイルの内容をバイト列として返すメソッド。
- `open()` - 開いたときにファイル オブジェクトを提供するメソッド。
- `filesystem` - 標準の fsspec メソッドを使用して承認された `AbstractFilesystem` へのアクセスができるフィールド。

## 独自のトランスフォーマーを作成する

`filesystem` リソースはクラウドストレージまたはローカルファイルシステムからファイルを生成しますが、ファイルからレコードを取得するにはトランスフォーマーリソースを適用する必要があります。dlt はネイティブで 3 つのファイルタイプをサポートしています: [CSV](../../file-formats/csv.md) と [Parquet](../../file-formats/parquet.md) と [JSONL](../../file-formats/jsonl.md) (詳細については [filesystem transformer リソース](../filesystem/basic#2-choose-the-right-transformer-resource)を参照してください)

ただし、独自のものを簡単に作成できます。これを行うには、`FileItemDict` イテレータを入力として受け取り、レコードのリスト (パフォーマンスのために推奨) または個々のレコードを生成する関数が必要です。

### 例: Excel ファイルからデータを読み取る

以下のコードは、スタンドアロンのトランスフォーマーを使用してExcelファイルから読み取るパイプラインを設定します:

```py
import dlt
from dlt.common.storages.fsspec_filesystem import FileItemDict
from dlt.common.typing import TDataItems
from dlt.sources.filesystem import filesystem

BUCKET_URL = "s3://my_bucket/data"

# Define a standalone transformer to read data from an Excel file.
@dlt.transformer
def read_excel(
    items: Iterator[FileItemDict], sheet_name: str
) -> Iterator[TDataItems]:
    # Import the required pandas library.
    import pandas as pd

    # Iterate through each file item.
    for file_obj in items:
        # Open the file object.
        with file_obj.open() as file:
            # Read from the Excel file and yield its content as dictionary records.
            yield pd.read_excel(file, sheet_name).to_dict(orient="records")

# Set up the pipeline to fetch a specific Excel file from a filesystem (bucket).
example_xls = filesystem(
    bucket_url=BUCKET_URL, file_glob="../directory/example.xlsx"
) | read_excel("example_table")   # Pass the data through the transformer to read the "example_table" sheet.

pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb", dataset_name="example_xls_data")
# Execute the pipeline and load the extracted data into the "duckdb" destination.
load_info = pipeline.run(example_xls.with_name("example_xls_data"))
# Print the loading information.
print(load_info)
```

### 例: XML ファイルからデータを読み取る

任意のサードパーティライブラリを使用して `xml` ファイルを解析できます (例: [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)、[pandas](https://pandas.pydata.org/docs/reference/api/pandas.read_xml.html))。次の例では、[xmltodict](https://pypi.org/project/xmltodict/) Python ライブラリを使用します。

```py
import dlt
from dlt.common.storages.fsspec_filesystem import FileItemDict
from dlt.common.typing import TDataItems
from dlt.sources.filesystem import filesystem

BUCKET_URL = "s3://my_bucket/data"

# Define a standalone transformer to read data from an XML file.
@dlt.transformer(standalone=True)
def read_xml(items: Iterator[FileItemDict]) -> Iterator[TDataItems]:
    # Import the required xmltodict library.
    import xmltodict

    # Iterate through each file item.
    for file_obj in items:
        # Open the file object.
        with file_obj.open() as file:
            # Parse the file to dict records.
            yield xmltodict.parse(file.read())

# Set up the pipeline to fetch a specific XML file from a filesystem (bucket).
example_xml = filesystem(
    bucket_url=BUCKET_URL, file_glob="../directory/example.xml"
) | read_xml()   # Pass the data through the transformer

pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb", dataset_name="example_xml_data")
# Execute the pipeline and load the extracted data into the "duckdb" destination.
load_info = pipeline.run(example_xml.with_name("example_xml_data"))

# Print the loading information.
print(load_info)
```

## 読み込み後にファイルをクリーンアップする

ファイルシステムリソースを抽出した後、処理済みのファイルなどを削除するために、ファイルシステムリソースから fsspec クライアントを取得できます。ファイルシステムモジュールには、次のように使用できる便利なメソッド `fsspec_from_resource` が含まれています:

```py
from dlt.sources.filesystem import filesystem, read_csv
from dlt.sources.filesystem.helpers import fsspec_from_resource

# Get filesystem source.
gs_resource = filesystem("gs://ci-test-bucket/")
# Extract files.
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
pipeline.run(gs_resource | read_csv())
# Get fs client.
fs_client = fsspec_from_resource(gs_resource)
# Do any operation.
fs_client.ls("ci-test-bucket/standard_source/samples")
```

## ファイルをローカルにコピーする

ファイルをローカルにコピーするには、ファイルシステムリソースにステップを追加し、リストをデータベースにロードします:

```py
import os

import dlt
from dlt.common.storages.fsspec_filesystem import FileItemDict
from dlt.sources.filesystem import filesystem

def _copy(item: FileItemDict) -> FileItemDict:
    # Instantiate fsspec and copy file
    dest_file = os.path.join("./local_folder", item["file_name"])
    # Create destination folder
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    # Download file
    item.fsspec.download(item["file_url"], dest_file)
    # Return file item unchanged
    return item

BUCKET_URL = "gs://ci-test-bucket/"

# Use recursive glob pattern and add file copy step
downloader = filesystem(BUCKET_URL, file_glob="**").add_map(_copy)

# NOTE: You do not need to load any data to execute extract; below, we obtain
# a list of files in a bucket and also copy them locally
listing = list(downloader)
print(listing)
# Download to table "listing"
pipeline = dlt.pipeline(pipeline_name="my_pipeline", destination="duckdb")
load_info = pipeline.run(
    downloader.with_name("listing"), write_disposition="replace"
)
# Pretty print the information on data that was loaded
print(load_info)
print(listing)
print(pipeline.last_trace.last_normalize_info)
```

