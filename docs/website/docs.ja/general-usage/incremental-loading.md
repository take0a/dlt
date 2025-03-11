---
title: Incremental loading
description: Incremental loading with dlt
keywords: [incremental loading, loading methods, append, merge]
---

# インクリメンタルローディング

インクリメンタルローディングとは、すでにロードされている古いレコードではなく、新しいデータまたは変更されたデータのみをロードする操作です。これにより、低レイテンシで低コストのデータ転送が可能になります。

インクリメンタルなパイプラインの課題は、ロードの状態 (つまり、どの増分がロードされたか、どの増分がロードされるか) を追跡しないと、問題が発生する可能性があることです。状態の詳細については、[こちら](state.md) を参照してください。

## 書き込み処理の選択

### ３つの書き込み処理:

- **Full load**: 宛先データセットを、この実行でソースが生成したものに置き換えます。これを実現するには、リソースで `write_disposition='replace'` を使用します。詳細については、[フルロードのドキュメント](./full-loading.md)を参照してください。

- **Append**: 新しいデータを宛先に追加します。`write_disposition='append'` を使用します。

- **Merge**: `merge_key` を使用して新しいデータを宛先にマージしたり、`primary_key` を使用して新しいデータを重複排除/アップサートしたりします。

### 2つの簡単な質問で、使用する書き込み処理が決まります

<div style={{textAlign: 'center'}}>

![write disposition flowchart](https://storage.googleapis.com/dlt-blog-images/flowchart_for_scd2.png)

</div>

選択する「書き込み処理」は、データセットとその抽出方法によって異なります。

使用すべき「書き込み処理」を見つけるには、まず「データはステートフルかステートレスか」と自問する必要があります。ステートフル データの状態は変更される可能性があります (ユーザーのプロファイルなど)。ステートレス データは変更できません (ページ ビューなどの記録されたイベントなど)。

ステートレス データは更新する必要がないため、追加するだけで済みます。

ステートフル データの場合、2 番目の質問が来ます - ソースから増分的に抽出できますか? できる場合は、[ゆっくり変化するディメンション (タイプ 2)](#scd2-strategy) を使用する必要があります。これにより、時間の経過に伴うデータの変更の履歴レコードを維持できます。

そうでない場合は、データセット全体を置き換える必要があります。ただし、「昨日以降に追加または変更されたすべてのユーザー」のように、データを段階的に要求できる場合は、マージ書き込み処理を使用して既存のデータセットに変更を適用するだけで済みます。

## インクリメンタルローディングでのマージ

`merge`書き込み処理は3つの異なる戦略で使用できます:

1. `delete-insert` (default strategy)
2. `scd2`
3. `upsert`

### `delete-insert` 戦略

デフォルトの「削除-挿入」戦略は2つのシナリオで使用されます:

1. 特定のレコードのインスタンスを 1 つだけ保持したい場合、つまり、API から `user` 状態の更新を受信し、`user_id` ごとに 1 つのレコードだけを保持したい場合です。
2. データは毎日バッチで受信され、古いバッチをロードしたり、現在のバッチを 1 日に数回ロードする場合でも (つまり、「ライブ」更新を受信するため)、各バッチのレコードのインスタンスを常に 1 つだけ保持するようにする必要があります。

`delete-insert` 戦略は、データを `staging` データセットにロードし、`primary_key` が提供されている場合はステージング データを重複排除し、`merge_key` と `primary_key` を使用して宛先からデータを削除し、新しいレコードを挿入します。このすべては、ルートとすべてのネストされたテーブルに対して単一のアトミック トランザクションで実行されます。

以下の例では、すべての GitHub イベントをロードし、主キーとして「id」を使用して宛先で更新し、`github_repo_events` テーブルにイベントのコピーが 1 つだけ存在するようにします:

```py
@dlt.resource(primary_key="id", write_disposition="merge")
def github_repo_events():
    yield from _get_event_pages()
```

複合主キーも使用できます:

```py
@dlt.resource(primary_key=("id", "url"), write_disposition="merge")
def resource():
    ...
```

デフォルトでは、`primary_key` 重複排除は任意です。`dedup_sort` 列ヒントに `desc` または `asc` の値を渡して、重複排除後にどのレコードを残すかを指定できます。`desc` を使用すると、同じ `primary_key` を共有するレコードは重複排除前に降順で並べ替えられ、`dedup_sort` ヒントを持つ列の最高値を持つレコードが確実に残ります。`asc` は逆の動作をします。

```py
@dlt.resource(
    primary_key="id",
    write_disposition="merge",
    columns={"created_at": {"dedup_sort": "desc"}}  # select "latest" record
)
def resource():
    ...
```

以下の例では、指定されたレコードが有効な日を保持する列 `batch_day` でマージします。
マージキーは複合キーにすることもできます:

```py
@dlt.resource(merge_key="batch_day", write_disposition="merge")
def get_daily_batch(day):
    yield _get_batch_from_bucket(day)
```

他の書き込み処理と同様に、これを使用してアドホックにデータを読み込むことができます。以下では、`duckdb` リポジトリのトップ反応を持つ問題を読み込みます。リストには明らかに重複する問題が多数ありますが、各問題を 1 つのインスタンスだけ保持します。

```py
p = dlt.pipeline(destination="bigquery", dataset_name="github")
issues = []
reactions = ["%2B1", "-1", "smile", "tada", "thinking_face", "heart", "rocket", "eyes"]
for reaction in reactions:
    for page_no in range(1, 3):
      page = requests.get(f"https://api.github.com/repos/{REPO_NAME}/issues?state=all&sort=reactions-{reaction}&per_page=100&page={page_no}", headers=headers)
      print(f"got page for {reaction} page {page_no}, requests left", page.headers["x-ratelimit-remaining"])
      issues.extend(page.json())
p.run(issues, write_disposition="merge", primary_key="id", table_name="issues")
```

以下の例では、GitHub イベントをイベント タイプ別に複数のテーブルにディスパッチし、各イベントのコピーを「id」別に 1 つ保持し、「最後の値」増分を使用して過去のレコードの読み込みをスキップします。ご覧のとおり、これらすべてをリソース内で宣言するだけで済みます。

```py
@dlt.resource(primary_key="id", write_disposition="merge", table_name=lambda i: i['type'])
def github_repo_events(last_created_at = dlt.sources.incremental("created_at", "1970-01-01T00:00:00Z")):
    """A resource taking a stream of github events and dispatching them to tables named by event type. Deduplicates by 'id'. Loads incrementally by 'created_at' """
    yield from _get_rest_pages("events")
```

:::note
`merge` 書き込み処理を使用しても、マージまたは主キーを指定しない場合、merge は `append` にフォールバックします。
この場合、追加されたデータは、ほとんどの宛先に対して 1 つのトランザクションでステージングテーブルから挿入されます。
:::

#### レコードを削除する

`hard_delete`列ヒントは、宛先データセットからレコードを削除するために使用できます。削除メカニズムの動作は、ヒントでマークされた列のデータ型によって異なります。:

1) `bool` 型: `True` のみが削除につながり、`None` および `False` 値は無視されます。
2) その他のタイプ: `None でない` 値ごとに削除されます。

削除としてマークされているソース データセット内のレコードと同じ `primary_key` または `merge_key` を持つ宛先テーブル内の各レコードが削除されます。

削除は、存在する可能性のあるネストされたテーブルに伝播されます。ルート テーブルで削除されるレコードごとに、ネストされたテーブル内の対応するレコードもすべて削除されます。親テーブルとネストされたテーブルのレコードは、次のセクションで説明する `ルートキー` を通じてリンクされます。

##### 例: 主キーとブール値の削除列

```py
@dlt.resource(
    primary_key="id",
    write_disposition="merge",
    columns={"deleted_flag": {"hard_delete": True}}
)
def resource():
    # This will insert a record (assuming a record with id = 1 does not yet exist).
    yield {"id": 1, "val": "foo", "deleted_flag": False}

    # This will update the record.
    yield {"id": 1, "val": "bar", "deleted_flag": None}

    # This will delete the record.
    yield {"id": 1, "val": "foo", "deleted_flag": True}

    # Similarly, this would have also deleted the record.
    # Only the key and the column marked with the "hard_delete" hint suffice to delete records.
    yield {"id": 1, "deleted_flag": True}
...
```

