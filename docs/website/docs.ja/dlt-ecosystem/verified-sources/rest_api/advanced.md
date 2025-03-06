---
title: Advanced configuration
description: Learn custom response processing
keywords: [rest api, restful api]
---

`rest_api_source()` 関数は [dlt ソース](../../../general-usage/source.md)を作成し、次のパラメータを設定できます:

- `config`: REST API 構成辞書。
- `name`: ソースのオプションの名前。
- `section`: 構成ファイル内のオプションのセクション名。
- `max_table_nesting`: ネストされたテーブルの最大深度を設定します。これを超えると、残りのノードが構造体または JSON としてロードされます。
- `root_key` (bool): ルート外部キーをネストされたテーブルに伝播することで、すべてのリソースのマージを有効にします。このオプションは、リソースの書き込み処理を変更してマージを無効/有効にする場合に最も役立ちます。デフォルトは False です。
- `schema_contract`: このリソースに適用されるスキーマ コントラクト設定。
- `spec`: ソースに必要な構成とシークレット値の仕様。

### レスポンスに対するアクション

エンドポイント構成の `response_actions` フィールドを使用すると、API からの特定のレスポンスまたはすべてのレスポンスの処理方法を指定できます。たとえば、特定のステータス コードまたはコンテンツ サブストリングを含むレスポンスは無視できます。
さらに、すべてのレスポンスまたは特定のステータス コードまたはコンテンツ サブストリングを含むレスポンスのみを、関数などのカスタム呼び出し可能オブジェクトで変換できます。この呼び出し可能オブジェクトは、[レスポンスフック](https://requests.readthedocs.io/en/latest/user/advanced/#event-hooks)としてリクエスト ライブラリに渡されます。呼び出し可能オブジェクトはレスポンスオブジェクトを変更することができ、変更を有効にするにはそれを返す必要があります。

:::caution Experimental Feature
これは実験的な機能であり、将来のリリースで変更される可能性があります。
:::

**フィールド:**

- `status_code` (int, optional): 一致する HTTP ステータス コード。
- `content` (str, optional): レスポンスコンテンツ内で検索するサブ文字列。
- `action` (str or Callable or List[Callable], optional):条件が満たされたときに実行されるアクション。現在サポートされているアクション:
  - `"ignore"`: レスポンスを無視します。
  - レスポンスオブジェクトを受けて、返す、呼び出し可能なオブジェクト
  - レスポンスオブジェクトを受けて、返す、呼び出し可能なオブジェクトのリスト


#### 例 A

```py
{
    "path": "issues",
    "response_actions": [
        {"status_code": 404, "action": "ignore"},
        {"content": "Not found", "action": "ignore"},
        {"status_code": 200, "content": "some text", "action": "ignore"},
    ],
}
```

この例では、ソースはステータス コードが 404 の応答、コンテンツが「見つかりません」の応答、およびステータス コードが 200 でコンテンツが「何らかのテキスト」の応答を無視します。

#### 例 B

```py
from requests.models import Response
from dlt.common import json

def set_encoding(response, *args, **kwargs):
    # Sets the encoding in case it's not correctly detected
    response.encoding = 'windows-1252'
    return response


def add_and_remove_fields(response: Response, *args, **kwargs) -> Response:
    payload = response.json()
    for record in payload["data"]:
        record["custom_field"] = "foobar"
        record.pop("email", None)
    modified_content: bytes = json.dumps(payload).encode("utf-8")
    response._content = modified_content
    return response


source_config = {
    "client": {
        # ...
    },
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "issues",
                "response_actions": [
                    set_encoding,
                    {
                        "status_code": 200,
                        "content": "some text",
                        "action": add_and_remove_fields,
                    },
                ],
            },
        },
    ],
}
```

この例では、リソースはまずすべての応答に対して正しいエンコーディングを設定します。その後、ステータス コード 200 のすべての応答に対して、フィールド `custom_field` を追加し、フィールド `email` を削除します。

#### 例 C

```py
def set_encoding(response, *args, **kwargs):
    # Sets the encoding in case it's not correctly detected
    response.encoding = 'windows-1252'
    return response

source_config = {
    "client": {
        # ...
    },
    "resources": [
        {
            "name": "issues",
            "endpoint": {
                "path": "issues",
                "response_actions": [
                    set_encoding,
                ],
            },
        },
    ],
}
```

この例では、リソースはすべての応答に対して正しいエンコーディングを設定します。response_actions のリストに、さらに呼び出し可能項目を追加できます。

