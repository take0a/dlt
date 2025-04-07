---
title: RESTClient
description: Learn how to use the RESTClient class to interact with RESTful APIs
keywords: [api, http, rest, request, extract, restclient, client, pagination, json, response, data_selector, session, auth, paginator, JSONLinkPaginator, headerlinkpaginator, offsetpaginator, jsonresponsecursorpaginator, queryparampaginator, bearer, token, authentication, headercursorpaginator]
---

`RESTClient`クラスは、RESTful APIと対話するためのインターフェースを提供し、次のような機能が含まれています:
- 自動ページネーション、
- さまざまな認証メカニズム、
- カスタマイズ可能なリクエスト/レスポンス処理。

このガイドでは、ページ分割された API 応答からデータを取得するための `paginate()` メソッドに焦点を当て、`RESTClient` クラスを使用して API からデータを読み取る方法を説明します。

## RESTClient インスタンスの作成

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth
from dlt.sources.helpers.rest_client.paginators import JSONLinkPaginator

client = RESTClient(
    base_url="https://api.example.com",
    headers={"User-Agent": "MyApp/1.0"},
    auth=BearerTokenAuth(token="your_access_token_here"),  # type: ignore
    paginator=JSONLinkPaginator(next_url_path="pagination.next"),
    data_selector="data",
    session=MyCustomSession()
)
```

`RESTClient`クラスは次のパラメータで初期化されます:

- `base_url`: API のルート URL。すべてのリクエストはこの URL を基準にして行われます。
- `headers`: すべてのリクエストに含めるデフォルトのヘッダー。これを使用して、`User-Agent` などの共通ヘッダーやその他のカスタム ヘッダーを設定できます。
- `auth`: 認証構成。詳細については、[認証](#authentication)セクションを参照してください。
- `paginator`: ページ分割されたレスポンスを処理するためのページネーター インスタンス。以下の [ページネーター](#paginators) セクションを参照してください。
- `data_selector`: 応答からデータを抽出するための [JSONPath セレクター](https://github.com/h2non/jsonpath-ng?tab=readme-ov-file#jsonpath-syntax)。これは、応答 JSON からデータを抽出する方法を定義します。ページ分割時にのみ使用されます。
- `session`: リクエストを行うためのオプションのセッション。これは、クライアントのカスタム リクエスト動作を設定するために使用できる [リクエスト セッション](https://requests.readthedocs.io/en/latest/api/#requests.Session) インスタンスである必要があります。

## 基本的なリクエストを行う

基本的なGETおよびPOSTリクエストを実行するには、それぞれ`get()`および`post()`メソッドを使用します。これは、`requests`ライブラリの動作に似ています:

```py
client = RESTClient(base_url="https://api.example.com")
response = client.get("/posts/1")
```

## API レスポンスのページ分割

`RESTClient.paginate()`メソッドは、ページ区切りのレスポンスを処理するために特別に設計されており、各ページの`PageData`インスタンスを生成します。:

```py
for page in client.paginate("/posts"):
    print(page)