##### 例: マージキーと非ブール削除列

```py
@dlt.resource(
    merge_key="id",
    write_disposition="merge",
    columns={"deleted_at_ts": {"hard_delete": True}})
def resource():
    # This will insert two records.
    yield [
        {"id": 1, "val": "foo", "deleted_at_ts": None},
        {"id": 1, "val": "bar", "deleted_at_ts": None}
    ]

    # This will delete two records.
    yield {"id": 1, "val": "foo", "deleted_at_ts": "2024-02-22T12:34:56Z"}
...
```

##### 例: 主キーと「dedup_sort」ヒントを使用

```py
@dlt.resource(
    primary_key="id",
    write_disposition="merge",
    columns={"deleted_flag": {"hard_delete": True}, "lsn": {"dedup_sort": "desc"}})
def resource():
    # This will insert one record (the one with lsn = 3).
    yield [
        {"id": 1, "val": "foo", "lsn": 1, "deleted_flag": None},
        {"id": 1, "val": "baz", "lsn": 3, "deleted_flag": None},
        {"id": 1, "val": "bar", "lsn": 2, "deleted_flag": True}
    ]

    # This will insert nothing, because the "latest" record is a delete.
    yield [
        {"id": 2, "val": "foo", "lsn": 1, "deleted_flag": False},
        {"id": 2, "lsn": 2, "deleted_flag": True}
    ]
...
```

:::note
インデックス作成は、特にマージ書き込みの場合に列値による検索を実行し、一部の宛先で許容できるパフォーマンスを確保する上で重要です。
:::

#### ルートキーの伝播を強制する

マージ書き込み処理では、ルート テーブルの `_dlt_id` (`row_key`) をネストされたテーブルに伝播する必要があります。この概念は外部キーに似ていますが、中間の親をスキップして常にルート (最上位) テーブルを参照します。これを `ルート キー` と呼びます。ルート キーは、`merge` 書き込み処理が設定されているすべてのテーブルに自動的に伝播されます。これはストレージ スペースを占有するため、どこでも有効にできるわけではありません。ただし、場合によっては、ルート キーの伝播を永続的に有効にする必要があります。

```py
pipeline = dlt.pipeline(
    pipeline_name='facebook_insights',
    destination='duckdb',
    dataset_name='facebook_insights_data',
    dev_mode=True
)
fb_ads = facebook_ads_source()
# enable root key propagation on a source that is not a merge one by default.
# this is not required if you always use merge but below we start with replace
fb_ads.root_key = True
# load only disapproved ads
fb_ads.ads.bind(states=("DISAPPROVED", ))
info = pipeline.run(fb_ads.with_resources("ads"), write_disposition="replace")
# merge the paused ads. the disapproved ads stay there!
fb_ads = facebook_ads_source()
fb_ads.ads.bind(states=("PAUSED", ))
info = pipeline.run(fb_ads.with_resources("ads"), write_disposition="merge")
```

上記の例では、`fb_ads.root_key = True` を使用してルート キーの伝播を強制しています。これにより、最初の `replace` ロードで正しいデータが伝播され、将来の `merge` ロードが実行できるようになります。デコレータ `@dlt.source(root_key=True)` でも同じことを実現できます。

### `scd2` 戦略

