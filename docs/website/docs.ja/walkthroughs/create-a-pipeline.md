---
title: Create a pipeline
description: How to create a pipeline
keywords: [how to, create a pipeline, rest client]
---

# パイプラインを作成する

このガイドでは、[REST API クライアント](../general-usage/http/rest-client) を使用して [DuckDB](../dlt-ecosystem/destinations/duckdb) に接続するパイプラインの作成手順を説明します。

:::tip
ここでは DuckDB を宛先として使用していますが、[コマンド](../reference/command-line-interface#dlt-init) `dlt init <source> <destination>` を使用してパイプラインを適宜調整することで、任意の [ソース](../dlt-ecosystem/verified-sources/) と [宛先](../dlt-ecosystem/destinations/) に手順を適応させることができます。
:::

以下の手順を実行する前に、[`dlt`](../reference/installation) がインストールされていることを確認してください。

## タスクの概要

GitHub プロジェクトの Issue をローカルで分析したいとします。

これを実現するには、以下の処理を実行するコードを記述する必要があります。

1. 正しいリクエストを構築する。
2. リクエストを認証する。
3. ページ分けされた Issue データを取得して処理する。
4. 分析用にデータを保存する。

複雑に聞こえるかもしれませんが、dlt は [REST API クライアント](../general-usage/http/rest-client) を提供しており、API のやり取りの管理ではなく、データに集中することができます。

## 1. プロジェクトの初期化

次のコマンドを実行して、`dlt` プロジェクト用の新しい空のディレクトリを作成します:

```sh
mkdir github_api_duckdb && cd github_api_duckdb
```

次のコマンドを実行して、DuckDB にデータをロードするパイプライン テンプレートを使用して `dlt` プロジェクトを開始します:

```sh
dlt init github_api duckdb
```

DuckDB に必要な依存関係をインストールします:

```sh
pip install -r requirements.txt
```

## 2. GitHub から API 認証情報を取得して追加する

GitHub アカウントに [サインイン](https://github.com/login) し、[個人アクセストークンページ](https://github.com/settings/tokens) からアクセストークンを作成する必要があります。

新しいアクセストークンを `.dlt/secrets.toml` にコピーします。

```toml
[sources]
api_secret_key = '<api key value>'
```

このトークンは、`github_api_source()` によってリクエストの認証に使用されます。

**シークレット名** は、ソース関数の **引数名** に対応します。
以下では、`github_api_source()` が呼び出されると、`api_secret_key` は `secrets.toml` から [値を取得します](../general-usage/credentials/advanced)。

```py
@dlt.source
def github_api_source(api_secret_key: str = dlt.secrets.value):
    return github_api_resource(api_secret_key=api_secret_key)
```

`github_api_pipeline.py` パイプライン スクリプトを実行して、認証ヘッダーが正常かどうかをテストします:

```sh
python github_api_pipeline.py
```

API キーは、いくつかのテスト データとともに stdout に出力されるはずです。

## 3. GitHub APIからプロジェクトの問題をリクエストする


:::tip
GitHub プロジェクトの例として `dlt` リポジトリ (https://github.com/dlt-hub/dlt) を使用しますが、独自のリポジトリに置き換えても構いません。
:::

GitHub プロジェクトの API から問題データをリクエストするには、`github_api_pipeline.py` の `github_api_resource` を変更します。

```py
from dlt.sources.helpers.rest_client import paginate
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator

@dlt.resource(write_disposition="replace")
def github_api_resource(api_secret_key: str = dlt.secrets.value):
    url = "https://api.github.com/repos/dlt-hub/dlt/issues"

    for page in paginate(
        url,
        auth=BearerTokenAuth(api_secret_key), # type: ignore
        paginator=HeaderLinkPaginator(),
        params={"state": "open"}
    ):
        yield page
```

## 4. データをロードする

`github_api_pipeline.py` の `main` 関数内のコメントアウトされたコードのコメントを解除します。これにより、`python github_api_pipeline.py` コマンドを実行するとパイプラインも実行されるようになります。

```py
if __name__=='__main__':
    # configure the pipeline with your destination details
    pipeline = dlt.pipeline(
        pipeline_name='github_api_pipeline',
        destination='duckdb',
        dataset_name='github_api_data'
    )

    # print credentials by running the resource
    data = list(github_api_resource())

    # print the data yielded from resource
    print(data)

    # run the pipeline with your parameters
    load_info = pipeline.run(github_api_source())

    # pretty print the information on data that was loaded
    print(load_info)
```


`github_api_pipeline.py` パイプライン スクリプトを実行して、API 呼び出しが機能するかどうかをテストします:

```sh
python github_api_pipeline.py
```

これにより、GitHub プロジェクトの課題を含む JSON データが出力されます。

`load_info` オブジェクトも出力されます。

[コマンド](../reference/command-line-interface#dlt-pipeline-show) `dlt pipeline <pipeline_name> show` を使って、読み込まれたデータを確認してみましょう。

:::info
`streamlit` がインストールされていることを確認してください: `pip install streamlit`
:::

```sh
dlt pipeline github_api_pipeline show
```

これにより、読み込まれたデータの概要を示す Streamlit アプリが開きます。

## 5. 次のステップ

パイプラインが機能したら、以下の点について検討してみてください。

- [REST クライアント](../general-usage/http/rest-client)。
- [GitHub Actions でこのパイプラインをデプロイ](deploy-a-pipeline/deploy-with-github-actions)。これにより、データがスケジュールに従って自動的に読み込まれるようになります。
- [読み込まれたデータ](../dlt-ecosystem/transformations)をdbtまたはPandas DataFramesで変換します。
- パイプラインを本番環境に導入する際に、[実行](../running-in-production/running)、[監視](../running-in-production/monitoring)、[アラート](../running-in-production/alerting)を行う方法を学習します。
- [Google BigQuery](../dlt-ecosystem/destinations/bigquery)、[Amazon Redshift](../dlt-ecosystem/destinations/redshift)、[Postgres](../dlt-ecosystem/destinations/postgres) などの別の保存先にデータをロードしてみます。
