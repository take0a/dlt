---
title: Requests wrapper
description: Use the dlt requests wrapper to make HTTP requests with automatic retries and timeouts
keywords: [http, requests, retry, timeout]
---

`dlt` は、自動再試行と構成可能なタイムアウトを備えたカスタマイズされた [Python Requests](https://requests.readthedocs.io/en/latest/) クライアントを提供します。

これを使用してソースで API 呼び出しを行うことをお勧めします。これにより、パイプライン全体の障害を引き起こす可能性のある断続的なネットワーク エラーやその他のランダムな不具合に対するパイプラインの耐性が向上します。

dlt request クライアントは、デフォルトのユーザーエージェントヘッダーを `dlt/{DLT_VERSION_NAME}` に追加で設定します。

ほとんどのユースケースでは、これは`requests`の代替品なので、通常:

```py
import requests
```

代わりに:

```py
from dlt.sources.helpers import requests
```

そして、`requests`と同じように使用します:

```py
response = requests.get(
    'https://example.com/api/contacts',
    headers={'Authorization': API_KEY}
)
data = response.json()
...
```

## 再試行ルール

デフォルトでは、失敗したリクエストは、指数関数的に増加する遅延で最大 5 回再試行されます。つまり、最初の再試行は 1 秒待機し、5 回目の再試行は 16 秒待機します。

すべての再試行が失敗した場合、対応するリクエスト例外が発生します。例: `requests.HTTPError` または `requests.ConnectionTimeout`。

すべての標準的なHTTPサーバーエラーは再試行を引き起こします。これには以下が含まれます。:

* エラーのステータスコード:

    すべてのステータス コードは `500` の範囲と `429` (リクエストが多すぎます) です。
    通常、サーバーは `429` および `503` 応答に `Retry-After` ヘッダーを含めます。
    検出された場合、この値は標準の再試行遅延よりも優先されます。

* 接続およびタイムアウトエラー

    リモート サーバーに到達できない場合、接続が予期せず切断された場合、または要求が構成された `timeout` よりも長くかかった場合。

## 再試行設定のカスタマイズ

多くのリクエスト設定は`config.toml`のランタイムセクションに追加できます。例えば:

```toml
[runtime]
request_max_attempts = 10  # Stop after 10 retry attempts instead of 5
request_backoff_factor = 1.5  # Multiplier applied to the exponential delays. Default is 1
request_timeout = 120  # Timeout in seconds
request_max_retry_delay = 30  # Cap exponential delay to 30 seconds
```

より細かく制御するには、独自の `dlt.sources.requests.Client` インスタンスを作成し、グローバル クライアントの代わりにそれを使用することができます。

これにより、再試行するステータスコードと例外をカスタマイズできます:

```py
from dlt.sources.helpers import requests

http_client = requests.Client(
    status_codes=(403, 500, 502, 503),
    exceptions=(requests.ConnectionError, requests.ChunkedEncodingError)
)
```

また、述語の形式でカスタム再試行条件を指定することもできます。
これは、HTTP エラー コードを使用しない非標準 API から読み込むときに必要になることがあります。

例えば:

```py
from dlt.sources.helpers import requests

def retry_if_error_key(response: Optional[requests.Response], exception: Optional[BaseException]) -> bool:
    """Decide whether to retry the request based on whether
    the json response contains an `error` key
    """
    if response is None:
        # Fall back on the default exception predicate.
        return False
    data = response.json()
    return 'error' in data

http_client = Client(
    retry_condition=retry_if_error_key
)
```

