---
title: Cursor-based incremental loading
description: Track changes using cursor fields with dlt
keywords: [incremental loading, cursor, timestamp, last_value]
---

# カーソルベースの増分ロード

ほとんどのREST API（およびその他のデータソース、つまりデータベーステーブル）では、「最後の」レコードのタイムスタンプまたはIDをクエリに渡すことで、新規データまたは更新データをリクエストできます。API/データベースは、次回のロード時に最大/最小のタイムスタンプ/IDを取得するために、新規/更新されたレコードのみを返します。

この方法で増分ロードを行うには、以下の手順が必要です。

- 変更を追跡するために使用するフィールド（いわゆる**カーソルフィールド**）を特定します（例："inserted_at"、"updated_at" など）。
- 新規データまたは変更されたデータのみを取得するために、カーソルフィールドの「最後の」（最大/最小）値をAPIに渡す方法を決定します（方法はソースAPIによって異なります）。

一度理解してしまえば、`dlt` はカーソルフィールドの最大値/最小値の検出、重複の削除、そしてカーソルの最後の値による状態管理などをすべて処理してくれます。以下の GitHub の例をご覧ください。ここでは最近作成された Issue をリクエストしています。

```py
@dlt.resource(primary_key="id")
def repo_issues(
    access_token=dlt.secrets.value,
    repository=dlt.config.value,
    updated_at = dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    # Get issues since "updated_at" stored in state on previous run (or initial_value on first run)
    for page in _get_issues_page(access_token, repository, since=updated_at.start_value):
        yield page
        # Last_value is updated after every page
        print(updated_at.last_value)
```

