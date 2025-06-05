---
title: Destination tables
description: Understanding the tables created in the destination database
keywords: [destination tables, loaded data, data structure, schema, table, nested table, load package, load id, lineage, staging dataset, versioned dataset]
---

# 宛先テーブル

[パイプライン](pipeline.md)を実行すると、DLTは宛先データベースにテーブルを作成し、[ソース](source.md)からこれらのテーブルにデータをロードします。
このセクションでは、宛先テーブルがどのように見えるか、そしてどのように構成されているかを詳しく見ていきます。

まず、シンプルなDLTパイプラインから始めます。

```py
import dlt

data = [
    {'id': 1, 'name': 'Alice'},
    {'id': 2, 'name': 'Bob'}
]

pipeline = dlt.pipeline(
    pipeline_name='quick_start',
    destination='duckdb',
    dataset_name='mydata'
)
load_info = pipeline.run(data, table_name="users")
```

:::note

ここでは、インメモリデータベースである[DuckDb destination](../dlt-ecosystem/destinations/duckdb.md)を使用しています。他のデータベースの destination も同様の動作をし、同様の概念を持ちます。

:::

このパイプラインを実行すると、宛先データベース（DuckDB）にデータベーススキーマと「users」という名前のテーブルが作成されます。
ヒント：宛先データベースのテーブルを確認するには、`dlt pipeline` CLI の `show` コマンドを使用できます（../general-usage/dataset-access/streamlit）。

## データベーススキーマ

データベーススキーマは、データベースにロードしたデータを表すテーブルの集合です。
スキーマ名は、パイプライン定義で指定した「dataset_name」と同じです。
上記の例では、「dataset_name」を明示的に「mydata」に設定しています。
設定しない場合は、パイプライン名にサフィックス「_dataset」が付加された名前が設定されます。

このセクションで参照されているスキーマは、[dltスキーマ](schema.md)とは異なることに注意してください。
データベーススキーマは、テーブル定義やリレーションシップなど、データベース内のデータの構造と構成に関係します。
一方、「dltスキーマ」は、dltパイプライン内の正規化されたデータの形式と構造を具体的に指します。

## テーブル

パイプライン定義内の各 [リソース](resource.md) は、出力先にあるテーブルで表されます。

上記の例では、リソースが 1 つ (`users`) なので、出力先にはテーブルが 1 つ (`mydata.users`) あります。
ここで、`mydata` はスキーマ名、`users` はテーブル名です。
ここでも、`table_name` を明示的に `users` に設定しています。
`table_name` が設定されていない場合、テーブル名はリソース名に設定されます。

例えば、上記のパイプラインを次のように書き換えることができます。

```py
@dlt.resource
def users():
    yield [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]

pipeline = dlt.pipeline(
    pipeline_name='quick_start',
    destination='duckdb',
    dataset_name='mydata'
)
load_info = pipeline.run(users)
```

結果は同じになります。`table_name="users"` を `pipeline.run` に明示的に渡さず、リソース名に基づいてテーブルに暗黙的に `users` という名前が付けられることに注意してください (例: `users()` に `@dlt.resource` が付加されます)。

:::note

パイプラインの状態を追跡するために、特別なテーブルが作成されます。
これらのテーブルには「_dlt_」というプレフィックスが付いており、「dlt pipeline」CLIの「show」コマンドでは表示されません。ただし、データベースに直接接続すると表示されます。

:::

## ネストされたテーブル

では、より複雑な例を見てみましょう:

```py
import dlt

data = [
    {
        'id': 1,
        'name': 'Alice',
        'pets': [
            {'id': 1, 'name': 'Fluffy', 'type': 'cat'},
            {'id': 2, 'name': 'Spot', 'type': 'dog'}
        ]
    },
    {
        'id': 2,
        'name': 'Bob',
        'pets': [
            {'id': 3, 'name': 'Fido', 'type': 'dog'}
        ]
    }
]

pipeline = dlt.pipeline(
    pipeline_name='quick_start',
    destination='duckdb',
    dataset_name='mydata'
)
load_info = pipeline.run(data, table_name="users")
```

