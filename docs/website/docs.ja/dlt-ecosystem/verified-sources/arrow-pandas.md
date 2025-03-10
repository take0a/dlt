---
title: Arrow Table / Pandas
description: dlt source for Arrow tables and Pandas dataframes
keywords: [arrow, pandas, parquet, source]
---
import Header from './_source-info-header.md';

# Arrow table / Pandas

<Header/>

Arrow テーブルまたは Pandas データフレームから直接データを読み込むことができます。
これはすべての宛先でサポートされていますが、Parquet ファイル形式をネイティブにサポートする宛先 (例: [Snowflake](../destinations/snowflake.md) および [Filesystem](../destinations/filesystem.md)) を使用する場合に特に推奨されます。
詳細については、[宛先サポート](#destination-support-and-fallback) セクションを参照してください。

Parquet がサポートする宛先で使用すると、`dlt` はパイプラインを介して JSON オブジェクトを渡す際に通常必要となる多くの処理手順をバイパスするため、構造化データをロードするよりパフォーマンスの高い方法になります。
`dlt` は、Arrow テーブルのスキーマを宛先テーブルのスキーマに自動的に変換し、テーブルを parquet ファイルに書き込みます。このファイルは、それ以上の処理なしで宛先にアップロードされます。

## 使用法

Arrow ソースを書き込むには、`pyarrow.Table`、`pyarrow.RecordBatch`、または `pandas.DataFrame` オブジェクト (またはそのリスト) をパイプラインの `run` または `extract` メソッドに渡すか、`@dlt.resource` デコレートされた関数からテーブル/データフレームを生成します。

この例では、Pandas データフレームを Snowflake テーブルにロードします。:

```py
import dlt
from dlt.common import pendulum
import pandas as pd


df = pd.DataFrame({
    "order_id": [1, 2, 3],
    "customer_id": [1, 2, 3],
    "ordered_at": [pendulum.DateTime(2021, 1, 1, 4, 5, 6), pendulum.DateTime(2021, 1, 3, 4, 5, 6), pendulum.DateTime(2021, 1, 6, 4, 5, 6)],
    "order_amount": [100.0, 200.0, 300.0],
})

pipeline = dlt.pipeline("orders_pipeline", destination="snowflake")

pipeline.run(df, table_name="orders")
```

Pandas のインデックスはデフォルトでは保存されないことに注意してください (`dlt` バージョン 1.4.1 以降)。何らかの理由で保存先が必要な場合は、`preserve_index` を True に設定して `Table.from_pandas` を使用して、データフレームを明示的に arrow テーブルに変換します。

`pyarrow`テーブルも同様の方法でロードできる:

```py
import pyarrow as pa

# Create dataframe and pipeline same as above
...

table = pa.Table.from_pandas(df)
pipeline.run(table, table_name="orders")
```

注: データ変換は実行されないため、テーブル内のデータは宛先データベースと互換性がある必要があります。サポートされているデータ型の詳細については、宛先のドキュメントを参照してください。

## 宛先のサポート

Parquet 形式をネイティブにサポートする宛先では、データファイルが可能な限り直接アップロードされます。多くの場合、ファイルの書き換えは完全に回避できます。

宛先が Parquet をサポートしていない場合、行はテーブルから抽出され、宛先のネイティブ形式 (通常は `insert_values`) で書き込まれます。これは、テーブルを行ごとに処理し、データをディスクに書き直す必要があるため、通常、はるかに遅くなります。

出力ファイルの形式は宛先の機能に基づいて自動的に選択されるため、arrow フレームまたは pandas フレームを任意の宛先に読み込むことができますが、パフォーマンスは異なります。

### 直接読み込み用に parquet をネイティブにサポートする宛先

* duckdb & motherduck
* redshift
* bigquery
* snowflake
* filesystem
* athena
* databricks
* dremio
* synapse

## テーブルに `_dlt_load_id` と `_dlt_id` を追加します

`dlt` は、Arrow テーブルをロードするときに、デフォルトではデータ系統列を追加しません。これは、最高のパフォーマンスを提供し、不要なデータのコピーを回避するためです。

ただし、必要な場合は、次の構成オプションを使用して、`_dlt_load_id` (行が追加されたときのロード操作のID) と `_dlt_id` (行の一意のID) 列をそれぞれ追加できます:

```toml
[normalize.parquet_normalizer]
add_dlt_load_id = true
add_dlt_id = true
```

これらを有効にするとパフォーマンスのオーバーヘッドが発生することに注意してください:

- `add_dlt_load_id` は、parquet ファイルがディスクに書き込まれる前の `extract` ステージでメモリ内の arrow テーブルに列が追加されるため、オーバーヘッドは最小限です。
- `add_dlt_id` は、ファイルがディスクに抽出された後の `normalize` 段階で列を追加します。ファイルは、チャンク単位でディスクから読み戻され、処理され、新しい列で書き直される必要があります。

## Arrow テーブルによるインクリメンタルローディング

Arrow テーブルでもインクリメンタルロードを使用できます。
使用方法は他の dlt リソースと同じです。詳細については、[インクリメンタルローディング](../../general-usage/incremental-loading.md)ガイドを参照してください。

例:

```py
import dlt
from dlt.common import pendulum
import pandas as pd

# Create a resource that yields a dataframe, using the `ordered_at` field as an incremental cursor
@dlt.resource(primary_key="order_id")
def orders(ordered_at = dlt.sources.incremental('ordered_at')):
    # Get a dataframe/arrow table from somewhere
    # If your database supports it, you can use the last_value to filter data at the source.
    # Otherwise, it will be filtered automatically after loading the data.
    df = _get_orders(since=ordered_at.last_value)
    yield df

pipeline = dlt.pipeline("orders_pipeline", destination="snowflake")
pipeline.run(orders)
# Run again to load only new data
pipeline.run(orders)
```

:::tip
[Connector X + Arrow の例](../../examples/connector_x_arrow/)を参照して、運用データベースからデータを高速にロードする方法を確認してください。
:::

## JSONドキュメントの読み込み

デフォルトの `dlt` JSON ノーマライザーをスキップする場合は、利用可能な任意の方法を使用して JSON ドキュメントを表形式のデータに変換できます。

* **pandas** には `read_json` と `json_normalize` メソッドがあります。
* **pyarrow** は、テーブルスキーマを推測し、`read_json` を使用してJSONファイルをテーブルに変換できます。
* **duckdb** は `read_json_auto` で同じことができます。

```py
import duckdb

conn = duckdb.connect()
table = conn.execute("SELECT * FROM read_json_auto('./json_file_path')").fetch_arrow_table()
```

**duckdb** および **pyarrow** メソッドは、ネストされたデータに対して [ネストされた型](#loading-nested-types) を生成しますが、これは `dlt` では部分的にしかサポートされていないことに注意してください。

## サポートされる Arrow データ型

Arrowデータ型は次のようにdltデータ型に変換されます。:

| Arrow 型        | dlt 型    | 注記                              |
|-------------------|-------------|------------------------------------|
| `string`          | `text`      |                                    |
| `float`/`double`  | `double`    |                                    |
| `boolean`         | `bool`      |                                    |
| `timestamp`       | `timestamp` | 精度はタイムスタンプの単位によって決まります。 |
| `date`            | `date`      |                                    |
| `time<bit_width>` | `time`      | 精度は時間の単位によって決まります。  |
| `int<bit_width>`  | `bigint`    | 精度はビット幅によって決まります。    |
| `binary`          | `binary`    |                                    |
| `decimal`         | `decimal`   | 精度とスケールは、型のプロパティによって決まります。 |
| `struct`          | `json`      |                                    |
|                   |             |                                    |

## ネストされた型のロード

すべての構造体型は `json` として表され、JSON（宛先が許可する場合）または文字列としてロードされます。現在、**struct** 型は宛先に存在していてもサポートされていません（**BigQuery** は [処理するように構成できます](../destinations/bigquery.md#use-bigquery-schema-autodetect-for-nested-fields))

ネストされたデータを別々のテーブルとして表現したい場合は、pandas フレームと arrow テーブルをレコードとして生成する必要があります。上記の例では:

```py
# yield panda frame as records
pipeline.run(df.to_dict(orient='records'), table_name="orders")

# yield arrow table
pipeline.run(table.to_pylist(), table_name="orders")
```

Pandas と Arrow はどちらもレコードをバッチでストリーミングできます。
