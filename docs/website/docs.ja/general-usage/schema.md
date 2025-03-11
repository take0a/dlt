---
title: Schema
description: Schema
keywords: [schema, dlt schema, yaml]
---

# Schema

スキーマは、正規化されたデータの構造 (テーブル、列、データ型など) を記述し、データの処理方法とロード方法に関する指示を提供します。dlt は、正規化プロセス中にデータからスキーマを生成します。ユーザーは、テーブル、列、その他のメタデータの生成方法とデータのロード方法を変更する **ヒント** を提供することで、この標準の動作に影響を与えることができます。このようなヒントは、コード内で、つまり `dlt.resource` デコレータまたは `pipeline.run` メソッドに渡すことができます。スキーマは、直接変更できるファイルとしてエクスポートおよびインポートすることもできます。

> 💡 `dlt` はスキーマを [ソース](source.md) に関連付け、テーブルスキーマを [リソース](resource.md) に関連付けます。

## スキーマコンテンツのハッシュとバージョン

各スキーマファイルには、コンテンツベースのハッシュ「version_hash」が含まれており:

1. スキーマへの手動変更 (つまり、ユーザーによるコンテンツの編集) を検出します。
1. 宛先データベースのスキーマがファイルのスキーマと同期されているかどうかを検出します。

スキーマが保存されるたびに、バージョンハッシュが更新されます。

各スキーマには数値バージョンが含まれており、スキーマが更新されて保存されるたびに自動的に増加します。数値バージョンは人間が判読できるようになっています。順序が失われる場合があります (並列処理)。

> 💡 ハッシュが `_dlt_versions` テーブルに格納されていない場合、宛先のスキーマは移行されます。原則として、多くのパイプラインが単一のデータセットにデータを送信する場合があります。テーブル名が競合する場合は、列の結合を含む単一のテーブルが作成されます。列が競合し、タイプが異なるなどの場合、データを強制変換できないとロードが失敗する可能性があります。

## 命名規則

`dlt` は、データからテーブル、ネストされたテーブル、および列スキーマを作成します。ロードされるデータ (通常は JSON ドキュメント) には、任意の Unicode 文字、任意の長さ、および命名スタイルを持つ識別子 (辞書内のキー名など) が含まれます。一方、宛先は識別子に対して非常に厳密な名前空間を受け入れます。Redshift と同様に、最大 127 文字の大文字と小文字を区別しない英数字の識別子を受け入れます。

各スキーマには、[命名規則](naming-convention.md) が含まれており、これは dlt に識別子を宛先が理解できる名前空間に変換する方法を伝えます。この規則は、コードで構成したり、変更したり、宛先を介して適用したりできます。

デフォルトの命名規則:

1. 識別子をスネークケース、小文字に変換します。ASCII 英数字とアンダースコアを除くすべての ASCII 文字を削除します。
1. 名前が数字で始まる場合は `_` を追加します。
1. 複数の `_` は 1 つの `_` に変換されます。
1. ネストは名前の中で二重の `_` として表現されます。
1. 宛先で識別子の長さを超える場合は、識別子を短縮します。

> 💡 `dlt` の標準的な動作は、**すべての宛先に同じ命名規則を使用する** ことで、ユーザーはデータベース内で常に同じテーブルと列を参照できます。

> 💡 デコレータまたは引数 (つまり、`table_name` または `columns`) を介して識別子を含むスキーマ要素を指定すると、使用されるすべての名前は、スキーマに追加するときに命名規則によって変換されます。たとえば、`dlt.run(... table_name="CamelCase")` を実行すると、データは `camel_case` にロードされます。

> 💡 すべてにシンプルで短い小文字の識別子を使用してください。

元の命名規則を維持するには（`"createdAt"` を `"created_at"` に変換せずにそのままにしておくなど）、次のように "config.toml" で直接命名規則を使用できます:

```toml
[schema]
naming="direct"
```