```

:::tip
`paginator` が指定されていない場合、`paginate()` メソッドは API が使用するページ区切りメカニズムを自動的に検出しようとします。API がレスポンスのヘッダーまたは JSON 本文に `next` リンクを持つなどの標準のページ区切りメカニズムを使用する場合、`paginate()` メソッドはこれを自動的に処理します。それ以外の場合は、ページ区切りオブジェクトを明示的に指定するか、カスタム ページ区切りを実装できます。
:::

### 応答からデータを選択する

API レスポンスをページ分割する場合、`RESTClient` はレスポンスからデータを自動的に抽出しようとします。ただし、レスポンス JSON からデータを抽出する方法を明示的に指定する必要がある場合もあります。

`RESTClient` クラスの `data_selector` パラメータまたは `paginate()` メソッドを使用して、クライアントにデータの抽出方法を指示します。
`data_selector` は、抽出するデータを含む JSON 内のキーを指す [JSONPath](https://github.com/h2non/jsonpath-ng?tab=readme-ov-file#jsonpath-syntax) 式です。

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

応答から投稿のリストを抽出するには、`data_selector` を `"posts"` に設定する必要があります。

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

`data_selector` は `"results.posts"` に設定する必要があります。セレクターの記述方法については、[JSONPath 構文](https://github.com/h2non/jsonpath-ng?tab=readme-ov-file#jsonpath-syntax) の詳細をご覧ください。

### PageData

各 `PageData` インスタンスには、1 つのページのデータと、元のリクエストやレスポンス オブジェクトなどのコンテキストが含まれており、詳細な検査が可能です。`PageData` は、次の属性を含むリストのようなオブジェクトです:

- `request`: 元のリクエストオブジェクト。
- `response`: 応答オブジェクト。
- `paginator`: 応答をページ分割するために使用されるページネーター オブジェクト。
- `auth`: リクエストに使用される認証オブジェクト。

### Paginators

ページネーターはページ区切りのレスポンスを処理するために使用されます。`RESTClient`クラスには、一般的なページ区切りメカニズム用の組み込みの Paginator が付属しています。:

- [JSONLinkPaginator](#JSONLinkPaginator) - 次のページへのリンクが JSON 応答に含まれる。
- [HeaderLinkPaginator](#headerlinkpaginator) - 次のページへのリンクがレスポンスヘッダーに含まれる。
- [OffsetPaginator](#offsetpaginator) - オフセットと制限クエリパラメータに基づくページング。
- [PageNumberPaginator](#pagenumberpaginator) - ページ番号に基づいたページング。
- [JSONResponseCursorPaginator](#jsonresponsecursorpaginator) - JSON 応答内のカーソルに基づいたページング。
- [HeaderCursorPaginator](#headercursorpaginator) - 応答ヘッダー内のカーソルに基づいたページング。

API が非標準のページネーションを使用する場合は、`BasePaginator` クラスをサブクラス化することで [カスタム ページネーターを実装](#implementing-a-custom-paginator) できます。

#### JSONLinkPaginator

`JSONLinkPaginator` は、レスポンスの JSON 本文に次のページの URL が含まれている API 用に設計されています。このページネーターは JSONPath を使用して、JSON レスポンス内で次のページの URL を見つけます。

**パラメータ:**

- `next_url_path`: 次のページの URL を含む JSON 応答内のキーを指す JSONPath 文字列。

**例:**

`https://api.example.com/posts`のAPIレスポンスが次のようになるとします:

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

このレスポンスをページ分割するには、`next_url_path` を `"pagination.next"` に設定した `JSONLinkPaginator` を使用します:

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import JSONLinkPaginator

client = RESTClient(
    base_url="https://api.example.com",
    paginator=JSONLinkPaginator(next_url_path="pagination.next")
)

@dlt.resource
def get_data():
    for page in client.paginate("/posts"):
        yield page
```

#### HeaderLinkPaginator

このページネーターは、レスポンス ヘッダー内の次のページへのリンク (GitHub API で使用される `Link` ヘッダーなど) に基づいてページ区切りを処理します。

**パラメータ:**

- `links_next_key`: リンクヘッダーで次のページのリンクを識別する関係タイプ (rel)。デフォルトは「next」です。

注: 通常、このページネーターは API が `Link` ヘッダーを返すときに自動的に使用されるため、明示的に指定する必要はありません。まれに、API が異なるリレーション タイプを使用する場合にページネーターを指定する必要がある場合があります。

#### OffsetPaginator

`OffsetPaginator` は、クエリ パラメータ内のオフセットと制限に基づいてページ区切りを処理します。

**パラメータ:**

- `limit`: 各リクエストで取得するアイテムの最大数。
- `offset`: 最初のリクエストの初期オフセット。デフォルトは `0` です。
- `offset_param`: オフセットを指定するために使用されるクエリ パラメータの名前。デフォルトは `"offset"` です。
- `limit_param`: 制限を指定するために使用されるクエリ パラメータの名前。デフォルトは `"limit"` です。
- `total_path`: アイテムの合計数を表す JSONPath 式。指定しない場合、ページ区切りは `maximum_offset` と `stop_after_empty_page` によって制御されます。
- `maximum_offset`: オプションの最大オフセット値。合計数がなくてもページ区切りを制限します。
- `stop_after_empty_page`: ページに結果項目が含まれていない場合にページ区切りを停止するかどうか。デフォルトは `True` です。

**例:**

API エンドポイント `https://api.example.com/items` が `offset` および `limit` パラメータによるページ区切りをサポートしていると仮定します。
たとえば、`https://api.example.com/items?offset=0&limit=100`、`https://api.example.com/items?offset=100&limit=100` などであり、応答に合計数が含まれます。例:

```json
{
  "items": ["one", "two", "three"],
  "total": 1000
}
```

`OffsetPaginator` を使用して、この API からの応答をページ分割できます。

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=OffsetPaginator(
        limit=100,
        total_path="total"
    )
)
```

ページにレコードが含まれていない場合、ページ区切りはデフォルトで停止します。これは、API が合計アイテム数を提供しない場合に特に便利です。
ここでは、API が合計数を提供しないため、`total_path` パラメータは `None` に設定されています。

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=OffsetPaginator(
        limit=100,
        total_path=None,
    )
)
```

さらに、開発中などに`maximum_offset`でページ区切りを制限することもできます。最初の空のページが表示される前に`maximum_offset`に達すると、ページ区切りが停止します。:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=OffsetPaginator(
        limit=10,
        maximum_offset=20,  # limits response to 20 records
        total_path=None,
    )
)
```

`stop_after_empty_page = False` を設定することで、ページネーションの自動停止を無効にすることができます。この場合、ページネーターが終了することを保証するために、`total_path` または `maximum_offset` のいずれかを指定する必要があります。

#### PageNumberPaginator

`PageNumberPaginator` は、リクエストごとにページ番号を増やすことで機能します。

**パラメータ:**

- `base_page`: API の観点から見た初期ページのインデックス。通常、ページのインデックスは 0 ベースまたは 1 ベース (例: 1、2、3、...) です。デフォルトは 0 です。
- `page`: 最初のリクエストのページ番号。指定しない場合は、初期値は `base_page` に設定されます。
- `page_param`: ページ番号のクエリ パラメータ名。デフォルトは `"page"` です。
- `total_path`: 合計ページ数の JSONPath 式。指定しない場合、ページ区切りは `maximum_page` と `stop_after_empty_page` によって制御されます。
- `maximum_page`: オプションの最大ページ番号。このページに到達するとページ区切りが停止します。
- `stop_after_empty_page`: ページに結果項目が含まれていない場合にページ区切りを停止するかどうか。デフォルトは `True` です。

**例:**

API エンドポイント `https://api.example.com/items` がページ番号でページ分割し、応答で合計ページ数を提供すると仮定します。例:

```json
{
  "items": ["one", "two", "three"],
  "total_pages": 10
}
```

`PageNumberPaginator` を使用して、この API からの応答をページ分割できます:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=PageNumberPaginator(
        total_path="total_pages"  # Uses the total page count from the API
    )
)
```

ページにレコードが含まれていない場合、ページ区切りはデフォルトで停止します。これは、API が合計アイテム数を提供しない場合に特に便利です。
ここでは、API が合計数を提供しないため、`total_path` パラメータは `None` に設定されています。

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=PageNumberPaginator(
        total_path=None
    )
)
```

さらに、開発中などに `maximum_page` を使用してページ区切りを制限することもできます。最初の空のページが表示される前に `maximum_page` に達すると、ページ区切りが停止します:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=PageNumberPaginator(
        maximum_page=2,  # Limits response to 2 pages
        total_path=None
    )
)
```

`stop_after_empty_page = False` を設定することで、ページネーションの自動停止を無効にすることができます。この場合、ページネーターが終了することを保証するために、`total_path` または `maximum_page` のいずれかを指定する必要があります。

#### JSONResponseCursorPaginator

`JSONResponseCursorPaginator` は、JSON レスポンス内のカーソルに基づいてページ区切りを処理します。

**パラメータ:**

- `cursor_path`: JSON 応答内のカーソルを指す JSONPath 式。このカーソルは後続のページを取得するために使用されます。デフォルトは `"cursors.next"` です。
- `cursor_param`: The query parameter used to send the cursor value in the next request. Defaults to `"cursor"` if neither `cursor_param` nor `cursor_body_path` is provided.
- `cursor_body_path`: A JSONPath expression specifying where to place the cursor in the request JSON body. Use this instead of `cursor_param` when sending the cursor in the request body.

Note: You must provide either `cursor_param` or `cursor_body_path`, but not both. If neither is provided, `cursor_param` will default to `"cursor"`.

**例:**

次のページへのカーソルがレスポンスに含まれる構造を返す API エンドポイント `https://api.example.com/data` について考えてみましょう:

```json
{
  "items": ["one", "two", "three"],
  "cursors": {
    "next": "cursor_string_for_next_page"
  }
}
```

To paginate through responses from this API using GET requests with query parameters, use `JSONResponseCursorPaginator` with `cursor_path` and `cursor_param`:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=JSONResponseCursorPaginator(
        cursor_path="cursors.next",
        cursor_param="cursor"
    )
)
```

For requests with a JSON body, you can specify where to place the cursor in the request body using the `cursor_body_path` parameter:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=JSONResponseCursorPaginator(
        cursor_path="nextPageToken",
        cursor_body_path="nextPageToken"  # Adds cursor to root of JSON body
    )
)

# For nested placement in JSON body
client = RESTClient(
    base_url="https://api.example.com",
    paginator=JSONResponseCursorPaginator(
        cursor_path="meta.nextToken",
        cursor_body_path="pagination.cursor"  # Will create {"pagination": {"cursor": "token_value"}}
    )
)

@dlt.resource
def get_data():
    for page in client.paginate("/search", method="POST", json={"query": "example"}):
        yield page
```

#### HeaderCursorPaginator

`HeaderCursorPaginator` は、応答ヘッダー内のカーソルに基づいてページ区切りを処理します。

**パラメータ:**

- `cursor_key`: カーソル値を含む応答ヘッダー内のキー。デフォルトは `"next"` です。
- `cursor_param`: 次のリクエストでカーソル値を送信するために使用されるクエリ パラメータ。デフォルトは `"cursor"` です。

**例:**

次のページのカーソルを含む `NextPageToken` ヘッダーを含むレスポンスを返す API エンドポイント `https://api.example.com/items` を考えてみましょう:

```text
Content-Type: application/json
NextPageToken: n3xtp4g3

[
    {"id": 1, "name": "item1"},
    {"id": 2, "name": "item2"},
    ...
]
```

この API からの応答をページ分割するには、`cursor_key` を `"NextPageToken"` に設定した `HeaderCursorPaginator` を使用します:

```py
client = RESTClient(
    base_url="https://api.example.com",
    paginator=HeaderCursorPaginator(cursor_key="NextPageToken")
)
```

### カスタムページネーターの実装

非標準のページネーション スキームを使用する API を使用する場合、またはページネーション プロセスをより細かく制御する必要がある場合は、`BasePaginator` クラスをサブクラス化し、`init_request`、`update_state`、および `update_request` メソッドを実装することで、カスタム ページネーターを実装できます。

- `init_request(request: Request) -> None`: このメソッドは、`RESTClient.paginate` メソッドで最初の API 呼び出しを行う前に呼び出されます。このメソッドを使用して、初期リクエスト クエリ パラメータ、ヘッダーなどを設定できます。たとえば、初期ページ番号やカーソル値を設定できます。

- `update_state(response: Response, data: Optional[List[Any]]) -> None`: このメソッドは、API 呼び出しの応答に基づいてページネーターの状態を更新します。通常、応答からページネーションの詳細 (次のページ参照など) を抽出し、ページネーター インスタンスに保存します。

- `update_request(request: Request) -> None`: `RESTClient.paginate` メソッドで次の API 呼び出しを行う前に、`update_request` を使用して、次のページを取得するために必要なパラメータでリクエストを変更します (ページネーターの現在の状態に基づきます)。たとえば、リクエストにクエリ パラメータを追加したり、URL を変更したりできます。

#### 例 1: クエリパラメータページネーターの作成

API がページネーションにクエリ パラメータを使用し、レスポンスで次のページへの直接リンクを提供せずに、後続の各ページのページ パラメータを増分するとします。例えば、 `https://api.example.com/posts?page=1`、`https://api.example.com/posts?page=2` など。このスキームのページネーターを実装する方法は次のとおりです:

