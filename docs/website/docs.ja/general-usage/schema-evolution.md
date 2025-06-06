---
title: スキーマの進化
description: A small guide to elaborate on how schema evolution works
keywords: [schema evolution, schema, dlt schema]
---

## `dlt` によるスキーマの進化

`dlt` は、最初のパイプライン実行の初期スキーマを自動的に推測します。ただし、ほとんどの場合、スキーマは時間の経過とともに変化する傾向があるため、下流の消費者がスキーマの変更に適応することが重要になります。

新しい列の追加やデータ型の変更など、データの構造が変化すると、`dlt` はこれらのスキーマの変更を処理し、速度を落とさずに変更に適応できるようにします。

## ネストされたデータからスキーマを推測する

パイプラインの最初の実行では、パイプラインを通過するデータがスキャンされ、スキーマが生成されます。ネストされたデータをリレーショナル形式に変換するために、`dlt` は辞書をフラット化し、ネストされたリストをサブテーブルに展開します。

ここでいくつかの例を確認し、`dlt` がどのように初期スキーマを作成し、正規化がどのように機能するかを理解します。次のスキーマをロードするパイプラインを検討します:

```py
data = [{
    "organization": "Tech Innovations Inc.",
    "address": {
        'building': 'r&d',
        "room": 7890,
    },
    "Inventory": [
        {"name": "Plasma ray", "inventory nr": 2411},
        {"name": "Self-aware Roomba", "inventory nr": 268},
        {"name": "Type-inferrer", "inventory nr": 3621}
    ]
}]

# Run `dlt` pipeline
dlt.pipeline("organizations_pipeline", destination="duckdb").run(data, table_name="org")
```

上記のデータのスキーマは次のように宛先にロードされます:

<iframe width="560" height="315" src='https://dbdiagram.io/e/65e5c68bcd45b569fb7805e8/65e7ff92cd45b569fba253d9'> </iframe>

### スキーマ推論エンジンは何を実行しましたか?

上でご覧のとおり、DLT の推論エンジンは、ソースと提供されたヒントに基づいてデータの構造を生成します。データを正規化し、テーブルと列を作成し、データ型を推論します。

詳細については、ドキュメントの [スキーマ](./schema) および [スキーマの調整](../walkthroughs/adjust-a-schema) セクションを参照してください。

## スキーマの進化

一般的なデータ ソースの場合、スキーマは時間の経過とともに変化する傾向があり、dlt はこの変化するスキーマをシームレスに処理します。

次の4つのケースを追加してみましょう:

- 列が追加されました: 「CEO」という名前のフィールドが追加されました。
- 列の型が変更されました: 「inventory_nr」という列のデータ型が整数から文字列に変更されました。
- 列が削除されました: 「room」という名前のフィールドがコメントアウト/削除されました。
- 列の名前が変更されました: フィールド「building」の名前が「main_block」に変更されました。

上記のケースのパイプラインを更新してください。

```py
data = [{
    "organization": "Tech Innovations Inc.",
    # Column added:
    "CEO": "Alice Smith",
    "address": {
        # 'building' renamed to 'main_block'
        'main_block': 'r&d',
	      # Removed room column
        # "room": 7890,
    },
    "Inventory": [
        # Type change: 'inventory_nr' changed to string from int
        {"name": "Plasma ray", "inventory nr": "AR2411"},
        {"name": "Self-aware Roomba", "inventory nr": "AR268"},
        {"name": "Type-inferrer", "inventory nr": "AR3621"}
    ]
}]

# Run `dlt` pipeline
dlt.pipeline("organizations_pipeline", destination="duckdb").run(data, table_name="org")
```

データをロードしてテーブルを見てみましょう:

<iframe width="560" height="315" src='https://dbdiagram.io/e/65e80303cd45b569fba28e9d/65e80556cd45b569fba2b8ab'> </iframe>

何が起きたの？

- 追加された列:
    - 「org」テーブルに `ceo` という名前の新しい列が追加されます。
- バリアント列:
    - 列のデータ型が「整数」から「文字列」に変更されたため、`inventory_nr__v_text` という名前の新しい列が追加されました。
- 列を削除し、ロードを停止しました:
    - 列 `room` への新しいデータは読み込まれません。
- 列の読み込みが停止し、新しい列が追加されました:
    - 新しい列 `address__main_block` が追加され、データはそこにロードされ、列 `address__building` でのロードは停止します。

## 新しいデータをキュレートするためにスキーマの変更を警告する

データのロードの技術的プロセスをキュレーションから分離することで、データ エンジニアはエンジニアリングに専念でき、アナリティクスは技術的な障害なしにデータをキュレーションできるようになります。そのため、アナリストは常に最新情報を把握しておく必要があります。

**カラムの系統を追跡する**

