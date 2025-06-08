---
title: Dispatch stream of events to multiple tables in DuckDB
description: Learn how to efficiently dispatch a stream of GitHub events, categorized by event type, to different tables in DuckDB
keywords: [dispatch, stream, events, tables, event type]
---

これは、[GitHub イベント](https://docs.github.com/en/rest/activity/events?apiVersion=2022-11-28) を [dlt](https://github.com/dlt-hub/dlt) リポジトリから処理する方法の実践的な例です。イベントには Issue や Pull Request の作成、コメントの追加などがあります。
[GitHub API](https://docs.github.com/en/rest) を使用してイベントを取得し、送信先として [duckdb](https://duckdb.org/) を使用します。
各イベントタイプは、DuckDB 内の個別のテーブルに送信されます。

# Setup

1. duckdb サポート付きの dlt をインストールします:

```sh
pip install "dlt[duckdb]"
```

2. 新しいファイル `github_events_dispatch.py​​` を作成し、次のコードを貼り付けます:

```py
import dlt
from dlt.sources.helpers import requests

@dlt.resource(
    primary_key="id",
    table_name=lambda i: i["type"],
    write_disposition="append",
)
def repo_events(last_created_at=dlt.sources.incremental("created_at")):
    url = "https://api.github.com/repos/dlt-hub/dlt/events?per_page=100"

    while True:
        response = requests.get(url)
        response.raise_for_status()
        yield response.json()

        # Stop requesting pages if the last element was already older than
        # the initial value.
        # Note: incremental will skip those items anyway, we just do not
        # want to use the API limits.
        if last_created_at.start_out_of_range:
            break

        # Get the next page.
        if "next" not in response.links:
            break
        url = response.links["next"]["url"]


pipeline = dlt.pipeline(
    pipeline_name="github_events",
    destination="duckdb",
    dataset_name="github_events_data",
)
load_info = pipeline.run(repo_events)
row_counts = pipeline.last_trace.last_normalize_info

print(row_counts)
print("------")
print(load_info)
```

上記のコードでは、GitHub API からイベントを取得するリソース `repo_events` を定義しています。

イベントの内容は変更されないため、`append` 書き込み処理を使用し、`created_at` フィールドを使用して新しいイベントを追跡できます。

イベントデータを受け取ってテーブル名を返す関数 `table_name=lambda i: i["type"]` を使用してテーブルに名前を付けます。

3. スクリプトを実行します:@

```sh
python github_events_dispatch.py
```

4. 作成されたテーブルを確認します:

```sh
dlt pipeline -v github_events info
dlt pipeline github_events trace
```

5. データをプレビューします:

```sh
dlt pipeline -v github_events show
```

:::tip
一部のイベントは、多数のネストされたテーブルを含むテーブルを生成します。
デコレータを使用することで、[テーブルのネストレベルを制御](general-usage/source.md#reduce-the-nesting-level-of-generated-tables)できます。

もう一つの楽しい[Colabデモ](https://colab.research.google.com/drive/1BXvma_9R9MX8p_iSvHE4ebg90sUroty2#scrollTo=a3OcZolbaWGf) - duckdbリポジトリでの反応を分析します！

:::

詳細:
* デコレータを使用して [テーブルのネストレベルを変更する](general-usage/source.md#reduce-the-nesting-level-of-generated-tables)。


