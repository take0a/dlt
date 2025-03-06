---
title: "Build a dlt pipeline"
description: Build a data pipeline with dlt
keywords: [getting started, quick start, basic examples]
---

このチュートリアルでは、基本的な DLT の概念を紹介し、純粋な Python データ構造から DuckDB にデータをロードするカスタム データ パイプラインの構築方法を示します。簡単な例から始まり、より高度なトピックと使用シナリオに進みます。

## 学ぶ内容

- Python 辞書のリストから DuckDB にデータをロードします。
- 組み込みの HTTP クライアントを使用した低レベル API の使用。
- データをロードする動作を理解し、管理します。
- 新しいデータをインクリメンタルにロードし、既存のデータとの重複を排除します。
- 動的なリソースの作成とコードの冗長性の削減。
- リソースをソースにグループ化します。
- 秘密を安全に扱います。
- 再利用可能なデータ ソースを作成します。

## 前提条件

- Python 3.9 以上がインストールされている
- 仮想環境のセットアップ

## dlt のインストール

始める前に、Python 仮想環境が設定されていることを確認してください。[インストール ガイド](../reference/installation)の指示に従って、新しい仮想環境を作成し、dlt をインストールしてください。

ターミナルで次のコマンドを実行して、dltがインストールされていることを確認します:

```sh
dlt --version
```

## クイックスタート

まず、Python 辞書のリストを DuckDB にロードし、作成されたデータセットを調べてみましょう。コードは次のとおりです:

```py
import dlt

data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

pipeline = dlt.pipeline(
    pipeline_name="quick_start", destination="duckdb", dataset_name="mydata"
)
load_info = pipeline.run(data, table_name="users")

print(load_info)
```

上記のコードを見ると:
1. `dlt` ライブラリをインポートします。
2. ロードするデータを定義します。
3. DuckDB にデータをロードするパイプラインを作成します。ここでは、`pipeline_name` と `dataset_name` も指定します。どちらもすぐに使用します。
4. パイプラインを実行します。

この Python スクリプトを `quick_start_pipeline.py` という名前で保存し、次のコマンドを実行します:

```sh
python quick_start_pipeline.py
```

出力は次のようになります:

```sh
Pipeline quick_start completed in 0.59 seconds
1 load package(s) were loaded to destination duckdb and into dataset mydata
The duckdb destination used duckdb:////home/user-name/quick_start/quick_start.duckdb location to store data
Load package 1692364844.460054 is LOADED and contains no failed jobs
```

`dlt` は、**users** テーブルを含む **mydata** (`dataset_name`) というデータベース スキーマを作成しました。

### Pythonでデータを探索する

dlt の [datasets](../general-usage/dataset-access/dataset) を使用すると、純粋な Python でデータを簡単にクエリできます。

```py
# get the dataset
dataset = pipeline.dataset("mydata")

# get the user relation
table = dataset.users

# query the full table as dataframe
print(table.df())

# query the first 10 rows as arrow table
print(table.limit(10).arrow())
```

### Streamlitでデータを探索する