列の系統は、「load_info」を宛先にロードすることで追跡できます。「load_info」には、列のデータ型、追加時刻、ロード ID に関する情報が含まれています。詳細については、ブログの [データ系統の記事](https://dlthub.com/blog/dlt-data-lineage) をご覧ください。

**通知を受け取る**

ロード結果を読み取り、dlt を使用して Slack Webhook に送信できます。

```py
# Import the send_slack_message function from the dlt library
from dlt.common.runtime.slack import send_slack_message

# Define the URL for your Slack webhook
hook = "https://hooks.slack.com/services/xxx/xxx/xxx"

# Iterate over each package in the load_info object
for package in load_info.load_packages:
    # Iterate over each table in the schema_update of the current package
    for table_name, table in package.schema_update.items():
        # Iterate over each column in the current table
        for column_name, column in table["columns"].items():
            # Send a message to the Slack channel with the table
						# and column update information
            send_slack_message(
                hook,
                message=(
                    f"\tTable updated: {table_name}: "
                    f"Column changed: {column_name}: "
                    f"{column['data_type']}"
                )
            )
```

このスクリプトは、`dlt` ライブラリの `send_slack_message` 関数を使用して、スキーマの更新に関する Slack 通知を送信します。更新されたテーブルと列の詳細を提供します。

## 進化を制御する方法

`dlt` は、スキーマとデータ コントラクトを介してスキーマ進化の制御を可能にします。詳細については、**[ドキュメント](./schema-contracts)** を参照してください。

### 削除された列をテストする方法 - 「not null」制約を適用する

列が存在しないということと、列が null であることは、2 つの異なることです。ただし、API と JSON に関しては、通常はすべて同じように扱われます。つまり、キーと値のペアは単に存在しないことになります。

列を削除するには、リソース関数の出力から除外します。後続のデータ挿入では、この列は null として扱われます。列の削除を確認するには、not null 制約を適用します。たとえば、「room」列を削除した後、not null 制約を適用して除外を確認します。

```py
data = [{
    "organization": "Tech Innovations Inc.",
    "address": {
        'building': 'r&d'
        #"room": 7890,
    },
    "Inventory": [
        {"name": "Plasma ray", "inventory nr": 2411},
        {"name": "Self-aware Roomba", "inventory nr": 268},
        {"name": "Type-inferrer", "inventory nr": 3621}
    ]
}]

pipeline = dlt.pipeline("organizations_pipeline", destination="duckdb")
# Adding not null constraint
pipeline.run(data, table_name="org", columns={"room": {"data_type": "bigint", "nullable": False}})
```

パイプラインの実行中に、データ検証エラーは、削除された列が null として渡されていることを示します。

## データのスキーマ変更

上記のパイプライン内のデータが変更されます。

```py
data = [{
    "organization": "Tech Innovations Inc.",
    "CEO": "Alice Smith",
    "address": {'main_block': 'r&d'},
    "Inventory": [
        {"name": "Plasma ray", "inventory nr": "AR2411"},
        {"name": "Self-aware Roomba", "inventory nr": "AR268"},
        {
            "name": "Type-inferrer", "inventory nr": "AR3621",
            "details": {
                "category": "Computing Devices",
                "id": 369,
                "specifications": [{
                    "processor": "Quantum Core",
                    "memory": "512PB"
                }]
            }
        }
    ]
}]

# Run `dlt` pipeline
dlt.pipeline("organizations_pipeline", destination="duckdb").run(data, table_name="org")
```

上記のデータのスキーマは次のように宛先にロードされます:

<iframe width="560" height="315" src='https://dbdiagram.io/e/65e80b31cd45b569fba33169/65e81055cd45b569fba3aa20'> </iframe>

## スキーマ進化エンジンは何ができますか？

`dlt`ライブラリのスキーマ進化エンジンは、時間の経過とともにデータの構造が変化するのを処理するように設計されています。たとえば:

- 上記の推論されたスキーマの続きとして、「specifications」は「details」にネストされ、さらに「details」は「Inventory」にネストされ、すべて「org」というテーブル名の下にあります。したがって、プロジェクト用に作成されたテーブルは `org__inventory__details__specifications` です。

これは、スキーマの進化がどのように機能するかを示す簡単な例です。

## スキーマとデータのコントラクトを使用したスキーマの進化

スキーマとデータのコントラクトについて説明せずにスキーマの進化を示すことは、物事の片面にすぎません。スキーマとデータのコントラクトは、宛先に書き込まれるスキーマがどのように進化するかという条件を規定します。

スキーマとデータ コントラクトは、コントラクト モード (「evolve」、「freeze」、「discard_rows」、「discard_columns」など) を使用して、「tables」、「columns」、「data_types」などのエンティティに適用でき、特定のエンティティにコントラクトを適用する方法を dlt に指示します。**スキーマとデータのコントラクト** の詳細については、[ドキュメント](./schema-contracts) をお読みください。