```py
from typing import Any, List, Optional
from dlt.sources.helpers.rest_client.paginators import BasePaginator
from dlt.sources.helpers.requests import Response, Request

class QueryParamPaginator(BasePaginator):
    def __init__(self, page_param: str = "page", initial_page: int = 1):
        super().__init__()
        self.page_param = page_param
        self.page = initial_page

    def init_request(self, request: Request) -> None:
        # This will set the initial page number (e.g., page=1)
        self.update_request(request)

    def update_state(self, response: Response, data: Optional[List[Any]] = None) -> None:
        # Assuming the API returns an empty list when no more data is available
        if not response.json():
            self._has_next_page = False
        else:
            self.page += 1

    def update_request(self, request: Request) -> None:
        if request.params is None:
            request.params = {}
        request.params[self.page_param] = self.page
```

カスタム ページネーターを定義したら、クライアントの初期化中にページネーターのインスタンスをページネーター パラメーターに渡すことで、`RESTClient` で使用できます。`QueryParamPaginator` の使用方法は次のとおりです:

```py
from dlt.sources.helpers.rest_client import RESTClient

client = RESTClient(
    base_url="https://api.example.com",
    paginator=QueryParamPaginator(page_param="page", initial_page=1)
)

@dlt.resource
def get_data():
    for page in client.paginate("/data"):
        yield page
```

