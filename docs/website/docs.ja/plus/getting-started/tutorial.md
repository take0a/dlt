---
title: Project tutorial
description: Using the dlt+ cli commands to create and manage dlt+ Project
keywords: [command line interface, cli, dlt init, dlt+, project]
---

このチュートリアルでは、dlt+ プロジェクトと、その作成と管理に必要な基本的な CLI コマンドを紹介します。以下の方法を学習します。

* 新しい dlt+ プロジェクトの初期化
* `dlt.yml` ファイルの操作
* ソース、デスティネーション、パイプラインの追加
* CLI コマンドを使用したパイプラインの実行
* データセットの検査
* dlt+ プロファイルを使用してさまざまな設定を有効にする

## 前提条件

このチュートリアルを進めるには、以下の条件を満たしている必要があります。

- dlt+ が [インストールガイド](./installation.md) に従ってセットアップされていること
- [dlt のコアコンセプト](../../reference/explainers/how-dlt-works.md) を理解していること

:::tip
利用可能な CLI コマンドの完全なリストは、[CLI リファレンス](../reference.md) で確認できます。
:::

## 新しい dlt+ プロジェクトの作成

まず、プロジェクト用の新しいフォルダを作成します。次に、ターミナルでそのフォルダに移動します。

```sh
mkdir tutorial && cd tutorial
```

新しい dlt+ プロジェクトを初期化するには、次のコマンドを実行します:

```sh
# Initialize a dlt+ Project named "tutorial", the name is derived from the folder name
dlt project init arrow duckdb
```

このコマンドは、以下の内容を含む「tutorial」という名前のプロジェクトを生成します。
- 1 つの [パイプライン](../../general-usage/pipeline)
- 1 つの Arrow ソース (`sources/arrow.py` で定義)
- 1 つの DuckDB 宛先
- 1 つの DuckDB 宛先上のデータセット