:::caution
`"direct"` 命名を選択すると、ほとんどの名前正規化プロセスがバイパスされます。つまり、存在する異常な文字は変更されずにデータベース テーブルと列に引き継がれます。潜在的な問題を回避するために、この動作に注意してください。
:::

命名規則は設定可能で、ユーザーは独自の規則を簡単に作成できます。つまり、宛先がそれを受け入れる場合 (つまり、DuckDB)、すべての識別子を変更せずに渡すことができます。

## データ正規化

データ ノーマライザーは、入力データの構造を変更して、宛先にロードできるようにします。標準の `dlt` ノーマライザーは、Python 辞書とリストからリレーショナル構造を作成します。テーブルや列の定義などの構造の要素がスキーマに追加されます。

データ正規化機能は構成可能で、ユーザーは独自の正規化機能をプラグインして、たとえば、ネストされたテーブルのリンクを別の方法で処理したり、ネストされたテーブルの代わりに parquet のようなデータ構造を生成したりできます。

## テーブルと列

スキーマの主要コンポーネントはテーブルと列です。テーブルの辞書は、`tables` キー内、または Schema オブジェクトの `tables` プロパティで見つけることができます。

テーブルスキーマには次のプロパティがあります:

1. `name` と `description`。
2. テーブルスキーマの辞書に `columns`
3. `write_disposition` ヒントは、テーブルに送られる新しいデータがどのようにロードされるかを `dlt` に伝えます。
4. `schema_contract` - [テーブル上の契約](schema-contracts.md)を記述します。
5. `parent` はネストされた参照の一部であり、ネストされたテーブル上で定義され、親テーブルを指します。

テーブル スキーマはデータ ノーマライザーによって拡張されます。標準データノーマライザーは、伝播された列を追加します。

列スキーマには次のプロパティが含まれます:

1. テーブル内の列の `name` と `description`。

データ型の情報:

1. 列のデータ型を持つ `data_type`。
2. `precision` は、**text**、**timestamp**、**time**、**bigint**、**binary**、および **decimal** 型の精度です。
3. `scale` は **decimal** 型のスケールです。
4. `timezone` は、TZ 対応または NTZ **timestamp** と **time** を示すフラグです。デフォルト値は **true** です。
5. `nullable` は列が null 可能かどうかを示します。
6. `is_variant` は、列が別の列のバリアントとして生成されたことを示します。

列スキーマには以下の基本的なヒントが含まれています:

1. `primary_key` は列を主キーの一部としてマークします。
2. `unique` は列が一意であることを示します。一部の宛先では、これにより一意のインデックスが生成されます。
3. `merge_key` は、[インクリメンタルロード](./incremental-loading.md#merge-incremental_loading) で使用されるマージ キーの一部として列をマークします。

以下のヒントは、[ネストされた参照](#root-and-nested-tables-nested-references) を作成するために使用されます:

1. `row_key` は、データの行を一意に識別するために `dlt` によって作成される特別な形式の主キーです。
2. `parent_key` は、ネストされたテーブルが親テーブルを参照するために使用する特別な形式の外部キーです。
3. `root_key` は、常にルート テーブルを参照する外部キーの一種であるルート キーの一部として列をマークします。
4. `_dlt_list_idx` は、ネストされたテーブルが作成されるネストされたリスト上のインデックスです。

`dlt` を使用すると、追加のパフォーマンスヒントを定義できます。:

1. `partition` は、データをパーティション分割するために使用される列をマークします。
2. `cluster` は、データをクラスタ化するために使用する列をマークします。
3. `sort` は、列をソート可能/順序付きとしてマークします。一部の宛先では、この非一意のインデックスが生成されます。

:::note
各宛先は独自の方法でヒントを解釈できます。たとえば、`cluster` ヒントは、Redshift ではテーブル分散を定義するために使用され、BigQuery ではクラスター列を指定するために使用されます。DuckDB と Postgres はテーブルの作成時にこれを無視します。
:::

### バリアント列

バリアント列は、既存の列に強制変換できないタイプのデータ項目に遭遇したときに、ノーマライザーによって生成されます。内部でどのように動作するかを確認するには、[`coerce_row`](https://github.com/dlt-hub/dlt/blob/7d9baf1b8fdf2813bcf7f1afe5bb3558993305ca/dlt/common/schema/schema.py#L205) を参照してください。

少し異なるアプローチで [はじめに](../intro) の例を考えてみましょう。ここでは、最初は `id` が整数型です:

```py
data = [
  {"id": 1, "human_name": "Alice"}
]
```

パイプラインが実行されると、次のスキーマが作成されます:

| name          | data_type     | nullable |
| ------------- | ------------- | -------- |
| id            | bigint        | true     |
| human_name    | text          | true     |

ここで、データが変更され、`id` フィールドにも文字列が含まれていると想像してください:

```py
data = [
  {"id": 1, "human_name": "Alice"},
  {"id": "idx-nr-456", "human_name": "Bob"}
]
```

したがって、パイプラインを実行すると、`dlt` は自動的に型の変更を推測し、`id` の新しいデータ型を反映するためにスキーマ `id__v_text` に新しいフィールドを追加します。整数と互換性のない型の場合は、新しいフィールドが作成されます。

| name          | data_type     | nullable |
| ------------- | ------------- | -------- |
| id            | bigint        | true     |
| human_name    | text          | true     |
| id__v_text    | text          | true     |

一方、`id` フィールドがすでに文字列である場合、`id` に他の型を含む新しいデータを導入しても、強制的に文字列に変換できるため、スキーマは変更されません。

次に、`id` が浮動小数点数である新しいレコードを追加してみてください。スキーマに新しいフィールド `id__v_double` が表示されます。

### データ型

| dlt Data Type | Source Value Example                              | Precision and Scale |
| ------------- | ------------------------------------------------- |-------------------- |
| text          | `'hello world'` | 精度をサポートし、通常は **VARCHAR(N)** にマッピングされます。 |
| double        | `45.678`                            |                         |
| bool          |                |                                                       |
| timestamp     | `'2023-07-26T14:45:00Z'`, `datetime.datetime.now()` | 秒単位で表された精度をサポート       |
| date          | `datetime.date(2023, 7, 26)           |                                 |
| time          | `'14:01:02'`, `datetime.time(14, 1, 2)`   | 精度をサポートします - **timestamp** を参照してください            |
| bigint        | `9876543210`  | ビット数による精度をサポート                    |
| binary        | `b'\x00\x01\x02\x03'`    | **text** のような精度をサポートします     |
| json          | `[4, 5, 6]`, `{'a': 1}   |                                              |
| decimal       | `Decimal('4.56')`  | 精度とスケールをサポート          |
| wei           | `2**56`      |                                                         |

`wei` は、ネイティブ Ethereum 256 ビット整数と固定小数点小数を最適に表現しようとするデータ型です。Postgres と BigQuery では正しく動作します。他のすべての宛先では精度が不十分です。

`json` データ型は、`dlt` にその要素を JSON または文字列として読み込み、それをフラット化したりネストされたテーブルを作成したりしないように指示します。配列やマップなどの構造化型は、現時点では `dlt` ではサポートされていないことに注意してください。

`time` データ型はタイムゾーン情報なしで保存先に保存されます。タイムゾーンが含まれている場合は削除されます。例: `'14:01:02+02:00` -> `'14:01:02'`。

:::tip
精度とスケールは特定の宛先によって解釈され、列の作成時に検証されます。特定のデータ型の精度をサポートしていない宛先では、そのデータ型は無視されます。

**timestamp** の精度は、**parquet** ファイルを作成するときに役立ちます。ミリ秒の場合は 3、マイクロ秒の場合は 6、ナノ秒の場合は 9 を使用します。

**bigint** の精度は、使用可能な整数型、つまり TINYINT、INT、BIGINT にマップされます。デフォルトは 64 ビット (8 バイト) の精度 (BIGINT) です。
:::

## テーブル参照

`dlt`テーブルは他のテーブルを参照します。このような参照には2つの種類があります:

1. **ネストされた参照** は、ネストされたデータ (つまり、ネストされたリストを含む `json` ドキュメント) がリレーショナル形式に変換されるときに自動的に作成されます。これらの参照は、特殊な列とテーブルのヒントを使用し、たとえば [データのマージ](incremental-loading.md) 時に使用されます。
2. **テーブル参照** は、検証および強制されないオプションのユーザー定義の注釈ですが、たとえば、読み込まれたデータの自動テストやモデルを生成するために下流のツールによって使用される場合があります。

### ネストされた参照: ルートとネストされたテーブル

`dlt` がネストされたデータをリレーショナル スキーマに正規化すると、[**ルート** テーブルと **ネストされた** テーブル](destination-tables.md) が自動的に作成され、**ネストされた参照** を使用してリンクされます。

1. すべてのテーブルには、データの各行を一意に識別するための `row_key` ヒント (デフォルトでは `_dlt_id` という名前) を持つ列が割り当てられます。
2. ネストされたテーブルは、親テーブルの名前を持つ `parent` テーブルヒントを受け取ります。ルート テーブルには `parent` ヒントが定義されていません。
3. ネストされたテーブルは、`parent` テーブルの `row_key` を参照する `parent_key` ヒント (デフォルトでは `_dlt_parent_id` という名前) を持つ列を受け取ります。

`parent` + `row_key` + `parent_key` は、ネストされたテーブルから `parent` テーブルへの **ネストされた参照** を形成し、データのロード時に広く使用されます。`replace` と `merge` はどちらも処理を書き込みます。

`row_key` は次のように作成されます:

1. [`upsert`](incremental-loading.md#upsert-strategy) および [`scd2`](incremental-loading.md#scd2-strategy) マージ戦略を除く **root** テーブル上のランダムな文字列。この場合、これは `primary_key` (または PK が定義されていない場合は行全体、いわゆる `content_hash`) の決定論的なハッシュです。
2. **ネストされた** テーブルの場合、`parent_key`、`parent` テーブル名、およびリスト内の位置 (`_dlt_list_idx`) の決定論的なハッシュ。

データ (ルートとネストの両方) に `_dlt_id` 列/フィールドを追加することで、独自の `row_key` を使用できます。等号演算子を持つすべてのデータ型がサポートされています。

`merge` 書き込み処理には、**ネストされた** テーブルから **ルート** テーブルまで、その間にあるすべての親テーブルをスキップする追加のネストされた参照が必要です。この参照は、`root_key` (デフォルトでは `_dlt_root_id` という名前) [ヒントを含む列](incremental-loading.md#forcing-root-key-propagation)をネストされたテーブルに追加することによって作成されます。

### テーブル参照

テーブル参照を使用してテーブルに注釈を付けることができます。この機能は近日中にリリースされる予定です。

## スキーマ設定

スキーマ ファイルの `settings` セクションでは、データからテーブルと列を推測する方法に影響を与えるさまざまなグローバル ルールを定義できます。たとえば、`id` という名前のすべての列に **primary_key** ヒントを割り当てたり、正規表現パターンを使用して `timestamp` を含むすべての列に **timestamp** データ型を強制したりできます。

### データ型自動検出

値から列のデータ型を推測するために使用される関数のセットを定義できます。関数はリストの上から下に向かって実行されます。何が利用できるかを確認するには、`detections.py` を参照してください。ISO 8601 文字列を探して **timestamp** に変換する **iso_timestamp** 検出器は、デフォルトで有効になっています。

```yaml
settings:
  detections:
    - timestamp
    - iso_timestamp
    - iso_date
    - large_integer
    - hexbytes_to_text
    - wei_to_double
```

あるいは、コードから検出を追加したり削除したりすることもできます:

```py
  source = data_source()
  # remove iso time detector
  source.schema.remove_type_detection("iso_timestamp")
  # convert UNIX timestamp (float, within a year from NOW) into timestamp
  source.schema.add_type_detection("timestamp")
```

上記では、**timestamp** 検出器を使用して UNIX タイムスタンプを検出するために、ソースに付属するスキーマを変更します。

### 列ヒントのルール

新しく推測された列にヒントを適用するグローバル ルールを定義できます。これらのルールは正規化された列名に適用されます。列名は直接使用することも、正規表現を使用して使用することもできます。`dlt` は、**命名規則で正規化された後の**列名と一致します。

デフォルトでは、スキーマはjson(リレーショナル)ノーマライザーからヒントルールを採用し、ノーマライザーによって追加された列の正しいヒントをサポートします:

```yaml
settings:
  default_hints:
    row_key:
      - _dlt_id
    parent_key:
      - _dlt_parent_id
    not_null:
      - _dlt_id
      - _dlt_root_id
      - _dlt_parent_id
      - _dlt_list_idx
      - _dlt_load_id
    unique:
      - _dlt_id
    root_key:
      - _dlt_root_id
```

上記では、ヒントを適用するには列名が完全に一致している必要があります。次のように正規表現（`SimpleRegex`と呼びます）を使用することもできます:

```yaml
settings:
    partition:
      - re:_timestamp$
```

上記では、`_timestamp`で終わるすべての列に`partition`ヒントを追加しています。コードでも同じことができます:

```py
  from dlt.common.schema.typing import TSimpleRegex
  
  source = data_source()
  # this will update existing hints with the hints passed
  source.schema.merge_hints({"partition": [TSimpleRegex("re:_timestamp$")]})
```

### 推奨されるデータ型

新しく作成された列のデータ型を設定するルールを定義できます。ルールは、`settings` の `preferred_types` キーの下に配置します。左側には列名に関するルールがあり、右側にはデータ型があります。列名は直接使用することも、正規表現を使用して使用することもできます。`dlt` は、**命名規則で正規化された後** に列名と一致します。

例:

```yaml
settings:
  preferred_types:
    re:timestamp: timestamp
    inserted_at: timestamp
    created_at: timestamp
    updated_at: timestamp
```

上記では、**timestamp** サブ文字列を含むすべての列に `timestamp` データ型を使用し、いくつかの完全一致 (つまり **created_at**) を定義します。
同じことをコードで表すと次のようになります:

```py
  source = data_source()
  source.schema.update_preferred_types(
    {
      TSimpleRegex("re:timestamp"): "timestamp",
      TSimpleRegex("inserted_at"): "timestamp",
      TSimpleRegex("created_at"): "timestamp",
      TSimpleRegex("updated_at"): "timestamp",
    }
  )
```

### `@dlt.resource` と `apply_hints` を使用してデータ型を直接適用する

`dlt` は、スキーマのインポートや調整を必要とせず、コードにデータ型とヒントを直接適用する柔軟性を提供します。このアプローチは、動的なスキーマ要件を持つデータ ソースの迅速なプロトタイピングと処理に最適です。

### `@dlt.resource` での直接指定

`@dlt.resource` デコレータ内でデータ型とそのプロパティ（null 値など）を直接定義します。これにより、外部スキーマ ファイルへの依存がなくなります。たとえば:

```py
@dlt.resource(name='my_table', columns={"my_column": {"data_type": "bool", "nullable": True}})
def my_resource():
    for i in range(10):
        yield {'my_column': i % 2 == 0}
```

このコード スニペットは、デコレータ内で直接 `my_column` という名前の null 許容のブール列を設定します。

#### `apply_hints` の使用

動的に生成されたリソースを扱ったり、プログラムでヒントを設定したりする必要がある場合は、`apply_hints` が役立ちます。これは、さまざまなコレクションやテーブルに一度にヒントを適用する場合に特に便利です。

たとえば、MongoDBソースからのすべてのコレクションに`json`データ型を適用するには:

```py
all_collections = ["collection1", "collection2", "collection3"]  # replace with your actual collection names
source_data = mongodb().with_resources(*all_collections)

for col in all_collections:
    source_data.resources[col].apply_hints(columns={"column_name": {"data_type": "json"}})

pipeline = dlt.pipeline(
    pipeline_name="mongodb_pipeline",
    destination="duckdb",
    dataset_name="mongodb_data"
)
load_info = pipeline.run(source_data)
```

この例では、MongoDB コレクションを反復処理し、**json** [データ型](schema#data-types) を指定された列に適用してから、`pipeline.run` を使用してデータを処理します。

## スキーマを表示および印刷する

デフォルトのスキーマをYAML形式で表示および印刷するには、次のコマンドを使用します:

```py
pipeline.default_schema.to_pretty_yaml()
```

これはパイプラインで次のように使用できます:

```py
# Create a pipeline
pipeline = dlt.pipeline(
               pipeline_name="chess_pipeline",
               destination='duckdb',
               dataset_name="games_data")

# Run the pipeline
load_info = pipeline.run(source)

# Print the default schema in a pretty YAML format
print(pipeline.default_schema.to_pretty_yaml())
```

これにより、スキーマの構造化された YAML 表現が表示され、テーブル、列、データ型、メタデータ (バージョン、version_hash、engine_version など) などの詳細が示されます。

## スキーマファイルのエクスポートとインポート

パイプラインで YAML スキーマ ファイルをエクスポートおよびインポートするには、[スキーマを調整する方法](../walkthroughs/adjust-a-schema.md) のガイドに従ってください。

## ソースにスキーマを添付する

スキーマを明示的に作成しないことをお勧めします。代わりに、ユーザーはいくつかのグローバルスキーマ設定を提供し、リソースヒントとデータ自体からテーブルと列のスキーマを生成できるようにする必要があります。

`dlt.source`デコレータは、自分で作成して好きなように変更できるスキーマインスタンスを受け入れます。デコレータは、いくつかの典型的な使用例もサポートしています:

### デコレータによって暗黙的に作成されたスキーマ

スキーマ インスタンスが渡されない場合、デコレータは名前をソース名に設定し、すべての設定をデフォルトにしたスキーマを作成します。

### ソース Python モジュールに保存されたスキーマファイルを自動ロード

スキーマ インスタンスが渡されず、装飾された関数を含むモジュールと同じフォルダーに `{source name}_schema.yml` という名前のファイルが存在する場合、そのファイルは自動的に読み込まれ、スキーマとして使用されます。

これにより、完全に指定された（または事前構成された）スキーマをソースにバンドルすることが容易になります。

### ソース関数本体でスキーマが変更される

たとえば、ソース資格情報とユーザー設定が利用可能な場合、スキーマ関数内でのみスキーマを構成したり、一部のテーブルを追加したりできるとしたらどうでしょうか。たとえば、誰かがテーブル データのロードを要求したときに、すべてのデータベース テーブルの詳細なスキーマを追加できます。この情報は、ソース関数が呼び出された瞬間にのみ利用できます。

`source_state()` および `resource_state()` と同様に、ソースおよびリソース関数には `dlt.current.source_schema()` を介して利用できる現在のスキーマがあります。

例:

```py
@dlt.source
def textual(nesting_level: int):
    # get the source schema from the `current` context
    schema = dlt.current.source_schema()
    # remove date detector
    schema.remove_type_detection("iso_timestamp")
    # convert UNIX timestamp (float, within a year from NOW) into timestamp
    schema.add_type_detection("timestamp")

    return dlt.resource([])
```

