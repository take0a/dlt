---
title: REST API source
description: Learn how to set up and configure
keywords: [rest api, restful api]
---
import Header from '../_source-info-header.md';

<Header/>

これは、任意の REST API からデータを抽出するために使用できる dlt ソースです。[宣言型の構成](#source-configuration) を使用して、API エンドポイント、それらの [関係](#define-resource-relationships)、[ページネーション](#pagination) の処理方法、および[認証](#authentication) を定義します。

### 簡単な例

架空のブログAPIから投稿と関連コメントを読み込むためのREST APIソースの設定例を示します:

```py
import dlt
from dlt.sources.rest_api import rest_api_source

source = rest_api_source({
    "client": {
        "base_url": "https://api.example.com/",
        "auth": {
            "token": dlt.secrets["your_api_token"],
        },
        "paginator": {
            "type": "json_link",
            "next_url_path": "paging.next",
        },
    },
    "resources": [
        # "posts" will be used as the endpoint path, the resource name,
        # and the table name in the destination. The HTTP client will send
        # a request to "https://api.example.com/posts".
        "posts",

        # The explicit configuration allows you to link resources
        # and define query string parameters.
        {
            "name": "comments",
            "endpoint": {
                "path": "posts/{resources.posts.id}/comments",
                "params": {
                    "sort": "created_at",
                },
            },
        },
    ],
})

pipeline = dlt.pipeline(
    pipeline_name="rest_api_example",
    destination="duckdb",
    dataset_name="rest_api_data",
)

load_info = pipeline.run(source)
```

このパイプラインを実行すると、DuckDB に `posts` と `comments` の 2 つのテーブルが作成され、それぞれの API エンドポイントからのデータが格納されます。`comments` リソースは、`posts` リソースの `id` フィールドを使用して、各投稿のコメントを取得します。

## Setup

### 前提条件

`dlt` ライブラリがインストールされていることを確認してください。[インストール ガイド](../../../intro)を参照してください。

### REST APIソースを初期化する

ターミナルに次のコマンドを入力してください:

```sh
dlt init rest_api duckdb
```

[dlt init](../../../reference/command-line-interface) は、REST API を [source](../../../general-usage/source) として、[duckdb](../../destinations/duckdb.md) を [destination](../../destinations) としてパイプラインの例を初期化します。

`dlt init`を実行すると、現在のフォルダに次のものが作成されます:

- `rest_api_pipeline.py` パイプラインの例の定義のファイル:
    - GitHub API の例
    - Pokemon API の例
- `.dlt` フォルダには:
     - `secrets.toml` アクセストークンやその他の機密情報を保存するファイル
     - `config.toml` 設定を保存するファイル
- `requirements.txt` 必要な依存関係を持つファイル

`rest_api_pipeline.py` ファイルを変更して、REST API ソースをニーズに合わせて変更します。詳細な [ソース構成](#source-configuration) セクションについては、以下を参照してください。

:::note
ガイドの残りの部分では、[GitHub API](https://docs.github.com/en/rest?apiVersion=2022-11-28) と [Pokemon API](https://pokeapi.co/) をサンプルソースとして使用します。
:::

このソースは、[RESTClient クラス](../../../general-usage/http/rest-client.md) に基づいています。

### 資格情報を追加する

`.dlt` フォルダには、`secrets.toml` というファイルがあり、アクセス トークンやその他の機密情報を安全に保存できます。このファイルは慎重に取り扱い、安全に保管することが重要です。

GitHub API では、一部のエンドポイントにアクセスし、API 呼び出しのレート制限を増やすために [アクセス トークン](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28) が必要です。GitHub トークンを取得するには、[個人用アクセス トークンの管理](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) に関する GitHub ドキュメントに従ってください。

トークンを取得したら、それを `secrets.toml` ファイルに追加します。

```toml
[sources.rest_api_pipeline.github_source]
github_token = "your_github_token"
```

## パイプラインを実行する

1. 次のコマンドを実行して必要な依存関係をインストールします:

   ```sh
   pip install -r requirements.txt
   ```

2. パイプラインを実行する:

   ```sh
   python rest_api_pipeline.py
   ```

3. 次のコマンドを使用して、すべてが正しくロードされたことを確認します:

   ```sh
   dlt pipeline rest_api show
   ```

## ソース構成

### 簡単な例

`rest_api_pipeline.py`ファイルのGitHubの例を見てみましょう:

```py
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

@dlt.source
def github_source(github_token=dlt.secrets.value):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://api.github.com/repos/dlt-hub/dlt/",
            "auth": {
                "token": github_token,
            },
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
            {
                "name": "issue_comments",
                "endpoint": {
                    "path": "issues/{resources.issues.number}/comments",
                },
                "include_from_parent": ["id"],
            },
        ],
    }

    yield from rest_api_resources(config)

def load_github() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="rest_api_github",
        destination="duckdb",
        dataset_name="rest_api_data",
    )

    load_info = pipeline.run(github_source())
    print(load_info)
```

宣言型リソース構成は `config` 辞書で定義されます。これには次のキーコンポーネントが含まれます:

1. `client`: API のベース URL と認証方法を定義します。この場合、トークンベースの認証を使用します。トークンは `secrets.toml` ファイルに保存されます。

2. `resource_defaults`: すべての[リソース](#resource-configuration)のデフォルト設定が含まれます。この例では、すべてのリソースが以下のように定義されます:
    - `id` を [主キー](../../../general-usage/resource#define-schema)とする
    - [write disposition](../../../general-usage/incremental-loading.md#choosing-a-write-disposition)に `merge` を指定して、宛先の既存データをマージする
    - ページあたりより多くの結果を取得するため、各リクエストで `per_page=100` クエリパラメータを送信します。

3. `resources`: ロードする[リソース](#resource-configuration)のリスト。ここでは、GitHub API のエンドポイントである[repository issues](https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues) と [issue comments](https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments) に対応する `issues ` と `issue_comments` という２つのリソースがあります。各問題のコメントを取得するには問題番号が必要であることに注意してください。この番号は `issues` リソースから取得されます。詳細については、[リソース関係](#define-resource-relationships) セクションを参照してください。

構成を詳しく見てみましょう。

### 設定の構造

:::tip
`rest_api` モジュールから `RESTAPIConfig` タイプをインポートして、エディター/IDE で便利なヒントを取得し、それを使用して構成オブジェクトを定義します。

```py
from dlt.sources.rest_api import RESTAPIConfig
```
:::

REST API汎用ソースに渡される構成オブジェクトには3つの主要な要素があります:

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

#### `client`

`client` 構成は、API のエンドポイントに接続するために使用されます。これには次のフィールドが含まれます:

- `base_url` (str): API のベース URL。この文字列は、すべてのエンドポイント パスの先頭に追加されます。たとえば、ベース URL が `https://api.example.com/v1/` で、エンドポイント パスが `users` の場合、完全な URL は `https://api.example.com/v1/users` になります。
- `headers` (dict, optional): 各リクエストとともに送信される追加のヘッダー。
- `auth` (optional): 認証構成。これは、単純なトークン、`AuthConfigBase` オブジェクト、またはより複雑な認証方法が設定できます。
- `paginator` (optional): ページネーションをサポートするリソースに使用されるデフォルトのページネーションの設定。詳細については、[ページネーション](#pagination) セクションを参照してください。

#### `resource_defaults` (optional)

`resource_defaults` には、[dlt リソースを構成する](#resource-configuration)ためのデフォルト値が含まれています。この構成は、リソース固有の構成によって上書きされない限り、すべてのリソースに適用されます。

たとえば、主キー、書き込み処理、その他のデフォルト設定をここで設定できます:

```py
config = {
    "client": {
        # ...
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
        "resource1",
        {
            "name": "resource2_name",
            "write_disposition": "append",
            "endpoint": {
                "params": {
                    "param1": "value1",
                },
            },
        }
    ],
}
```

上記では、すべてのリソースの `primary_key` が `id` に設定され、`resource1` の `write_disposition` が `merge` に設定され、`resource2` はデフォルトの `write_disposition` を `append` で上書きします。
`resource1` と `resource2` の両方で `per_page` パラメータが 100 に設定されます。

#### `resources`

これは、ロードされる API エンドポイントを定義するリソース構成のリストです。各リソース構成は:
- [リソース設定](#resource-configuration)の辞書
- 文字列。この場合、文字列はエンドポイント パスとリソース名の両方として使用され、リソース構成は `resource_defaults` 構成が存在する場合はそこから取得されます。

### リソースの設定

リソースの設定は、APIエンドポイントからロードされるデータの[dltリソース](../../../general-usage/resource.md)を定義するために使用されます。これには次のキーフィールドが含まれます:

- `endpoint`: リソースのエンドポイント構成。エンドポイント設定を表す文字列または辞書になります。詳細については、[エンドポイント設定](#endpoint-configuration) セクションを参照してください。
- `write_disposition`: リソースの書き込み処理。
- `primary_key`: リソースの主キー。
- `include_from_parent`: リソース出力に含める親リソースのフィールドのリスト。詳細については、[リソース関係](#include-fields-from-the-parent-resource) セクションを参照してください。
- `processing_steps`: データをフィルタリングおよび変換するための[処理手順](#processing-steps-filter-and-transform-data)のリスト
- `selected`: リソースが読み込み対象として選択されているかどうかを示すフラグ。これは、親リソースからではなく子リソースからのみデータを読み込む場合に役立ちます。
- `auth`: オプションの `AuthConfig` インスタンス。渡された場合、[client](#client) 定義で定義されたインスタンスよりも優先して使用されます。例:

```py
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth

config = {
    "client": {
        "auth": {
            "type": "bearer",
            "token": dlt.secrets["your_api_token"],
        }
    },
    "resources": [
        "resource-using-bearer-auth",
        {
            "name": "my-resource-with-special-auth",
            "endpoint": {
                # ...
                "auth": HttpBasicAuth("user", dlt.secrets["your_basic_auth_password"])
            },
            # ...
        }
    ]
    # ...
}
```

これにより、`resource-using-bearer-auth` には `client` で定義されている `Bearer` 認証が使用され、`my-resource-with-special-auth` には `Http Basic` 認証が使用されます。

dlt リソースを構成するために使用される追加のリソースパラメータを渡すこともできます。詳細については、[dlt リソース API リファレンス](../../../api_reference/extract/decorators#resource)を参照してください。

### Endpoint 設定

エンドポイント設定は、APIエンドポイントをクエリする方法を定義します。簡単な例:

```py
{
    "path": "issues",
    "method": "GET",
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
    "data_selector": "results",
}
```

エンドポイント構成のフィールドは:

- `path`: API エンドポイントへのパス。デフォルトでは、このパスは指定された `base_url` に追加されます。これが `http:` または `https:` で始まる完全修飾 URL である場合は、そのまま使用され、`base_url` は無視されます。
- `method`: 使用する HTTP メソッド。デフォルトは `GET` です。
- `params`: 各リクエストとともに送信されるクエリ パラメータ。たとえば、結果を並べ替える `sort` や、[インクリメンタルローディング](#incremental-loading) を指定する `since` などがあります。これは、[リソース関係](#define-resource-relationships) を定義するためにも使用できます。
- `json`: リクエストとともに送信される JSON ペイロード (POST および PUT リクエストの場合)。
- `paginator`: エンドポイントのページネーション設定。詳細については、[ページネーション](#pagination) セクションを参照してください。
- `data_selector`: レスポンスからデータを選択するための JSONPath。詳細については、[データ選択](#data-selection) セクションを参照してください。
- `response_actions`: 応答データの処理方法を定義するアクションのリスト。詳細については、[応答アクション](./advanced#response-actions)セクションを参照してください。
- `incremental`: [インクリメンタルローディング](#incremental-loading)の設定

### ページネーション

REST API ソースは、ページ区切りを自動的に処理しようとします。これは、最初の API 応答からページ区切りの詳細を検出することによって機能します。

特別な場合には、ページネーション設定を明示的に指定する必要があります。

ページネーション設定を指定するには、[client](#client) または [endpoint](#endpoint-configuration) 設定の `paginator` フィールドを使用します。 `type` フィールドに文字列エイリアスを含む辞書と必要なパラメータを使用するか、[paginator クラスのインスタンス](../../../general-usage/http/rest-client.md#paginators) を使用します。

#### 例

`https://api.example.com/posts` のAPIレスポンスに次のページのURLを含む `next`フィールドが含まれているとします:

```json
{
    "data": [
        {"id": 1, "title": "Post 1"},
        {"id": 2, "title": "Post 2"},
        {"id": 3, "title": "Post 3"}
    ],
    "pagination": {
        "next": "https://api.example.com/posts?page=2"
    }
}
```

`posts`リソースのページネーションは次のように設定できます:

```py
{
    "path": "posts",
    "paginator": {
        "type": "json_link",
        "next_url_path": "pagination.next",
    }
}
```

あるいは、ページネーターインスタンスを直接使用することもできます:

```py
from dlt.sources.helpers.rest_client.paginators import JSONLinkPaginator

# ...

{
    "path": "posts",
    "paginator": JSONLinkPaginator(
        next_url_path="pagination.next"
    ),
}
```

:::note
現在、ページネーションはGETリクエストに対してのみサポートされています。ページネーションを使用してPOSTリクエストを処理するには、[カスタムページネーター](../../../general-usage/http/rest-client.md#custom-paginator)を実装する必要があります。
:::

利用可能なページネーターは次のとおりです:

| `type` | Paginator class | Description |
| ------------ | -------------- | ----------- |
| `json_link` | [JSONLinkPaginator](../../../general-usage/http/rest-client.md#jsonresponsepaginator) | 次のページへのリンクは、レスポンスの本文 (JSON) にあります。<br/>*パラメータ:*<ul><li>`next_url_path` (str) - 次のページの URL への JSONPath</li></ul> |
| `header_link` | [HeaderLinkPaginator](../../../general-usage/http/rest-client.md#headerlinkpaginator) | 次のページへのリンクは、レスポンス ヘッダーにあります。<br/>*パラメーター:*<ul><li>`links_next_key` (str) - リンクを含むヘッダーの名前。デフォルトは "next" です。</li></ul> |
| `offset` | [OffsetPaginator](../../../general-usage/http/rest-client.md#offsetpaginator) | ページ区切りはオフセット パラメータに基づいており、合計アイテム数はレスポンス本文内または明示的に提供されます。<br/>*パラメータ:*<ul><li>`limit` (int) - 各リクエストで取得するアイテムの最大数</li><li>`offset` (int) - 最初のリクエストの初期オフセット。デフォルトは `0` です</li><li>`offset_param` (str) - オフセットを指定するために使用されるクエリ パラメータの名前。デフォルトは "offset" です</li><li>`limit_param` (str) - 制限を指定するために使用されるクエリ パラメータの名前。デフォルトは "limit" です</li><li>`total_path` (str) - アイテムの合計数の JSONPath 式。指定されていない場合、ページ区切りは `maximum_offset` と `stop_after_empty_page` によって制御されます</li><li>`maximum_offset` (int) - オプションの最大オフセット値。合計数がなくてもページ区切りを制限します</li><li>`stop_after_empty_page` (bool) - ページに結果項目が含まれていない場合にページ区切りを停止するかどうか。デフォルトは `True` です</li></ul> |
| `page_number` | [PageNumberPaginator](../../../general-usage/http/rest-client.md#pagenumberpaginator) | ページ区切りはページ番号パラメータに基づいており、総ページ数はレスポンス本文内または明示的に提供されます。<br/>*パラメータ:*<ul><li>`base_page` (int) - 開始ページ番号。デフォルトは `0` です。</li><li>`page_param` (str) - ページ番号のクエリパラメータ名。デフォルトは "page" です。</li><li>`total_path` (str) - 総ページ数の JSONPath 式。指定されていない場合、ページ区切りは `maximum_page` と `stop_after_empty_page` によって制御されます。</li><li>`maximum_page` (int) - オプションの最大ページ番号。このページに到達するとページ区切りが停止します。</li><li>`stop_after_empty_page` (bool) - ページに結果項目が含まれていない場合にページ区切りを停止するかどうか。デフォルトは `True` です。</li></ul> |
| `cursor` | [JSONResponseCursorPaginator](../../../general-usage/http/rest-client.md#jsonresponsecursorpaginator) | ページネーションはカーソル パラメータに基づいており、カーソルの値はレスポンス本文 (JSON) に含まれています。<br/>*パラメータ:*<ul><li>`cursor_path` (str) - カーソル値への JSONPath。デフォルトは "cursors.next" です。</li><li>`cursor_param` (str) - カーソルのクエリ パラメータ名。Defaults to "cursor" if neither `cursor_param` nor `cursor_body_path` is provided.</li><li>`cursor_body_path` (str, optional) - the JSONPath to place the cursor in the request body.</li></ul>Note: You must provide either `cursor_param` or `cursor_body_path`, but not both. If neither is provided, `cursor_param` will default to "cursor". |
| `single_page` | SinglePagePaginator | 応答は、ページ区切りのメタデータを無視して、単一ページの応答として解釈されます。 |
| `auto` | `None` | ソースがページ区切り方法を自動的に検出するように明示的に指定します。 |

より複雑なページネーション方法の場合は、[カスタムページネーター](../../../general-usage/http/rest-client.md#implementing-a-custom-paginator)を実装し、インスタンス化して、構成で使用することができます。

あるいは、カスタムページネーターにも辞書設定構文を使用できます。そのためには、カスタムページネーターを登録する必要があります:

```py
from dlt.sources.rest_api.config_setup import register_paginator

class CustomPaginator(SinglePagePaginator):
    # custom implementation of SinglePagePaginator
    pass

register_paginator("custom_paginator", CustomPaginator)

{
    # ...
    "paginator": {
        "type": "custom_paginator",
        "next_url_path": "paging.nextLink",
    }
}
```

### データの選択

エンドポイント構成の `data_selector` フィールドを使用すると、レスポンスからデータを選択するための JSONPath を指定できます。デフォルトでは、ソースはデータの場所を自動的に検出しようとします。

応答内のデータの場所を明示的に指定する必要がある場合にこのフィールドを使用します。

たとえば、APIレスポンスが次のようになる場合:

```json
{
    "posts": [
        {"id": 1, "title": "Post 1"},
        {"id": 2, "title": "Post 2"},
        {"id": 3, "title": "Post 3"}
    ]
}
```

次のエンドポイント構成を使用できます:

```py
{
    "path": "posts",
    "data_selector": "posts",
}
```

このようなネストされた構造の場合:

```json
{
    "results": {
        "posts": [
            {"id": 1, "title": "Post 1"},
            {"id": 2, "title": "Post 2"},
            {"id": 3, "title": "Post 3"}
        ]
    }
}
```

次のエンドポイント構成を使用できます:

```py
{
    "path": "posts",
    "data_selector": "results.posts",
}
```

セレクターの記述方法については、[JSONPath 構文](https://github.com/h2non/jsonpath-ng?tab=readme-ov-file#jsonpath-syntax) の詳細をご覧ください。

### 認証

エンドポイントにアクセスするために認証を必要とする API の場合、REST API ソースは、トークンベースの認証、クエリ パラメータ、基本認証、カスタム認証など、さまざまな認証方法をサポートしています。認証構成は、[クライアント](#client) の `auth` フィールドで、辞書または [authentication クラス](../../../general-usage/http/rest-client.md#authentication) のインスタンスとして指定されます。

#### 簡単な例

bearer トークンを使用して認証を構成する方法は次のとおりです:

```py
{
    "client": {
        # ...
        "auth": {
            "type": "bearer",
            "token": dlt.secrets["your_api_token"],
        },
        # ...
    },
}
```

あるいは、authentication クラスを直接使用することもできます:

```py
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

config = {
    "client": {
        "auth": BearerTokenAuth(dlt.secrets["your_api_token"]),
    },
    "resources": [
    ]
    # ...
}
```

トークンベースの認証は最も一般的な方法の1つであるため、次のショートカットを使用できます:

```py
{
    "client": {
        # ...
        "auth": {
            "token": dlt.secrets["your_api_token"],
        },
        # ...
    },
}
```

<!-- :::warning
アクセス トークンやその他の機密情報は必ず `secrets.toml` ファイルに保存し、バージョン管理システムにコミットしないでください。
:::

利用可能な認証タイプ:

| Authentication class | String Alias (`type`) | Description |
| ------------------- | ----------- | ----------- |
| [BearerTokenAuth](../../../general-usage/http/rest-client.md#bearer-token-authentication) | `bearer` | Bearer トークン認証 |
| [HTTPBasicAuth](../../../general-usage/http/rest-client.md#http-basic-authentication) | `http_basic` | HTTP ベーシック認証 |
| [APIKeyAuth](../../../general-usage/http/rest-client.md#api-key-authentication) | `api_key` | クエリパラメータまたはヘッダーで定義されたキーを使用した API キー認証。 |
| [OAuth2ClientCredentials](../../../general-usage/http/rest-client.md#oauth20-authorization) | `oauth2_client_credentials` | 認可サーバーから取得した一時アクセス トークンを使用した OAuth 2.0 認可。 | -->


:::warning
アクセス トークンやその他の機密情報は必ず `secrets.toml` ファイルに保存し、バージョン管理システムにコミットしないでください。
:::

利用可能な認証タイプ:

| `type` | Authentication class | Description |
| ----------- | ------------------- | ----------- |
| `bearer` | [BearerTokenAuth](../../../general-usage/http/rest-client.md#bearer-token-authentication) | Bearer トークン認証<br/>パラメータ:<ul><li>`token` (str)</li></ul> |
| `http_basic` | [HTTPBasicAuth](../../../general-usage/http/rest-client.md#http-basic-authentication) | HTTP ベーシック認証<br/>パラメータ:<ul><li>`username` (str)</li><li>`password` (str)</li></ul> |
| `api_key` | [APIKeyAuth](../../../general-usage/http/rest-client.md#api-key-authentication) | クエリパラメータまたはヘッダーで定義されたキーを使用した API キー認証。<br/>パラメータ:<ul><li>`name` (str) - クエリパラメータまたはヘッダーの名前</li><li>`api_key` (str) - API キーの値</li><li>`location` (str, optional) - リクエスト内の API キーの場所。`query` または `header` を指定できます。デフォルトは `header` です。</li></ul> |
| `oauth2_client_credentials` | [OAuth2ClientCredentials](../../../general-usage/http/rest-client.md#oauth-20-authorization) | ユーザーの同意なしにサーバー間通信を行うための OAuth 2.0 クライアント資格情報の承認。 <br/>パラメータ:<ul><li>`access_token` (str, optional) - 一時トークン。通常はここでは指定しません。`client_id` と `client_secret` を交換することでサーバーから自動的に取得されるためです。デフォルトは `None` です。</li><li>`access_token_url` (str) - `access_token` を要求するURL</li><li>`client_id` (str) - アプリの識別子。通常は開発者ポータルから発行されます</li><li>`client_secret` (str) - 承認を得るためのクライアント認証情報。通常は開発者ポータル経由で発行されます。</li><li>`access_token_request_data` (dict, optional) -`client_id`、`client_secret`、`"grant_type": "client_credentials"` 以外に認可サーバーが必要とするデータを含む辞書。デフォルトは `None` です。</li><li>`default_token_expiration` (int, optional) - 一時アクセス トークンの有効期限が切れるまでの時間 (秒数)。デフォルトは 3600 です。</li><li>`session` (requests.Session, optional) - カスタムセッションオブジェクト。主にテストに使用されます</li></ul> |

より複雑な認証方法の場合は、[カスタム authentication クラス](../../../general-usage/http/rest-client.md#implementing-custom-authentication)を実装し、構成で使用することができます。

次のように登録すれば、カスタム authentication クラスに対しても、辞書設定構文が使用できます:

```py
from dlt.sources.rest_api.config_setup import register_auth

class CustomAuth(AuthConfigBase):
    pass

register_auth("custom_auth", CustomAuth)

{
    # ...
    "auth": {
        "type": "custom_auth",
        "api_key": dlt.secrets["sources.my_source.my_api_key"],
    }
}
```

### リソース関係を定義する

別のリソースに依存するリソースがある場合 (たとえば、子リソースを取得するために必要な ID を取得するには親リソースを取得する必要があるような場合)、特別なプレースホルダーを使用して親リソース内のフィールドを参照できます。
これにより、子リソース内の 1 つ以上の[パス](#via-request-path)、[クエリ文字列](#via-query-string-parameters)、または [JSON 本文](#via-json-body)パラメータを親リソースのデータ内のフィールドにリンクできます。

#### リクエストパスを通して

GitHub の例では、`issue_comments` リソースは `issues` リソースに依存しています。`resources.issues.number` プレースホルダーは、`issues` リソース データの `number` フィールドを現在のリクエストのパス パラメータにリンクします。

```py
{
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "issues",
                # ...
            },
        },
        {
            "name": "issue_comments",
            "endpoint": {
                "path": "issues/{resources.issues.number}/comments",
            },
            "include_from_parent": ["id"],
        },
    ],
}
```

この構成は、ソースに `issues` リソース データから issue 番号を取得し、それを使用して各 issue 番号のコメントを取得するように指示します。したがって、各 issue 項目について、`"{resources.issues.number}"` はリクエスト パス内の issue 番号に置き換えられます。
たとえば、`issues`リソースが次のデータを生成する場合:

```json
[
    {"id": 1, "number": 123},
    {"id": 2, "number": 124},
    {"id": 3, "number": 125}
]
```

`issue_comments`リソースは次のエンドポイントにリクエストを送信します:

- `issues/123/comments`
- `issues/124/comments`
- `issues/125/comments`

プレースホルダーの構文は `resources.<parent_resource_name>.<field_name>` です。

#### クエリ文字列パラメータを通して

プレースホルダ構文は、クエリ文字列パラメータでも使用できます。たとえば、ブログ投稿 (`/posts` 経由) とそのコメント (`/comments?post_id=<post_id>` 経由) を取得できる API では、リソース `posts` と、`posts` リソースに依存するリソース `post_comments` を定義できます。その後、`post_comments` リソースで `posts` リソースの `id` フィールドを参照できます:

```py
{
    "resources": [
        "posts",
        {
            "name": "post_comments",
            "endpoint": {
                "path": "comments",
                "params": {
                    "post_id": "{resources.posts.id}",
                },
            },
        },
    ],
}
```

上記の GitHub の例と同様に、`posts` リソースから次のデータが生成される場合:

```json
[
    {"id": 1, "title": "Post 1"},
    {"id": 2, "title": "Post 2"},
    {"id": 3, "title": "Post 3"}
]
```

`post_comments`リソースは次のエンドポイントにリクエストを送信します:

- `comments?post_id=1`
- `comments?post_id=2`
- `comments?post_id=3`

#### JSON本文を通して

多くの API では、リクエスト パスやクエリ パラメータではなく、POST リクエストの JSON 本文を通じて複雑なクエリや構成を送信できます。たとえば、複数のフィルターと設定をサポートする架空の `/search` エンドポイントを考えてみましょう。各投稿の `id` を持つ親リソース `posts` と、`id` を使用してカスタム検索を実行する 2 番目のリソース `post_details` があるとします。

以下の例では、JSON 本文の `posts` リソースの `id` フィールドをプレースホルダー経由で参照しています:

```py
{
    "resources": [
        "posts",
        {
            "name": "post_details",
            "endpoint": {
                "path": "search",
                "method": "POST",
                "json": {
                    "filters": {
                        "id": "{resources.posts.id}",
                    },
                    "order": "desc",
                    "limit": 5,
                }
            },
        },
    ],
}
```


#### レガシー構文: パラメータ設定の `resolve` フィールド

:::warning
`resolve` はパスパラメータに対してのみ機能します。新しいプレースホルダ構文はより柔軟であり、新しい構成が推奨されます。
:::

リソース関係を定義する従来の代替方法は、パラメータ設定で `resolve` フィールドを使用することです。
以下は、上記と同じ `resolve` フィールドを使用する例です:

```py
{
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "issues",
                # ...
            },
        },
        {
            "name": "issue_comments",
            "endpoint": {
                "path": "issues/{issue_number}/comments",
                "params": {
                    "issue_number": {
                        "type": "resolve",
                        "resource": "issues",
                        "field": "number",
                    }
                },
            },
            "include_from_parent": ["id"],
        },
    ],
}
```

パラメータ設定の`resolve`フィールドの構文は:

```py
{
    "<parameter_name>": {
        "type": "resolve",
        "resource": "<parent_resource_name>",
        "field": "<parent_resource_field_name_or_jsonpath>",
    }
}
```

`field` 値を [JSONPath](https://github.com/h2non/jsonpath-ng?tab=readme-ov-file#jsonpath-syntax) として指定して、親リソース データ内のネストされたフィールドを選択できます。例: `"field": "items[0].id"`。


#### 親リソースから複数のパスパラメータを解決

子リソースが単一の親リソースの複数のフィールドに依存する場合、エンドポイント構成で複数の `resolve` パラメータを定義できます。たとえば:

```py
{
    "resources": [
        "groups",
        {
            "name": "users",
            "endpoint": {
                "path": "groups/{group_id}/users",
                "params": {
                    "group_id": {
                        "type": "resolve",
                        "resource": "groups",
                        "field": "id",
                    },
                },
            },
        },
        {
            "name": "user_details",
            "endpoint": {
                "path": "groups/{group_id}/users/{user_id}/details",
                "params": {
                    "group_id": {
                        "type": "resolve",
                        "resource": "users",
                        "field": "group_id",
                    },
                    "user_id": {
                        "type": "resolve",
                        "resource": "users",
                        "field": "id",
                    },
                },
            },
        },
    ],
}
```

上記の構成では:

- `users` リソースは `groups` リソースに依存し、`groups` の `id` フィールドから `group_id` パラメータを解決します。
- `user_details` リソースは `users` リソースに依存し、`users` のフィールドから `group_id` と `user_id` の両方のパラメータを解決します。

#### 親リソースのフィールドを含める

リソース設定の `include_from_parent` フィールドを使用すると、親リソースのデータを子リソースに含めることができます。たとえば:

```py
{
    "name": "issue_comments",
    "endpoint": {
        ...
    },
    "include_from_parent": ["id", "title", "created_at"],
}
```

これにより、`issues` リソースの `id`、`title`、および `created_at` フィールドが `issue_comments` リソース データに含まれます。含まれるフィールドの名前には、親リソース名とアンダースコア (`_`) がプレフィックスとして付けられます (例: `_issues_id`、`_issues_title`、`_issues_created_at`)。

### REST エンドポイントではないリソースを定義する

場合によっては、別のエンドポイントによって返されない特定の値を持つエンドポイントを要求したいことがあります。
したがって、すべてのパスに対してリソースを定義する代わりに、`RESTAPIConfig` に任意の dlt リソースを含めることもできます。

次の例では、3 つのリポジトリに属する​​ issue をロードします。
パス `dlt-hub/dlt/issues/`、`dlt-hub/verified-sources/issues/`、`dlt-hub/dlthub-education/issues/` ごとに 1 つずつ、3 つの異なる issue リソースを定義する代わりに、依存リソース `issues` によって取得されるリポジトリ名のリストを生成するリソース `repositories` を使用します。

```py
from dlt.sources.rest_api import RESTAPIConfig

@dlt.resource()
def repositories() -> Generator[List[Dict[str, Any]], Any, Any]:
    """A seed list of repositories to fetch"""
    yield [{"name": "dlt"}, {"name": "verified-sources"}, {"name": "dlthub-education"}]


config: RESTAPIConfig = {
    "client": {"base_url": "https://github.com/api/v2"},
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "dlt-hub/{repository}/issues/",
                "params": {
                    "repository": {
                        "type": "resolve",
                        "resource": "repositories",
                        "field": "name",
                    },
                },
            },
        },
        repositories(),
    ],
}
```

親リソースは `Generator[List[Dict[str, Any]]]` を返す必要があることに注意してください。したがって、以下は機能しません:

```py
@dlt.resource
def repositories() -> Generator[Dict[str, Any], Any, Any]:
    """Not working seed list of repositories to fetch"""
    yield from [{"name": "dlt"}, {"name": "verified-sources"}, {"name": "dlthub-education"}]
```

### 処理手順: データのフィルタリングと変換

リソース構成の `processing_steps` フィールドを使用すると、API から取得したデータを宛先にロードする前に変換を適用できます。これは、特定のレコードをフィルター処理したり、データ構造を変更したり、機密情報を匿名化したりする必要がある場合に便利です。

各処理ステップは、操作のタイプ (`filter` または `map`) と適用する関数を指定する辞書です。ステップはリストされている順序で適用されます。

#### 簡単な例

```py
def lower_title(record):
    record["title"] = record["title"].lower()
    return record

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.example.com",
    },
    "resources": [
        {
            "name": "posts",
            "processing_steps": [
                {"filter": lambda x: x["id"] < 10},
                {"map": lower_title},
            ],
        },
    ],
}
```

上記の例では:

- まず、`filter` ステップでは、ラムダ関数を使用して、`id` が 10 未満のレコードのみを含めます。
- その後、`map` ステップは残りの各レコードに `lower_title` 関数を適用します。

#### `filter` の使用

`filter` ステップを使用すると、特定の基準を満たさないレコードを除外できます。提供された関数は、レコードを保持する場合は `True` を返し、除外する場合は `False` を返す必要があります:

```py
{
    "name": "posts",
    "endpoint": "posts",
    "processing_steps": [
        {"filter": lambda x: x["id"] in [10, 20, 30]},
    ],
}
```

この例では、`id` が 10、20、または 30 であるレコードのみが含まれます。

#### `map` の使用

`map`ステップでは、APIから取得したレコードを変更できます。提供された関数は、レコードを引数として受け取り、変更されたレコードを返します。たとえば、`email`フィールドを匿名化するには:

```py
def anonymize_email(record):
    record["email"] = "REDACTED"
    return record

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.example.com",
    },
    "resources": [
        {
            "name": "users",
            "processing_steps": [
                {"map": anonymize_email},
            ],
        },
    ],
}
```

#### `filter` と `map` を組み合わせる

複数の処理ステップを組み合わせて複雑な変換を実現できます:

```py
{
    "name": "posts",
    "endpoint": "posts",
    "processing_steps": [
        {"filter": lambda x: x["id"] < 10},
        {"map": lower_title},
        {"filter": lambda x: "important" in x["title"]},
    ],
}
```

:::tip
#### ベストプラクティス

1. 順序は重要です: 処理手順はリストされている順序で適用されます。特に `map` と `filter` を組み合わせる場合は、順序に注意してください。
2. 関数定義: 明確さと再利用のために、フィルター関数とマップ関数を個別に定義します。
3. 処理する必要があるデータの量を減らすために、プロセスの早い段階で `filter` を使用してレコードを除外します。
4. 連続する `map` ステップを 1 つの関数に結合して、実行を高速化します。
:::

## インクリメンタルなローディング

一部の API では、新しいデータまたは変更されたデータのみを取得する方法が提供されています (ほとんどの場合、`updated_at`、`created_at` などのタイムスタンプ フィールドや増分 ID を使用します)。
これは [インクリメンタルなローディング](../../../general-usage/incremental-loading.md) と呼ばれ、読み込み時間と転送されるデータ量を削減できるため非常に便利です。

Let's continue with our imaginary blog API example to understand incremental loading with query parameters.

次のようなエンドポイント「https://api.example.com/posts」があるとします:

1. 特定の日付以降に作成された投稿を取得するために、`created_since` クエリ パラメータを受け入れます。
2. 各投稿の `created_at` フィールドを含む投稿のリストを返します。

たとえば、エンドポイントを `https://api.example.com/posts?created_since=2024-01-25` でクエリすると、次の応答が返されます:

```json
{
    "results": [
        {"id": 1, "title": "Post 1", "created_at": "2024-01-26"},
        {"id": 2, "title": "Post 2", "created_at": "2024-01-27"},
        {"id": 3, "title": "Post 3", "created_at": "2024-01-28"}
    ]
}
```

When the API endpoint supports incremental loading, you can configure dlt to load only the new or changed data using these three methods:

1. Using [placeholders for incremental loading](#using-placeholders-for-incremental-loading)
2. Defining a special parameter in the `params` section of the [endpoint configuration](#endpoint-configuration) (DEPRECATED)
3. Using the `incremental` field in the [endpoint configuration](#endpoint-configuration) with the `start_param` field (DEPRECATED)

:::caution
The last two methods are deprecated and will be removed in a future dlt version.
:::

### Using placeholders for incremental loading

The most flexible way to configure incremental loading is to use placeholders in the request configuration along with the `incremental` section.
Here's how it works:

1. Define the `incremental` section in the [endpoint configuration](#endpoint-configuration) to specify the cursor path (where to find the incremental value in the response) and initial value (the value to start the incremental loading from).
2. Use the placeholder `{incremental.start_value}` in the request configuration to reference the incremental value.

Let's take the example from the previous section and configure it using placeholders:

```py
{
    "path": "posts",
    "data_selector": "results",
    "params": {
        "created_since": "{incremental.start_value}",  # Uses cursor value in query parameter
    },
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25T00:00:00Z",
    },
}
```

When you first run this pipeline, dlt will:
1. Replace `{incremental.start_value}` with `2024-01-25T00:00:00Z` (the initial value)
2. Make a GET request to `https://api.example.com/posts?created_since=2024-01-25T00:00:00Z`
3. Parse the response (e.g., posts with created_at values like "2024-01-26", "2024-01-27", "2024-01-28")
4. Track the maximum value found in the "created_at" field (in this case, "2024-01-28")

On the next pipeline run, dlt will:
1. Replace `{incremental.start_value}` with "2024-01-28" (the last seen maximum value)
2. Make a GET request to `https://api.example.com/posts?created_since=2024-01-28`
3. The API will only return posts created on or after January 28th

Let's break down the configuration:
1. We explicitly set `data_selector` to `"results"` to select the list of posts from the response. This is optional; if not set, dlt will try to auto-detect the data location.
2. We define the `created_since` parameter in `params` section and use the placeholder `{incremental.start_value}` to reference the incremental value.

Placeholders are versatile and can be used in various request components. Here are some examples:

#### In JSON body (for POST requests)

If the API lets you filter the data by a range of dates (e.g. `fromDate` and `toDate`), you can use the placeholder in the JSON body:

```py
{
    "path": "posts/search",
    "method": "POST",
    "json": {
        "filters": {
            "fromDate": "{incremental.start_value}",  # In JSON body
            "toDate": "2024-03-25"
        },
        "limit": 1000
    },
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25T00:00:00Z",
    },
}
```

#### In path parameters

Some APIs use path parameters to filter the data:

```py
{
    "path": "posts/since/{incremental.start_value}/list",  # In URL path
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25",
    },
}
```

#### In request headers

It's not so common, but you can also use placeholders in the request headers:

```py
{
    "path": "posts",
    "headers": {
        "X-Since-Timestamp": "{incremental.start_value}"  # In custom header
    },
    "incremental": {
        "cursor_path": "created_at",
        "initial_value": "2024-01-25T00:00:00Z",
    },
}
```

You can also use different placeholder variants depending on your needs:

| Placeholder | Description |
| ----------- | ----------- |
| `{incremental.start_value}` | The value to use as the starting point for this request (either the initial value or the last tracked maximum value) |
| `{incremental.initial_value}` | Always uses the initial value specified in the configuration |
| `{incremental.last_value}` | The last seen value (same as start_value in most cases, see the [incremental loading](../../../general-usage/incremental/cursor.md) guide for more details) |
| `{incremental.end_value}` | The end value if specified in the configuration |


### Legacy method: Incremental loading in `params` (DEPRECATED)

:::caution
DEPRECATED: This method is deprecated and will be removed in a future version. Use the [placeholder method](#using-placeholders-for-incremental-loading) instead.
:::

:::note
This method only works for query string parameters. For other request parts (path, JSON body, headers), use the [placeholder method](#using-placeholders-for-incremental-loading).
:::

For query string parameters, you can also specify incremental loading directly in the `params` section:

```py
{
    "path": "posts",
    "data_selector": "results",  # Optional JSONPath to select the list of posts
    "params": {
        "created_since": {
            "type": "incremental",
            "cursor_path": "created_at", # The JSONPath to the field we want to track in each post
            "initial_value": "2024-01-25",
        },
    },
}
```

Above we define the `created_since` parameter as an incremental parameter as:

```py
{
    "created_since": {
        "type": "incremental",
        "cursor_path": "created_at",
        "initial_value": "2024-01-25",
    },
}
```

The fields are:

- `type`: パラメータ定義のタイプ。この場合、`incremental` に設定する必要があります。
- `cursor_path`: リスト内の各アイテム内のフィールドへの JSONPath。このフィールドの値は、次のリクエストで使用されます。上記の例では、アイテムは `{"id": 1, "title": "Post 1", "created_at": "2024-01-26"}` のようになっているため、作成時間を追跡するには、`cursor_path` を `"created_at"` に設定します。JSONPath は、レスポンスのルートからではなく、アイテム (dict) のルートから始まることに注意してください。
- `initial_value`: カーソルの初期値。これはインクリメンタルローディングの状態を初期化する値です。この場合、`2024-01-25` です。値の型は、データ項目内のフィールドの型と一致する必要があります。

### Incremental loading using the `incremental` field (DEPRECATED)

:::caution
DEPRECATED: This method is deprecated and will be removed in a future dlt version. Use the [placeholder method](#using-placeholders-for-incremental-loading) instead.
:::

Another alternative method is to use the `incremental` field in the [endpoint configuration](#endpoint-configuration) while specifying names of the query string parameters to be used as start and end conditions.

上記と同じ例を取り上げ、`incremental`フィールドを使用して設定してみましょう:

```py
{
    "path": "posts",
    "data_selector": "results",
    "incremental": {
        "start_param": "created_since",
        "cursor_path": "created_at",
        "initial_value": "2024-01-25",
    },
}
```

`incremental`フィールドの利用可能な完全な設定は次のとおりです。:

```py
{
    "incremental": {
        "start_param": "<start_parameter_name>",
        "end_param": "<end_parameter_name>",
        "cursor_path": "<path_to_cursor_field>",
        "initial_value": "<initial_value>",
        "end_value": "<end_value>",
        "convert": my_callable,
    }
}
```

フィールドは:

- `start_param` (str): 開始条件として使用されるクエリ パラメータの名前。上記の例を使用する場合は、`"created_since"` になります。
- `end_param` (str): 終了条件として使用されるクエリ パラメータの名前。これはオプションであり、開始条件のみを追跡する必要がある場合は省略できます。これは、特定の範囲内でデータを取得する必要があり、API が終了条件 (`created_before` クエリ パラメータなど) をサポートしている場合に便利です。
- `cursor_path` (str): リスト内の各項目内のフィールドへの JSONPath。これはインクリメンタルローディングを追跡するために使用されるフィールドです。上記の例では、`"created_at"` です。
- `initial_value` (str): カーソルの初期値。これはインクリメンタルローディングの状態を初期化する値です。
- `end_value` (str): インクリメンタルローディングを停止するカーソルの終了値。これはオプションであり、開始条件のみを追跡する必要がある場合は省略できます。このフィールドを設定する場合は、`initial_value` も設定する必要があります。
- `convert` (callable): カーソル値をクエリ パラメータに必要な形式に変換する呼び出し可能オブジェクト。たとえば、UNIX タイムスタンプを ISO 8601 の日付に変換したり、日付を `created_at+gt+{date}` に変換したりできます。

詳細については、[インクリメンタルローディング](../../../general-usage/incremental/cursor.md)ガイドを参照してください。

インクリメンタルローディングで問題が発生した場合は、インクリメンタルローディングガイドの[トラブルシューティング セクション](../../../general-usage/incremental/troubleshooting.md)を参照してください。

### APIを呼び出す前に増分値を変換する

カーソル フィールドの値を API エンドポイントに渡す前に変換する必要がある場合は、キー `convert` で呼び出し可能関数を指定できます。たとえば、API は UNIX エポック タイムスタンプを返す可能性がありますが、ISO 8601 日付でクエリされることを想定しています。これを実現するには、API によって返される日付形式を API リクエストに必要な日付形式に変換する関数を指定できます。

次の例では、フィールド `updated_at` で API から `1704067200` が返されますが、API は `?created_since=2024-01-01` で呼び出されます。

`params` フィールドを使用したインクリメンタルローディング:
```py
{
    "created_since": {
        "type": "incremental",
        "cursor_path": "updated_at",
        "initial_value": "1704067200",
        "convert": lambda epoch: pendulum.from_timestamp(int(epoch)).to_date_string(),
    }
}
```

`incremental` フィールドを使用したインクリメンタルロード:

```py
{
    "path": "posts",
    "data_selector": "results",
    "incremental": {
        "start_param": "created_since",
        "cursor_path": "updated_at",
        "initial_value": "1704067200",
        "convert": lambda epoch: pendulum.from_timestamp(int(epoch)).to_date_string(),
    },
}
```

## トラブルシューティング

パイプラインの実行中に問題が発生した場合は、[ログ記録](../../../running-in-production/running.md#set-the-log-level-and-format)を有効にして、実行に関する詳細情報を取得します。:

```sh
RUNTIME__LOG_LEVEL=INFO python my_script.py
```

これには、HTTP リクエストの詳細も提供されます。

### 設定の課題

#### 検証エラーが発生する

パイプラインを実行していて `DictValidationException` が発生した場合は、[ソース構成](#source-configuration) が正しくないことを意味します。エラー メッセージには、フィールドへのパスや予想されるタイプなど、問題の詳細が示されます。

たとえば、次のようなソース構成の場合:

```py
config: RESTAPIConfig = {
    "client": {
        # ...
    },
    "resources": [
        {
            "name": "issues",
            "params": {             # <- Wrong: this should be inside
                "sort": "updated",  #    the endpoint field below
            },
            "endpoint": {
                "path": "issues",
                # "params": {       # <- Correct configuration
                #     "sort": "updated",
                # },
            },
        },
        # ...
    ],
}
```

次のようなエラーが表示されます:

```sh
dlt.common.exceptions.DictValidationException: In path .: field 'resources[0]'
expects the following types: str, EndpointResource. Provided value {'name': 'issues', 'params': {'sort': 'updated'},
'endpoint': {'path': 'issues', ... }} with type 'dict' is invalid with the following errors:
For EndpointResource: In path ./resources[0]: following fields are unexpected {'params'}
```

これは、最初のリソース構成 (`resources[0]`) では、`params` フィールドが `endpoint` フィールド内にある必要があることを意味します。

:::tip
`rest_api` モジュールから `RESTAPIConfig` タイプをインポートして、エディター/IDE で便利なヒントを取得し、それを使用して構成オブジェクトを定義します。

```py
from dlt.sources.rest_api import RESTAPIConfig
```
:::

#### 間違ったデータやデータがない

エンドポイントから間違ったデータを受信した場合は、[エンドポイント構成](#endpoint-configuration) の `data_selector` フィールドを確認してください。JSONPath が正確であり、応答本文の正しいデータを指していることを確認してください。`rest_api` はデータの場所を自動検出しようとしますが、必ずしも成功するとは限りません。詳細については、[データ選択](#data-selection) セクションを参照してください。

#### データが不十分であるか、ページ番号が正しくありません

設定の `paginator` フィールドを確認してください。明示的に指定されていない場合、ソースはページ区切り方法を自動検出しようとします。自動検出が失敗した場合、またはシステムが不明な場合は、警告が記録されます。実稼働環境では、設定で明示的にページ区切りを指定することをお勧めします。詳細については、[ページネーション](#pagination)のセクションを参照してください。一部の API には非標準のページ区切り方法がある場合があり、[カスタムページ区切り](../../../general-usage/http/rest-client.md#implementing-a-custom-paginator)を実装する必要がある場合があります。

#### インクリメンタルローディングが機能しない

インクリメンタルなローディングの問題については、[トラブルシューティング ガイド](../../../general-usage/incremental/troubleshooting.md)を参照してください。

#### HTTP 404 エラーが発生する

一部の API は、存在しないリソースやデータがないリソースに対して 404 エラーを返す場合があります。これらの応答を管理するには、[応答アクション](./advanced#response-actions)で `ignore` アクションを設定します。

### 認証の問題

401（Unauthorized）エラーが発生した場合、これは次のことを示している可能性があります:

- 認証資格情報が正しくありません。`secrets.toml` 内の資格情報を確認してください。詳細については、[シークレットと構成](../../../general-usage/credentials/setup#troubleshoot-configuration-errors)を参照してください。
- 認証タイプが正しくありません。適切な方法については、API ドキュメントを参照してください。詳細については、[認証](#authentication) セクションを参照してください。一部の API では、[カスタム認証方法](../../../general-usage/http/rest-client.md#custom-authentication) が必要になる場合があります。

### 一般的なガイドライン

`rest_api` ソースは、HTTP リクエストで [RESTClient](../../../general-usage/http/rest-client.md) クラスを使用します。デバッグのヒントについては、RESTClient [トラブルシューティング ガイド](../../../general-usage/http/rest-client.md#troubleshooting) を参照してください。

さらにサポートが必要な場合は、[Slack コミュニティ](https://dlthub.com/community) にご参加ください。喜んでお手伝いいたします!

