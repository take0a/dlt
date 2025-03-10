---
title: DuckDB
description: DuckDB `dlt` destination
keywords: [duckdb, destination, data warehouse]
---

# DuckDB

## DuckDB で dlt をインストールする

**DuckDB との依存関係を持つ dlt ライブラリをインストールするには、以下を実行します:**

```sh
pip install "dlt[duckdb]"
```

## セットアップガイド

**1. DuckDB にロードするパイプラインでプロジェクトを初期化するには、以下を実行します:**

```sh
dlt init chess duckdb
```

**2. DuckDB に必要な依存関係をインストールするには、次のコマンドを実行します。:**

```sh
pip install -r requirements.txt
```

**3. パイプラインを実行する:**

```sh
python3 chess_pipeline.py
```

## 書き込み処理

すべての書き込み処理がサポートされています。

## データのロード

`dlt` は、デフォルトで大きな INSERT VALUES ステートメントを使用してデータをロードします。ロードはマルチスレッド化されます (デフォルトでは 20 スレッド)。`pyarrow` をインストールしても問題ない場合は、ファイル形式として Parquet に切り替えることをお勧めします。ロードが高速化されます (マルチスレッド化もされます)。

### データ型

`duckdb` はさまざまな [タイムスタンプ型](https://duckdb.org/docs/sql/data_types/timestamp.html) をサポートしています。これらは、`dlt.resource` デコレータまたは `pipeline.run` メソッドの列フラグ `timezone` および `precision` を使用して設定できます。

- **Precision**: サポートされている精度の値は、小数秒の場合は 0、3、6、9 です。`timezone` と `precision` は一緒に使用できないことに注意してください。これらを組み合わせようとするとエラーが発生します。
- **Timezone**:
  - `timezone=False` を設定すると `TIMESTAMP` にマップされます。
  - `timezone=True` を設定すると (またはフラグを省略すると、デフォルトで `True` になります)、`TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`) にマップされます。

#### 精度の例: TIMESTAMP_MS

```py
@dlt.resource(
    columns={"event_tstamp": {"data_type": "timestamp", "precision": 3}},
    primary_key="event_id",
)
def events():
    yield [{"event_id": 1, "event_tstamp": "2024-07-30T10:00:00.123"}]

pipeline = dlt.pipeline(destination="duckdb")
pipeline.run(events())
```

#### タイムゾーンの例: TIMESTAMP

```py
@dlt.resource(
    columns={"event_tstamp": {"data_type": "timestamp", "timezone": False}},
    primary_key="event_id",
)
def events():
    yield [{"event_id": 1, "event_tstamp": "2024-07-30T10:00:00.123+00:00"}]

pipeline = dlt.pipeline(destination="duckdb")
pipeline.run(events())
```

### 名前の正規化

`dlt` は、すべての宛先で同一のテーブルと列の識別子を維持するために、標準の **snake_case** 命名規則を使用します。テーブル名と列名に **duckdb** の幅広い文字 (つまり、絵文字) を使用したい場合は、ほぼすべての文字列を識別子として受け入れる **duck_case** 命名規則に切り替えることができます。:
* 改行 (`\n`)、復帰 (`\r`)、二重引用符 (`"`) はアンダースコア (`_`) に変換されます。
* 連続したアンダースコア (`_`) は 1 つの `_` に変換されます。

`config.toml` を使用して命名規則を切り替える:

```toml
[schema]
naming="duck_case"
```

または環境変数`SCHEMA__NAMING`経由、またはコード内で直接:

```py
dlt.config["schema.naming"] = "duck_case"
```

:::caution
**duckdb** 識別子は **大文字と小文字を区別しません** が、表示名では大文字と小文字が保持されます。たとえば、JSON を `{"Column": 1, "column": 2}` でロードすると、データが 1 つの列にマップされるため、名前の衝突が発生する可能性があります。
:::

## サポートされているファイル形式