`dlt` は、ソースで変更されるディメンション テーブルに対して [Slowly Changing Dimension Type 2](https://en.wikipedia.org/wiki/Slowly_changing_dimension#Type_2:_add_new_row) (SCD2) 宛先テーブルを作成できます。デフォルトでは、リソースは実行ごとにソース テーブルの完全な抽出を提供することが想定されていますが、[インクリメンタルな抽出](#example-incremental-scd2) も可能です。行ハッシュは `_dlt_id` に格納され、挿入、更新、または削除されたソース レコードを識別するための代理キーとして使用されます。デフォルトでは、アクティブなレコードを示すために `NULL` 値が使用されますが、代わりに構成可能な上限タイムスタンプ (例: 9999-12-31 00:00:00.000000) を使用することもできます。

:::note
`scd2` を使用する場合、ルート テーブルの `_dlt_id` の `unique` ヒントは `false` に設定されます。これは [デフォルトの動作](./destination-tables.md#child-and-parent-tables) とは異なります。その理由は、`_dlt_id` に格納されている代理キーに、_insert-delete-reinsert_ パターンの後に重複が含まれているためです。:

1. 代理キー X を持つレコードが `t1` でのロードで挿入されます。
2. 代理キー X を持つレコードは、後の `t2` でのロードで削除されます。
3. 代理キー X を持つレコードは、さらに後の `t3` でのロードで再挿入されます。

このパターンの後、宛先の `scd2` テーブルには、代理キー X のレコードが 2 つあります。1 つは有効期間 `[t1, t2]` 用、もう 1 つは `[t3, NULL]` 用です。両方のレコードに同じ代理キーがあるため、`_dlt_id` に重複した値が存在します。

以下に注意ください:

- 複合キー `(_dlt_id, _dlt_valid_from)` は一意です。
- `_dlt_id` はネストされたテーブルに対して一意のままです。`scd2` はこれに影響しません。
:::

#### 例: `scd2` マージ戦略

```py
@dlt.resource(
    write_disposition={"disposition": "merge", "strategy": "scd2"}
)
def dim_customer():
    # initial load
    yield [
        {"customer_key": 1, "c1": "foo", "c2": 1},
        {"customer_key": 2, "c1": "bar", "c2": 2}
    ]

pipeline.run(dim_customer())  # first run — 2024-04-09 18:27:53.734235
...
```

*最初の実行後の `dim_customer` 宛先テーブル - 初期ロードに存在する 2 つのレコードを挿入し、有効性判定列を追加しました:*

| `_dlt_valid_from` | `_dlt_valid_to` | `customer_key` | `c1` | `c2` |
| -- | -- | -- | -- | -- |
| 2024-04-09 18:27:53.734235 | NULL | 1 | foo | 1 |
| 2024-04-09 18:27:53.734235 | NULL | 2 | bar | 2 |

```py
...
def dim_customer():
    # second load — record for customer_key 1 got updated
    yield [
        {"customer_key": 1, "c1": "foo_updated", "c2": 1},
        {"customer_key": 2, "c1": "bar", "c2": 2}
]

pipeline.run(dim_customer())  # second run — 2024-04-09 22:13:07.943703
```

*2 回目の実行後の `dim_customer` 宛先テーブル - `customer_key` 1 の新しいレコードが挿入され、`_dlt_valid_to` を更新することで古いレコードが削除されました。:*

| `_dlt_valid_from` | `_dlt_valid_to` | `customer_key` | `c1` | `c2` |
| -- | -- | -- | -- | -- |
| 2024-04-09 18:27:53.734235 | **2024-04-09 22:13:07.943703** | 1 | foo | 1 |
| 2024-04-09 18:27:53.734235 | NULL | 2 | bar | 2 |
| **2024-04-09 22:13:07.943703** | **NULL** | **1** | **foo_updated** | **1** |

```py
...
def dim_customer():
    # third load — record for customer_key 2 got deleted
    yield [
        {"customer_key": 1, "c1": "foo_updated", "c2": 1},
    ]

pipeline.run(dim_customer())  # third run — 2024-04-10 06:45:22.847403
```

*3 回目の実行後の `dim_customer` 宛先テーブル - `_dlt_valid_to` を更新することで削除されたレコードが廃止されました:*

| `_dlt_valid_from` | `_dlt_valid_to` | `customer_key` | `c1` | `c2` |
| -- | -- | -- | -- | -- |
| 2024-04-09 18:27:53.734235 | 2024-04-09 22:13:07.943703 | 1 | foo | 1 |
| 2024-04-09 18:27:53.734235 | **2024-04-10 06:45:22.847403** | 2 | bar | 2 |
| 2024-04-09 22:13:07.943703 | NULL | 1 | foo_updated | 1 |

#### 例: インクリメンタルな `scd2`

`merge_key` は、完全抽出ではなくインクリメンタルな抽出で動作するように指定できます。`merge_key` を使用すると、存在しない行のうち「削除済み」と見なされるものを定義できます。複合自然キーが許可されており、`merge_key` として列名のリストを提供することで指定できます。

*ケース1: 不在の記録を破棄しない*

不在の行の廃止を防ぐために、自然キーを `merge_key` として設定できます。この場合、不在の行は削除されたとは見なされません。対応する自然キーがソース抽出に存在しない場合、レコードは宛先で廃止されません。これにより、更新されたレコードのみを含む増分抽出が可能になります。

```py
@dlt.resource(
    merge_key="customer_key",
    write_disposition={"disposition": "merge", "strategy": "scd2"}
)
def dim_customer():
    # initial load
    yield [
        {"customer_key": 1, "c1": "foo", "c2": 1},
        {"customer_key": 2, "c1": "bar", "c2": 2}
    ]

pipeline.run(dim_customer())  # first run — 2024-04-09 18:27:53.734235
...
```

*最初の実行後の `dim_customer` 宛先テーブル:*

| `_dlt_valid_from` | `_dlt_valid_to` | `customer_key` | `c1` | `c2` |
| -- | -- | -- | -- | -- |
| 2024-04-09 18:27:53.734235 | NULL | 1 | foo | 1 |
| 2024-04-09 18:27:53.734235 | NULL | 2 | bar | 2 |

```py
...
def dim_customer():
    # second load — record for customer_key 1 got updated, customer_key 2 absent
    yield [
        {"customer_key": 1, "c1": "foo_updated", "c2": 1},
]

pipeline.run(dim_customer())  # second run — 2024-04-09 22:13:07.943703
```

*2 回目の実行後の `dim_customer` 宛先テーブル - 顧客キー 2 は廃止されませんでした:*

| `_dlt_valid_from` | `_dlt_valid_to` | `customer_key` | `c1` | `c2` |
| -- | -- | -- | -- | -- |
| 2024-04-09 18:27:53.734235 | **2024-04-09 22:13:07.943703** | 1 | foo | 1 |
| 2024-04-09 18:27:53.734235 | NULL | 2 | bar | 2 |
| **2024-04-09 22:13:07.943703** | **NULL** | **1** | **foo_updated** | **1** |

*ケース2: 指定されたパーティションのレコードのみを破棄する*

:::note
技術的には、レコードをマージするために使用されるキーが自然キーではないため、これは SCD2 ではありません。
:::

特定のパーティションの不在の行を削除するには、「パーティション」列を `merge_key` として設定します。この場合、パーティション値が抽出に存在する場合にのみ、不在の行が削除されたとみなされます。テーブルの物理的なパーティション分割は必要ありません。ここでは、「パーティション」という単語は概念的に使用されています。

```py
@dlt.resource(
    merge_key="date",
    write_disposition={"disposition": "merge", "strategy": "scd2"}
)
def some_data():
    # load 1 — "2024-01-01" partition
    yield [
        {"date": "2024-01-01", "name": "a"},
        {"date": "2024-01-01", "name": "b"},
    ]

pipeline.run(some_data())  # first run — 2024-01-02 03:03:35.854305
...
```

*最初の実行後の `some_data` 宛先テーブル:*

| `_dlt_valid_from` | `_dlt_valid_to` | `date` | `name` |
| -- | -- | -- | -- |
| 2024-01-02 03:03:35.854305 | NULL | 2024-01-01 | a |
| 2024-01-02 03:03:35.854305 | NULL | 2024-01-01 | b |

```py
...
def some_data():
    # load 2 — "2024-01-02" partition
    yield [
        {"date": "2024-01-02", "name": "c"},
        {"date": "2024-01-02", "name": "d"},
    ]

pipeline.run(some_data())  # second run — 2024-01-03 03:01:11.943703
...
```

*2 回目の実行後の `some_data` 宛先テーブル - 2024-01-02 レコードが追加され、2024-01-01 レコードには影響しませんでした:*

| `_dlt_valid_from` | `_dlt_valid_to` | `date` | `name` |
| -- | -- | -- | -- |
| 2024-01-02 03:03:35.854305 | NULL | 2024-01-01 | a |
| 2024-01-02 03:03:35.854305 | NULL | 2024-01-01 | b |
| **2024-01-03 03:01:11.943703** | **NULL** | **2024-01-02** | **c** |
| **2024-01-03 03:01:11.943703** | **NULL** | **2024-01-02** | **d** |

```py
...
def some_data():
    # load 3 — reload "2024-01-01" partition
    yield [
        {"date": "2024-01-01", "name": "a"},  # unchanged
        {"date": "2024-01-01", "name": "bb"},  # new
    ]

pipeline.run(some_data())  # third run — 2024-01-03 10:30:05.750356
...
```

*3 回目の実行後の `some_data` 宛先テーブル - b を廃止し、bb を追加し、2024-01-02 パーティションには触れなかった:*

| `_dlt_valid_from` | `_dlt_valid_to` | `date` | `name` |
| -- | -- | -- | -- |
| 2024-01-02 03:03:35.854305 | NULL | 2024-01-01 | a |
| 2024-01-02 03:03:35.854305 | **2024-01-03 10:30:05.750356** | 2024-01-01 | b |
| 2024-01-03 03:01:11.943703 | NULL | 2024-01-02 | c |
| 2024-01-03 03:01:11.943703 | NULL | 2024-01-02 | d |
| **2024-01-03 10:30:05.750356** | **NULL** | **2024-01-01** | **bb** |


#### 例: 有効な列名を構成する

`_dlt_valid_from` と `_dlt_valid_to` は、有効性判定列名としてデフォルトで使用されます。他の名前は次のように設定できます:

```py
@dlt.resource(
    write_disposition={
        "disposition": "merge",
        "strategy": "scd2",
        "validity_column_names": ["from", "to"],  # will use "from" and "to" instead of default values
    }
)
def dim_customer():
    ...
...
```

#### 例: アクティブレコードのタイムスタンプを設定する

`active_record_timestamp` を使用して、アクティブ レコードを示すために使用されるリテラルを設定できます。`active_record_timestamp` が省略されているか、`None` に設定されている場合、デフォルトのリテラル `NULL` が使用されます。代わりに上限のタイムスタンプを使用する場合は、日付値を指定します。

```py
@dlt.resource(
    write_disposition={
        "disposition": "merge",
        "strategy": "scd2",
        # accepts various types of date/datetime objects
        "active_record_timestamp": "9999-12-31",
    }
)
def dim_customer():
    ...
```

#### 例: 境界タイムスタンプを構成する

`boundary_timestamp` を使用して、レコードの有効期間ウィンドウに使用される「境界タイムスタンプ」を設定できます。指定された日付 (時刻) 値は、新しいレコードの「有効開始日」として、また廃止されたレコードの「有効終了日」として使用されます。`boundary_timestamp` が省略されている場合は、ロード パッケージが作成されたタイムスタンプが使用されます。

```py
@dlt.resource(
    write_disposition={
        "disposition": "merge",
        "strategy": "scd2",
        # accepts various types of date/datetime objects
        "boundary_timestamp": "2024-08-21T12:15:00+00:00",
    }
)
def dim_customer():
    ...
```

#### 例: 独自の行ハッシュを使用する

デフォルトでは、`dlt` はリソースによって提供されるすべての列に基づいて行ハッシュを生成し、それを `_dlt_id` に保存します。`write_disposition` ディクショナリで `row_version_column_name` を指定することで、代わりに独自のハッシュを使用できます。リソース内に行ハッシュとして自然に機能する列が既に存在する場合、新しいハッシュ値を生成するよりも、既存のハッシュ値を使用する方が効率的です。このオプションを使用すると、一部の列の変更を無視したい場合に、列のサブセットに基づくハッシュを使用することもできます。独自のハッシュを使用する場合、`_dlt_id` の値はランダムに生成されます。

```py
@dlt.resource(
    write_disposition={
        "disposition": "merge",
        "strategy": "scd2",
        "row_version_column_name": "row_hash",  # the column "row_hash" should be provided by the resource
    }
)
def dim_customer():
    ...
...
```

#### 🧪 scd2 を Arrow テーブルと Panda フレームで使用する

`dlt` は、**行ハッシュ** 列を表形式データに自動的に追加しません (現在作業中です)。
行ハッシュを計算する変換関数を `scd2` リソースに追加して、自分でこれを行う必要があります (pandas.util を使用すれば、かなり高速になるはずです)。

```py
import dlt
from dlt.sources.helpers.transform import add_row_hash_to_table

scd2_r = dlt.resource(
          arrow_table,
          name="tabular",
          write_disposition={
              "disposition": "merge",
              "strategy": "scd2",
              "row_version_column_name": "row_hash",
          },
      ).add_map(add_row_hash_to_table("row_hash"))
```

`add_row_hash_to_table` は、`row_version_column_name` によってハッシュを保持すると宣言されている `row_hash` 列を計算して作成する変換関数の名前です。

:::tip
`apply_hints` を呼び出して `write_disposition` で `scd2` 構成を渡し、次に `add_map` を使用して変換を追加することで、表形式でデータを生成する既存のリソースを変更できます。
:::

#### ネストされたテーブル

ネストされたテーブルがある場合、そのテーブルには有効性判定列は含まれません。有効性判定列はルート テーブルにのみ追加されます。ネストされたテーブル内のレコードの有効性判定列の値は、`_dlt_root_id` (`root_key`) を使用してルート テーブルを結合することで取得できます。

#### 制限事項

* `primary_key` 内で一意であるレコードの `updated_at` や整数 `version` などの列は使用できません (定義されている場合でも)。ハッシュ列はルート テーブルに対して一意である必要があります。`updated_at` スタイルの追跡を可能にするために取り組んでいます。
* 対応する親行の行ハッシュが変更されていない場合、ネストされたテーブルの変更 (新しいレコードを除く) は検出されません。ネストされたデータの変更をスタンプするには、ルート テーブルで `updated_at` または同様の列を使用します。

### `upsert` 戦略

:::caution
`upsert` マージ戦略は現在、これらの宛先でサポートされています:

- `athena`
- `bigquery`
- `databricks`
- `mssql`
- `postgres`
- `snowflake`
- `delta` テーブル形式の `filesystem` (制限事項については [こちら](../dlt-ecosystem/destinations/filesystem.md#known-limitations)を参照)
:::

`upsert`マージ戦略は主キーベースの*upsert*を実行します:

- 対象テーブルにキーが存在する場合はレコードを*更新*する
- キーがターゲットテーブルに存在しない場合はレコードを*挿入*します

`hard_delete` ヒントを使用して[レコードを削除](#delete-records)できます。

#### `upsert` と `delete-insert`

デフォルトの`delete-insert`マージ戦略とは異なり、`upsert`戦略は:

1. `primary_key` が必要です
2. この `primary_key` は一意であることが期待されます (`dlt` は重複を排除しません)
3. `merge_key` をサポートしていません
4. 更新を処理するために `MERGE` または `UPDATE` 操作を使用します

#### 例: `upsert` マージ戦略

```py
@dlt.resource(
    write_disposition={"disposition": "merge", "strategy": "upsert"},
    primary_key="my_primary_key"
)
def my_upsert_resource():
    ...
...
```

## カーソルフィールドによるインクリメンタルロード

ほとんどの REST API (および他のデータ ソース、つまりデータベース テーブル) では、クエリに「最後の」レコードのタイムスタンプまたは ID を渡すことで、新しいデータまたは更新されたデータを要求できます。API/データベースは、次のロードの最大/最小のタイムスタンプ/ID を取得する新しい/更新されたレコードのみを返します。

この方法でインクリメンタルローディングを行うには、:

- 変更を追跡するために使用されるフィールド (いわゆる **カーソル フィールド**) を特定します (例: 「inserted_at」、「updated_at」など)。
- 新しいデータまたは変更されたデータのみを取得するために、カーソル フィールドの「最後の」(最大/最小) 値を API に渡す方法を決定します (これを行う方法は、ソース API によって異なります)。

それを理解したら、`dlt` はカーソル フィールドの最大/最小値の検索、重複の削除、カーソルの最後の値による状態の管理を行います。最近作成された問題をリクエストする以下の GitHub の例をご覧ください。

```py
@dlt.resource(primary_key="id")
def repo_issues(
    access_token,
    repository,
    updated_at = dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    # Get issues since "updated_at" stored in state on previous run (or initial_value on first run)
    for page in _get_issues_page(access_token, repository, since=updated_at.start_value):
        yield page
        # Last_value is updated after every page
        print(updated_at.last_value)
```

ここでは、`1970-01-01T00:00:00Z` に初期化された増分状態を受け取る `updated_at` 引数を追加します。これは、`repo_issues` リソースによって生成された問題の `updated_at` フィールドを追跡するように構成されています。最新の `updated_at` 値が `dlt` [state](state.md) に保存され、次のパイプライン実行時に `updated_at.start_value` で使用できるようになります。この値は、`_get_issues_page` 関数で、[GitHub API](https://docs.github.com/en/rest/issues/issues?#list-repository-issues) へのリクエスト クエリ パラメータ **since** に挿入されます。

本質的には、上記の`dlt.sources.incremental`インスタンスは:

* **updated_at.initial_value** は常にコンストラクタで渡される「1970-01-01T00:00:00Z」に等しい
* **updated_at.start_value** 前回の実行からの最大の `updated_at` 値、または最初の実行時の **initial_value**
* **updated_at.last_value** は、各アイテムまたはページが yield されるたびに更新される「リアルタイム」の `updated_at` 値です。最初の yield の前は、**start_value** と同じです。
* **updated_at.end_value** (ここでは使用されていません) [バックフィル範囲の終了をマーク](#using-end_value-for-backfill)

ページ区切りを行う場合、リソースの実行中に変更されない **start_value** が必要になる可能性がありますが、ほとんどのページ区切りは、使用すべき **次のページ** リンクを返します。

舞台裏では、dlt は結果の重複を排除します。つまり、最後の問題が再度返される場合 (`updated_at` フィルターが含まれます)、すでに読み込まれた問題をスキップします。

以下の例では、GitHub イベントを段階的にロードします。API では最新のイベントをフィルタリングできず、常にすべてのイベントが返されます。ただし、`dlt` は新しい項目のみをロードし、重複と過去の問題をすべて除外します。

```py
# Use naming function in table name to generate separate tables for each event
@dlt.resource(primary_key="id", table_name=lambda i: i['type'])  # type: ignore
def repo_events(
    last_created_at = dlt.sources.incremental("created_at", initial_value="1970-01-01T00:00:00Z", last_value_func=max), row_order="desc"
) -> Iterator[TDataItems]:
    repos_path = "/repos/%s/%s/events" % (urllib.parse.quote(owner), urllib.parse.quote(name))
    for page in _get_rest_pages(access_token, repos_path + "?per_page=100"):
        yield page
```

すべてのイベントを生成し、`dlt` がフィルタリングを実行します (`primary_key` として宣言された `id` 列を使用)。

GitHub は、新しいものから古いものの順にイベントを返します。そのため、`rows_order` を **descending** として宣言し、[増分値が範囲外になったらそれ以上のページをリクエストしないようにします](#declare-row-order-to-not-request-unnecessary-data)。`created_at` が `initial_value` より早い最初のイベントを見つけたら、API からそれ以上のデータをリクエストしないようにします。

:::note
`dlt.sources.incremental` は [フィルタ関数](resource.md#filter-transform-and-pivot-data) として実装されており、`add_map` または `add_filter` で追加した他のすべての変換の **後** に実行されます。つまり、増分フィルタがデータ項目を認識する前に、データ項目を操作できるということです。たとえば:
* 他の列から代理主キーを作成することができます
* カーソル値を変更したり、他のフィールドで構成される新しいフィールドを作成したりできます。
* Pydantic モデルを Python 辞書にダンプして、増分的にカスタム値を見つけられるようにする

[Pydantic によるデータ検証](schema-contracts.md#use-pydantic-models-for-data-validation) は、インクリメンタルフィルタリングの **前** に実行されます。
:::

### 最大値、最小値、またはカスタムの `last_value_func`

`dlt.sources.incremental` を使用すると、カーソル値を現在の `last_value` に順序付け (比較) する関数を選択できます。
* デフォルトの関数は組み込みの `max` で、2 つの値のうち大きい方の値を返します。
* 別の組み込み関数 `min` は、小さい方の値を返します。

カスタム関数を渡すこともできます。これにより、ネストされた型、つまり辞書に `last_value` を定義し、単純な型だけでなく最後の値のインデックスを保存できます。`last_value` 引数は [JSON パス](https://github.com/json-path/JsonPath#operators) であり、ネストされたデータ (`$` が使用されている場合はデータ項目全体を含む) を選択できます。以下の例では、作成されたテーブル名ごとに最大の `created_at` 値を保持する辞書である最後の値を作成します。

```py
def by_event_type(event):
    last_value = None
    if len(event) == 1:
        item, = event
    else:
        item, last_value = event

    if last_value is None:
        last_value = {}
    else:
        last_value = dict(last_value)
    item_type = item["type"]
    last_value[item_type] = max(item["created_at"], last_value.get(item_type, "1970-01-01T00:00:00Z"))
    return last_value

@dlt.resource(primary_key="id", table_name=lambda i: i['type'])
def get_events(last_created_at = dlt.sources.incremental("$", last_value_func=by_event_type)):
    with open("tests/normalize/cases/github.events.load_page_1_duck.json", "r", encoding="utf-8") as f:
        yield json.load(f)
```

### バックフィルに`end_value`を使用する

インクリメンタルローディングを定義するときに、開始日と終了日の両方を指定できます。Githubの例に戻りましょう:

```py
@dlt.resource(primary_key="id")
def repo_issues(
    access_token,
    repository,
    created_at=dlt.sources.incremental("created_at", initial_value="1970-01-01T00:00:00Z", end_value="2022-07-01T00:00:00Z")
):
    # get issues created from the last "created_at" value
    for page in _get_issues_page(access_token, repository, since=created_at.start_value, until=created_at.end_value):
        yield page
```

上記では、`incremental` の `initial_value` 引数と `end_value` 引数を使用して、取得する問題の範囲を定義し、この範囲を Github API (`since` と `until`) に渡しています。上記の例と同様に、`dlt` は定義された範囲の問題のみが返されるようにします。

`end_date` が指定されている場合、`dlt` は **既存の増分状態を変更しません** ので注意してください。バックフィルは **ステートレス** であり、次のようになります:

1. バックフィルと増分ロードを単一のパイプラインで並行して（つまり、Airflow DAG で）実行できます。
2. バックフィルをいくつかの小さなチャンクに分割し、それらを並行して実行することもできます。

ロードする特定の範囲を定義するには、リソース内の増分引数をオーバーライドするだけです。次に例を示します:

```py
july_issues = repo_issues(
    created_at=dlt.sources.incremental(
        initial_value='2022-07-01T00:00:00Z', end_value='2022-08-01T00:00:00Z'
    )
)
august_issues = repo_issues(
    created_at=dlt.sources.incremental(
        initial_value='2022-08-01T00:00:00Z', end_value='2022-09-01T00:00:00Z'
    )
)
...
```

dlt の増分フィルタリングでは、範囲が半分閉じているとみなされることに注意してください。`initial_value` は包括的で、`end_value` は排他的であるため、上記のような範囲の連鎖は重複せずに機能します。この動作は、`range_start` (デフォルトは `"closed"`) および `range_end` (デフォルトは `"open"`) 引数で変更できます。

### 不要なデータを要求しないように行順序を宣言する

`row_order` 引数を設定し、カーソル フィールドの値が **start** 値と **end** 値の範囲外であることを検出すると、dlt はデータソース (GitHub API など) からのデータの取得を停止します。

特に:

* dlt は、リソースが `end_value` と等しいかそれより大きいカーソル値を持つ項目を生成し、`row_order` が **asc** に設定されている場合、処理を停止します。(`end_value` は含まれません)
* dlt は、リソースが `last_value` より _低い_ カーソル値を持つ項目を生成し、`row_order` が **desc** に設定されている場合、処理を停止します。(`last_value` が含まれます)

:::note
ここでの「higher」と「lower」は、デフォルトの `last_value_func` (`max()`) が使用される場合を指します。`min()` を使用する場合、「higher」と「lower」は逆になります。
:::

:::caution
`row_order` を使用する場合は、**データ ソースがカーソル フィールドで順序付けられたレコード (昇順 / 降順) を返すことを確認してください**。
たとえば、API が特定の順序なしで指定された `end_value` よりも高い結果と低い結果の両方を返す場合、データの読み取りが停止し、順序が間違っているデータ項目が失われます。
:::

行順は次のような場合に最も便利です:

1. データ ソースでは、結果の開始/終了フィルタリングは**提供されません** (例: `start_time/end_time` クエリ パラメータなどはありません)。
2. ソースは**カーソル フィールドで順序付けられた**結果を返します。

GitHub イベントの例はまさにそのようなケースです。結果はカーソル値の降順で並べられますが、返される項目を特定の日付より前に作成されたものに限定するように API に指示する方法はありません。`row_order` 設定がなければ、`github_events` リソースを抽出するたびにすべてのイベントが取得されます。

同様に、`row_order` を使って **バックフィルを最適化** し、範囲の終わりに達した後に不要な API リクエストを続行しないようにすることができます。たとえば:

```py
@dlt.resource(primary_key="id")
def tickets(
    zendesk_client,
    updated_at=dlt.sources.incremental(
        "updated_at",
        initial_value="2023-01-01T00:00:00Z",
        end_value="2023-02-01T00:00:00Z",
        row_order="asc"
    ),
):
    for page in zendesk_client.get_pages(
        "/api/v2/incremental/tickets", "tickets", start_time=updated_at.start_value
    ):
        yield page
```

この例では、Zendesk からチケットを読み込んでいます。Zendesk API は、ページ分けされ、古いものから新しいものの順に並べられたアイテムを生成しますが、フィルタリング用に `start_time` パラメータしか提供していないため、`end_value` でデータの取得を停止するように指示することはできません。代わりに、`row_order` を `asc` に設定すると、`dlt` は、カーソル値 `updated_at` を持つ最初のページが `end_value` より古いことが検出された後、API からそれ以上ページを取得できなくなります。

:::caution
まれに、Incremental をトランスフォーマーと共に使用すると、`dlt` は範囲外の行に関連付けられたジェネレーターを自動的に閉じることができません。それでも、incremental で `can_close()` メソッドを呼び出して、true の場合は yield ループを終了することができます。
:::

:::tip
`dlt.sources.incremental` インスタンスは、`start_out_of_range` 属性と `end_out_of_range` 属性を提供します。これらの属性は、リソースが初期値または終了値よりも高い/低いカーソル値を持つ要素を生成するときに設定されます。`dlt` による処理を自動的に停止せず、代わりにこのようなイベントを自分で処理したい場合は、`row_order` を指定しないでください:

```py
@dlt.transformer(primary_key="id")
def tickets(
    zendesk_client,
    updated_at=dlt.sources.incremental(
        "updated_at",
        initial_value="2023-01-01T00:00:00Z",
        end_value="2023-02-01T00:00:00Z",
        row_order="asc"
    ),
):
    for page in zendesk_client.get_pages(
        "/api/v2/incremental/tickets", "tickets", start_time=updated_at.start_value
    ):
        yield page
        # Stop loading when we reach the end value
        if updated_at.end_out_of_range:
            return

```
:::

### 主キーで重複範囲を重複排除する

`Incremental` は、**merge** 書き込み処理のようにデータセットの重複を排除**しません。** ただし、データの別の部分が抽出されるときに、以前にロードされたレコードが再び含まれないようにします。`dlt` は、下限が含まれる (つまり、より大きいか等しい) データの範囲をロードすることを前提としています。これにより、データが失われることがなくなり、一部の行が再取得されます。たとえば、日単位の `updated_at` カーソル フィールドを持つデータベース テーブルがある場合、特定の日にデータを抽出した後、さらにレコードが追加される可能性が高くなります。翌日に抽出するときは、すべてのレコードが存在するように、最終日からデータを再取得する必要があります。ただし、これにより、前回の抽出のデータとの重複が作成されます。

デフォルトでは、重複排除にはコンテンツ ハッシュ (行の JSON 表現のハッシュ) が使用されます。これは遅い場合があるため、`dlt.sources.incremental` はリソースに設定されている主キーを継承します。オプションで、重複排除専用でテーブル ヒントにならない `primary_key` を設定できます。同じ設定で、空のタプルが渡されたときに重複排除を完全に無効にすることもできます。以下では、重複排除を無効にするために `primary_key` を `incremental` に直接渡します。これにより、リソースに設定されている `delta` primary_key が上書きされます。

```py
@dlt.resource(primary_key="delta")
# disable the unique value check by passing () as primary key to incremental
def some_data(last_timestamp=dlt.sources.incremental("item.ts", primary_key=())):
    for i in range(-10, 10):
        yield {"delta": i, "item": {"ts": pendulum.now().timestamp()}}
```

この重複排除プロセスは、`range_start` が `"closed"` (デフォルト) に設定されている場合に常に有効になります。
`range_start="open"` を渡すと、前のカーソル値を持つ行が除外されるため重複排除は不要となり、実行されません。カーソル フィールドが一意であることが保証されている場合、これは重複排除のパフォーマンス オーバーヘッドを回避するための便利な最適化になります。

### 動的に作成されたリソースで `dlt.sources.incremental` を使用する

リソースが[動的に作成される](source.md#create-resources-dynamically)場合は、`dlt.sources.incremental`定義も使用できます。

```py
@dlt.source
def stripe():
    # declare a generator function
    def get_resource(
        endpoints: List[str] = ENDPOINTS,
        created: dlt.sources.incremental=dlt.sources.incremental("created")
    ):
        ...

    # create resources for several endpoints on a single decorator function
    for endpoint in endpoints:
        yield dlt.resource(
            get_resource,
            name=endpoint.value,
            write_disposition="merge",
            primary_key="id"
        )(endpoint)
```

上記の例では、`get_resource` が、エンドポイントをバインドする `dlt.resource` に関数として渡されることに注意してください: **dlt.resource(...)(endpoint)**。

:::caution
よくある間違いは、以下のようにジェネレータ（関数ではない）を渡すことです:

`yield dlt.resource(get_resource(endpoint), name=endpoint.value, write_disposition="merge", primary_key="id")`.

ここでは **get_resource(endpoint)** を呼び出し、リソースが作成される未評価のジェネレーターを作成します。これにより、実行時に `dlt` が **created** 引数を制御できなくなり、`IncrementalUnboundError` 例外が発生します。
:::

### バックフィルとインクリメンタルロードにエアフロースケジュールを使用する

[Airflow タスクを実行する](../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer.md#2-modify-dag-file) ときに、DAG に関連付けられた Airflow スケジュールから `initial_value`/`start_value` および `end_value` を取得するようにリソースをオプトインできます。**Zendesk チケット** リソースに、何千ものチケットを含む 1 年分のデータが含まれていると仮定します。過去 1 年間のデータを週ごとにバックフィルし、その後は毎日増分読み込みを続行します。

```py
@dlt.resource(primary_key="id")
def tickets(
    zendesk_client,
    updated_at=dlt.sources.incremental[int](
        "updated_at",
        allow_external_schedulers=True
    ),
):
    for page in zendesk_client.get_pages(
        "/api/v2/incremental/tickets", "tickets", start_time=updated_at.start_value
    ):
        yield page
```

`allow_external_schedulers` を `True` に設定して、Airflow スケジューラにオプトインします:

1. Airflow 上で実行する場合、開始値と終了値は Airflow によって制御され、dlt [state](state.md) は使用されません。
2. その他のすべての環境では、`incremental` は通常どおり動作し、dlt 状態を維持します。

`dlt deploy zendesk_pipeline.py airflow-composer` を使用してデプロイメントを生成し、DAG をカスタマイズしましょう:

```py
from dlt.helpers.airflow_helper import PipelineTasksGroup

@dag(
    schedule_interval='@weekly',
    start_date=pendulum.DateTime(2023, 2, 1),
    end_date=pendulum.DateTime(2023, 8, 1),
    catchup=True,
    max_active_runs=1,
    default_args=default_task_args
)
def zendesk_backfill_bigquery():
    tasks = PipelineTasksGroup("zendesk_support_backfill", use_data_folder=False, wipe_local_data=True)

    # import zendesk like in the demo script
    from zendesk import zendesk_support

    pipeline = dlt.pipeline(
        pipeline_name="zendesk_support_backfill",
        dataset_name="zendesk_support_data",
        destination='bigquery',
    )
    # select only incremental endpoints in support api
    data = zendesk_support().with_resources("tickets", "ticket_events", "ticket_metric_events")
    # create the source, the "serialize" decompose option will convert dlt resources into Airflow tasks. use "none" to disable it
    tasks.add_run(pipeline, data, decompose="serialize", trigger_rule="all_done", retries=0, provide_context=True)


zendesk_backfill_bigquery()
```

何がカスタマイズできるか:

1. 週単位のスケジュールを使用し、2023 年 2 月 (`start_date`) から 7 月末 (`end_date`) までのデータを取得したいと考えています。
2. Airflow で毎週の実行をすべて生成します (`catchup` は True)。
3. バックフィルする増分リソースのみを選択する `zendesk_support` リソースを作成します。

Airflow で DAG を有効にすると、2 月から 8 月まで複数の実行が生成され、実行が開始されます。リソースには、`2023-02-12、00:00:00 UTC` から `2023-02-19、00:00:00 UTC` までの後続の週次間隔が送信されます。

上記のDAGを再利用して、バックフィル後（またはバックフィル中）に新しいデータを段階的にロードすることができます:

```py
@dag(
    schedule_interval='@daily',
    start_date=pendulum.DateTime(2023, 2, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_task_args
)
def zendesk_new_bigquery():
    tasks = PipelineTasksGroup("zendesk_support_new", use_data_folder=False, wipe_local_data=True)

    # import your source from pipeline script
    from zendesk import zendesk_support

    pipeline = dlt.pipeline(
        pipeline_name="zendesk_support_new",
        dataset_name="zendesk_support_data",
        destination='bigquery',
    )
    tasks.add_run(pipeline, zendesk_support(), decompose="serialize", trigger_rule="all_done", retries=0, provide_context=True)
```

上記では、日次スケジュールに切り替え、キャッチアップと終了日を無効にしています。また、すべてのサポート リソースをバックフィルと同じデータセット (`zendesk_support_data`) にロードします。
この DAG をバックフィル DAG と並行して実行する場合は、パイプライン名を上記のように `zendesk_support_new` などに変更します。

**フードの下**

`dlt` が増分リソースの実行を開始する前に、`data_interval_start` および `data_interval_end` Airflow タスク コンテキスト変数を探します。これらは、`Incremental` クラスの `initial_value` および `end_value` にマッピングされます:

1. `dlt` は、リソースが使用している場合、Airflow の日時を ISO 文字列または Unix タイムスタンプに変換できるほどスマートです。例では、`updated_at=dlt.sources.incremental[int]` をインスタンス化し、最後の値の型を **int** として宣言します。`initial_value` 引数を指定した場合、`dlt` は型を推測することもできます。
2. `data_interval_end` が将来の日付または None の場合、`dlt` は `end_value` を **now** に設定します。
3. `data_interval_start` == `data_interval_end` の場合、DAG 実行は手動でトリガーされます。その場合、`data_interval_end` も **now** に設定されます。

**手動実行**

DAG を手動で実行することもできますが、過去の実行の Airflow 論理日付を指定することを忘れないでください (Run with config オプションを使用)。このような実行の場合、`dlt` はその過去の日付から現在までのすべてのデータをロードします。
過去の日付を指定しないと、範囲 (現在、現在) での実行が行われ、データは生成されません。

### 構成からインクリメンタルローディングのパラメータを読み取る

「config.toml」からインクリメンタルローディングのパラメータを読み取る以下の例を考えてください。「id」、「idAfter」、および「name」を生成する `generate_incremental_records` リソースを作成します。このリソースは、「config.toml」から `cursor_path` と `initial_value` を取得します。

1. 「config.toml」で、`cursor_path`と`initial_value`を次のように定義します:

   ```toml
   # Configuration snippet for an incremental resource
   [pipeline_with_incremental.sources.id_after]
   cursor_path = "idAfter"
   initial_value = 10
   ```

   `cursor_path` には、初期値 10 の "idAfter" という値が割り当てられます。

1. `generate_incremental_records` リソースが "config.toml" で定義された `cursor_path` を使用する方法は次のとおりです:

   ```py
   @dlt.resource(table_name="incremental_records")
   def generate_incremental_records(id_after: dlt.sources.incremental = dlt.config.value):
       for i in range(150):
           yield {"id": i, "idAfter": i, "name": "name-" + str(i)}

   pipeline = dlt.pipeline(
       pipeline_name="pipeline_with_incremental",
       destination="duckdb",
   )

   pipeline.run(generate_incremental_records)
   ```

   `id_after` は、将来のパイプライン実行のために最新の `cursor_path` 値を増分的に保存します。

### 増分カーソル パスが見つからないか、値が None/NULL の場合のロード

パラメータ `on_cursor_value_missing` を設定することで、dlt の増分処理をカスタマイズできます。

デフォルト設定で段階的にロードする場合、2つの前提があります:

1. 各行にはカーソルのパスが含まれます。
2. 各行には、カーソル パスに `None`以外の値が含まれている必要があります。

たとえば、次の2つのソースデータはエラーを発生させます:

```py
@dlt.resource
def some_data_without_cursor_path(updated_at=dlt.sources.incremental("updated_at")):
    yield [
        {"id": 1, "created_at": 1, "updated_at": 1},
        {"id": 2, "created_at": 2},  # cursor field is missing
    ]

list(some_data_without_cursor_path())

@dlt.resource
def some_data_without_cursor_value(updated_at=dlt.sources.incremental("updated_at")):
    yield [
        {"id": 1, "created_at": 1, "updated_at": 1},
        {"id": 3, "created_at": 4, "updated_at": None},  # value at cursor field is None
    ]

list(some_data_without_cursor_value())
```


一部のレコードに増分カーソルパスが含まれていない、またはカーソルパスの値が `None` であるデータセットを処理するには、次の4つのオプションがあります。:

1. `incremental(..., on_cursor_value_missing="raise")` を使用して、カーソルパスが欠落しているか、値が `None` である行がある場合に例外を発生させるようにインクリメンタルロードを構成します。これがデフォルトの動作です。
2. `incremental(..., on_cursor_value_missing="include")` を使用して、欠落しているカーソル パスと `None` 値を許容するようにインクリメンタルロードを構成します。
3. `incremental(..., on_cursor_value_missing="exclude")` を使用して、欠落しているカーソル パスと `None` 値を除外するようにインクリメンタルロードを構成します。
4. 増分処理を開始する前に、増分フィールドが存在することを確認し、増分カーソルの値を `None` 以外の値に変換します。[以下のドキュメントを参照](#transform-records-before-incremental-processing)

増分カーソル値が欠落しているか `None` である行を含める例を次に示します。

```py
@dlt.resource
def some_data(updated_at=dlt.sources.incremental("updated_at", on_cursor_value_missing="include")):
    yield [
        {"id": 1, "created_at": 1, "updated_at": 1},
        {"id": 2, "created_at": 2},
        {"id": 3, "created_at": 4, "updated_at": None},
    ]

result = list(some_data())
assert len(result) == 3
assert result[1] == {"id": 2, "created_at": 2}
assert result[2] == {"id": 3, "created_at": 4, "updated_at": None}
```

カーソルパスのないレコードやカーソルパスの値が `None` であるレコードをインポートしたくない場合は、次のインクリメンタル構成を使用します:

```py
@dlt.resource
def some_data(updated_at=dlt.sources.incremental("updated_at", on_cursor_value_missing="exclude")):
    yield [
        {"id": 1, "created_at": 1, "updated_at": 1},
        {"id": 2, "created_at": 2},
        {"id": 3, "created_at": 4, "updated_at": None},
    ]

result = list(some_data())
assert len(result) == 1
```

### 増分処理の前にレコードを変換する

`None` 値を含むデータをロードする場合は、増分処理の前にレコードを変換できます。
[データをフィルター処理、変換、またはピボットする](../general-usage/resource.md#filter-transform-and-pivot-data) 手順をパイプラインに追加できます。

:::caution
実行順序を制御し、増分処理の開始前にカスタム ステップが実行されるようにするには、`add_map` 関数の `insert_at` パラメータを設定することが重要です。
次の例では、データ生成のステップは `index = 0`、カスタム変換は `index = 1`、増分処理は `index = 2` です。
:::

`add_map()` を使用して増分処理の前に行を変更する方法と、`add_filter()` を使用して行をフィルター処理する方法については、以下を参照してください。

```py
@dlt.resource
def some_data(updated_at=dlt.sources.incremental("updated_at")):
    yield [
        {"id": 1, "created_at": 1, "updated_at": 1},
        {"id": 2, "created_at": 2, "updated_at": 2},
        {"id": 3, "created_at": 4, "updated_at": None},
    ]

def set_default_updated_at(record):
    if record.get("updated_at") is None:
        record["updated_at"] = record.get("created_at")
    return record

# Modifies records before the incremental processing
with_default_values = some_data().add_map(set_default_updated_at, insert_at=1)
result = list(with_default_values)
assert len(result) == 3
assert result[2]["updated_at"] == 4

# Removes records before the incremental processing
without_none = some_data().add_filter(lambda r: r.get("updated_at") is not None, insert_at=1)
result_filtered = list(without_none)
assert len(result_filtered) == 2
```

##  Lag / Attribution Window

多くの場合、インクリメンタルローディング中に特定のデータを再取得する必要があります。たとえば、毎日の分析レポートを取得するときに常に過去 7 日間のデータを取得したり、7 日間の移動ウィンドウで Slack メッセージの返信を更新したりする必要がある場合があります。ここで、「lag」または「attribution window」の概念が役立ちます。

`lag` パラメータは、`datetime`、`date`、`integer`、および `float` のいくつかのタイプの増分カーソルをサポートする float です。`last_value_func` が `min` または `max` (デフォルトは `max`) に設定されている場合にのみ使用できます。

### `lag` の仕組み

- **Datetime cursors**: `lag` は、ロードされた `last_value` から加算または減算される秒数です。
- **Date cursors**: `lag` は日数を表します。
- **Numeric cursors (integer or float)**: `lag` はカーソルの指定された単位を尊重します。

この柔軟性により、`lag` はさまざまなデータ コンテキストに適応できます。

### `write_disposition` として `merge` を使用した `datetime` 増分カーソルの使用例

この例では、`lag` パラメータを使用して `datetime` カーソルを使用し、`write_disposition` として `merge` を適用する方法を示します。セットアップは 2 回実行され、2 回目の実行中に、`lag` パラメータは最新のエントリを再取得して更新をキャプチャします。

1. **First Run**: `initial_entries` を読み込みます。
2. **Second Run**: 指定されたラグで `second_run_events` をロードし、以前にロードされたエントリを更新します。

この設定は、`lag` によって定義された期間のデータが更新され、attribution window 内で更新または変更がキャプチャされる仕組みを示しています。

```py
pipeline = dlt.pipeline(
    destination=dlt.destinations.duckdb(credentials=duckdb.connect(":memory:")),
)

# Flag to indicate the second run
is_second_run = False

@dlt.resource(name="events", primary_key="id", write_disposition="merge")
def events_resource(
    _=dlt.sources.incremental("created_at", lag=3600, last_value_func=max)
):
    global is_second_run

    # Data for the initial run
    initial_entries = [
        {"id": 1, "created_at": "2023-03-03T01:00:00Z", "event": "1"},
        {"id": 2, "created_at": "2023-03-03T02:00:00Z", "event": "2"},  # lag applied during second run
    ]

    # Data for the second run
    second_run_events = [
        {"id": 1, "created_at": "2023-03-03T01:00:00Z", "event": "1_updated"},
        {"id": 2, "created_at": "2023-03-03T02:00:01Z", "event": "2_updated"},
        {"id": 3, "created_at": "2023-03-03T03:00:00Z", "event": "3"},
    ]

    # Yield data based on the current run
    yield from second_run_events if is_second_run else initial_entries

# Run the pipeline twice
pipeline.run(events_resource)
is_second_run = True  # Update flag for second run
pipeline.run(events_resource)
```


## 完全なリフレッシュを行う

`merge` および `append` パイプラインの完全な更新を強制することができます:

1. `merge` の場合、宛先のデータは削除され、新しくロードされます。現在、完全更新中にデータの重複排除は行われません。
1. `dlt.sources.incremental` の場合、データは削除され、最初からロードされます。増分の状態は初期値にリセットされます。

例:

```py
p = dlt.pipeline(destination="bigquery", dataset_name="dataset_name")
# Do a full refresh
p.run(merge_source(), write_disposition="replace")
# Do a full refresh of just one table
p.run(merge_source().with_resources("merge_table"), write_disposition="replace")
# Run a normal merge
p.run(merge_source())
```

書き込み処理を `replace` に渡すと、パイプラインの実行中に `repo_events` 内のすべてのリソースの書き込み処理が変更されます。

## パイプライン状態によるカスタムなインクリメンタルローディング

パイプラインの状態は、データとともにアトミックにコミットされる Python 辞書です。リソース内でその値を設定し、次回のパイプライン実行時にその値を要求することが可能です。

パイプラインの状態は、原則としてリソースにスコープが設定されます。リソースによって設定された状態のすべての値はプライベートであり、他のリソースから分離されています。ソース スコープの状態にアクセスすることもできます。これは、リソース間で共有できます。
[パイプラインの状態の詳細については、こちらを参照してください](state.md#pipeline-state)。

### リソース状態の最後の値を保持する

「最後の値」または同様の読み込みチェックポイントを保持する目的で、以下のようにキーとデフォルト値を持つ dlt 状態辞書を開くことができます。リソースが実行され、データがロードされると、生成されたリソース データは状態の更新と同時にロードされます。

以下の 2 つの例では、`dlt.sources.incremental` が内部でどのように動作しているかがわかります。

```py
@resource()
def tweets():
    # Get the last value from loaded metadata. If it does not exist, get None
    last_val = dlt.current.resource_state().setdefault("last_updated", None)
    # Get data and yield it
    data = _get_data(start_from=last_val)
    yield data
    # Change the state to the new value
    dlt.current.resource_state()["last_updated"] = data["last_timestamp"]
```

リストまたは辞書を状態に保持すると、オブジェクト内の基礎となる値を変更できるため、状態を明示的に元に戻す必要がなくなります。

```py
@resource()
def tweets():
    # Get the last value from loaded metadata. If it does not exist, get None
    loaded_dates = dlt.current.resource_state().setdefault("days_loaded", [])
    # Do stuff: get data and add new values to the list
    # `loaded_date` is a reference to the `dlt.current.resource_state()["days_loaded"]` list
    # and thus modifying it modifies the state
    yield data
    loaded_dates.append('2023-01-01')
```

状態を取得または設定する方法のステップバイステップの説明:

1. 関数 `var = dlt.current.resource_state().setdefault("key", [])` を使用できます。これにより、`key` の値を取得できます。`key` がまだ設定されていない場合は、代わりにデフォルト値 `[]` が取得されます。
2. これで、`var` を Python リストとして扱うことができるようになりました。新しい値を追加したり、該当する場合は以前のロードから値を読み取ったりすることができます。
3. パイプラインを実行すると、データが読み込まれ、新しい `var` の値が状態に保存されます。状態は宛先に保存されるため、後続の実行で使用できます。

### 高度な状態の使用法: 処理されたエンティティのリストの保存

チェス パイプラインの `player_games` リソースを見てみましょう。チェス API には、特定の月のゲーム アーカイブを要求するメソッドがあります。そのタスクは、ユーザーが間違って同じ月の範囲を再度要求した場合でも、同じ月のデータを 2 回ロードしないようにすることです:

- データは 2 つのステップで要求されます:
  - 利用可能なすべてのアーカイブ URL を取得します。
  - 各 URL からデータを取得します。
- 作成したこのリストに「チェス アーカイブ」の URL を追加します。
- これにより、ロードしたデータを追跡できるようになります。
- データがロードされると、アーカイブのリストも一緒にロードされます。
- 後でこのリストを読み取って、どのデータがすでにロードされているかを知ることができます。

次の例では、空のリストをデフォルトとして変数を初期化します:

```py
@dlt.resource(write_disposition="append")
def players_games(chess_url, players, start_month=None, end_month=None):
    loaded_archives_cache = dlt.current.resource_state().setdefault("archives", [])

    # As far as Python is concerned, this variable behaves like
    # loaded_archives_cache = state['archives'] or []
    # Afterwards, we can modify the list, and finally
    # when the data is loaded, the cache is updated with our loaded_archives_cache

    # Get archives for a given player
    archives = _get_players_archives(chess_url, players)
    for url in archives:
        # If not in cache, yield the data and cache the URL
        if url not in loaded_archives_cache:
            # Add URL to cache and yield the associated data
            loaded_archives_cache.append(url)
            r = requests.get(url)
            r.raise_for_status()
            yield r.json().get("games", [])
        else:
            print(f"Skipping archive {url}")
```

### 高度な状態の使用: Twitter API のすべての検索用語の最後の値を追跡する

```py
@dlt.resource(write_disposition="append")
def search_tweets(twitter_bearer_token=dlt.secrets.value, search_terms=None, start_time=None, end_time=None, last_value=None):
    headers = _headers(twitter_bearer_token)
    for search_term in search_terms:
        # Make cache for each term
        last_value_cache = dlt.current.resource_state().setdefault(f"last_value_{search_term}", None)
        print(f'last_value_cache: {last_value_cache}')
        params = {...}
        url = "https://api.twitter.com/2/tweets/search/recent"
        response = _get_paginated(url, headers=headers, params=params)
        for page in response:
            page['search_term'] = search_term
            last_id = page.get('meta', {}).get('newest_id', 0)
            # Set it back - not needed if we
            dlt.current.resource_state()[f"last_value_{search_term}"] = max(last_value_cache or 0, int(last_id))
            # Print the value for each search term
            print(f'new_last_value_cache for term {search_term}: {last_value_cache}')

            yield page
```

## トラブルシューティング

インクリメンタルローディングが期待どおりに機能せず、パイプラインの実行間で増分値が変更されない場合は、次の点を確認してください。

1. パイプラインの実行間で、`destination`、`pipeline_name`、および `dataset_name` が同じであることを確認します。

2. パイプライン構成で `dev_mode` が `False` になっているかどうかを確認します。関連するソースとリソースの `refresh` が有効になっていないかどうかを確認します。

3. ログで`Bind incremental on <resource_name> ...` メッセージを確認します。このメッセージは、増分値がリソースにバインドされたことを示し、増分値の状態を示します。

4. パイプラインの実行後、パイプラインの状態を確認します。これは、次のコマンドを実行して実行できます:

```sh
dlt pipeline -v <pipeline_name> info
```

たとえば、パイプラインが次のように定義されているとします:

```py
@dlt.resource
def my_resource(
    incremental_object = dlt.sources.incremental("some_key", initial_value=0),
):
    ...

pipeline = dlt.pipeline(
    pipeline_name="example_pipeline",
    destination="duckdb",
)

pipeline.run(my_resource)
```

次の出力が表示されます:

```text
Attaching to pipeline <pipeline_name>
...

sources:
{
  "example": {
    "resources": {
      "my_resource": {
        "incremental": {
          "some_key": {
            "initial_value": 0,
            "last_value": 42,
            "unique_hashes": [
              "nmbInLyII4wDF5zpBovL"
            ]
          }
        }
      }
    }
  }
}
```

パイプラインの実行間で `last_value` が更新されていることを確認します。

