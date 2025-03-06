---
title: Load data from a REST API
description: How to extract data from a REST API using dlt's REST API source
keywords: [tutorial, api, github, duckdb, rest api, source, pagination, authentication]
---

このチュートリアルでは、dlt の REST API ソースを使用して REST API からデータを抽出し、それを宛先にロードする方法を説明します。[Pokemon](https://pokeapi.co/) と [GitHub API](https://docs.github.com/en/) からローカルの DuckDB データベースにデータをロードするデータ パイプラインの構築方法を学習します。

dlt を使用すると、API からデータを抽出するのは簡単です。ベース URL を指定し、取得するリソースを定義すると、dlt がページ区切り、認証、およびデータの読み込みを処理します。

## 学ぶ内容

- REST APIソースの設定方法
- APIエンドポイント設定の基本
- 宛先のデータベースの構成
- 異なるリソース間の関係
- 宛先でデータを追加、置換、結合する方法
- 新しいデータまたは更新されたデータのみを取得してデータをインクリメンタルにロードする

## 前提条件

- Python 3.9 以上がインストールされている
- 仮想環境がセットアップされている

## dlt のインストール

始める前に、Python 仮想環境が設定されていることを確認してください。[インストールガイド](../reference/installation)の指示に従って、新しい仮想環境を作成し、dlt をインストールします。

ターミナルで次のコマンドを実行して、dltがインストールされていることを確認します:

```sh
dlt --version
```

バージョン番号 (「dlt 0.5.3」など) が表示されたら、続行する準備は完了です。

## 新しいプロジェクトの設定

REST API ソースと 宛先の DuckDB を指定して新しい dlt プロジェクトを初期化します:

```sh
dlt init rest_api duckdb
```

`dlt init` はプロジェクト用の複数のファイルとディレクトリを作成します。プロジェクト構造を見てみましょう:

```sh
rest_api_pipeline.py
requirements.txt
.dlt/
    config.toml
    secrets.toml
```

各ファイルとディレクトリの内容は次のとおりです:

- `rest_api_pipeline.py`: これは、データ パイプラインを定義するメイン スクリプトです。Pokemon と GitHub API の 2 つの基本的なパイプライン例が含まれています。必要に応じて、このファイルを変更したり、名前を変更したりできます。
- `requirements.txt`: このファイルには、プロジェクトに必要なすべての Python 依存関係がリストされます。
- `.dlt/`: このディレクトリには、プロジェクトの [構成ファイル](../general-usage/credentials/) が含まれています:
    - `secrets.toml`: このファイルには、API キー、トークン、その他の機密情報が保存されます。
    - `config.toml`: このファイルには、dlt プロジェクトの構成設定が含まれています。

## 依存関係のインストール

先に進む前に、このチュートリアルに必要な依存関係をインストールしましょう。次のコマンドを実行して、`requirements.txt`ファイルにリストされている依存関係をインストールします:

```sh
pip install -r requirements.txt
```

## パイプラインの実行

パイプラインが期待通りに動作していることを確認しましょう。次のコマンドを実行してパイプラインを実行します:

```sh
python rest_api_pipeline.py
```

ターミナルにパイプライン実行の出力が表示されます。出力には、データが保存されている DuckDB データベースファイルの場所も表示されます:

```sh
Pipeline rest_api_pokemon load step completed in 1.08 seconds
1 load package(s) were loaded to destination duckdb and into dataset rest_api_data
The duckdb destination used duckdb:////home/user-name/quick_start/rest_api_pokemon.duckdb location to store data
Load package 1692364844.9254808 is LOADED and contains no failed jobs
```

## データの調査

パイプラインが正常に実行されたので、DuckDB にロードされたデータを調べてみましょう。dlt には、データを操作できる組み込みのブラウザアプリケーションが付属しています。これを有効にするには、次のコマンドを実行します:

```sh
pip install streamlit
```

次に、以下のコマンドを実行してデータブラウザを起動します:

```sh
dlt pipeline rest_api_pokemon show
```

このコマンドは、データブラウザアプリケーションを含む新しいブラウザを開きます。`rest_api_pokemon` は、`rest_api_pipeline.py` ファイルで定義されているパイプラインの名前です。
読み込まれたデータを調べたり、クエリを実行したり、パイプライン実行の詳細を確認したりできます:

![Explore rest_api data in Streamlit App](https://dlt-static.s3.eu-central-1.amazonaws.com/images/docs-rest-api-tutorial-streamlit-screenshot.png)

## REST API ソースの構成

REST API ソースの構成環境とプロジェクトがセットアップされたので、REST API ソースの構成を詳しく見てみましょう。エディタで`rest_api_pipeline.py`ファイルを開き、次のコードスニペットを見つけます:

```py
import dlt
from dlt.sources.rest_api import rest_api_source

def load_pokemon() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="rest_api_pokemon",
        destination="duckdb",
        dataset_name="rest_api_data",
    )

    pokemon_source = rest_api_source(
        {
            "client": {
                "base_url": "https://pokeapi.co/api/v2/"
            },
            "resource_defaults": {
                "endpoint": {
                    "params": {
                        "limit": 1000,
                    },
                },
            },
            "resources": [
                "pokemon",
                "berry",
                "location",
            ],
        }
    )

    ...

    load_info = pipeline.run(pokemon_source)
    print(load_info)
```

コード内で何が起こっているか見てみましょう:

1. `dlt.pipeline()` 関数で、DuckDB を宛先とし、`rest_api_data` をデータセット名として、`rest_api_pokemon` という名前の新しいパイプラインを定義します。
2. `rest_api_source()` 関数は、新しい REST API ソース オブジェクトを作成します。
3. このソース オブジェクトを `pipeline.run()` メソッドに渡して、パイプラインの実行を開始します。`run()` メソッド内で、dlt は API からデータを取得し、それを DuckDB データベースにロードします。
4. `print(load_info)` はパイプライン実行の詳細をコンソールに出力します。

REST API ソースの構成を詳しく見てみましょう。これは、`client`、`resource_defaults`、`resources` の 3 つの主要部分で構成されています。

```py
config: RESTAPIConfig = {
    "client": {
        # ...
    },
    "resource_defaults": {
        # ...
    },
    "resources": [
        # ...
    ],
}
```

- `client` 構成は、Web サーバーに接続し、必要に応じて認証するために使用されます。この簡単な例では、API の `base_url`: `https://pokeapi.co/api/v2/` のみを指定する必要があります。
- `resource_defaults` 構成では、すべてのリソースのデフォルト パラメータを設定できます。通常、ここではページ区切りの制限などの共通パラメータを設定します。Pokemon API の例では、すべてのリソースの `limit` パラメータを 1000 に設定して、1 回のリクエストでより多くのデータを取得し、HTTP API 呼び出しの数を減らしています。
- `resources` リストには、API からロードするリソースの名前が含まれています。REST API は、いくつかの規則を使用して、リソース名に基づいてエンドポイント URL を決定します。たとえば、リソース名 `pokemon` は、エンドポイント URL `https://pokeapi.co/api/v2/pokemon` に変換されます。

:::note
### ページネーション
`rest_api_source()` 関数でページネーション設定を指定していないことにお気づきかもしれません。これは、ベスト プラクティスに従う REST API の場合、dlt がページネーションを自動的に検出して処理できるためです。[ページネーションの設定](../dlt-ecosystem/verified-sources/rest_api/basic#pagination)の詳細については、REST API ソース ドキュメントを参照してください。
:::

## 読み込まれたデータの追加、置換、およびマージ

`python rest_api_pipeline.py` でパイプラインを再度実行してみてください。すべてのテーブルに重複したデータがあることに気づくでしょう。これは、dlt がデフォルトでデータを宛先テーブルに追加するために発生します。dlt では、リソース構成で `write_disposition` パラメータを設定することで、宛先テーブルにデータをロードする方法を制御できます。可能な値は次のとおりです。:
- `append`: データを宛先テーブルに追加します。これがデフォルトです。
- `replace`: 宛先テーブル内のデータを新しいデータに置き換えます。
- `merge`: 主キーに基づいて、新しいデータを宛先テーブル内の既存のデータとマージします。

### データの置換

今回の場合、パイプラインを実行するたびにデータを追加することは望ましくありません。まずは、よりシンプルな `replace` 書き込み処理から始めましょう。

書き込み処理を `replace` に変更するには、`rest_api_pipeline.py` ファイルの `resource_defaults` 構成を更新します:

```py
...
pokemon_source = rest_api_source(
    {
        "client": {
            "base_url": "https://pokeapi.co/api/v2/",
        },
        "resource_defaults": {
            "endpoint": {
                "params": {
                    "limit": 1000,
                },
            },
            "write_disposition": "replace", # Setting the write disposition to `replace`
        },
        "resources": [
            "pokemon",
            "berry",
            "location",
        ],
    }
)
...
```

`python rest_api_pipeline.py` を使用してパイプラインを再度実行します。今回は、宛先テーブルでデータが追加されるのではなく、置き換えられます。

### データのマージ

新しいデータがロードされるときに既存のデータを更新したい場合は、`merge` 書き込み処理を使用できます。これには、リソースの主キーを指定する必要があります。主キーは、新しいデータを宛先テーブル内の既存のデータと一致させるために使用されます。

`merge` 書き込み処理を使用するように例を更新してみましょう。`pokemon` リソースの主キーを指定し、書き込み処理を `merge` に設定する必要があります:

```py
...
pokemon_source = rest_api_source(
    {
        "client": {
            "base_url": "https://pokeapi.co/api/v2/",
        },
        "resource_defaults": {
            "endpoint": {
                "params": {
                    "limit": 1000,
                },
            },
            # For the `berry` and `location` resources, we keep
            # the `replace` write disposition
            "write_disposition": "replace",
        },
        "resources": [
            # We create a specific configuration for the `pokemon` resource
            # using a dictionary instead of a string to configure
            # the primary key and write disposition
            {
                "name": "pokemon",
                "primary_key": "name",
                "write_disposition": "merge",
            },
            # The `berry` and `location` resources will use the default
            "berry",
            "location",
        ],
    }
)
```

`python rest_api_pipeline.py` を使用してパイプラインを実行すると、`p​​okemon` リソースのデータが、`name` フィールドに基づいて宛先テーブル内の既存のデータとマージされます。

## データのインクリメンタルなロード

一部の API を使用する場合、毎回データセット全体を取得することを回避し、読み込み時間を短縮するために、データを段階的に読み込む必要がある場合があります。 増分読み込みをサポートする API は通常、新しいデータまたは変更されたデータのみを取得する方法を提供します (ほとんどの場合、`updated_at`、`created_at` などのタイムスタンプ フィールド、または増分 ID を使用します)。

増分読み込みを説明するために、GitHub APIを考えてみましょう。`rest_api_pipeline.py`ファイルには、GitHub APIからデータを増分的に読み込む方法の例があります。設定を見てみましょう:

```py
import dlt
from dlt.sources.rest_api import rest_api_source

pipeline = dlt.pipeline(
    pipeline_name="rest_api_github",
    destination="duckdb",
    dataset_name="rest_api_data",
)

github_source = rest_api_source({
    "client": {
        "base_url": "https://api.github.com/repos/dlt-hub/dlt/",
    },
    "resource_defaults": {
        "primary_key": "id",
        "write_disposition": "merge",
        "endpoint": {
            "params": {
                "per_page": 100,
            },
        },
    },
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "issues",
                "params": {
                    "sort": "updated",
                    "direction": "desc",
                    "state": "open",
                    "since": {
                        "type": "incremental",
                        "cursor_path": "updated_at",
                        "initial_value": "2024-01-25T11:21:28Z",
                    },
                },
            },
        },
    ],
})

load_info = pipeline.run(github_source)
print(load_info)
```

この構成では、`since` パラメータは特別な増分パラメータとして定義されています。`cursor_path` フィールドは、更新されたデータを取得するために使用されるフィールドへの JSON パスを指定し、増分パラメータの初期値として `initial_value` を使用します。この値は、データを取得する最初のリクエストで使用されます。

パイプラインが実行されると、dlt は応答データの最新の値で `since` パラメータを自動的に更新します。これにより、API から新しいデータまたは更新されたデータのみを取得できます。

REST API ソースドキュメントの [インクリメンタルローディング](../dlt-ecosystem/verified-sources/rest_api/basic#incremental-loading) で詳細をご確認ください。

## 次は？

チュートリアルの完了おめでとうございます。dlt で REST API ソースを設定し、データ パイプラインを実行してデータを DuckDB にロードする方法を学びました。

dlt についてもっと知りたいですか？いくつか提案があります:

- REST API ソース構成の詳細については、[REST API ソースドキュメント](../dlt-ecosystem/verified-sources/rest_api/) を参照してください。
- 上級チュートリアルで[カスタムソースを作成する](./load-data-from-an-api.md)方法を学習します。

