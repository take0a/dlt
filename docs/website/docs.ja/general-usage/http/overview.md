---
title: REST API helpers
description: Use the dlt RESTClient to interact with RESTful APIs and paginate the results
keywords: [api, http, rest, restful, requests, restclient, paginate, pagination, json]
---

dlt には API からデータを取得するためのサポートが組み込まれています:
- RESTful API と対話し、結果をページ分割するための [RESTClient](./rest-client.md)
- 自動再試行とタイムアウトを備えたシンプルな HTTP リクエストを作成するための[Requests wrapper](./requests.md)

さらに、dlt は API の操作を簡素化するツールを提供します:
- [REST API 汎用ソース](../../dlt-ecosystem/verified-sources/rest_api)は、[宣言型構成](../../dlt-ecosystem/verified-sources/rest_api#source-configuration)を使用して API を統合し、カスタム コードを最小限に抑えます。
OpenAPI 仕様
- [OpenAPI ソースジェネレーター](../../dlt-ecosystem/verified-sources/openapi-generator)は、[OpenAPI 仕様書](https://swagger.io/specification/)から宣言型 API 構成を自動的に作成します。

## 簡単な例

これは、[dlt GitHub リポジトリ](https://github.com/dlt-hub/dlt/issues) から issue を読み取るシンプルなパイプラインです。API エンドポイントは https://api.github.com/repos/dlt-hub/dlt/issues です。結果は「ページ分割」されます。つまり、API はページごとに限られた数の issue を返します。`paginate()` メソッドはすべてのページを反復処理して結果を生成し、パイプラインで処理します。

```py
import dlt
from dlt.sources.helpers.rest_client import RESTClient

github_client = RESTClient(base_url="https://api.github.com")  # (1)

@dlt.resource
def get_issues():
    for page in github_client.paginate(                        # (2)
        "/repos/dlt-hub/dlt/issues",                           # (3)
        params={                                               # (4)
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
        },
    ):
        yield page                                             # (5)


pipeline = dlt.pipeline(
    pipeline_name="github_issues",
    destination="duckdb",
    dataset_name="github_data",
)
load_info = pipeline.run(get_issues)
print(load_info)
```

コードの動作は次のとおりです:
1. API のベース URL (この場合は GitHub API (https://api.github.com)) を使用して `RESTClient` インスタンスを作成します。
2. issue のエンドポイントは issue のリストを返します。issue は数百に及ぶ可能性があるため、API は結果を「ページ分割」します。つまり、各応答で限られた数の問題と、次の一連の問題 (または「ページ」) へのリンクを返します。`paginate()` メソッドはすべてのページを反復処理し、一連の issue を生成します。
3. ここでは、読み取り元のエンドポイントのアドレスを指定します: `/repos/dlt-hub/dlt/issues`。
4. 返されるデータを制御するために、実際の API 呼び出しにパラメータを渡します。この場合、ページごとに 100 件の issue (`"per_page": 100`) を要求し、最終更新日 (`"sort": "updated"`) で降順 (`"direction": "desc"`) に並べ替えます。
5. リソース関数からパイプラインにページを渡します。`page` は [`PageData`](#pagedata) のインスタンスであり、API レスポンスの現在のページのデータといくつかのメタデータが含まれています。

この例では、ページ区切りパラメータを明示的に指定していないことに注意してください。`paginate()` メソッドはページ区切りを自動的に処理します。つまり、レスポンスから API が使用するページ区切りメカニズムを検出します。ページ区切り方法とパラメータを明示的に指定する必要がある場合はどうすればよいでしょうか。以下の別の例でその方法を見てみましょう。

## ページネーションパラメータを明示的に指定する

```py
import dlt
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import JSONLinkPaginator

github_client = RESTClient(
    base_url="https://pokeapi.co/api/v2",
    paginator=JSONLinkPaginator(next_url_path="next"),   # (1)
    data_selector="results",                             # (2)
)

@dlt.resource
def get_pokemons():
    for page in github_client.paginate(
        "/pokemon",
        params={
            "limit": 100,                                    # (3)
        },
    ):
        yield page

pipeline = dlt.pipeline(
    pipeline_name="get_pokemons",
    destination="duckdb",
    dataset_name="github_data",
)
load_info = pipeline.run(get_pokemons)
print(load_info)
```

上記の例では:
1. API のベース URL (この場合は [PokéAPI](https://pokeapi.co/)) を使用して `RESTClient` インスタンスを作成します。また、使用するページネーターを明示的に指定します: `next_url_path` が `"next"` に設定された `JSONLinkPaginator`。これにより、ページネーターは JSON 応答の `next` キーで次のページの URL を探すように指示されます。
2. `data_selector` では、レスポンスからデータを抽出するための JSON パスを指定します。これは、レスポンス JSON からデータを抽出するために使用されます。
3. デフォルトでは、ページあたりのアイテム数は 20 に制限されています。API 呼び出しで `limit` パラメータを指定してこれを上書きします。