このパイプラインを実行すると、出力先に `users` (**ルートテーブル**) と `users__pets` (**ネストテーブル**) の 2 つのテーブルが作成されます。
`users` テーブルには最上位レベルのデータが含まれ、`users__pets` テーブルには Python リストにネストされたデータが含まれます。
テーブルは次のようになります:

**mydata.users**

| id | name | _dlt_id | _dlt_load_id |
| --- | --- | --- | --- |
| 1 | Alice | wX3f5vn801W16A | 1234562350.98417 |
| 2 | Bob | rX8ybgTeEmAmmA | 1234562350.98417 |

**mydata.users__pets**

| id | name | type | _dlt_id | _dlt_parent_id | _dlt_list_idx |
| --- | --- | --- | --- | --- | --- |
| 1 | Fluffy | cat | w1n0PEDzuP3grw | wX3f5vn801W16A | 0 |
| 2 | Spot | dog | 9uxh36VU9lqKpw | wX3f5vn801W16A | 1 |
| 3 | Fido | dog | pe3FVtCWz8VuNA | rX8ybgTeEmAmmA | 0 |

データベーススキーマを推論する際、dlt は Python オブジェクト（つまり、解析済みの JSON ファイル）の構造をネストされたテーブルにマッピングし、それらの間の参照を作成します。

動作は次のとおりです。

1. dlt によって作成されたすべてのデータテーブル（ルートおよびネストされた）の各行には、`_dlt_id` という一意の列（**行キー**）が含まれます。
2. 各ネストされたテーブルには、親テーブル（**親キー**）の特定の行（`_dlt_id`）を参照する `_dlt_parent_id` という列が含まれます。
3. ネストされたテーブルの行は Python リストから取得されます。`dlt` はリスト内の各項目の位置を `_dlt_list_idx` に格納します。
4. `merge` 書き込み処理でロードされたネストされたテーブルには、子テーブルからルートテーブルの行を参照する `_dlt_root_id` という**ルートキー**列を追加します。

