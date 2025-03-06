---
title: Load data from a cloud storage or a file system
description: Learn how to load data files like JSON, JSONL, CSV, and Parquet from a cloud storage (AWS S3, Google Cloud Storage, Google Drive, Azure Blob Storage) or a local file system using dlt.
keywords: [dlt, tutorial, filesystem, cloud storage, file system, python, data pipeline, incremental loading, json, jsonl, csv, parquet, duckdb]
---

このチュートリアルは、JSONL、CSV、Parquet などのデータ ファイルを Cloud Storage (AWS S3、Google Cloud Storage、Google Drive、Azure Blob Storage など)、リモート (SFTP)、またはローカルファイルシステムからロードする必要がある場合に役立ちます。

## 学ぶ内容

- ファイルシステムまたはクラウドストレージをデータソースとして設定する方法
- ファイルシステムとクラウドストレージの構成の基本
- ロードの方法
- ファイルシステムまたはクラウドストレージからのデータのインクリメンタルなロード
- その他の種類のデータをロードする方法

## 0. 前提条件

- Python 3.9 以上がインストールされている
- 仮想環境がセットアップされている
- `dlt` がインストールされている。[インストールガイド](../reference/installation)の指示に従って、新しい仮想環境を作成し、dlt をインストールしてください。

## 1. 新しいプロジェクトの設定

すぐに使い始めるために、dlt は便利な CLI コマンドをいくつか提供しています。これらのコマンドの 1 つは、新しい dlt プロジェクトを設定するのに役立ちます:

```sh
dlt init filesystem duckdb
```

このコマンドは、ファイル システムから DuckDB データベースにデータをロードするプロジェクトを作成します。duckdb を他の [サポートされている宛先](../dlt-ecosystem/destinations) に簡単に切り替えることができます。
このコマンドを実行すると、プロジェクトは次の構造になります:

```text
filesystem_pipeline.py
requirements.txt
.dlt/
    config.toml
    secrets.toml
```

各ファイルの機能は次のとおりです:

- `filesystem_pipeline.py`: これは、データパイプラインを定義するメインスクリプトです。ファイルシステムソースからデータをロードするさまざまな例が含まれています。
- `requirements.txt`: このファイルには、プロジェクトに必要なすべての Python 依存関係がリストされています。
- `.dlt/`: このディレクトリには、プロジェクトの[構成ファイル](../general-usage/credentials/)が含まれています:
    - `secrets.toml`: このファイルには、API キー、トークン、その他の機密情報が保存されます。
    - `config.toml`: このファイルには、dlt プロジェクトの構成設定が含まれています。