ここでは、`1970-01-01T00:00:00Z` に初期化された増分状態を受け取る `updated_at` 引数を追加します。これは、`repo_issues` リソースによって生成された Issue の `updated_at` フィールドを追跡するように構成されています。最新の `updated_at` 値が `dlt` [state](../state.md) に保存され、次回のパイプライン実行時に `updated_at.start_value` で使用できるようになります。この値は、`_get_issues_page` 関数の [GitHub API](https://docs.github.com/en/rest/issues/issues?#list-repository-issues) へのリクエストクエリパラメータ **since** に挿入されます。

本質的には、上記の `dlt.sources.incremental` インスタンスは以下のようになります。
* **updated_at.initial_value** は、コンストラクタに渡される「1970-01-01T00:00:00Z」と常に等しくなります。
* **updated_at.start_value** は、前回の実行時の最大の `updated_at` 値、または初回実​​行時の **initial_value** です。
* **updated_at.last_value** は、生成されるアイテムまたはページごとに更新される「リアルタイム」の `updated_at` 値です。最初のyieldの前は、**start_value** と等しくなります。
* **updated_at.end_value** (ここでは使用されません) [バックフィル範囲の終了を示す](#using-end_value-for-backfill)

ページネーションを行う場合、リソースの実行中に変化しない **start_value** が必要になる可能性があります。ただし、ほとんどのページネータは **次のページ** へのリンクを返すので、これを使用する必要があります。

dltは、バックグラウンドで結果の重複を排除します。つまり、最後の問題が再度返される場合（`updated_at`フィルタは含まれます）、すでにロードされている問題はスキップします。

以下の例では、GitHubイベントを段階的にロードします。APIでは最新のイベントをフィルタリングできず、常にすべてのイベントが返されます。それでも、`dlt`は新しい項目のみをロードし、重複と過去の問題をすべて除外します。
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

すべてのイベントをyieldし、`dlt`がフィルタリングを行います（`primary_key`として宣言された`id`列を使用）。

GitHubは新しいイベントから古いイベントの順に返します。そこで、`rows_order`を**descending**として宣言し、[増分値が範囲外になった場合にそれ以上のページをリクエストしないようにする](#declare-row-order-to-not-request-unnecessary-data)。`created_at`が`initial_value`よりも前の最初のイベントを見つけた後、APIからそれ以上のデータをリクエストしないようにします。

:::note
`dlt.sources.incremental` は [フィルター関数](../resource.md#filter-transform-and-pivot-data) として実装されており、`add_map` または `add_filter` で追加した他のすべての変換の **後** に実行されます。つまり、増分フィルターがデータ項目を認識する前に、そのデータ項目を操作できます。例:
* 他の列から代理主キーを作成できます。
* カーソル値を変更したり、他のフィールドで構成される新しいフィールドを作成したりできます。
* Pydantic モデルを Python 辞書にダンプして、増分フィルターがカスタム値を検出できるようにします。

[Pydantic によるデータ検証](../schema-contracts.md#use-pydantic-models-for-data-validation) は、増分フィルタリングの **前** に実行されます。
:::

## 最大値、最小値、またはカスタムの `last_value_func`

`dlt.sources.incremental` を使用すると、カーソル値を現在の `last_value` に順序付け（比較）する関数を選択できます。
* デフォルトの関数は組み込み関数の `max` で、2 つの値のうち大きい方の値を返します。
* もう一つの組み込み関数である `min` は、小さい方の値を返します。

カスタム関数を渡すこともできます。これにより、ネストされた型（つまり辞書）に `last_value` を定義し、単純な型だけでなく、最後の値のインデックスを格納できます。`last_value` 引数は [JSON パス](https://github.com/json-path/JsonPath#operators) であり、ネストされたデータ（`$` を使用した場合はデータ項目全体を含む）を選択できます。
以下の例では、作成されたテーブル名ごとに最大の `created_at` 値を保持する辞書である最後の値を作成します。

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

## バックフィルに `end_value` を使用する

増分ロードを定義する際に、開始日と終了日の両方を指定できます。GitHub の例に戻りましょう。
```py
@dlt.resource(primary_key="id")
def repo_issues(
    access_token=dlt.secrets.value,
    repository=dlt.config.value,
    updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z", end_value="2022-07-01T00:00:00Z")
):
    # get issues updated in range defined by incremental
    for page in _get_issues_page(access_token, repository, since=updated_at.start_value, until=updated_at.end_value):
        yield page
```
上記では、`incremental` の `initial_value` 引数と `end_value` 引数を使用して、取得する問題の範囲を定義し、この範囲を Github API に渡しています（`since` と `until`）。上記の例と同様に、`dlt` は定義された範囲の問題のみが返されるようにします。

`end_date` が指定されている場合、`dlt` は**既存の増分状態を変更しない**ことに注意してください。バックフィルは**ステートレス**であり、次のようになります。
1. バックフィルと増分ロードを単一のパイプラインで並行して（つまり、Airflow DAG 内で）実行できます。
2. バックフィルを複数の小さなチャンクに分割し、それらを並行して実行することもできます。

ロードする特定の範囲を定義するには、リソースの incremental 引数をオーバーライドするだけです。例:

```py
july_issues = repo_issues(
    updated_at=dlt.sources.incremental(
        initial_value='2022-07-01T00:00:00Z', end_value='2022-08-01T00:00:00Z'
    )
)
august_issues = repo_issues(
    updated_at=dlt.sources.incremental(
        initial_value='2022-08-01T00:00:00Z', end_value='2022-09-01T00:00:00Z'
    )
)
...
```

dlt の増分フィルタリングでは、範囲が半分閉じているとみなされることに注意してください。`initial_value` は範囲を含み、`end_value` は範囲を含まないため、上記のように範囲を連結しても重複は発生しません。この動作は、`range_start`（デフォルトは `"closed"`）および `range_end`（デフォルトは `"open"`）引数で変更できます。

## 不要なデータを要求しないように行順序を宣言します。

`row_order` 引数を設定すると、カーソルフィールドの値が **start** と **end** の範囲外にあることを検出すると、dlt はデータソース（GitHub API など）からのデータの取得を停止します。

具体的には、次のようになります。
* dlt は、リソースが `end_value` 以上のカーソル値を持つアイテムを生成し、かつ `row_order` が **asc** に設定されている場合に処理を停止します。(`end_value` は含まれません)
* dlt は、リソースが `last_value` より小さいカーソル値を持つアイテムを生成し、かつ `row_order` が **desc** に設定されている場合に処理を停止します。(`last_value` は含まれます)

:::note
ここでの「高い」と「低い」は、デフォルトの `last_value_func` (`max()`) が使用される場合を指し、`min()` を使用する場合は「高い」と「低い」が逆になります。
:::

:::caution
`row_order` を使用する場合は、**データ ソースがカーソル フィールドで順序付けられたレコード (昇順 / 降順) を返すことを確認してください**。たとえば、API が指定された `end_value` よりも高い結果と低い結果を特定の順序なしで返す場合、データの読み取りが停止し、順序が狂ったデータ項目が失われます。
:::

行順序は、次のような場合に最も役立ちます。

1. データソースが結果の開始/終了フィルタリングを**提供していない**場合（例：`start_time/end_time` クエリパラメータなどがない場合）。
2. ソースが **カーソルフィールドで順序付けられた** 結果を返す場合。

GitHub イベントの例はまさにこのようなケースです。結果はカーソル値の降順で順序付けられますが、返される項目を特定の日付より前に作成されたものに限定するように API に指示する方法がありません。`row_order` 設定がないと、`github_events` リソースを抽出するたびにすべてのイベントが取得されてしまいます。

同様に、`row_order` を使用して **バックフィルを最適化** することで、範囲の終わりに達した後も不要な API リクエストが繰り返されないようにすることができます。例:

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

この例では、Zendeskからチケットを読み込んでいます。Zendesk APIは、古いものから新しいものの順にページ分けされたアイテムを返しますが、フィルタリングには`start_time`パラメータしか提供されていないため、`end_value`でデータの取得を停止することはできません。代わりに、`row_order`を`asc`に設定すると、`dlt`はカーソル値`updated_at`を持つ最初のページが`end_value`よりも古いことが検出された時点で、APIからそれ以上のページを取得できなくなります。

:::caution
稀に、Incremental をトランスフォーマーと併用すると、`dlt` は範囲外の行に関連付けられたジェネレーターを自動的に閉じることができません。
それでも、incremental で `can_close()` メソッドを呼び出し、true の場合は yield ループを終了することができます。
:::

:::tip
`dlt.sources.incremental` インスタンスは、`start_out_of_range` 属性と `end_out_of_range` 属性を提供します。これらの属性は、リソースが初期値または終了値よりも高い/低いカーソル値を持つ要素を生成したときに設定されます。
`dlt` による処理を自動的に停止せず、このようなイベントを自分で処理したい場合は、`row_order` を指定しないでください。
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

## 主キーによる重複範囲の重複排除

`Incremental` は、**merge** 書き込み処理のようにデータセットの重複排除は**行いません**。ただし、データの別の部分を抽出する際に、以前にロードされたレコードが再び含まれないようにします。`dlt` は、下限値が包含的（つまり、より大きいか等しい）なデータ範囲をロードすることを前提としています。これにより、データが失われることはありませんが、一部の行は再取得されます。例えば、`updated_at` に日単位のカーソルフィールドを持つデータベーステーブルがある場合、特定の日にデータを抽出した後でも、さらにレコードが追加される可能性が高くなります。翌日にデータを抽出する際は、すべてのレコードが揃っていることを確認するために、最終日のデータを再取得する必要があります。ただし、これにより、前回の抽出データとの重複が発生します。

デフォルトでは、コンテンツハッシュ（行の JSON 表現のハッシュ）が重複排除に使用されます。これは遅くなる可能性があるため、`dlt.sources.incremental` はリソースに設定されている主キーを継承します。オプションで、重複排除専用でテーブルヒントにならない `primary_key` を設定することもできます。同じ設定で、空のタプルが渡されたときに重複排除を完全に無効にすることもできます。以下では、重複排除を無効にするために `primary_key` を `incremental` に直接渡しています。これにより、リソースに設定されている `delta` primary_key がオーバーライドされます。

```py
@dlt.resource(primary_key="delta")
# disable the unique value check by passing () as primary key to incremental
def some_data(last_timestamp=dlt.sources.incremental("item.ts", primary_key=())):
    for i in range(-10, 10):
        yield {"delta": i, "item": {"ts": pendulum.now().timestamp()}}
```

この重複排除プロセスは、`range_start` が `"closed"` (デフォルト) に設定されている場合は常に有効です。
`range_start="open"` を指定した場合は、前のカーソル値を持つ行が除外されるため重複排除は不要となり、実行されません。カーソルフィールドが一意であることが保証されている場合、これは重複排除によるパフォーマンスのオーバーヘッドを回避するための有効な最適化となります。

## 動的に作成されたリソースで `dlt.sources.incremental` を使用する

リソースが[動的に作成](../source.md#create-resources-dynamically)される場合も、`dlt.sources.incremental` 定義を使用できます。

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

上記の例では、`get_resource` が関数として `dlt.resource` に渡され、エンドポイントがバインドされていることに注意してください: **dlt.resource(...)(endpoint)**。

:::caution
よくある間違いは、以下のようにジェネレーター（関数ではなく）を渡すことです。

`yield dlt.resource(get_resource(endpoint), name=endpoint.value, write_disposition="merge", primary_key="id")`.

ここでは **get_resource(endpoint)** を呼び出し、リソースを作成するための未評価のジェネレータを作成します。これにより、`dlt` は実行時に **created** 引数を制御できなくなり、`IncrementalUnboundError` 例外が発生します。
:::

## Airflow スケジュールを使用したバックフィルと増分ロード

[Airflow タスクの実行](../../walkthroughs/deploy-a-pipeline/deploy-with-airflow-composer.md#2-modify-dag-file) 時に、DAG に関連付けられた Airflow スケジュールから `initial_value`/`start_value` および `end_value` を取得するようにリソースをオプトインできます。**Zendesk チケット** リソースに、数千件のチケットを含む 1 年分のデータが含まれていると仮定します。過去 1 年間のデータを週ごとにバックフィルし、その後は毎日増分ロードを継続します。

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

`allow_external_schedulers` を `True` に設定することで、Airflow スケジューラを有効にします。
1. Airflow 上で実行する場合、開始値と終了値は Airflow によって制御され、dlt [state](../state.md) は使用されません。
2. その他の環境では、`incremental` は通常どおり動作し、dlt の状態が維持されます。

`dlt deploy zendesk_pipeline.py airflow-composer` でデプロイメントを生成し、DAG をカスタマイズしてみましょう。

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

カスタマイズ内容：
1. 週次スケジュールを使用し、2023年2月（`start_date`）から7月末（`end_date`）までのデータを取得します。
2. Airflow ですべての週次実行を生成するようにします（`catchup` は True）。
3. バックフィルする増分リソースのみを選択する `zendesk_support` リソースを作成します。

Airflow で DAG を有効にすると、2月から8月まで複数の実行が生成され、実行されます。リソースには、`2023-02-12, 00:00:00 UTC` から `2023-02-19, 00:00:00 UTC` までの週次間隔が送信されます。

上記の DAG を再利用して、バックフィル後（またはバックフィル中）に新しいデータを増分的にロードできます。

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

上記では、日次スケジュールに切り替え、キャッチアップと終了日の設定を無効にしています。また、すべてのサポートリソースをバックフィルと同じデータセット（`zendesk_support_data`）にロードしています。
このDAGをバックフィルDAGと並行して実行する場合は、パイプライン名を上記のように（例えば`zendesk_support_new`）に変更してください。

**内部処理**

`dlt` は増分リソースの実行を開始する前に、Airflow タスクコンテキスト変数 `data_interval_start` と `data_interval_end` を探します。これらは、`Incremental` クラスの `initial_value` と `end_value` にマッピングされます。
1. `dlt` は、リソースが ISO 文字列または Unix タイムスタンプを使用している場合、Airflow の datetime をそれらに変換します。この例では、`updated_at=dlt.sources.incremental[int]` をインスタンス化し、最後の値の型を **int** として宣言しています。`dlt` は、`initial_value` 引数を指定すれば型を推論することもできます。
2. `data_interval_end` が将来の日付または None の場合、`dlt` は `end_value` を **now** に設定します。
3. `data_interval_start` == `data_interval_end` の場合、DAG 実行は手動でトリガーされます。この場合、`data_interval_end` も **now** に設定されます。

**手動実行**

DAG を手動で実行することは可能ですが、Airflow の論理日付を過去の日付で指定する必要があります（「Run with config」オプションを使用）。このような実行では、`dlt` は指定された日付から現在までのすべてのデータを読み込みます。
過去の日付を指定しない場合は、範囲指定（現在、現在）による実行となり、データは生成されません。

## 設定から増分読み込みパラメータを読み取る

「config.toml」から増分読み込みパラメータを読み取る以下の例を考えてみましょう。「id」、「idAfter」、「name」を生成する `generate_incremental_records` リソースを作成します。このリソースは、「config.toml」から `cursor_path` と `initial_value` を取得します。

1. 「config.toml」で、`cursor_path` と `initial_value` を次のように定義します。
   ```toml
   # Configuration snippet for an incremental resource
   [pipeline_with_incremental.sources.id_after]
   cursor_path = "idAfter"
   initial_value = 10
   ```

`cursor_path` には、初期値 10 の「idAfter」という値が割り当てられます。

1. `generate_incremental_records` リソースが「config.toml」で定義された `cursor_path` を使用する方法を以下に示します。
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
   `id_after` incrementally stores the latest `cursor_path` value for future pipeline runs.

## 増分カーソルパスが欠落しているか、値が None/NULL の場合のロード

パラメータ `on_cursor_value_missing` を設定することで、dlt の増分処理をカスタマイズできます。

デフォルト設定で増分ロードする場合、次の 2 つの前提があります。
1. 各行にカーソルパスが含まれます。
2. 各行には、カーソルパスに `None` 以外の値が含まれていることが想定されます。

例えば、次の 2 つのソースデータはエラーになります。
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


一部のレコードに増分カーソルパスが含まれていない、またはカーソルパスの値が「None」であるデータセットを処理するには、次の4つのオプションがあります。

1. `incremental(..., on_cursor_value_missing="raise")` を使用して、カーソルパスが欠落している行またはカーソルパスの値が「None」である行がある場合に例外を発生させるように増分ロードを設定します。これはデフォルトの動作です。
2. `incremental(..., on_cursor_value_missing="include")` を使用して、欠落しているカーソルパスと「None」値を許容するように増分ロードを設定します。
3. `incremental(..., on_cursor_value_missing="exclude")` を使用して、欠落しているカーソルパスと「None」値を除外するように増分ロードを設定します。
4. 増分処理を開始する前に、増分フィールドが存在することを確認し、増分カーソルの値を「None」以外の値に変換します。 [以下のドキュメントを参照](#transform-records-before-incremental-processing)

増分カーソル値が欠落しているか「None」である行を含める例を次に示します。
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

カーソル パスのないレコード、またはカーソル パスの値が `None` であるレコードをインポートしたくない場合は、次の増分構成を使用します。

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

## 増分処理の前にレコードを変換する
「None」値を含むデータをロードする場合は、増分処理の前にレコードを変換できます。
パイプラインに[データのフィルタリング、変換、またはピボット](../resource.md#filter-transform-and-pivot-data)を実行するステップを追加できます。

:::caution
実行順序を制御し、増分処理の開始前にカスタムステップが実行されるようにするには、`add_map` 関数の `insert_at` パラメータを設定することが重要です。
次の例では、データ生成のステップは `index = 0`、カスタム変換は `index = 1`、増分処理は `index = 2` で実行されます。
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