こっそり覗いて基本的な情報を得るには、[Streamlit の組み込み統合](../reference/command-line-interface#show-tables-and-data-in-the-destination) を利用できます。:

```sh
dlt pipeline quick_start show
```

**quick_start** は上記のスクリプトのパイプラインの名前です。Streamlit をまだインストールしていない場合は:

```sh
pip install streamlit
```

**users** テーブルが表示されるはずです:

![Streamlit Explore data](/img/streamlit-new.png)
Streamlit Explore data. Schema and data for a test pipeline “quick_start”.

:::tip
`dlt` は Jupyter Notebook と Google Colab で動作します。[クイックスタート Colab デモ](https://colab.research.google.com/drive/1NfSB1DpwbbHX9_t5vlalBTf13utwpMGx?usp=sharing) をご覧ください。

すべてのスニペットのソース コードをお探しですか? [このリポジトリ](https://github.com/dlt-hub/dlt/blob/devel/docs/website/docs/getting-started-snippets.py)から見つけて実行できます。
:::

dlt の基本的な使い方を理解したので、さらに詳しく知りたいと思うかもしれません。そのためには、より高度なデータ ソースである GitHub API に切り替える必要があります。[dlt-hub/dlt](https://github.com/dlt-hub/dlt) リポジトリから問題を読み込みます。

:::note
このチュートリアルでは、デモンストレーション目的でのみ GitHub REST API を使用します。REST API からデータを読み取る必要がある場合は、dlt の REST API ソースの使用を検討してください。クイック スタートについては [REST API ソース チュートリアル](./rest-api) を、詳細については [REST API ソース リファレンス](../dlt-ecosystem/verified-sources/rest_api) を参照してください。
:::

## パイプラインを作成する

まず、[パイプライン](../general-usage/pipeline)を作成する必要があります。パイプラインは`dlt`の主要な構成要素であり、ソースから宛先にデータをロードするために使用されます。お気に入りのテキストエディタを開いて、`github_issues.py`というファイルを作成します。次のコードを追加します。:

<!--@@@DLT_SNIPPET basic_api-->


上記のコードが行うことは次のとおりです:
1. GitHub API エンドポイントにリクエストを送信し、応答が成功したかどうかを確認します。
2. 次に、`github_issues` という名前の dlt パイプラインを作成し、データを `duckdb` の宛先と `github_data` データセットにロードするように指定します。まだ何もロードされていません。
3. 最後に、API レスポンス (`response.json()`) のデータを使用してパイプラインを実行し、データを `issues` テーブルにロードするように指定します。`run` メソッドは、ロードされたデータに関する情報を含む `LoadInfo` オブジェクトを返します。

## パイプラインを実行する

`github_issues.py`を保存し、次のコマンドを実行します:

```sh
python github_issues.py
```

データが読み込まれたら、Streamlitアプリを使用して作成されたデータセットを検査できます:

```sh
dlt pipeline github_issues show
```

## データを追加または置換する

`python github_issues.py` を使用してパイプラインを再度実行してみてください。**issues** テーブルに同じデータのコピーが 2 つ含まれていることがわかります。これは、デフォルトのロード モードが `append` であるために発生します。これは、たとえば、毎日データが更新され、それを取り込みたい場合などに非常に便利です。

最新のデータを取得するには、スクリプトを再度実行する必要があります。しかし、データを重複させずにそれを実行するにはどうすればよいでしょうか?
1 つの選択肢は、`dlt` に `replace` 書き込み処理を使用して、宛先の既存のテーブルのデータを置き換えるように指示することです。`github_issues.py` スクリプトを次のように変更します。:

```py
import dlt
from dlt.sources.helpers import requests

# Specify the URL of the API endpoint
url = "https://api.github.com/repos/dlt-hub/dlt/issues"
# Make a request and check if it was successful
response = requests.get(url)
response.raise_for_status()

pipeline = dlt.pipeline(
    pipeline_name='github_issues',
    destination='duckdb',
    dataset_name='github_data',
)
# The response contains a list of issues
load_info = pipeline.run(
    response.json(),
    table_name="issues",
    write_disposition="replace"  # <-- Add this line
)

print(load_info)
```

このスクリプトを 2 回実行すると、**issues** テーブルにはまだデータのコピーが 1 つだけ含まれていることがわかります。

:::tip
API が変更され、レスポンスに新しいフィールドが追加された場合はどうなるでしょうか?
`dlt` がテーブルを移行します!
[スキーマ進化 colab デモ](https://colab.research.google.com/drive/1H6HKFi-U1V4p0afVucw_Jzv1oiFbH2bu#scrollTo=e4y4sQ78P_OM) で、`replace` モードとテーブル スキーマ移行の実際の様子をご覧ください。
:::

もっと詳しく知る:

- [フルロード - データの置き換え方法](../general-usage/full-loading).
- [テーブルの追加、置換、結合](../general-usage/incremental-loading).

## ローディングの振る舞いを宣言する

これまでは、データを直接 `run` メソッドに渡してきました。これは、すぐに開始できる方法です。ただし、多くの場合、データをチャンクで受信し、到着時にロードする必要があります。たとえば、ページ区切りのある API エンドポイントからデータをロードしたり、メモリに収まらない大きなファイルをロードしたりする場合があります。このような場合は、Python ジェネレーターをデータ ソースとして使用できます。

ジェネレーターを `run` メソッドに直接渡すか、`@dlt.resource` デコレータを使用してジェネレーターを [dlt リソース](../general-usage/resource) に変換することができます。デコレータを使用すると、読み込み動作と関連するリソース パラメータを指定できます。

### 新しいデータのみをロードする（インクリメンタルロード）

GitHub API の例を改良して、最後のロード以降に作成された問題のみを取得してみましょう。
`replace` 書き込み処理を使用してパイプラインが実行されるたびにすべての問題をダウンロードする代わりに、次の操作を行います:

<!--@@@DLT_SNIPPET incremental-->


上記のコードを詳しく見てみましょう。

`@dlt.resource` デコレータを使用して、データがロードされるテーブル名を宣言し、`append` 書き込み処理を指定しています。

**created_at** フィールド (降順) で順序付けられた dlt-hub/dlt リポジトリの問題を要求し、`get_issues` ジェネレーター関数でページごとに生成します。

また、`dlt.sources.incremental` を使用して、各 issue に存在する `created_at` フィールドを追跡し、新しく作成されたものをフィルタリングします。

次にスクリプトを実行します。リポジトリからすべての問題が `duckdb` にロードされます。もう一度実行すると、問題が追加されていないことがわかります (その間に問題が作成されなかった場合)。

これで、このスクリプトを毎日のスケジュールで実行できるようになり、各日には前回のパイプラインの実行後に作成された問題のみが読み込まれます。

:::tip
パイプラインの実行中、`dlt` はデータをロードした同じデータベースに状態を保持します。
その状態、ロードされたテーブル、その他の情報を確認するには、:

```sh
dlt pipeline -v github_issues_incremental info
```
:::

もっと詳しく知る:

- [リソース](../general-usage/resource)を宣言し、Pythonデコレータを使用して[ソース](../general-usage/source)にグループ化します。
- [インクリメンタルローディングの「最後の値」を設定します。](../general-usage/incremental-loading#incremental_loading-with-last-value)
- [ロード後にパイプラインを検査します。](../walkthroughs/run-a-pipeline#4-inspect-a-load-process)
- [`dlt` コマンドラインインターフェース。](../reference/command-line-interface)

### データを更新して重複を排除する

上記のスクリプトは、**新しい** issue を見つけてデータベースに追加します。
**既存の** issue のテキスト、絵文字での反応などの更新は無視されます。
すべての issue の最新のコンテンツを常に取得するには、以下のスクリプトのように、インクリメンタルなロードと `merge` 書き込み処理を組み合わせます。

<!--@@@DLT_SNIPPET incremental_merge-->


上記では、`dlt.resource()` に `primary_key` 引数を追加し、データベース内の問題を識別して、コンテンツをマージする重複を見つける方法を `dlt` に指示しています。

ここで、`updated_at` フィールドを追跡することに注意してください。これにより、前回のパイプライン実行以降に**更新**されたすべての問題 (新しく作成された問題も含まれます) がフィルター処理されます。

[GitHub API](https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues) の **since** パラメータと `updated_at.last_value` を使用して、渡した日付より**後**に更新された問題のみを返すように GitHub に指示する方法に注意してください。`updated_at.last_value` は、前回の実行からの最後の `updated_at` 値を保持します。

[マージ書き込み処理の詳細](../general-usage/incremental-loading#merge-incremental_loading)を参照してください。

## ページネーションヘルパーの使用

前の例では、`requests` ライブラリを使用して GitHub API への HTTP リクエストを作成し、ページネーションを手動で処理しました。`dlt` には、API リクエストを簡素化する組み込みの [REST クライアント](../general-usage/http/rest-client.md)があります。次の例では、その `paginate()` ヘルパーを使用します。`paginate` 関数は、URL とオプションのパラメーター (`requests` と非常に似ています) を受け取り、データページを生成するジェネレーターを返します。

更新されたスクリプトは次のようになります:

```py
import dlt
from dlt.sources.helpers.rest_client import paginate

@dlt.resource(
    table_name="issues",
    write_disposition="merge",
    primary_key="id",
)
def get_issues(
    updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    for page in paginate(
        "https://api.github.com/repos/dlt-hub/dlt/issues",
        params={
            "since": updated_at.last_value,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
            "state": "open",
        },
    ):
        yield page

pipeline = dlt.pipeline(
    pipeline_name="github_issues_merge",
    destination="duckdb",
    dataset_name="github_data_merge",
)
load_info = pipeline.run(get_issues)
row_counts = pipeline.last_trace.last_normalize_info

print(row_counts)
print("------")
print(load_info)
```

変化に注目してみましょう:

1. ページネーションを処理する `while` ループは、 `paginate()` ジェネレータからページを読み取ることに置き換えられます。
2. `paginate()` は、API エンドポイントの URL とオプションのパラメータを受け取ります。この場合、最後のパイプライン実行後に更新された問題のみを取得するために `since` パラメータを渡します。
3. ページネーションを明示的に設定しているわけではありません。`paginate()` がそれを処理します。魔法のようです! 内部的には、`paginate()` がレスポンスを分析し、API が使用するページネーション メソッドを検出します。ページネーションの詳細については、[REST クライアント ドキュメント](../general-usage/http/rest-client.md#paginating-api-responses) を参照してください。

`dlt` ライブラリを最大限に活用したい場合は、既存のビルディング ブロックからソースを構築することを強くお勧めします。
`dlt` を最大限に活用するには、次の点を考慮してください。

## ソースデコレータを使用する

前のステップでは、GitHub APIから issue を読み込みました。今度は、APIからコメントも読み込みます。これを実行するサンプルの[dltリソース](../general-usage/resource)を以下に示します:

```py
import dlt
from dlt.sources.helpers.rest_client import paginate

@dlt.resource(
    table_name="comments",
    write_disposition="merge",
    primary_key="id",
)
def get_comments(
    updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    for page in paginate(
        "https://api.github.com/repos/dlt-hub/dlt/comments",
        params={"per_page": 100}
    ):
        yield page
```

このリソースは、issuesリソースとは別に読み込むことができますが、issuesとcommentsの両方を一度に読み込む方が効率的です。そのためには、リソースのリストを返す関数で`@dlt.source`デコレータを使用します:

```py
@dlt.source
def github_source():
    return [get_issues, get_comments]
```

`github_source()` はリソースを [source](../general-usage/source) にグループ化します。dlt ソースはリソースの論理的なグループです。同じ API からデータをロードするなど、同じグループに属するリソースをグループ化するために使用します。ソースからのデータのロードは、単一のパイプラインで実行できます。更新されたスクリプトは次のようになります:

```py
import dlt
from dlt.sources.helpers.rest_client import paginate

@dlt.resource(
    table_name="issues",
    write_disposition="merge",
    primary_key="id",
)
def get_issues(
    updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    for page in paginate(
        "https://api.github.com/repos/dlt-hub/dlt/issues",
        params={
            "since": updated_at.last_value,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
            "state": "open",
        }
    ):
        yield page


@dlt.resource(
    table_name="comments",
    write_disposition="merge",
    primary_key="id",
)
def get_comments(
    updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
):
    for page in paginate(
        "https://api.github.com/repos/dlt-hub/dlt/comments",
        params={
            "since": updated_at.last_value,
            "per_page": 100,
        }
    ):
        yield page


@dlt.source
def github_source():
    return [get_issues, get_comments]


pipeline = dlt.pipeline(
    pipeline_name='github_with_source',
    destination='duckdb',
    dataset_name='github_data',
)

load_info = pipeline.run(github_source())
print(load_info)
```

### 動的リソース

`get_issues` 関数と `get_comments` 関数には多くのコード重複があることに気付いたでしょう。共通のフェッチコードを別の関数に抽出し、両方のリソースで使用することで、重複を減らすことができます。さらに良い方法は、`dlt.resource` を関数として使用し、それを `fetch_github_data()` ジェネレーター関数に直接渡すことです。リファクタリングしたコードは次のとおりです:

```py
import dlt
from dlt.sources.helpers.rest_client import paginate

BASE_GITHUB_URL = "https://api.github.com/repos/dlt-hub/dlt"

def fetch_github_data(endpoint, params={}):
    url = f"{BASE_GITHUB_URL}/{endpoint}"
    return paginate(url, params=params)

@dlt.source
def github_source():
    for endpoint in ["issues", "comments"]:
        params = {"per_page": 100}
        yield dlt.resource(
            fetch_github_data(endpoint, params),
            name=endpoint,
            write_disposition="merge",
            primary_key="id",
        )

pipeline = dlt.pipeline(
    pipeline_name='github_dynamic_source',
    destination='duckdb',
    dataset_name='github_data',
)
load_info = pipeline.run(github_source())
row_counts = pipeline.last_trace.last_normalize_info
```

## 秘密を扱う

次のステップでは、GitHub API から dlt リポジトリの [リポジトリ クローンの数](https://docs.github.com/en/rest/metrics/traffic?apiVersion=2022-11-28#get-repository-clones) を取得する必要があります。ただし、データを返す `traffic/clones` エンドポイントでは [認証](https://docs.github.com/en/rest/overview/authenticating-to-the-rest-api?apiVersion=2022-11-28) が必要です。

まず`fetch_github_data()`関数を変更してこれを処理しましょう:

```py
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

def fetch_github_data_with_token(endpoint, params={}, access_token=None):
    url = f"{BASE_GITHUB_URL}/{endpoint}"
    return paginate(
        url,
        params=params,
        auth=BearerTokenAuth(token=access_token) if access_token else None,
    )


@dlt.source
def github_source_with_token(access_token: str):
    for endpoint in ["issues", "comments", "traffic/clones"]:
        params = {"per_page": 100}
        yield dlt.resource(
            fetch_github_data_with_token(endpoint, params, access_token),
            name=endpoint,
            write_disposition="merge",
            primary_key="id",
        )

...
```

ここで、`access_token`パラメータを追加し、これを使用してアクセストークンをリクエストに渡すことができます:

```py
load_info = pipeline.run(github_source_with_token(access_token="ghp_XXXXX"))
```

これは良いスタートです。しかし、ベスト プラクティスに従い、スクリプトにトークンをハードコードしないようにします。1 つのオプションは、トークンを環境変数として設定し、`os.getenv()` で読み込み、パラメーターとして渡すことです。dlt は、シークレットと認証情報を処理するより便利な方法を提供します。特別な `dlt.secrets.value` 引数値を使用して引数を挿入できます。

これを使用するには、`github_source()`関数を次のように変更します:

```py
@dlt.source
def github_source_with_token(
    access_token: str = dlt.secrets.value,
):
    ...
```

`dlt.secrets.value` を引数のデフォルト値として追加すると、`dlt` は次の順序でさまざまな設定ソースからこの値をロードして挿入しようとします。:

1. 特別な環境変数。
2. `secrets.toml` ファイル.

`secrets.toml` ファイルは、`~/.dlt` フォルダ (グローバル構成の場合) またはプロジェクト フォルダ内の `.dlt` フォルダ (プロジェクト固有の構成の場合) にあります。

トークンを`~/.dlt/secrets.toml`ファイルに追加しましょう:

```toml
[github_with_source_secrets]
access_token = "ghp_A...3aRY"
```

これでスクリプトを実行すると、`traffic/clones`エンドポイントからデータがロードされます:

```py
...

@dlt.source
def github_source_with_token(
    access_token: str = dlt.secrets.value,
):
    for endpoint in ["issues", "comments", "traffic/clones"]:
        params = {"per_page": 100}
        yield dlt.resource(
            fetch_github_data_with_token(endpoint, params, access_token),
            name=endpoint,
            write_disposition="merge",
            primary_key="id",
        )


pipeline = dlt.pipeline(
    pipeline_name="github_with_source_secrets",
    destination="duckdb",
    dataset_name="github_data",
)
load_info = pipeline.run(github_source())
```

## 設定可能なソース

次のステップは、dlt GitHubソースを再利用可能にして、任意のGitHubリポジトリからデータをロードできるようにすることです。そのためには、`github_source()`と`fetch_github_data()`関数の両方を変更して、リポジトリ名をパラメータとして受け入れるようにします:

```py
import dlt
from dlt.sources.helpers.rest_client import paginate

BASE_GITHUB_URL = "https://api.github.com/repos/{repo_name}"


def fetch_github_data_with_token_and_params(repo_name, endpoint, params={}, access_token=None):
    """Fetch data from the GitHub API based on repo_name, endpoint, and params."""
    url = BASE_GITHUB_URL.format(repo_name=repo_name) + f"/{endpoint}"
    return paginate(
        url,
        params=params,
        auth=BearerTokenAuth(token=access_token) if access_token else None,
    )


@dlt.source
def github_source_with_token_and_repo(
    repo_name: str = dlt.config.value,
    access_token: str = dlt.secrets.value,
):
    for endpoint in ["issues", "comments", "traffic/clones"]:
        params = {"per_page": 100}
        yield dlt.resource(
            fetch_github_data_with_token_and_params(repo_name, endpoint, params, access_token),
            name=endpoint,
            write_disposition="merge",
            primary_key="id",
        )


pipeline = dlt.pipeline(
    pipeline_name="github_with_source_secrets",
    destination="duckdb",
    dataset_name="github_data",
)
load_info = pipeline.run(github_source())
```

次に、プロジェクトフォルダに`.dlt/config.toml`ファイルを作成し、それに`repo_name`パラメータを追加します。:

```toml
[github_with_source_secrets]
repo_name = "dlt-hub/dlt"
```

これで完了です。これで、任意の GitHub リポジトリからデータを読み込むことができる再利用可能なソースができました。

## 次は

チュートリアルを完了しました。おめでとうございます。[入門](../intro) ガイド以来、長い道のりを歩んできました。これまでに、さまざまな GitHub API エンドポイントからデータをロードし、リソースをソースに整理し、シークレットを安全に管理し、再利用可能なソースを作成する方法を習得しました。これらのスキルを使用して、独自のパイプラインを構築し、任意のソースからデータをロードできます。

もっと詳しく知りたいですか？いくつか提案があります:

1. これまではパイプラインをローカルで実行していました。[パイプラインをクラウドにデプロイして実行する](../walkthroughs/deploy-a-pipeline/)方法を学習します。
2. [dltの使用](../general-usage)セクションを読んで、dltの仕組みについてさらに詳しく学びましょう:
    - [インクリメンタルローディングで「最後の値」を設定する](../general-usage/incremental-loading#incremental_loading-with-last-value).
    - データ読み込み戦略について学習します: [追加、置換、およびマージ](../general-usage/incremental-loading)。
    - [トランスフォーマーをリソースに接続](../general-usage/resource#feeding-data-from-one-resource-into-another)して、追加のデータを読み込んだり、データを拡充したりします。
    - [データ スキーマをカスタマイズします。主キーとマージ キーを設定し、列の NULL 値許容性を定義し、データ型を指定します](../general-usage/resource#define-schema)。
    - [データからリソースを動的に作成します](../general-usage/source#create-resources-dynamically)。
    - [読み込む前にデータを変換](../general-usage/resource#customize-resources)し、[列名の変更や匿名化などのカスタマイズの例](../general-usage/customising-pipelines/renaming_columns)を確認してください。
    - [SQL](../dlt-ecosystem/transformations/sql) または [Pandas](../dlt-ecosystem/transformations/sql) を使用してデータ変換を実行します。
    - [ソースとリソースに設定と資格情報を渡します](../general-usage/credentials)。
    - [本番環境で実行: 検査、トレース、再試行ポリシー、クリーンアップ](../running-in-production/running)。
    - [リソースを並列実行し、バッファとローカルストレージを最適化する](../reference/performance.md)
    - [REST API クライアント ヘルパーを使用](../general-usage/http/rest-client.md)すると、REST API の操作が簡単になります。
3. 私たちとコミュニティが提供する[宛先](../dlt-ecosystem/destinations/)と[ソース](../dlt-ecosystem/verified-sources/)を探索してください。
4. [例](../examples)セクションを参照して、実際のシナリオで dlt がどのように使用されるかを確認してください。
