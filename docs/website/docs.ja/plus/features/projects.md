# Project


<img src="https://storage.googleapis.com/dlt-blog-images/plus/dlt_plus_projects.png" width="500"/>

[dlt+ プロジェクト](../core-concepts/project.md) は、データエンジニアリングチームにベストプラクティスを実装しながら、データワークフローを体系的に整理するための構造化された独自のアプローチを提供します。

dlt+ プロジェクトは、データの読み込み、データ変換、データカタログ、データガバナンスといった主要なプロセスを自動化し、データチームのさまざまなメンバー間の連携を容易にします。

dlt+ プロジェクトを使用すると、次の方法でデータワークフローを効率的に管理できます。

1. [宣言型の `dlt.yml` ファイル](#the-dlt-manifest-file-dltyml) を使用して、ソース、出力先、パイプライン、および変換を定義します。
2. さまざまなユースケースと環境に合わせて [異なるプロファイル](../core-concepts/profiles.md) を構成します。
3. [dlt+ テストユーティリティ](./quality/tests.md) を使用してテストを定義し、データ品質を確保します。
4. プロジェクトをPythonパッケージとしてパッケージ化し、PyPIまたはGitリポジトリ経由で配布する [近日公開予定]

この構造化されたアプローチにより、チームはデータワークフローの柔軟性と制御を維持しながら、効率的に作業を進めることができます。

## プロジェクト構造

dlt+ プロジェクトの一般的な構造は次のとおりです:

```text
├── .dlt/                 # folder containing dlt configurations and profile settings
│   ├── config.toml
│   ├── dev.secrets.toml  # credentials for access profile 'dev'
│   └── secrets.toml
├── _data/                # local storage for your project, excluded from git
├── sources/              # modules containing the source code for sources
│   └── github.py         # source code for a GitHub source
├── transformations/      # modules containing the source code for transformations
├── .gitignore
└── dlt.yml               # the main project manifest
```

## DLTマニフェストファイル (dlt.yml)

DLT+プロジェクトの主要コンポーネントは、DLTマニフェストファイル (`dlt.yml`) です。
これはプロジェクトのルートを示し、主要な設定が含まれています。
ここで、すべてのデータプラットフォームエンティティをYAML形式で宣言できます。
以下のセクションが含まれます。

### ソース

このセクションでは、宣言的に、または`sources/`内のPythonモジュールの実装を参照することで、ソースを定義できます。
以下の例では、2つのソースが宣言されています。
1. マニフェスト内でパラメータが渡されるdlt REST APIソース
2. `source`関数で定義されたGitHubソース。`sources/github.py`内のソースコードが参照されます。

```yaml
sources:
  pokemon:
    type: rest_api
    client:
      base_url: https://pokeapi.co/api/v2/
    resource_defaults:
      endpoint:
        params:
          limit: 1000
    resources:
      - pokemon
      - berry

  github:
    type: github.source
```
:::tip
ソース **type** は、Python コード内で `@dlt.source` で装飾された関数が存在する場所を参照するために使用されます。
Python モジュール内の関数名へのフルパスは常に使用できますが、省略表記と相対表記もサポートされています。
例:
* `rest_api` は `dlt.sources.rest_api.rest_api` に展開されます。ここで、`dlt.sources.rest_api` は OSS dlt 内の Python モジュールであり、`rest_api` はそのモジュール内の関数名です。
* `github.source` は、現在のプロジェクト内で `sources.github.sources` に展開されます。

**type** を解決できない場合、dlt+ は検索されたすべての候補タイプの詳細なリストを提供するので、必要な修正を行うことができます。
:::

### 宛先

宛先セクションでは、純粋なPythonのDLTプロジェクトで定義する方法と同様の方法で、DLTの宛先を定義します。
ソースと同様に、`destinations/`フォルダを作成し、その中に宛先のカスタム実装を参照することもできます。

```yaml
destinations:
    duckdb:
        type: duckdb
```

### パイプライン

パイプラインは、ソースから宛先へデータをロードするために使用できます。
以下で定義されるパイプラインは、GitHub ソースから duckdb 宛先内の「github_events_dataset」というデータセットにデータをロードします。

```yaml
github_pipeline:
  source: github
  destination: duckdb
  dataset_name: github_events_dataset
```

このセクションでは、`dlt.pipeline` のすべての引数を宣言できます。
引数の完全なリストについては、[docstrings](https://github.com/dlt-hub/dlt/blob/71b4975c70d1931750b3245e919a520a2400e870/dlt/pipeline/__init__.py#L30) を参照してください。

### データセット

datasets セクションでは、出力先（destinations セクションで定義）に保存されるデータセットを定義します。
[pipeline セクション](#pipelines) で宣言されたデータセットは、ここで宣言されていない場合は自動的に作成されます。
dlt+ のデータセットの詳細については、[こちら](../core-concepts/datasets.md) をご覧ください。

```yaml
datasets:
  github_events_dataset:
    destination:
      - duckdb
```

### キャッシュ 🧪

このセクションでは、変換する入力テーブルと、変換後に書き込む出力テーブルを指定します。
以下の例では、出力先データセット「github_events_dataset」からテーブル「events」をローカルキャッシュに読み込み、`transformations/` フォルダ内の変換を使用して変換し、最後に元の「events」テーブルと変換後の「events_aggregated」テーブルの2つのテーブルをデータセット「github_events_dataset」に書き戻します。
ローカルキャッシュを変換に使用する方法の詳細については、[こちら](../core-concepts/datasets.md) をご覧ください。

キャッシュ機能は現在、特定のユースケースに限定されており、ファイルシステムベースの出力先に保存されているデータにのみ対応しています。
キャッシュの入力データセットがファイルシステムベースの保存先 ([Iceberg](../ecosystem/iceberg.md)、[Delta](../ecosystem/delta.md)、または [クラウド ストレージとファイルシステム](../../dlt-ecosystem/destinations/filesystem.md)) にあることを確認してください。

```yaml
caches:
  github_events_cache:
    inputs:
      - dataset: github_events_dataset
        tables:
          events: events
    outputs:
      - dataset: github_events_dataset
        tables:
          events: events
          events_aggregated: events_aggregated
```
:::note
🚧 この機能は現在開発中です。早期テスターに​​ご興味をお持ちですか？[dlt+早期アクセスにご参加ください](https://info.dlthub.com/waiting-list)
:::

### 変換 🧪

ここでは、変換の設定を指定します。
コード例では、キャッシュ「github_events_cache」を操作する arrow ベースの変換を定義しています。
これは、`transformations/` フォルダ内のコードを使用します。
変換の実行方法の詳細については、[こちら](../features/transformations/index.md) をご覧ください。

```yaml
transformations:
  github_events_transformations:
    engine: arrow
    cache: github_events_cache
```
:::note
🚧 この機能は現在開発中です。早期テスターに​​ご興味をお持ちですか？[dlt+早期アクセスにご参加ください](https://info.dlthub.com/waiting-list)
:::

### プロファイル

profiles セクションを使用して、異なる環境（例：dev、staging、prod、tests）を定義できます。
1 つのパッケージに複数のプロファイルが存在する場合があり、これらは dlt+ cli コマンドを使用して指定できます。
デフォルトのプロファイル名は `dev` です。これは `tests` プロファイルと一緒に自動的に作成されます。

```yaml
profiles:
  dev: # Using "dev" profile will write to local filesystem
    destinations:
      delta_lake:
        type: delta
        bucket_url: delta_lake
  prod: # Using "prod" profile will write to s3 bucket
    destinations:
      delta_lake:
        type: delta
        bucket_url: s3://dlt-ci-test-bucket/dlt_example_project/
```

### プロジェクト設定と変数置換

`project` セクションを使用して、デフォルトのプロジェクト設定をオーバーライドできます。
* `project_dir` - プロジェクトのルートディレクトリ、つまりプロジェクトの Python モジュールが保存されているディレクトリ。
* `data_dir` と `local_dir` - [パイプラインと出力先によって作成されるファイル](#local-and-temporary-files-data_dir)。現在のプロファイル名で区切られます。
* `name` - プロジェクト名。
* `default_profile` - デフォルトのプロファイル名。上記のように、プロジェクトセクションで設定できます。
* `allow_undefined_entities` - デフォルトでは、dlt+ は出力先、ソース、データセットなどのエンティティをアドホックに作成します。このフラグは、このような動作を無効にします。

以下の例で：

```yaml
project:
  name: test_project
  data_dir: "{env.DLT_DATA_DIR}/{current_profile}"
  allow_undefined_entities: false
  default_profile: tests
  local_dir: "{data_dir}/local"
```

* プロジェクト名を `test_project` に設定し、デフォルト（親フォルダ名）を上書きします。
* `data_dir` を環境変数 `DLT_DATA_DIR` の値に設定し、プロファイル名 `current_profile` で区切ります。
* 未定義のエンティティ（`allow_undefined_entities`）（データセットや出力先など）が作成されないようにします。
* デフォルトのプロファイル名を `tests` に設定します。
* `local_dir` を、上記で定義した `data_dir` 内のフォルダ `local` に設定します。

上記の例からお分かりいただけるように、Python スタイルのフォーマッタを使用して変数を置換できます。
* `{env.ENV_VARIABLE_NAME}` 構文を使用して環境変数を参照できます。
* プロジェクト設定もすべて置換可能です。

### 暗黙的なエンティティ

デフォルトでは、dlt+ はユーザーまたは実行されたコードからデータセットや宛先などのエンティティが要求されたときに、それらを自動的に作成します。
例えば、最小限の `dlt.yml` 設定は次のようになります。

```yaml
sources:
  arrow:
    type: sources.arrow.source

destinations:
  duckdb:
    type: duckdb

pipelines:
  my_pipeline:
    source: arrow
    destination: duckdb
    dataset_name: my_pipeline_dataset
```

次のコマンドを実行すると、パイプラインが実行されます:

```sh
dlt pipeline my_pipeline run
```

この場合、`my_pipeline_dataset` データセットは明示的に宣言されていないため、dlt+ によって自動的に作成されます。
`duckdb` 宛先と `arrow` ソースは明示的に定義されているため、暗黙的に作成する必要はありません。
ただし、エンティティ（ソースや宛先など）がパイプライン内でのみ参照され、対応するセクションで定義されていない場合、dlt+ によって暗黙的に作成されます。

エンティティの暗黙的な作成は、プロジェクト設定の `allow_undefined_entities` 設定を使用して制御できます。

```yaml
project:
  allow_undefined_entities: false
```

`allow_undefined_entities` が `false` に設定されている場合、dlt+ は不足しているエンティティを自動的に作成しなくなります。
データセットと宛先は `dlt.yml` ファイルで明示的に宣言する必要があります。

```yaml
datasets:
  my_pipeline_dataset:
    destination:
        - duckdb
```

### データセットと出力先の管理

`dlt.yml` ファイルでデータセットを明示的に宣言する場合、`destination` フィールドにデータセットの実体化が許可されるすべての出力先をリストする必要があります。
これは、`allow_undefined_entities` が `true` に設定されている場合でも適用されます。
データセットを参照する各パイプラインは、データセットの `destination` リストに含まれる出力先を使用する必要があります。
パイプラインでリストにない出力先を指定した場合、dlt+ は構成エラーを発生させます。

```yaml
datasets:
  my_pipeline_dataset:
    destination:
      - duckdb
      - bigquery
```

この場合、`duckdb` または `bigquery` のいずれかを宛先として使用するパイプラインは、`my_pipeline_dataset` を安全に参照できます。

:::note
宛先フィールドは配列であり、データセットを具体化できる 1 つ以上の宛先を指定できます。
:::

### その他の設定

`dlt.yml` は [dlt 設定プロバイダ](../../general-usage/credentials/setup.md) であり、`config.toml` と同じように使用できます。
例えば、ログレベルを設定できます。

```yaml
runtime:
  log_level: WARNING
```

または、[パフォーマンス](../../reference/performance.md)の章で説明されている設定のいずれか。

## ローカルファイルと一時ファイル (`data_dir`)

dlt+ プロジェクトには専用の場所 (`data_dir`) があり、そこにすべての作業ファイルが保存されます。
デフォルトでは、プロジェクトのルートにある `_data` フォルダです。
各プロファイルの作業ファイルは個別に保存されます。
例えば、`dev` プロファイルのファイルは `_data/dev` に保存されます。

作業ファイルには以下が含まれます。
* パイプラインの作業ディレクトリ（`{data_dir}/pipelines` フォルダ）。ロードパッケージ、パイプラインの状態、スキーマがローカルに保存されます。
* 出力先（`{data_dir}/local`）によって作成されたすべてのファイル（ローカルの `filesystem` バケット、duckdb データベース、iceberg、delta lakes（ローカルファイルシステム用に設定されている場合）。
* アドホック（dbt 関連）Python 仮想環境のデフォルトの場所。

:::tip
ローカルファイルを生成する出力先を設定する際は、相対パスを使用して、プロファイルで区切られた `{data_dir}/local` フォルダに自動的に配置されるようにしてください。
例:

```yaml
destinations:
  iceberg:
    bucket_url: lake
  my_duckdb:
    type: duckdb
```

`iceberg` 宛先は `_data/dev/local/lake` フォルダに iceberg レイクを作成し、`duckdb` は `_data/dev/local/my_duckdb.duckdb` にデータベースを作成します。

`dlt project --profile name clean` コマンドを使用して、作業ファイルをクリーンアップできます。
:::

## dlt-plus プロジェクトを操作するための Python API

Python インターフェースを介して、dlt+ プロジェクトのあらゆるエンティティまたは関数にアクセスできます。
現在のモジュールは、アクティブな dlt+ プロジェクトのさまざまな部分へのアクセスを提供します。

`import` ステートメント:

```py
from dlt_plus import current
```

利用可能なメソッド:
- `current.project()` - プロジェクト構成を取得します
- `current.entities()` - インスタンス化されたすべてのエンティティを含むファクトリーを返します
- `current.catalog()` - カタログ内のすべての定義済みデータセットにアクセスできるようにします
- `current.runner()` - プログラムでパイプラインを実行できるようにします

:::info
dlt+ プロジェクトを pip でインストール可能なパッケージにパッケージ化した場合、上記のすべてのメソッドにパッケージから直接アクセスできます。
例:

```py
import my_dlt_package

my_dlt_package.catalog()
```

プロジェクトをパッケージ化する方法については、[詳細](../getting-started/advanced_tutorial.md)をご覧ください。
:::

### プロジェクト設定へのアクセス

プロジェクトオブジェクトからアクセスできる項目の例をいくつか示します:

```py
from dlt_plus import current

# show the currently active profile
print(current.project().current_profile)
# show the main project dir
print(current.project().project_dir)
# show the project config
print(current.project().config)
# list explicitly defined datasets (also works with destinations, sources, pipelines, etc.)
print(current.project().datasets)
```
### エンティティへのアクセス

コード内でのエンティティへのアクセスは、`dlt.yml` ファイル内でのエンティティ参照と同じように機能します。
許可されている場合、暗黙的なエンティティが自動的に作成され、返されます。
許可されていない場合は、エラーが発生します。

```py
import dlt_plus
from dlt_plus import current

entities = dlt_plus.current.entities()
pipeline = entities.get_pipeline("my_pipeline")
destination = entities.get_destination("duckdb")
transformation = entities.get_transformation("stressed_transformation")

```

ここで、エンティティ マネージャーにアクセスして、ソース、宛先、パイプライン、その他のオブジェクトを作成できます。

### ランナーを使ったパイプラインの実行

`dlt+` にはパイプラインランナーが含まれており、これは CLI からパイプラインを実行するときに使用するものと同じです。
プロジェクトコンテキストを通じてコード内で直接使用することもできます。

```py
from dlt_plus import current

# get the runner
runner = current.runner()
# run the "my_pipeline" pipeline from the currently active project
runner.run_pipeline("my_pipeline")
```

### カタログへのアクセス

カタログを使用すると、明示的に定義されたすべてのデータセットにアクセスできます:

```py
from dlt_plus import current

# Get a dataset instance pointing to the default destination (first in dataset destinations list) and access data inside of it
# Note: The dataset must already exist physically for this to work
dataset = current.catalog().dataset("my_pipeline_dataset")
# Get the row counts of all tables in the dataset as a dataframe
print(dataset.row_counts().df())
```

:::tip
DLTデータセットで利用可能なデータアクセス方法の詳細については、[Pythonロードデータアクセスガイド](../../general-usage/dataset-access/dataset)をお読みください。
このガイドでは、テーブルの参照、フィルタリング、さまざまな形式のデータの取得方法について説明しています。
:::

### カタログへのデータの書き戻し

dlt+ カタログ内のデータセットにデータを書き込むこともできます。
各データセットには、データを書き戻すための `.save()` メソッドがあります。
将来的には、コントラクトを使用して書き込み可能なデータセットを制御できるようになります。
`dlt+` は内部的にアドホックパイプラインを実行して書き込み操作を処理します。

:::warning
カタログへのデータの書き込みは**試験的な機能**です。
完全に安定するまでは注意してご使用ください。
:::

```py
import pandas as pd
from dlt_plus import current

# Get a dataset from the catalog (it must already exist and be defined in dlt.yml)
dataset = current.catalog().dataset("my_pipeline_dataset")
# Write a DataFrame to the "my_table" table in the dataset
dataset.save(pd.DataFrame({"name": ["John", "Jane", "Jim"], "age": [30, 25, 35]}), table_name="my_table")
```

既存のテーブルからデータを読み取り、同じデータセットまたは別のデータセット内の新しいテーブルにデータを書き込むこともできます:

```py
from dlt_plus import current

# Get dataset from the catalog
dataset = current.catalog().dataset("my_pipeline_dataset")

# This function reads data in chunks from an existing table and yields each chunk
def transform_frames():
    # Read the 'items' table in chunks of 1000 rows
    for df in dataset.items.iter_df(chunk_size=1000):
        # You can process the data here if needed
        yield df

# Write the data to a new table called "my_new_table"
dataset.save(transform_frames, table_name="my_new_table")
```

### コード内でのプロファイルの切り替え

デフォルトでは、コード内でプロジェクトにアクセスすると、デフォルトまたは固定されたプロファイルが使用されます。
`switch_profile` 関数を使用して、別のプロファイルに切り替えることができます。

例を以下に示します。

```py
from dlt_plus import current
from dlt_plus.project.run_context import switch_profile

if __name__ == "__main__":
    # Shows the current active profile
    print(current.project().current_profile)
    # Switch to the tests profile
    switch_profile("tests")
    # Now "tests" is the active profile, merged with the project config
    print(current.project().current_profile)
```

## 設定とシークレット

上記のように、マニフェストファイル自体に追加の DLT 設定と構成を渡すことが可能です。
ただし、既存の DLT 設定プロバイダーも通常通りサポートされています。例えば、以下のようになります。

1. Environ プロバイダー
2. `.dlt/config.toml` プロバイダー（グローバル設定を含む）
3. `.dlt/<profile_name>.secrets.toml`（シークレット toml プロバイダーですが、特定のプロファイルにスコープが限定されています）。
`secrets.toml` ファイルの代わりに、プロファイルごとのバージョン（`dev.secrets.toml`）が検索されます。

:::note
[設定ドキュメント](../../general-usage/credentials/setup#choose-where-to-store-configuration)に記載されている優先順位に関する情報に基づき、yamlファイルは、設定値のデフォルト値のすぐ上に、すべてのプロバイダーの中で最も低い優先順位を提供します。したがって、yamlファイルの設定は、`toml`および`env`変数が存在する場合、それらによって上書きされます。
:::

## プロジェクトコンテキスト

`dlt.yml` はプロジェクトのルートを示します。
プロジェクトはネストすることもできます。
dlt プロジェクトの CLI コマンドを実行すると、dlt は現在の作業ディレクトリからファイルシステムツリー内のプロジェクトルートを検索し、見つかったプロジェクトに対してすべての操作を実行します。
つまり、`dlt.yml` が `tutorial` フォルダ内にある場合、このフォルダまたは任意のサブフォルダから `dlt pipeline my_pipeline run` を実行すると、`tutorial` プロジェクトに対してパイプラインが実行されます。

## プロジェクトのパッケージ化と配布

プロジェクトはPythonパッケージとして配布でき、組織内で共有したり、データアクセスを可能にしたりすることができます。
これらのPythonパッケージのビルド方法については、近日中に公開予定です。
[早期アクセス](https://info.dlthub.com/waiting-list)プログラムにご参加いただき、詳細をご確認ください。