duckdbにデータをロードするには、次のファイル形式を設定できます:

* [insert-values](../file-formats/insert-format.md) は、デフォルトです。
* [Parquet](../file-formats/parquet.md) は、サポートされます。

:::note
`duckdb` は、複数のスレッドから単一のテーブルに多数の Parquet ファイルを COPY できません。この状況では、dlt はロードをシリアル化します。それでも、INSERT よりも高速になる可能性があります。
:::

* [JSONL](../file-formats/jsonl.md)

:::tip
`duckdb` には、ミリ秒からナノ秒までの解像度を持つ [タイムスタンプ型](https://duckdb.org/docs/sql/data_types/timestamp.html) があります。ただし、タイムゾーンを認識するのはマイクロ秒解像度 (最も一般的に使用される) のみです。`dlt` はデフォルトでタイムゾーン付きのタイムスタンプを生成するため、デフォルト設定で parquet ファイルをロードすると失敗します (`duckdb` は tz 対応のタイムスタンプをナイーブなタイムスタンプに強制変換しません)。
次のように `dlt` [Parquet ライター設定](../file-formats/parquet.md#writer-settings) を変更して、タイムゾーンを無効にします。:

```sh
DATA_WRITER__TIMESTAMP_TIMEZONE=""
```
tz 調整を無効にします。
:::

## サポートされている列のヒント

`duckdb` は、`unique` ヒントを使用して列に一意のインデックスを作成できます。ただし、データの読み込み速度が大幅に低下する可能性があるため、**この機能はデフォルトで無効になっています**。

## 宛先構成

デフォルトでは、DuckDB データベースは現在の作業ディレクトリに `<pipeline_name>.duckdb` (上記の例では `chess.duckdb`) という名前で作成されます。ロード後は、`DuckDBPyConnection` のラッパーである `with pipeline.sql_client() as con:` を介して **読み取り/書き込み** モードで使用できます。詳細については、[duckdb ドキュメント](https://duckdb.org/docs/api/python/overview#persistent-storage) を参照してください。データを **読み取り** する場合は、`sql_client` ではなく [pipeline.dataset()](../../general-usage/dataset-access/dataset) を使用します。

`duckdb` 認証情報には秘密の値は必要ありません。[認証情報と設定を明示的に渡すことができます](../../general-usage/destination.md#pass-explicit-credentials)。例えば:

```py
# will load data to files/data.db (relative path) database file
p = dlt.pipeline(
  pipeline_name='chess',
  destination=dlt.destinations.duckdb("files/data.db"),
  dataset_name='chess_data',
  dev_mode=False
)

# will load data to /var/local/database.duckdb (absolute path)
p = dlt.pipeline(
  pipeline_name='chess',
  destination=dlt.destinations.duckdb("/var/local/database.duckdb"),
  dataset_name='chess_data',
  dev_mode=False
)
```

名前付き `duckdb` 宛先は、現在の作業ディレクトリに `<destination_name>.duckdb` というデータベースファイルを作成します。たとえば、:

```py
# will load data to files/data.db (relative path) database file
p = dlt.pipeline(
  pipeline_name='chess',
  destination=dlt.destinations.duckdb(destination_name="chessdb"),
  dataset_name='chess_data',
)
```

データベース `chessdb.duckdb' を作成します。

:::caution
データセットをデータベースと同じ名前にすることは避けてください。カタログとスキーマが同じであるため、`duckdb`バインダーが混乱します。例:

```py
pipeline = dlt.pipeline(
        pipeline_name="dummy",
        destination="duckdb",
        dataset_name="dummy",
    )
```

データベース `dummy.duckdb` とスキーマ (データセット) `dummy` が作成されますが、これらが混乱してバインダー エラーが発生します。
:::

宛先は `credentials` を介して `duckdb` 接続インスタンスを受け入れるため、自分でデータベース接続を開いて `dlt` に渡して使用することもできます。

```py
import duckdb

db = duckdb.connect()
p = dlt.pipeline(
  pipeline_name="chess",
  destination=dlt.destinations.duckdb(db),
  dataset_name="chess_data",
  dev_mode=False,
)

# Or if you would like to use an in-memory duckdb instance
db = duckdb.connect(":memory:")
p = pipeline_one = dlt.pipeline(
  pipeline_name="in_memory_pipeline",
  destination=dlt.destinations.duckdb(db),
  dataset_name="chess_data",
)

print(db.sql("DESCRIBE;"))

# Example output
# ┌──────────┬───────────────┬─────────────────────┬──────────────────────┬───────────────────────┬───────────┐
# │ database │    schema     │        name         │     column_names     │     column_types      │ temporary │
# │ varchar  │    varchar    │       varchar       │      varchar[]       │       varchar[]       │  boolean  │
# ├──────────┼───────────────┼─────────────────────┼──────────────────────┼───────────────────────┼───────────┤
# │ memory   │ chess_data    │ _dlt_loads          │ [load_id, schema_n…  │ [VARCHAR, VARCHAR, …  │ false     │
# │ memory   │ chess_data    │ _dlt_pipeline_state │ [version, engine_v…  │ [BIGINT, BIGINT, VA…  │ false     │
# │ memory   │ chess_data    │ _dlt_version        │ [version, engine_v…  │ [BIGINT, BIGINT, TI…  │ false     │
# │ memory   │ chess_data    │ my_table            │ [a, _dlt_load_id, …  │ [BIGINT, VARCHAR, V…  │ false     │
# └──────────┴───────────────┴─────────────────────┴──────────────────────┴───────────────────────┴───────────┘
```

:::note
注意してください! Python スクリプトが終了すると、データベースのメモリ内インスタンスは破棄されます。
:::

この宛先は、[duckdb-engine](https://github.com/Mause/duckdb_engine#configuration) で使用される形式のデータベース接続文字列を受け入れます。

DuckDB の宛先は、[secret / config values](../../general-usage/credentials) を使用して設定できます (例: `secrets.toml` ファイルを使用)

```toml
destination.duckdb.credentials="duckdb:///_storage/test_quack.duckdb"
```

上記の **duckdb://** URL は、`_storage/test_quack.duckdb` への **相対** パスを作成します。**絶対** パスを定義するには、4 つのスラッシュ、つまり `duckdb:////_storage/test_quack.duckdb` を指定する必要があります。

スキーマをスキップしてパスを直接渡すこともできます:

```toml
destination.duckdb.credentials="_storage/test_quack.duckdb"
```

**:pipeline:** をパスとして渡すことで、パイプラインの作業ディレクトリにデータベースを配置することもできます。データベースの名前は `<pipeline_name>.duckdb` になります。

1. `config.toml` で

```toml
destination.duckdb.credentials=":pipeline:"
```

2. Python コードで

```py
p = pipeline_one = dlt.pipeline(
  pipeline_name="my_pipeline",
  destination=dlt.destinations.duckdb(":pipeline:"),
)
```

### 追加構成

次の設定値が設定されている場合は、読み込み中に一意のインデックスが作成されることがあります:

```toml
[destination.duckdb]
create_indexes=true
```

### dbt サポート

この宛先は、コミュニティがサポートするパッケージである [dbt-duckdb](https://github.com/jwills/dbt-duckdb) を介して [dbt と統合](../transformations/dbt/dbt.md) します。`duckdb` データベースは `dbt` と共有されます。まれに、バイナリ データベース形式が `dbt-duckdb` で想定されるデータベース形式と一致しないという情報が表示される場合があります。`dlt` プロジェクトで `duckdb` パッケージを `pip install -U` で更新することで、これを回避できます。

### `dlt` の状態の同期

この宛先は、[dlt state sync](../../general-usage/state#syncing-state-with-destination) を完全にサポートします。

<!--@@@DLT_TUBA duckdb-->