[ネストされた参照、行キー、親キーの詳細](schema.md#nested-references-root-and-nested-tables)

## 命名規則：テーブルと列

パイプライン実行中、dlt はテーブル名と列名の両方を正規化し（schema.md#naming-convention）、宛先データベースで許容される形式との互換性を確保します。
ソースデータの名前はすべてスネークケースに変換され、英数字のみで構成されます。
宛先データベースの名前は、元の入力と多少異なる場合がありますのでご注意ください。

### バリアント列

データの型が一致しない場合、`dlt` はデータを複数の **バリアント列** に振り分けます。
例えば、`answer` というフィールドを持つリソース（JSON ファイルなど）があり、データにブール値が含まれている場合、出力先には `BOOLEAN` 型の `answer` という列が作成されます。
何らかの理由で、次回のロード時に `answer` に整数値と文字列値が含まれる場合、不一致なデータはそれぞれ `answer__v_bigint` 列と `answer__v_text` 列に振り分けられます。
バリアント列の一般的な命名規則は `<original name>__v_<type>` です。ここで、`original_name` は既存の列名（データ型が衝突する列）、`type` はバリアントに格納されているデータ型の名前です。

## ロードパッケージとロードID

パイプラインを実行するたびに、1つ以上のロードパッケージが生成されます。
ロードパッケージには通常、特定の[ソース](glossary.md#source)のすべての[リソース](glossary.md#resource)から取得されたデータが含まれます。
これらのパッケージは、`load_id` によって一意に識別されます。特定のパッケージの`load_id`は、上位のデータテーブル（上記の例では `_dlt_load_id` 列）と、特別な`_dlt_loads`テーブルに追加され、ステータスは 0 になります（ロードプロセスが完全に完了した場合）。

これを説明するために、同じ宛先にさらにデータをロードしてみましょう。

```py
data = [
    {
        'id': 3,
        'name': 'Charlie',
        'pets': []
    },
]
```

パイプライン定義の残りの部分は変更ありません。
このパイプラインを実行すると、新しい `load_id` を持つ新しいロードパッケージが作成され、既存のテーブルにデータが追加されます。
`users` テーブルは次のようになります:

**mydata.users**

| id | name | _dlt_id | _dlt_load_id |
| --- | --- | --- | --- |
| 1 | Alice | wX3f5vn801W16A | 1234562350.98417 |
| 2 | Bob | rX8ybgTeEmAmmA | 1234562350.98417 |
| 3 | Charlie | h8lehZEvT3fASQ | **1234563456.12345** |

`_dlt_loads` テーブルは次のようになります:

**mydata._dlt_loads**

| load_id | schema_name | status | inserted_at | schema_version_hash |
| --- | --- | --- | --- | --- |
| 1234562350.98417 | quick_start | 0 | 2023-09-12 16:45:51.17865+00 | aOEb...Qekd/58= |
| **1234563456.12345** | quick_start | 0 | 2023-09-12 16:46:03.10662+00 | aOEb...Qekd/58= |

`_dlt_loads` テーブルは、完了したロードを追跡し、それらに基づいて連鎖変換を可能にします。
多くの出力先は、分散トランザクションや長時間実行トランザクションをサポートしていません (例: Amazon Redshift)。
その場合、ユーザーには部分的にロードされたデータが表示される可能性があります。
このようなデータはフィルタリング可能です。`_dlt_loads` に存在しない `load_id` を持つ行は、まだ完了していません。
同じ手順を使用して、完了していないパッケージのデータを特定して削除できます。

各ロードについて、テストを行い、異常 (例: データなし、テーブルへのロード量が多すぎるなど) が発生した場合に [アラート](../running-in-production/alerting.md) を生成できます。
前述の [Streamlit アプリ](../general-usage/dataset-access/streamlit) の `Load info` タブには、役立つロード統計情報もいくつかあります。

[変換](../dlt-ecosystem/transformations/)を追加し、`status`列を使用してそれらを連結することができます。
特定の`load_id`を持つすべてのデータに対して、ステータスが0の変換を開始し、その後ステータスを1に更新します。
次の変換はステータス1から開始され、その後ステータス2に更新されます。
これは、追加の変換ごとに繰り返すことができます。

### データリネージ

データリネージは、[データボールトアーキテクチャ](https://www.data-vault.co.uk/what-is-data-vault/)のようなアーキテクチャや、トラブルシューティングにおいて非常に重要です。
データボールトアーキテクチャは、大規模な組織が複数のシステムにまたがる同じプロセスを表現する際に使用するデータウェアハウスであり、データリネージの要件が追加されます。
`dlt` によってすぐに提供されるパイプライン名と `load_id` を使用することで、データのソースと時刻を特定できます。

特定の `load_id` について、ロードされたファイルのリスト、エラーメッセージ（ある場合）、経過時間、スキーマの変更など、完全なリネージ情報を[保存](../running-in-production/running.md#inspect-and-save-the-load-info-and-trace)できます。
これは、たとえば問題のトラブルシューティングに役立ちます。

## ステージングデータセット

これまで、サンプルパイプラインでは `append` 書き込み処理を使用してきました。
これは、パイプラインを実行するたびに、データが既存のテーブルに追加されることを意味します。
[merge 書き込み処理](incremental-loading.md) を使用すると、dlt はステージングデータ用のステージングデータベーススキーマを作成します。
このスキーマは [デフォルトで](../dlt-ecosystem/staging#staging-dataset) `<dataset_name>_staging` という名前で、宛先スキーマと同じテーブルが含まれています。
パイプラインを実行すると、ステージングテーブルのデータが単一のアトミックトランザクションで宛先テーブルにロードされます。

例を挙げて説明しましょう。
パイプラインを変更して、`merge` 書き込み処理を使用するようにします。

```py
import dlt

@dlt.resource(primary_key="id", write_disposition="merge")
def users():
    yield [
        {'id': 1, 'name': 'Alice 2'},
        {'id': 2, 'name': 'Bob 2'}
    ]

pipeline = dlt.pipeline(
    pipeline_name='quick_start',
    destination='duckdb',
    dataset_name='mydata'
)

load_info = pipeline.run(users)
```

このパイプラインを実行すると、宛先データベースに「mydata_staging」という名前のスキーマが作成されます。
このスキーマ内のテーブルを調べると、「mydata_staging.users」テーブルが、前の例の「mydata.users」テーブルと同一であることがわかります。

パイプライン実行後のテーブルは次のようになります。

**mydata_staging.users**

| id | name | _dlt_id | _dlt_load_id |
| --- | --- | --- | --- |
| 1 | Alice 2 | wX3f5vn801W16A | 2345672350.98417 |
| 2 | Bob 2 | rX8ybgTeEmAmmA | 2345672350.98417 |

**mydata.users**

| id | name | _dlt_id | _dlt_load_id |
| --- | --- | --- | --- |
| 1 | Alice 2 | wX3f5vn801W16A | 2345672350.98417 |
| 2 | Bob 2 | rX8ybgTeEmAmmA | 2345672350.98417 |
| 3 | Charlie | h8lehZEvT3fASQ | 1234563456.12345 |

`mydata.users` テーブルには、前回のパイプライン実行と現在のパイプライン実行の両方のデータが含まれていることに注意してください。

## 開発モード（バージョン管理）データセット

`dlt.pipeline` 呼び出しで `dev_mode` 引数を `True` に設定すると、dlt はバージョン管理されたデータセットを作成します。
つまり、パイプラインを実行するたびに、データは新しいデータセット（新しいデータベーススキーマ）にロードされます。
データセット名は、パイプライン定義で指定した `dataset_name` に日時ベースのサフィックスが付いたものになります。

`dev_mode` オプションを使用するようにパイプラインを変更し、その動作を確認します。

```py
import dlt

data = [
    {'id': 1, 'name': 'Alice'},
    {'id': 2, 'name': 'Bob'}
]

pipeline = dlt.pipeline(
    pipeline_name='quick_start',
    destination='duckdb',
    dataset_name='mydata',
    dev_mode=True # <-- add this line
)
load_info = pipeline.run(data, table_name="users")
```

このパイプラインを実行するたびに、宛先データベースに日付時刻ベースのサフィックスを持つ新しいスキーマが作成されます。
データはこのスキーマのテーブルにロードされます。
たとえば、パイプラインを初めて実行したとき、スキーマの名前は「mydata_20230912064403」になり、2回目には「mydata_20230912064407」になります。

## dlt によって作成されていない既存のテーブルへのデータのロード

`dlt` から、出力先データセットに既に存在するが `dlt` によって作成されていないテーブルにデータをロードすることもできます。
この操作を行う際には、いくつか留意すべき点があります。

存在するもののデータが含まれないテーブルにデータをロードする場合、ほとんどの場合、ロードは問題なく成功します。
`dlt` は必要な列を作成し、入力データを挿入します。
`dlt` は、検出または提供された内部スキーマに存在する列のみを認識します。そのため、出力先に `dlt` が予期しない列がある場合、それらの列は出力先に残りますが、`dlt` には認識されません。これは通常、問題にはなりません。

宛先テーブルが既に存在し、`dlt` によって検出された列と同じ名前を持つもののデータ型が一致しない列が含まれている場合、ロードは失敗します。そのため、まず宛先テーブルの列を修正するか、入力データの列名を別の名前に変更して衝突を回避する必要があります。

宛先テーブルが存在し、既にデータが含まれている場合も、`dlt` は必須メタデータを含む特別な `non-nullable` 列を作成するため、ロードは最初は失敗する可能性があります。
一部のデータベースでは、既存の行のこれらの列の初期値を推測できないため、データが存在するテーブルに `non-nullable` 列を作成できません。
既存のテーブルに適切な型の列を手動で作成し、それらを `nullable` に設定してから、既存の行に値を入力する必要があります。
一部のデータベースでは、同じコマンドで `non-nullable` の新しい列を作成し、既存の行のデフォルト値を取得できます。
作成する必要がある列は次のとおりです。

| name | type |
| --- | --- |
| _dlt_load_id | text/string/varchar |
| _dlt_id | text/string/varchar |

For nested tables, you may also need to create:

| name | type |
| --- | --- |
| _dlt_parent_id | text/string/varchar |
| _dlt_root_id | text/string/varchar |