:::tip
dlt に同梱されている [`PageNumberPaginator`](#pagenumberpaginator) は同じことを行いますが、柔軟性とエラー処理が向上しています。この例は、カスタム ページネーターを実装する方法を示すことを目的としています。ほとんどのユースケースでは、[組み込みのページネーター](#paginators) を使用する必要があります。
:::

#### 例 2: POSTリクエストのページネーターを作成する

一部の API では、ページネーションに POST リクエストを使用します。この場合、リクエスト本文にカーソルやその他のパラメータを含む POST リクエストを送信することで、次のページが取得されます。これは、「検索」API エンドポイントや、ペイロードが大きいその他のエンドポイントでよく使用されます。このような場合にページネーターを実装する方法は次のとおりです:

```py
from typing import Any, List, Optional
from dlt.sources.helpers.rest_client.paginators import BasePaginator
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.requests import Response, Request

class PostBodyPaginator(BasePaginator):
    def __init__(self):
        super().__init__()
        self.cursor = None

    def update_state(self, response: Response, data: Optional[List[Any]] = None) -> None:
        # Assuming the API returns an empty list when no more data is available
        if not response.json():
            self._has_next_page = False
        else:
            self.cursor = response.json().get("next_page_cursor")

    def update_request(self, request: Request) -> None:
        if request.json is None:
            request.json = {}

        # Add the cursor to the request body
        request.json["cursor"] = self.cursor

client = RESTClient(
    base_url="https://api.example.com",
    paginator=PostBodyPaginator()
)

@dlt.resource
def get_data():
    for page in client.paginate("/data"):
        yield page
```

## 認証

RESTClient は、`RESTClient` と `paginate()` メソッドの両方の `auth` パラメータを通じて構成される、bearer トークン、API キー、HTTP 基本認証などのさまざまな認証戦略をサポートします。

利用可能な認証方法は、`dlt.sources.helpers.rest_client.auth`モジュールで定義されています:

- [BearerTokenAuth](#bearer-token-authentication)
- [APIKeyAuth](#api-key-authentication)
- [HttpBasicAuth](#http-basic-authentication)
- [OAuth2ClientCredentials](#oauth-20-authorization)

特定のユースケースでは、`dlt.sources.helpers.rest_client.auth` モジュールから `AuthConfigBase` クラスをサブクラス化することで、[カスタム認証を実装](#implementing-custom-authentication)できます。
OAuth 2.0 の特定のフレーバーについては、`OAuth2ClientCredentials` をサブクラス化することで [カスタム OAuth 2.0 を実装](#oauth-20-authorization) できます。

### Bearer トークン認証

Bearer トークン認証 (`BearerTokenAuth`) は、クライアントがリクエストの Authorization ヘッダーでトークンを送信する認証方法です (例: `Authorization: Bearer <token>`)。サーバーはこのトークンを検証し、トークンが有効な場合はアクセスを許可します。

**パラメータ:**

- `token`: 認証で使用する bearer トークン

**例:**

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

client = RESTClient(
    base_url="https://api.example.com",
    auth=BearerTokenAuth(token="your_access_token_here")  # type: ignore
)

for page in client.paginate("/protected/resource"):
    print(page)
```

### API キー認証

API キー認証 (`ApiKeyAuth`) は、クライアントがカスタム ヘッダー (例: `X-API-Key: <key>`、またはクエリ パラメータとして) で API キーを送信する認証方法です。

**パラメータ:**

- `name`: API キーに使用するヘッダーまたはクエリ パラメータの名前。
- `api_key`: 認証に使用する API キー。
- `location`: API キーの場所 (`header` または `query`)。デフォルトは "header" です。

**例:**

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import APIKeyAuth

auth = APIKeyAuth(name="X-API-Key", api_key="your_api_key_here", location="header")  # type: ignore

# Create a RESTClient instance with API Key Authentication
client = RESTClient(base_url="https://api.example.com", auth=auth)

response = client.get("/protected/resource")
```

### HTTP 基本認証

HTTP 基本認証は、HTTP プロトコルに組み込まれたシンプルな認証スキームです。Authorization ヘッダーにエンコードされたユーザー名とパスワードを送信します。

**パラメータ:**

- `username`: 基本認証のユーザー名。
- `password`: 基本認証のパスワード。

**例:**

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth

auth = HttpBasicAuth(username="your_username", password="your_password")  # type: ignore
client = RESTClient(base_url="https://api.example.com", auth=auth)

response = client.get("/protected/resource")
```

### OAuth 2.0 認証

OAuth 2.0 は、認可のための一般的なプロトコルです。エンド ユーザー (リソース所有者) が承認を与える必要がないため、サーバー間認可に使用される 2 レッグ認可を実装しました。
REST クライアントは OAuth クライアントとして機能し、認可サーバーから一時的なアクセス トークンを取得します。このアクセス トークンは、保護されたコンテンツにアクセスするためにリソース サーバーに送信されます。アクセス トークンの有効期限が切れると、OAuth クライアントは自動的に更新します。

残念ながら、ほとんどの OAuth 2.0 実装は異なるため、対話する特定の認可サーバーの要件に合わせて `OAuth2ClientCredentials` をサブクラス化し、`build_access_token_request()` を実装する必要がある場合があります。

**パラメータ:**
- `access_token_url`: 一時アクセストークンを取得するための URL。
- `client_id`: 承認を取得するためのクライアント識別子。通常は開発者ポータル経由で発行されます。
- `client_secret`: 承認を取得するためのクライアント資格情報。通常は開発者ポータル経由で発行されます。
- `access_token_request_data`: `client_id`、`client_secret`、および `"grant_type": "client_credentials"` 以外に認可サーバーが必要とするデータを含む辞書。デフォルトは `None` です。
- `default_token_expiration`: 一時アクセス トークンの有効期限が切れるまでの時間 (秒数)。デフォルトは 3600 です。

**例:**

```py
from base64 import b64encode
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import OAuth2ClientCredentials

class OAuth2ClientCredentialsHTTPBasic(OAuth2ClientCredentials):
    """Used e.g. by Zoom Video Communications, Inc."""
    def build_access_token_request(self) -> Dict[str, Any]:
        authentication: str = b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        return {
            "headers": {
                "Authorization": f"Basic {authentication}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "data": self.access_token_request_data,
        }

oauth = OAuth2ClientCredentialsHTTPBasic(
    access_token_url=dlt.secrets["sources.zoom.access_token_url"],  # "https://zoom.us/oauth/token"
    client_id=dlt.secrets["sources.zoom.client_id"],
    client_secret=dlt.secrets["sources.zoom.client_secret"],
    access_token_request_data={
        "grant_type": "account_credentials",
        "account_id": dlt.secrets["sources.zoom.account_id"],
    },
)
client = RESTClient(base_url="https://api.zoom.us/v2", auth=oauth)

response = client.get("/users")
```

### カスタム認証の実装

`AuthConfigBase` クラスをサブクラス化し、`__call__` メソッドを実装することで、カスタム認証を実装できます:

```py
from dlt.sources.helpers.rest_client.auth import AuthConfigBase

class CustomAuth(AuthConfigBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        # Modify the request object to include the necessary authentication headers
        request.headers["Authorization"] = f"Custom {self.token}"
        return request
```

次に、`RESTClient` でカスタム認証クラスを使用できます:

```py
client = RESTClient(
    base_url="https://api.example.com",
    auth=CustomAuth(token="your_custom_token_here")
)
```

## 高度な使い方

`RESTClient.paginate()` を使用すると、レスポンス オブジェクトを変更するために使用できる [カスタム フック関数](https://requests.readthedocs.io/en/latest/user/advanced/#event-hooks) を指定できます。たとえば、特定の HTTP ステータス コードを適切に処理するには、次のようにします:

```py
def custom_response_handler(response, *args):
    if response.status_code == 404:
        # Handle not found
        pass

client.paginate("/posts", hooks={"response": [custom_response_handler]})
```

ハンドラ関数は、ページネーション ループを早期に終了するために `IgnoreResponseException` を発生させる場合があります。これは、ページネーションする項目がない場合に 404 ステータス コードを返すエンドポイントに役立ちます。

## API レスポンスをページ分割するためのショートカット

`paginate()` 関数は、API レスポンスをページ分割するためのショートカットを提供します。`RESTClient.paginate()` メソッドと同じパラメータを取りますが、指定されたベース URL を使用して RESTClient インスタンスを自動的に作成します:

```py
from dlt.sources.helpers.rest_client import paginate

for page in paginate("https://api.example.com/posts"):
    print(page)
```

## 再試行

`config.toml` を編集することで、RESTClient が失敗したリクエストを再試行する方法をカスタマイズできます。
[再試行ルールに関するドキュメント](requests#retry-rules)で、その他の例と説明を参照してください。

例:

```toml
[runtime]
request_max_attempts = 10  # Stop after 10 retry attempts instead of 5
request_backoff_factor = 1.5  # Multiplier applied to the exponential delays. Default is 1
request_timeout = 120  # Timeout in seconds
request_max_retry_delay = 30  # Cap exponential delay to 30 seconds
```

## トラブルシューティング

### `RESTClient.get()` と `RESTClient.post()` メソッド

これらのメソッドは、Requests ライブラリの [get()](https://docs.python-requests.org/en/latest/api/#requests.get) 関数や [post()](https://docs.python-requests.org/en/latest/api/#requests.post) 関数と同様に動作します。これらは、応答データを含む [Response](https://docs.python-requests.org/en/latest/api/#requests.Response) オブジェクトを返します。
`Response` オブジェクトを調べると、`response.status_code`、`response.headers`、`response.content` を取得できます。例えば:

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

client = RESTClient(base_url="https://api.example.com")
response = client.get("/posts", auth=BearerTokenAuth(token="your_access_token"))  # type: ignore

print(response.status_code)
print(response.headers)
print(response.content)
```

### `RESTClient.paginate()`

`paginate()` は [`PageData`](#pagedata) オブジェクトを生成するジェネレーター関数であるため、デバッグはより複雑です。`paginate()` メソッドをデバッグする方法はいくつかあります:

1. HTTP リクエストに関する詳細情報を表示するには、[ログ記録](../../running-in-production/running.md#set-the-log-level-and-format) を有効にします:

```sh
RUNTIME__LOG_LEVEL=INFO python my_script.py
```

2. [`PageData`](#pagedata) インスタンスを使用して、[request](https://docs.python-requests.org/en/latest/api/#requests.Request)
および [response](https://docs.python-requests.org/en/latest/api/#requests.Response) オブジェクトを検査します:

```py
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import JSONLinkPaginator

client = RESTClient(
    base_url="https://api.example.com",
    paginator=JSONLinkPaginator(next_url_path="pagination.next")
)

for page in client.paginate("/posts"):
    print(page.request)
    print(page.response)
```

3. `hooks` パラメータを使用して、`paginate()` メソッドにカスタム レスポンス ハンドラーを追加します:

```py
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

def response_hook(response, *args):
    print(response.status_code)
    print(f"Content: {response.content}")
    print(f"Request: {response.request.body}")
    # Or import pdb; pdb.set_trace() to debug

for page in client.paginate(
    "/posts",
    auth=BearerTokenAuth(token="your_access_token"),  # type: ignore
    hooks={"response": [response_hook]}
):
    print(page)
```