:::note
パイプラインを本番環境にデプロイする場合、すべての構成をファイルで管理するのは不便な場合があります。この場合、代わりに環境変数を使用してシークレットと構成を保存することをお勧めします。dlt で利用可能な [構成プロバイダー](../general-usage/credentials/setup#available-config-providers) の詳細をご覧ください。
:::

## 2. パイプラインの作成

ファイルシステムソースは、あらゆるタイプのファイルからデータをロードするためのビルディングブロックをユーザーに提供します。データの抽出は2つのステップに分けることができます:

1. バケット/ディレクトリ内のファイルを一覧表示します。
2. ファイルを読み取り、レコードを生成します。

dlt のファイルシステムソースにはいくつかのリソースが含まれています:

- `filesystem` リソースは、ディレクトリまたはバケット内のファイルを一覧表示します。
- いくつかのリーダーリソース (`read_csv`、`read_parquet`、`read_jsonl`) は、ファイルを読み取り、レコードを生成します。これらのリソースには特別なタイプがあり、[トランスフォーマー](../general-usage/resource#process-resources-with-dlttransformer) と呼ばれます。トランスフォーマーは、別のリソースからのアイテムを期待します。今回のケースでは、トランスフォーマーは `FileItem` オブジェクトを期待し、それを複数のレコードに変換します。

ソースを初期化し、Google Cloud Storage から DuckDB に CSV ファイルをロードするためのパイプラインを作成しましょう。`filesystem_pipeline.py` のコードを次のコードに置き換えることができます:

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(bucket_url="gs://filesystem-tutorial", file_glob="encounters*.csv")
reader = (files | read_csv()).with_name("encounters")
pipeline = dlt.pipeline(pipeline_name="hospital_data_pipeline", dataset_name="hospital_data", destination="duckdb")

info = pipeline.run(reader)
print(info)
```

上記のスニペットでは何が起こっているのでしょうか？

1. `filesystem` リソースをインポートし、バケット URL (`gs://filesystem-tutorial`) と `file_glob` パラメータで初期化します。dlt は `file_glob` を使用してバケット内のファイル名をフィルタリングします。`filesystem` はジェネレーター オブジェクトを返します。
2. ファイルシステムリソースによって生成されたファイル名をトランスフォーマーリソース `read_csv` にパイプして、各ファイルを読み取り、ファイルのレコードを反復処理します。`with_name()` メソッドを使用して、このトランスフォーマー リソースに `"encounters"` という名前を付けます。dlt は、データをロードするときに、リソース名 `"encounters"` をテーブル名として使用します。

:::note
dlt の [トランスフォーマー](../general-usage/resource#process-resources-with-dlttransformer) は、別のリソースからの各レコードを処理する特別なタイプのリソースです。これにより、複数のリソースを連結できます。
:::

3. dlt パイプラインを作成し、名前を `hospital_data_pipeline` に設定し、宛先として DuckDB を設定します。
4. `pipeline.run()` を呼び出します。ここで基礎となるジェネレータが反復処理されます。:
 - dlt はリモート データを取得し、
 - データを正規化し、
 - 宛先のテーブルを作成または更新し、
 - 抽出されたデータを宛先にロードします。
5. `print(info)` は、`pipeline.run()` から取得したパイプラインの実行統計を出力します。

## 3. ファイルシステムソースの設定

:::note
このチュートリアルでは、合成電子カルテを含む、公開アクセス可能なデータセット [Hospital Patient Records](https://mavenanalytics.io/data-playground?order=date_added%2Cdesc&search=Hospital%20Patient%20Records) を操作します。このチュートリアルの正確な認証情報を使用して、GCP からこのデータセットを読み込むことができます。
<details>
<summary>Citation</summary>
Jason Walonoski, Mark Kramer, Joseph Nichols, Andre Quina, Chris Moesel, Dylan Hall, Carlton Duffett, Kudakwashe Dube, Thomas Gallagher, Scott McLachlan, Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record, Journal of the American Medical Informatics Association, Volume 25, Issue 3, March 2018, Pages 230–238, https://doi.org/10.1093/jamia/ocx079
</details>
:::

次に、接続を構成する必要があります。具体的には、バケットの URL と認証情報を設定します。この例では、Google Cloud Storage を使用します。その他のクラウド ストレージ サービスについては、[ファイルシステム構成セクション](../dlt-ecosystem/verified-sources/filesystem/basic#configuration) を参照してください。

バケットのURLと認証情報を指定しましょう。これは次の方法で行うことができます:

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
# secrets.toml
[sources.filesystem.credentials]
client_email = "public-access@dlthub-sandbox.iam.gserviceaccount.com"
project_id = "dlthub-sandbox"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDGWsVHJRjliojx\nTo+j1qu+x8PzC5ZHZrMx6e8OD6tO8uxMyl65ByW/4FZkVXkS4SF/UYPigGN+rel4\nFmySTbP9orva4t3Pk1B9YSvQMB7V5IktmTIW9Wmdmn5Al8Owb1RehgIidm1EX/Z9\nLr09oLpO6+jUu9RIP2Lf2mVQ6tvkgl7UOdpdGACSNGzRiZgVZDOaDIgH0Tl4UWmK\n6iPxhwZy9YC2B1beLB/NU+F6DUykrEpBzCFQTqFoTUcuDAEvuvpU9JrU2iBMiOGw\nuP3TYSiudhBjmauEUWaMiqWAgFeX5ft1vc7/QWLdI//SAjaiTAu6pTer29Q0b6/5\niGh0jRXpAgMBAAECggEAL8G9C9MXunRvYkH6/YR7F1T7jbH1fb1xWYwsXWNSaJC+\nagKzabMZ2KfHxSJ7IxuHOCNFMKyex+pRcvNbMqJ4upGKzzmeFBMw5u8VYGulkPQU\nPyFKWRK/Wg3PZffkSr+TPargKrH+vt6n9x3gvEzNbqEIDugmRTrVsHXhvOi/BrYc\nWhppHSVQidWZi5KVwDEPJjDQiHEcYI/vfIy1WhZ8VuPAaE5nMZ1m7gTdeaWWKIAj\n/p2ZkLgRdCY8vNkfaNDAxDbvH+CMuTtOw55GydzsYYiofANS6xZ8CedGkYaGi82f\nqGdLghX61Sg3UAb5SI36T/9XbuCpTf3B/SMV20ew8QKBgQDm2yUxL71UqI/xK9LS\nHWnqfHpKmHZ+U9yLvp3v79tM8XueSRKBTJJ4H+UvVQrXlypT7cUEE+sGpTrCcDGL\nm8irtdUmMvdi7AnRBgmWdYKig/kgajLOUrjXqFt/BcFgqMyTfzqPt3xdp6F3rSEK\nHE6PQ8I3pJ0BJOSJRa6Iw2VH1QKBgQDb9WbVFjYwTIKJOV4J2plTK581H8PI9FSt\nUASXcoMTixybegk8beGdwfm2TkyF/UMzCvHfuaUhf+S0GS5Zk31Wkmh1YbmFU4Q9\nm9K/3eoaqF7CohpigB0wJw4HfqNh6Qt+nICOMCv++gw7+/UwfV72dCqr0lpzfX5F\nAsez8igTxQKBgDsq/axOnQr+rO3WGpGJwmS8BKfrzarxGXyjnV0qr51X4yQdfGWx\nV3T8T8RC2qWI8+tQ7IbwB/PLE3VURg6PHe6MixXgSDGNZ7KwBnMOqS23/3kEXwMs\nhn2Xg+PZeMeqW8yN9ldxYqmqViMTN32c5bGoXzXdtfPeHcjlGCerVOEFAoGADVPi\nRjkRUX3hTvVF6Gzxa2OyQuLI1y1O0C2QCakrngyI0Dblxl6WFBwDyHMYGepNnxMj\nsr2p7sy0C+GWuGDCcHNwluQz/Ish8SW28F8+5xyamUp/NMa0fg1vwS6AMdeQFbzf\n4T2z/MAj66KJqcV+8on5Z+3YAzVwaDgR56pdmU0CgYBo2KWcNWAhZ1Qa6sNrITLV\nGlxg6tWP3OredZrmKb1kj5Tk0V+EwVN+HnKzMalv6yyyK7SWq1Z6rvCye37vy27q\nD7xfuz0c0H+48uWJpdLcsxpTioopsRPayiVDKlHSe/Qa+MEjAG3ded5TJiC+5iSw\nxWJ51y0wpme0LWgzzoLbRw==\n-----END PRIVATE KEY-----\n"

# config.toml
[sources.filesystem]
bucket_url="gs://filesystem-tutorial"
```
  </TabItem>

<TabItem value="env">

```sh
export SOURCES__FILESYSTEM__CREDENTIALS__CLIENT_EMAIL="public-access@dlthub-sandbox.iam.gserviceaccount.com"
export SOURCES__FILESYSTEM__CREDENTIALS__PROJECT_ID="dlthub-sandbox"
export SOURCES__FILESYSTEM__CREDENTIALS__PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDGWsVHJRjliojx\nTo+j1qu+x8PzC5ZHZrMx6e8OD6tO8uxMyl65ByW/4FZkVXkS4SF/UYPigGN+rel4\nFmySTbP9orva4t3Pk1B9YSvQMB7V5IktmTIW9Wmdmn5Al8Owb1RehgIidm1EX/Z9\nLr09oLpO6+jUu9RIP2Lf2mVQ6tvkgl7UOdpdGACSNGzRiZgVZDOaDIgH0Tl4UWmK\n6iPxhwZy9YC2B1beLB/NU+F6DUykrEpBzCFQTqFoTUcuDAEvuvpU9JrU2iBMiOGw\nuP3TYSiudhBjmauEUWaMiqWAgFeX5ft1vc7/QWLdI//SAjaiTAu6pTer29Q0b6/5\niGh0jRXpAgMBAAECggEAL8G9C9MXunRvYkH6/YR7F1T7jbH1fb1xWYwsXWNSaJC+\nagKzabMZ2KfHxSJ7IxuHOCNFMKyex+pRcvNbMqJ4upGKzzmeFBMw5u8VYGulkPQU\nPyFKWRK/Wg3PZffkSr+TPargKrH+vt6n9x3gvEzNbqEIDugmRTrVsHXhvOi/BrYc\nWhppHSVQidWZi5KVwDEPJjDQiHEcYI/vfIy1WhZ8VuPAaE5nMZ1m7gTdeaWWKIAj\n/p2ZkLgRdCY8vNkfaNDAxDbvH+CMuTtOw55GydzsYYiofANS6xZ8CedGkYaGi82f\nqGdLghX61Sg3UAb5SI36T/9XbuCpTf3B/SMV20ew8QKBgQDm2yUxL71UqI/xK9LS\nHWnqfHpKmHZ+U9yLvp3v79tM8XueSRKBTJJ4H+UvVQrXlypT7cUEE+sGpTrCcDGL\nm8irtdUmMvdi7AnRBgmWdYKig/kgajLOUrjXqFt/BcFgqMyTfzqPt3xdp6F3rSEK\nHE6PQ8I3pJ0BJOSJRa6Iw2VH1QKBgQDb9WbVFjYwTIKJOV4J2plTK581H8PI9FSt\nUASXcoMTixybegk8beGdwfm2TkyF/UMzCvHfuaUhf+S0GS5Zk31Wkmh1YbmFU4Q9\nm9K/3eoaqF7CohpigB0wJw4HfqNh6Qt+nICOMCv++gw7+/UwfV72dCqr0lpzfX5F\nAsez8igTxQKBgDsq/axOnQr+rO3WGpGJwmS8BKfrzarxGXyjnV0qr51X4yQdfGWx\nV3T8T8RC2qWI8+tQ7IbwB/PLE3VURg6PHe6MixXgSDGNZ7KwBnMOqS23/3kEXwMs\nhn2Xg+PZeMeqW8yN9ldxYqmqViMTN32c5bGoXzXdtfPeHcjlGCerVOEFAoGADVPi\nRjkRUX3hTvVF6Gzxa2OyQuLI1y1O0C2QCakrngyI0Dblxl6WFBwDyHMYGepNnxMj\nsr2p7sy0C+GWuGDCcHNwluQz/Ish8SW28F8+5xyamUp/NMa0fg1vwS6AMdeQFbzf\n4T2z/MAj66KJqcV+8on5Z+3YAzVwaDgR56pdmU0CgYBo2KWcNWAhZ1Qa6sNrITLV\nGlxg6tWP3OredZrmKb1kj5Tk0V+EwVN+HnKzMalv6yyyK7SWq1Z6rvCye37vy27q\nD7xfuz0c0H+48uWJpdLcsxpTioopsRPayiVDKlHSe/Qa+MEjAG3ded5TJiC+5iSw\nxWJ51y0wpme0LWgzzoLbRw==\n-----END PRIVATE KEY-----\n"
export SOURCES__FILESYSTEM__BUCKET_URL="gs://filesystem-tutorial"
```
  </TabItem>

<TabItem value="code">

```py
import os

from dlt.common.configuration.specs import GcpClientCredentials
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(
    bucket_url="gs://filesystem-tutorial",
    # please, do not specify sensitive information directly in the code,
    # instead, you can use env variables to get the credentials
    credentials=GcpClientCredentials(
        client_email="public-access@dlthub-sandbox.iam.gserviceaccount.com",
        project_id="dlthub-sandbox",
        private_key=os.environ["GCP_PRIVATE_KEY"]  # type: ignore
    ),
    file_glob="encounters*.csv") | read_csv()
```
</TabItem>
</Tabs>

ご覧のとおり、`filesystem` のすべてのパラメータはコード内で直接指定することも、構成から取得することもできます。

:::tip
dlt は、ID ベースやデフォルトの認証情報など、クラウド ストレージを使用した認証のさまざまな方法をサポートしています。パイプラインに認証情報を追加する方法の詳細については、[構成とシークレットのセクション](../general-usage/credentials/complex_types#aws-credentials) を参照してください。
:::

## 4. パイプラインの実行

パイプラインが期待通りに動作していることを確認しましょう。次のコマンドを実行してパイプラインを実行します。:

```sh
python filesystem_pipeline.py
```

ターミナルにパイプライン実行の出力が表示されます。出力には、データが保存されているDuckDBデータベースファイルの場所も表示されます:

```sh
Pipeline hospital_data_pipeline load step completed in 4.11 seconds
1 load package(s) were loaded to destination duckdb and into dataset hospital_data
The duckdb destination used duckdb:////Users/vmishechk/PycharmProjects/dlt/hospital_data_pipeline.duckdb location to store data
Load package 1726074108.8017762 is LOADED and contains no failed jobs
```

## 5. データの調査

データの探索パイプラインが正常に実行されたので、DuckDBにロードされたデータを探索してみましょう。dltには、データを操作できる組み込みのブラウザアプリケーションが付属しています。これを有効にするには、次のコマンドを実行します:

```sh
pip install streamlit
```

次に、以下のコマンドを実行してデータブラウザを起動します。:

```sh
dlt pipeline hospital_data_pipeline show
```

このコマンドは、データ ブラウザ アプリケーションを含む新しいブラウザ ウィンドウを開きます。`hospital_data_pipeline` は、`filesystem_pipeline.py` ファイルで定義されているパイプラインの名前です。

![Streamlit Explore data](/img/filesystem-tutorial/streamlit-data.png)

読み込まれたデータを調べたり、クエリを実行したり、パイプライン実行の詳細を確認したりできます。

## 6. ロードされたデータの追加、置換、およびマージ

`python filesystem_pipeline.py` でパイプラインを再度実行してみると、すべてのテーブルに重複したデータがあることに気づくでしょう。これは、デフォルトでは dlt がデータを宛先テーブルに追加するために発生します。これは、たとえば、毎日データが更新され、それを取り込みたい場合に非常に便利です。dlt を使用すると、リソース構成で `write_disposition` パラメータを設定することで、データが宛先テーブルにロードされる方法を制御できます。可能な値は次のとおりです:
- `append`: データを宛先テーブルに追加します。これがデフォルトです。
- `replace`: 宛先テーブル内のデータを新しいデータに置き換えます。
- `merge`: 主キーに基づいて、新しいデータを宛先テーブル内の既存のデータとマージします。

`write_disposition` を指定するには、`pipeline.run` コマンドで設定します。書き込み処理を `merge` に変更してみましょう。この場合、dlt はデータを宛先にロードする前に重複排除します。

データの重複排除を有効にするには、dlt が 2 つのレコードが異なるかどうかを定義するために使用する `primary_key` または `merge_key` も指定する必要があります。両方のキーは複数の列で構成できます。dlt は `merge_key` の使用を試み、指定されていない場合は `primary_key` にフォールバックします。列タイプ、主キーなど、データに関するヒントを指定するには、[`apply_hints`](../general-usage/resource#set-table-name-and-adjust-schema) メソッドを使用できます。

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(file_glob="encounters*.csv")
reader = (files | read_csv()).with_name("encounters")
reader.apply_hints(primary_key="id")
pipeline = dlt.pipeline(pipeline_name="hospital_data_pipeline", dataset_name="hospital_data", destination="duckdb")

info = pipeline.run(reader, write_disposition="merge")
print(info)
```
:::tip
主キー列に一意の値があることを確認するために、`append` 書き込み処理を使用してデータを複数回ロードした場合は、以前にロードしたデータを削除する必要があるかもしれません。
:::

`write_disposition` の詳細については、増分読み込みページの [write dispositions セクション](../general-usage/incremental-loading#the-3-write-dispositions) を参照してください。

## 7. データをインクリメンタルにロードする

ファイルからデータをロードする場合、変更されたファイルのみをロードしたいことがよくあります。dltは[増分ロード](../general-usage/incremental-loading)でこれを簡単にします。変更されたファイルのみをロードするには、`apply_hint`メソッドを使用します:

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(file_glob="encounters*.csv")
files.apply_hints(incremental=dlt.sources.incremental("modification_date"))
reader = (files | read_csv()).with_name("encounters")
reader.apply_hints(primary_key="id")
pipeline = dlt.pipeline(pipeline_name="hospital_data_pipeline", dataset_name="hospital_data", destination="duckdb")

info = pipeline.run(reader, write_disposition="merge")
print(info)
```

`reader` ではなく `files` リソースで `apply_hints` を使用していることに注意してください。前述のように、`filesystem` リソースは `file_glob` パラメータに基づいてストレージ内のすべてのファイルをリストします。したがって、この時点で、ファイルをフィルター処理するための追加条件を指定することもできます。この場合、最後のロード以降に変更されたファイルのみをロードします。dlt は増分ロードの状態を自動的に保持し、適切なフィルター処理を管理します。

しかし、変更されたファイルを処理するだけでなく、新しいレコードだけをロードしたい場合はどうすればよいでしょうか。`encounters` テーブルには、エンカウンターの終了のタイムスタンプを示す `STOP` という列があります。コードを変更して、最後のロード以降に `STOP` タイムスタンプが更新されたレコードだけをロードするようにしてみましょう。

```py
import dlt
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(file_glob="encounters*.csv")
files.apply_hints(incremental=dlt.sources.incremental("modification_date"))
reader = (files | read_csv()).with_name("encounters")
reader.apply_hints(primary_key="id", incremental=dlt.sources.incremental("STOP"))
pipeline = dlt.pipeline(pipeline_name="hospital_data_pipeline", dataset_name="hospital_data", destination="duckdb")

info = pipeline.run(reader, write_disposition="merge")
print(info)
```

`files` と `reader` の両方に増分ロードを適用したことに注意してください。したがって、dlt は最初に変更されたファイルのみをフィルターし、次に `STOP` 列に基づいて新しいレコードをフィルターします。

`dlt pipeline hospital_data_pipeline show`を実行すると、パイプラインの状態に増分変数に関する新しい情報が含まれていることがわかります:

![Streamlit Explore data](/img/filesystem-tutorial/streamlit-incremental-state.png)

インクリメンタルなロードの詳細については、[ファイルシステムのインクリメンタルロードのセクション](../dlt-ecosystem/verified-sources/filesystem/basic#5-incremental-loading)を参照してください。

## 8. ファイルのメタデータでレコードを充実させる

次に、実際のレコードにファイル名を追加してみましょう。これは、ファイルの起源を実際のレコードに結び付けるのに役立ちます。

`filesystem` ソースはファイルに関する情報を生成するので、トランスフォーマーを変更して利用可能なメタデータを追加することができます。カスタムトランスフォーマー関数を作成しましょう。dlt コードから `read_csv` 関数をコピーして貼り付け、データフレームに `file_name` 列を 1 つ追加するだけです:

```py
from typing import Any, Iterator

import dlt
from dlt.sources import TDataItems
from dlt.sources.filesystem import FileItemDict
from dlt.sources.filesystem import filesystem


@dlt.transformer()
def read_csv_custom(items: Iterator[FileItemDict], chunksize: int = 10000, **pandas_kwargs: Any) -> Iterator[TDataItems]:
    import pandas as pd

    # Apply defaults to pandas kwargs
    kwargs = {**{"header": "infer", "chunksize": chunksize}, **pandas_kwargs}

    for file_obj in items:
        with file_obj.open() as file:
            for df in pd.read_csv(file, **kwargs):
                df["file_name"] = file_obj["file_name"]
                yield df.to_dict(orient="records")

files = filesystem(file_glob="encounters*.csv")
files.apply_hints(incremental=dlt.sources.incremental("modification_date"))
reader = (files | read_csv_custom()).with_name("encounters")
reader.apply_hints(primary_key="id", incremental=dlt.sources.incremental("STOP"))
pipeline = dlt.pipeline(pipeline_name="hospital_data_pipeline", dataset_name="hospital_data", destination="duckdb")

info = pipeline.run(reader, write_disposition="merge")
print(info)
```

このコードを実行すると、`encounters`テーブルに新しい列が表示されます:

![Streamlit Explore data](/img/filesystem-tutorial/streamlit-new-col.png)

## 9. 他の種類のファイルをロードする

dlt は、CSV、Parquet、JSONL の 3 つのファイルタイプをネイティブにサポートしています (詳細については、[ファイルシステムのトランスフォーマーリソース](../dlt-ecosystem/verified-sources/filesystem/basic#2-choose-the-right-transformer-resource) を参照してください)。ただし、独自のトランスフォーマーを簡単に作成できます。これを行うには、`FileItemDict` イテレータを入力として受け取り、レコードのリスト (パフォーマンスのために推奨) または個々のレコードを生成する関数が必要です。

CSV ではなく JSON ファイルを読み取るトランスフォーマーを作成して適用してみましょう (JSON の実装は JSONL とは少し異なります)。

```py
from typing import Iterator

import dlt
from dlt.common import json
from dlt.common.storages.fsspec_filesystem import FileItemDict
from dlt.common.typing import TDataItems
from dlt.sources.filesystem import filesystem

# Define a standalone transformer to read data from a JSON file.
@dlt.transformer(standalone=True)
def read_json(items: Iterator[FileItemDict]) -> Iterator[TDataItems]:
    for file_obj in items:
        with file_obj.open() as f:
            yield json.load(f)

files_resource = filesystem(file_glob="**/*.json")
files_resource.apply_hints(incremental=dlt.sources.incremental("modification_date"))
json_resource = files_resource | read_json()
pipeline = dlt.pipeline(pipeline_name="s3_to_duckdb", dataset_name="json_data", destination="duckdb")

info = pipeline.run(json_resource, write_disposition="replace")
print(info)
```

`excel` ファイルと `xml` ファイルからデータを読み取る方法を示した[その他の例](../dlt-ecosystem/verified-sources/filesystem/advanced#create-your-own-transformer) を確認してください。

## 次は？

チュートリアルの完了おめでとうございます。dlt でファイルシステムソースを設定し、データパイプラインを実行してデータを DuckDB にロードする方法を学びました。

dlt についてさらに詳しく知りたいですか? いくつか提案があります。

- ファイルシステム ソース構成の詳細については、[ファイルシステム ソース](../dlt-ecosystem/verified-sources/filesystem) を参照してください。
- [組み込みの認証情報](../general-usage/credentials/complex_types#built-in-credentials) のさまざまな認証情報タイプについて詳しく学びます。
- 上級チュートリアルで[カスタムソースを作成する](./load-data-from-an-api.md)方法を学びます

