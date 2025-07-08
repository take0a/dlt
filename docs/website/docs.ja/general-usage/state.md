---
title: State
description: Explanation of what a dlt state is
keywords: [state, metadata, dlt.current.resource_state, dlt.current.source_state]
---

# 状態

パイプラインの状態は、データと一緒に存在する Python 辞書です。そこに値を保存し、次回のパイプライン実行時に値を戻すように要求できます。

## リソース内のパイプラインの状態の読み取りと書き込み {#read-and-write-pipeline-state-in-a-resource}

リソースの状態を読み書きします。以下では、状態を使用してチェスの試合のアーカイブのリストを作成し、それを使用して [重複したリクエストを防止](incremental/advanced-state.md#advanced-state-usage-storing-a-list-of-processed-entities) します。

```py
@dlt.resource(write_disposition="append")
def players_games(chess_url, player, start_month=None, end_month=None):
    # create or request a list of archives from resource-scoped state
    checked_archives = dlt.current.resource_state().setdefault("archives", [])
    # get a list of archives for a particular player
    archives = _get_players_archives(chess_url, player)
    for url in archives:
        if url in checked_archives:
            print(f"skipping archive {url}")
            continue
        else:
            print(f"getting archive {url}")
            checked_archives.append(url)
        # get the filtered archive
        r = requests.get(url)
        r.raise_for_status()
        yield r.json().get("games", [])
```

上記では、リソース スコープの状態を要求しています。`archives` 辞書キーの下に格納されている `checked_archives` リストはプライベートであり、`players_games` リソースにのみ表示されます。

パイプラインの状態は [パイプライン作業ディレクトリ](pipeline.md#pipeline-working-directory) にローカルに保存されるため、異なる名前のパイプラインと共有することはできません。また、状態に書き込まれるデータが JSON シリアル化可能であることを確認する必要があります。標準の Python 型以外に、`dlt` は `DateTime`、`Decimal`、`bytes`、および `UUID` を処理します。

## リソース間で状態を共有し、ソース内の状態を読み取る

また、`dlt.current.source_state()` を使用してソース スコープの状態にアクセスすることもできます。これは、特定のソースのリソース間で共有でき、ソース装飾関数では読み取り専用で使用できます。ソース スコープの状態の最も一般的な使用例は、カスタム フィールドと表示可能な名前のマ​​ッピングを保存することです。リソース間で渡される状態の例については、[pipedrive ソース](https://github.com/dlt-hub/verified-sources/blob/master/sources/pipedrive/__init__.py#L118) を参照してください。

:::tip
[ソースを分解](../reference/performance.md#source-decomposition-for-serial-and-parallel-resource-execution)して、たとえば Airflow で並列実行します。これを避けられない場合は、リソースの 1 つを状態ライターとして指定し、その他すべてを状態リーダーとして指定します。これはまさに `pipedrive` パイプラインが行うことです。このような構造でも、一部のリソースを並列で実行できます。
:::
:::caution
`dlt.state()` は `dlt.current.source_state()` の非推奨のエイリアスであり、まもなく削除されます。:::

## 宛先と状態の同期

たとえば、すべてのタスクがクリーンなファイルシステムを取得し、[パイプライン作業ディレクトリ](pipeline.md#pipeline-working-directory)が常に削除される Airflow でパイプラインを実行するとどうなるでしょうか？ `dlt` は、他のすべてのデータとともに状態を宛先に読み込み、クリーンな開始に直面すると、宛先から状態を復元しようとします。

リモート状態は、パイプライン名、宛先の場所 (資格情報によって指定)、および宛先データセットによって識別されます。同じ状態を再利用するには、同じパイプライン名と宛先を使用します。

状態は宛先の `_dlt_pipeline_state` テーブルに保存され、パイプライン、パイプライン実行 (状態が属する)、および状態 BLOB に関する情報が含まれます。

`dlt` には `dlt pipeline sync` コマンドがあり、[そのテーブルから状態を返すように要求](../reference/command-line-interface.md#sync-pipeline-with-the-destination) できます。

> 💡 実行間でパイプラインの作業ディレクトリを維持できる場合は、`config.toml` で `restore_from_destination=false` を設定することで状態の同期を無効にすることができます。

## パイプラインの状態を使用する場合

- `dlt` は内部的に状態を使用して、[インクリメンタルロードの最後の値](incremental/cursor.md)を実装します。このユースケースは、パイプライン状態を使用するニーズの約 90% をカバーするはずです。
- リストが 10 万要素より大幅に大きくない場合は、[既に要求されたエンティティのリストを保存します](incremental/advanced-state.md#advanced-state-usage-storing-a-list-of-processed-entities)。
- 標準のインクリメンタルな構造で実装できない場合は、[最後の値の大きな辞書を保存](incremental/advanced-state.md#advanced-state-usage-tracking-the-last-value-for-all-search-terms-in-twitter-api)します。
- カスタムフィールドのディクショナリ、動的構成、およびその他のソーススコープの状態を保存します。

## 数百万レコードにまで増加する可能性がある場合は、パイプライン状態を使用しないでください。

`dlt` 状態は、数百万の要素にまで拡大する可能性がある場合には使用しないでください。数百万のユーザーレコードの変更タイムスタンプをすべて保存するつもりですか? これはおそらく悪い考えです! その場合は、次のようにすることができます:

- 抽出ステージが失敗した場合、無効な状態になってしまうことを考慮に入れて、状態を DynamoDB、Redis などに保存します。
- ロードしたデータを状態として使用します。`dlt` は `dlt.current.pipeline()` を介して現在のパイプラインを公開し、そこから [sqlclient](../dlt-ecosystem/transformations/sql.md) を取得して、目的のデータをロードできます。その場合は、少なくともユーザー レコードをバッチで処理するようにしてください。

### パイプライン状態ではなく宛先のデータにアクセスする

以下の例では、特定の `user_id` によって作成された最近のコメントを読み込みます。特定のユーザーの最大コメント ID を選択するために、`user_comments` テーブルにアクセスします。

```py
import dlt

@dlt.resource(name="user_comments")
def comments(user_id: str):
    current_pipeline = dlt.current.pipeline()
    # find the last comment id for the given user_id by looking in the destination
    max_id: int = 0
    # on the first pipeline run, the user_comments table does not yet exist so do not check at all
    # alternatively, catch DatabaseUndefinedRelation which is raised when an unknown table is selected
    if not current_pipeline.first_run:
        # get user comments table from pipeline dataset
        user_comments = current_pipeline.dataset().user_comments
        # get last user comment id with ibis expression, ibis-extras need to be installed
        max_id_df = user_comments.filter(user_comments.user_id == user_id).select(user_comments["_id"].max()).df()
        # if there are no comments for the user, max_id will be None, so we replace it with 0
        max_id = max_id_df[0][0] if len(max_id_df.index) else 0

    # use max_id to filter our results (we simulate an API query)
    yield from [
        {"_id": i, "value": letter, "user_id": user_id}
        for i, letter in zip([1, 2, 3], ["A", "B", "C"])
        if i > max_id
    ]
```

パイプラインを初めて実行したとき、宛先データセットと `user_comments` テーブルはまだ存在していません。パイプラインの `first_run` プロパティを使用して、宛先クエリをスキップします。また、`max_id` として None を 0 に置き換えることで、user_id にコメントがない状況を処理します。

## パイプラインの状態を検査する

[`dlt pipeline` コマンド](../reference/command-line-interface.md#dlt-pipeline)を使用してパイプラインの状態を検査できます。:

```sh
dlt pipeline -v chess_pipeline info
```

これにより、すべての既知のソースのソースおよびリソース状態スロットが表示されます。

## パイプラインの状態をリセット: 完全または部分的に

**状態を完全にリセットするには:**

- パイプラインを完全にリセットするには、宛先データセットをドロップします。
- [パイプラインを作成するときに `dev_mode` フラグを設定します](pipeline.md#do-experiments-with-dev-mode)。
- `dlt pipeline drop --drop-all` コマンドを使用して、[指定されたスキーマ名の状態とテーブルを削除します](../reference/command-line-interface.md#selectively-drop-tables-and-reset-state).

**状態を部分的にリセットするには:**

- `dlt pipeline drop <resource_name>` コマンドを使用して、[特定のリソースの状態とテーブルを削除します](../reference/command-line-interface.md#selectively-drop-tables-and-reset-state).
- `dlt pipeline drop --state-paths` コマンドを使用して、[テーブルやデータに触れることなく、指定されたパスの状態をリセットします](../reference/command-line-interface.md#selectively-drop-tables-and-reset-state).