:::caution
現在、`dlt project init` は限られた数のソースのみをサポートしています（例：[REST API](../../dlt-ecosystem/verified-sources/rest_api/index.md)、[SQL データベース](../../dlt-ecosystem/verified-sources/sql_database/index.md)、[ファイルシステム](../../dlt-ecosystem/verified-sources/filesystem/index.md) など）。
利用可能なすべてのソースを一覧表示するには、[cli コマンド](../reference.md#dlt-source-list) を使用してください。

```sh
dlt source list-available
```
他の検証済みソースのサポートも近日中に開始される予定です。
:::

### 生成されたフォルダ構造
コマンドを実行すると、次のフォルダ構造が作成されます。

```sh
.
├── .dlt/                 # your dlt settings including profile settings
│   ├── dev.secrets.toml
│   └── secrets.toml
├── _data/                # local storage for your project, excluded from git
├── sources/              # your sources, contains the code for the arrow source
│   └── arrow.py
├── .gitignore
├── requirements.txt
└── dlt.yml               # the main project manifest
```

### `dlt.yml` を理解する

`dlt.yml` ファイルは、dlt+ プロジェクトの中心的な設定ファイルです。パイプライン、ソース、およびデスティネーションを定義します。
生成されたプロジェクトでは、ファイルは次のようになります。

```yaml
profiles:
  # profiles allow you to configure different settings for different environments
  dev: {}

# your sources are the data sources you want to load from
sources:
  arrow:
    type: sources.arrow.source

# your destinations are the databases where your data will be saved
destinations:
  duckdb:
    type: duckdb

# your datasets are the datasets on your destinations where your data will go
datasets: {}

# your pipelines orchestrate data loading actions
pipelines:
  my_pipeline:
    source: arrow
    destination: duckdb
    dataset_name: my_pipeline_dataset
```

:::tip
ソース、宛先、パイプラインを最初から用意したくない場合は、`dlt project init --project-name tutorial` を実行するだけです。
これにより、空のソース、宛先、パイプラインを含むプロジェクトが生成されます。
:::

上記のプロジェクト構造の詳細：

* `runtime` セクションは config.toml の [runtime] セクションに類似しており、この場合は省略可能です。
* `profiles` セクションは、この場合はあまり意味を持ちません。`dev` と `tests` という 2 つの暗黙的なプロファイルがあり、これらはどのプロジェクトにも存在します。プロファイルについては後ほど詳しく説明します。

`dlt.yml` ファイルでは、`{env.ENV_VARIABLE_NAME}` 構文を使用して環境変数を参照できます。
さらに、dlt+ はいくつかの [定義済みプロジェクト変数](../features/projects.md#project-settings-and-variable-substitution) を提供しており、これらは読み込み時に自動的に置換されます。

:::tip
`dlt.yml` 構造の詳細については、[dlt+ プロジェクト セクション](../core-concepts/project.md) を参照してください。
:::

## パイプラインの実行

プロジェクトが初期化されたら、次のコマンドでパイプラインを実行できます。

```sh
dlt pipeline my_pipeline run
```

このコマンドは、次の処理を実行します。
- `dlt.yml` 内で `my_pipeline` という名前のパイプラインを検索します。
- それを実行し、`_data/dev/local/duckdb.duckdb` 内の [保存先として定義されている](../features/projects.md#local-and-temporary-files-data_dir) duckdb の保存先にデータを入力します。

:::tip
ネストされたプロジェクトの操作方法と、dlt が名前に基づいてパイプラインを検索する方法の詳細については、[プロジェクト コンテキスト](../features/projects.md#project-context) を参照してください。
:::

### 結果の検証

[`dlt dataset` コマンド](../reference.md#dlt-dataset) を使用して、DuckDB の保存先に保存されているデータセットを操作します。例:

### 読み込まれた行数をカウントする

データセット内の行数をカウントするには、次のコマンドを実行します。

```sh
dlt dataset my_pipeline_dataset row-counts
```

これにより、arrow ソースで指定されたアイテムテーブルの行数が表示されます。さらに、内部のDLTテーブルも表示されます。

```sh
            table_name  row_count
0                items        100
1         _dlt_version          1
2           _dlt_loads          1
3  _dlt_pipeline_state          1
```

### データの表示

`items` テーブルの最初の 5 行を表示するには:

```sh
dlt dataset my_pipeline_dataset head items
```

これにより、`items` テーブルの上位エントリが表示され、パイプラインの出力を迅速に検証できるようになります。
出力は次のようになります:

```sh
Loading first 5 rows of table items.

   id   name  age
0   0  jerry   49
1   1    jim   25
2   2   jane   46
3   3   john   48
4   4  jenny   49
```

より多くの行を表示するには、`--limit` フラグを使用します。

```sh
dlt dataset duckdb_dataset head items --limit 50
```

## プロジェクトへのソース、デスティネーション、パイプラインの追加

既存の dlt+ プロジェクトに新しいエンティティを追加するのは簡単です。
次のコマンドを実行することで、プロジェクトに新しいエンティティを追加できます。

```sh
dlt <entity_type> <entity_name> add
```

追加するエンティティに応じて、利用可能なオプションが異なります。
すべてのコマンドを確認するには、[cli コマンドリファレンス](../reference.md)を参照してください。
また、`--help` オプションを使用して、特定のエンティティで利用可能な設定を確認することもできます。
例: `dlt destination add --help`。
前の章で作成したデフォルトのプロジェクトを複製し、ソース、宛先、パイプラインを個別に新しいプロジェクトに追加してみましょう。

### 空のプロジェクトを作成する

`tutorial` フォルダ内のすべてのファイルを削除し、次のコマンドを実行して空のプロジェクトを作成します。

```sh
dlt project init
```

これにより、ソース、宛先、データセット、パイプラインのないプロジェクトが作成され、プロジェクトの名前はフォルダーに基づいて付けられます。

### すべてのエンティティを追加

これで、すべてのエンティティを個別に追加できるようになりました。
この方法では、エンティティに独自の名前を付けることもできます。これは、例えば同じタイプの送信先が複数ある場合などに便利です。

ソースを追加するには、次の操作を行います。

```sh
# add a new arrow source called "my_arrow_source"
dlt source my_arrow_source add arrow
```

宛先を追加するには:

```sh
# add a new duckdb destination called "my_duckdb_destination"
# this will also create a new dataset called "my_duckdb_destination_dataset"
dlt destination my_duckdb_destination add duckdb
```

ここで、先ほど追加したソースと宛先を使用するパイプラインを追加できます:

```sh
# add a new pipeline called "my_pipeline" which loads from my_arrow_source and saves to my_duckdb_destination
# we select the my_duckdb_destination_dataset with the optional flag
dlt pipeline my_pipeline add my_arrow_source my_duckdb_destination
```

### コアソースの追加

CLI コマンドを使用して複数のエンティティを追加できます。
今度は、別のソース、例えば [REST API](../../dlt-ecosystem/verified-sources/rest_api/index.md)、[SQL データベース](../../dlt-ecosystem/verified-sources/sql_database/index.md)、[ファイルシステム](../../dlt-ecosystem/verified-sources/filesystem/index.md) などのコアソースを追加してみましょう。

次のコマンドを実行して、`sql_db_1` という名前の SQL データベースソースを追加します。

```sh
# add a new sql_database source called "sql_db_1"
dlt source sql_db_1 add sql_database
```

これにより、新しいソースが `dlt.yml` ファイルに追加されます。

```yaml
sources:
  arrow:
    type: sources.arrow.source

  sql_db_1:
    type: sql_database
```

対応する認証情報プレースホルダーは `.dlt/secrets.toml` に追加されますが、`dlt.yml` で定義することもできます。

```toml
[sources.sql_db_1]
table_names = ["family", "clan"]

[sources.sql_db_1.credentials]
drivername = "mysql+pymysql"
database = "Rfam"
username = "rfamro"
host = "mysql-rfam-public.ebi.ac.uk"
port = 4497
```

## 構成とプロファイル

dlt+ は新しいコアコンセプトである [プロファイル](../core-concepts/profiles.md) を導入しました。これにより、環境ごとに異なる構成を管理できるようになります。
サンプルプロジェクトを見てみましょう。プロファイルセクションは現在、次のようになっています。

```yaml
profiles:
  dev: {}
```

つまり、`dev` プロファイルは空で、デフォルトではすべての設定がプロジェクト構成から継承されます。
プロジェクト構成の現在の状態を確認するには、次のコマンドを実行します。

```sh
dlt project --profile dev config show
```

これにより、`dev` プロファイルがロードされたプロジェクト構成の現在の状態が表示されます。
`--profile` オプションを指定しない場合は、デフォルトで `dev` プロファイルが使用されます。

### 新しいプロファイルの追加

これで、ロード先のduckdbファイルの場所、プロジェクトのログレベル、ロードする行数を変更する「prod」という新しいプロファイルを作成できます。
以下を実行してください。

```sh
dlt profile prod add
```

そして、prod プロファイルを次のように変更します:

```yaml
  prod:
    sources:
      my_arrow_source:
        row_count: 200
    runtime:
      log_level: INFO
    destinations:
      my_duckdb_destination:
        credentials: my_data_prod.duckdb
```

これで、prod プロファイルを検査できるようになりました。
新しい設定がプロジェクト構成と `dev` プロファイル設定にマージされていることがわかります。

```sh
dlt project --profile prod config show
```

### 新しいプロファイルでパイプラインを実行し、結果を確認します。

では、`prod` プロファイルでパイプラインを実行してみましょう。

```sh
dlt pipeline --profile prod my_pipeline run
```

ログレベルがより詳細になったため、コンソールに表示される出力が増え、ロードされた行数も 100 行から 200 行になりました。
各プロファイルのデータセットを調べてみましょう (前の章で作成した duckdb データベース ファイルがまだ残っていると仮定します)。

```sh
dlt dataset --profile dev my_duckdb_destination_dataset row-counts
dlt dataset --profile prod my_duckdb_destination_dataset row-counts
```

製品プロファイルでは、ロードされた行数が 100 ではなく 200 になっていることがわかります。

:::tip
プロファイルは他のプロファイルから継承することもできます。詳細については、[プロファイル](../core-concepts/profiles.md) を参照してください。
:::

### プロファイルでの設定ファイルの使用

同じ設定ファイルとシークレットのToMLファイル、および環境変数を使用することもできます。
プロジェクトには、プロファイル名が先頭に付いたシークレットファイルが複数含まれていることに気付いたかもしれません。
これらのシークレットファイルは、特定のプロファイルがアクティブな場合にのみ読み込まれます。
これを実証するために、duckdbの認証情報、ランタイム設定、およびソース設定を`dlt.yml`ファイルではなくToMLファイルに移動してみましょう。

まず、`dlt.yml`ファイルの`prod`セクションの内容をすべて削除しますが、キーと空のシークレットファイルはそのまま残しておきます。
`dlt.yml`ファイルから`runtime`セクションを削除し、出力先から`credentials`キーと`sources.my_arrow_source`セクションから`row_count`キーを削除することもできます。
この時点でパイプラインを実行しようとすると、dltは設定値が不足しているというエラーメッセージを表示します。

```sh
dlt pipeline my_pipeline run
```

次に、`dev.secrets.toml` ファイルに次の内容を追加します:

```toml
[runtime]
log_level = "WARNING"

[destination.my_duckdb_destination]
credentials = "my_data.duckdb"

[sources.my_arrow_source]
row_count = 100
```

そして、`prod.secrets.toml` ファイルに次の内容を追加します:

```toml
[runtime]
log_level = "INFO"

[destination.my_duckdb_destination]
credentials = "my_data_prod.duckdb"

[sources.my_arrow_source]
row_count = 200
```

`_data` ディレクトリをクリアし、上記の手順を繰り返して両方のパイプラインを実行し、両方のデータセットを検査します。toml ファイルの設定が適用されていることがわかります。

データを読み込みます:

```sh
dlt pipeline --profile dev my_pipeline run
dlt pipeline --profile prod my_pipeline run
```

データセットを検査します:

```sh
dlt dataset --profile dev my_duckdb_destination_dataset row-counts
dlt dataset --profile prod my_duckdb_destination_dataset row-counts
```

[ロードされたデータ](../features/projects.md#local-and-temporary-files-data_dir)を見つけるには、`_data\{profile name}\local`ディレクトリを確認してください。

