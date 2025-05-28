---
title: 🧪 Schema and data contracts
description: Controlling schema evolution and validating data
keywords: [data contracts, schema, dlt schema, pydantic]
---

`dlt` は、抽出されたデータの構造とデータ型に従って、出力先のスキーマを進化させます。
この自動スキーマ進化を制御するために使用できるモードはいくつかあります。スキーマへのすべての変更が受け入れられるデフォルトモードから、まったく変更されない固定スキーマまであります。

次の例を考えてみましょう:

```py
@dlt.resource(schema_contract={"tables": "evolve", "columns": "freeze"})
def items():
    ...
```

このリソースを使用すると、新しいテーブル (ネストされたテーブルと [動的な名前を持つテーブル](resource.md#dispatch-data-to-many-tables) の両方) を作成できますが、新しい列を含む既存のテーブルのデータが抽出されると例外がスローされます。

### コントラクトの設定

以下の**スキーマエンティティ**を制御できます:
* `tables` - 新しいテーブルが作成されるときにコントラクトが適用されます。
* `columns` - 既存のテーブルに新しい列が作成されるときにコントラクトが適用されます。
* `data_type` - 既存の列に関連付けられたデータ型にデータを強制変換できない場合にコントラクトが適用されます。

**コントラクトモード** を使用して、`dlt` に特定のエンティティに対するコントラクトの適用方法を指定できます:
* `evolve`: スキーマ変更に制約はありません。
* `freeze`: 既存のスキーマに適合しないデータが見つかった場合に例外が発生し、出力先にデータがロードされません。
* `discard_row`: 抽出された行が既存のスキーマに準拠していない場合は破棄され、その行は出力先にロードされません。
* `discard_value`: 抽出された行のうち、既存のスキーマに準拠していないデータを破棄し、そのデータなしで行がロードされます。

:::note
デフォルトモード (**evolve**) は次のように動作します。
1. 新しいテーブルは常に作成できます。
2. 新しい列は常に既存のテーブルに追加できます。
3. 特定の列の既存のデータ型に強制変換されないデータは、この特定の型用に作成された [バリアント列](schema.md#variant-columns) に送信されます。
:::

#### schema_contract 引数の渡し方

`schema_contract` は、[dlt.source](source.md) デコレータに、そのソース内のすべてのリソースのデフォルトとして存在します。また、[dlt.resource](source.md) デコレータには、個々のリソースのディレクティブとして、そして結果として、このリソースによって作成されるすべてのテーブルに適用されます。
さらに、`pipeline.run()` メソッドにも存在し、既存のすべての設定をオーバーライドします。

`schema_contract` 引数には、次の 2 つの形式があります。
1. **full**: スキーマエンティティとコントラクトモードのマッピング
2. **shorthand**: すべてのスキーマエンティティに適用されるコントラクトモード (文字列)

例えば、`schema_contract` を *freeze* に設定すると、次の完全形式に展開されます:

```py
{"tables": "freeze", "columns": "freeze", "data_type": "freeze"}
```

`schema_contract` プロパティを介して、**ソース** インスタンスのコントラクトを変更できます。
**リソース** の場合は、[apply_hints](resource#set-table-name-and-adjust-schema) を使用できます。


#### コントラクトモードのニュアンス

1. コントラクトは、**テーブル名と列名が正規化された後**に適用されます。
2. リソースに定義されたコントラクトは、そのリソースによって作成されたすべてのルートテーブルとネストされたテーブルに適用されます。
3. `discard_row` はテーブルレベルで機能します。例えば、ネストされたリレーションシップにある2つのテーブル、つまり *users* と *users__addresses* があり、*users__addresses* テーブルでコントラクト違反が発生した場合、そのテーブルの行は破棄され、*users* テーブルの親行がロードされます。

### Pydantic モデルを使用したデータ検証

Pydantic モデルは、[テーブルスキーマの定義と入力データの検証](resource.md#define-a-schema-with-pydantic) に使用できます。既存のモデルを自由に使用できます。
`dlt` は、必要に応じて、リソースの **スキーマコントラクト** に準拠した新しいモデルを内部的に合成します。

[dlt.resource](resource.md#define-a-schema-with-pydantic) の `column` 引数にモデルを渡すだけで、Pydantic のデフォルトの動作に準拠したスキーマコントラクトが設定されます。

```py
{
  "tables": "evolve",
  "columns": "discard_value",
  "data_type": "freeze"
}
```

新しいテーブルは許可され、追加フィールドは無視され、無効なデータは例外を発生させます。

スキーマコントラクトを明示的に渡すと、スキーマエンティティに対して以下の処理が行われます。
1. **tables** は Pydantic モデルに影響を与えません。
2. **columns** モードは Pydantic の **extra** モードにマッピングされます (下記参照)。`dlt` は、モデルに他のモデルが含まれている場合、この設定を再帰的に適用します。
3. **data_type** は Pydantic に対して以下のモードをサポートします。**evolve** は、あらゆるデータ型に対応する柔軟なモデルを合成します。
これにより、上流にバリアント列が発生する可能性があります。
**freeze** は `ValidationException` を再度発生させます。**discard_row** は、検証対象外のデータ項目を削除します。
**discard_value** は現在サポートされていません。Pydantic v2 で将来サポートされる可能性があります。

`dlt` は、列コントラクトモードを以下のように追加フィールド設定にマッピングします。

これは双方向に機能することに注意してください。
このような設定が明示的に構成されたモデルを使用する場合、`dlt` はそれに応じて列コントラクトモードを設定します。
これにより、変更されたモデルの合成も回避されます。

| column mode   | pydantic extra |
| ------------- | -------------- |
| evolve        | allow          |
| freeze        | forbid         |
| discard_value | ignore         |
| discard_row   | forbid         |

`discard_row` では、ValidationError が発生した場合に追加の処理が必要です。

:::tip
モデル検証は、リソースに[変換ステップ](resource.md#filter-transform-and-pivot-data)として追加されます。
このステップでは、入力データ項目を検証モデルのインスタンスに変換します。
リソースに対して `add_map(lambda item: item.dict())` を使用することで、簡単に辞書に戻すことができます。
:::

:::note
Pydantic モデルは、**名前が正規化される前、またはネストされたテーブルが作成される前の** **抽出された** データに対して動作します。
モデルフィールドには入力データと同じ名前を付け、ネストされたデータはネストされたモデルで処理するようにしてください。

結果として、ネストされたモデルが影響を受けた場合でも、`discard_row` はデータ項目全体を削除します。
:::

### Arrow テーブルと Pandas のコントラクト設定

すべてのコントラクト設定は [Arrow テーブルと Pandas フレーム](../dlt-ecosystem/verified-sources/arrow-pandas.md) にも適用されます。
1. **tables** モードは、データ項目の種類に関係なく同じです。
2. **columns** モードでは、新しい列の追加が許可されるか、例外が発生するか、抽出ステップ中のテーブル/フレームが変更され、Parquet ファイルの書き換えが回避されます。
3. **data_type** モードでは、テーブル/フレーム内のデータ型の変更は許可されておらず、データ型スキーマの衝突が発生します。
さらに多くのモードに対応できます（Arrow テーブルでデータ型を進化させるのは奇妙に聞こえるかもしれませんが、必要な場合は Slack でご連絡ください）。

`dlt` が列モードを処理する方法は次のとおりです。
1. **evolve** ：新しい列が許可されます（テーブルの順序が変更され、列が最後に配置される場合があります）。
2. **discard_value** ：列が削除されます。
3. **discard_row** ：列が存在する行が削除され、その後列が削除されます。
4. **freeze** ：新しい列で例外が発生します。

### フリーズモードで DataValidationError からコンテキストを取得する

フリーズモードでコントラクト違反が発生すると、`dlt` は `DataValidationError` 例外を発生させます。
この例外は完全なコンテキストへのアクセスを提供し、その証拠を呼び出し元に渡します。
パイプライン実行から発生する他の例外と同様に、`PipelineStepFailed` 例外によって再度発生し、except ブロックでキャッチする必要があります。

```py
try:
  pipeline.run()
except PipelineStepFailed as pip_ex:
  if pip_ex.step == "normalize":
    if isinstance(pip_ex.__context__.__context__, DataValidationError):
      ...
  if pip_ex.step == "extract":
    if isinstance(pip_ex.__context__, DataValidationError):
      ...
```

`DataValidationError` は以下のコンテキストを提供します。
1. `schema_name`、`table_name`、`column_name` は、コントラクト違反が発生した論理的な「位置」を示します。
2. `schema_entity` と `contract_mode` は、違反が発生したコントラクトを示します。
3. `table_schema` には、コントラクトの検証に使用されたスキーマが含まれます。これは、Pydantic モデルまたは dlt `TTableSchema` インスタンスのいずれかです。
4. `schema_contract` は、完全な展開済みスキーマ コントラクトです。
5. `data_item` は、原因となったデータ項目です（Python 辞書、アローテーブル、Pydantic モデル、またはそれらのリスト）。

### 新しいテーブルにおけるコントラクト

テーブルが宛先にまだ作成されていない**新しいテーブル**である場合、DLTは新しい列の作成を許可します。パイプラインを1回実行すると、列モードは（内部的に）**evolve**に変更され、その後元のモードに戻ります。これにより、最初のスキーマ推論が行われ、その後の実行では、推論されたコントラクトが新しいデータに適用されます。

以下のテーブルは新規テーブルとみなされます。
1. ネストされたデータから推論された子テーブル。
2. 抽出中にデータから作成された動的テーブル。
3. **不完全な**列（データ型がバインドされていない列）を含むテーブル。

たとえば、次のようなテーブルは、列 **number** が不完全 (主キーとして定義され、NULL ではないがデータ型がない) であるため、新規であるとみなされます:

```yaml
blocks:
  description: Ethereum blocks
  write_disposition: append
  columns:
    number:
      nullable: false
      primary_key: true
      name: number
```

新規とみなされないテーブル:
1. Pydantic モデルによって定義された列を持つテーブル。

### 初回ロード時に手動でテーブルと列を追加したデータセットの操作

場合によっては、dlt の外部で作成されたテーブルまたは列を含むデータセットを操作することがあります。dlt によって作成されていないテーブルに初めてロードする場合、dlt はスキーマ規約を適用する際にこのテーブルを認識しません。つまり、`tables` を `evolve` に設定してロードを実行すると、すべて計画どおりに動作します。`tables` を `freeze` に設定している場合、dlt は新しいテーブルを作成していると認識するため（dlt の観点からは新しいテーブルを作成していると認識されるため）、例外が発生します。1 回のロードで `evolve` を許可し、その後 `freeze` に戻すことができます。

`dlt` がテーブルを認識しているものの、ロード先に手動で列を追加し、`columns` を `freeze` に設定している場合も、同じことが起こります。

### コード例

以下のコードは、新しいサブテーブルを暗黙的に無視し、既存のテーブルへの新しい列の追加を許可し、列のバリアントが検出された場合にエラーを発生させます。

```py
@dlt.resource(schema_contract={"tables": "discard_row", "columns": "evolve", "data_type": "freeze"})
def items():
    ...
```

以下のコードは、スキーマ変更が発生するたびにエラーを発生させます。注: すべてのキーがこれらの値に設定されているかのように解釈される文字列をいつでも設定できます。

```py
pipeline.run(my_source, schema_contract="freeze")
```

以下のコードは、ソース上で上書き可能な設定を定義しています。これらの設定はリソース上で上書き可能で、さらに `run` メソッドのグローバルオーバーライドによって上書き可能です。
ここでは、すべてのリソースにおいてバリアント列が固定され、検出された場合はエラーが発生します。
`items` では新しい列が許可されますが、`other_items` はソースから `freeze` 設定を継承するため、そこで新しい列が固定されます。新しいテーブルは許可されます。

```py
@dlt.resource(schema_contract={"columns": "evolve"})
def items():
    ...

@dlt.resource()
def other_items():
    ...

@dlt.source(schema_contract={"columns": "freeze", "data_type": "freeze"})
def frozen_source():
  return [items(), other_items()]


# this will use the settings defined by the decorators
pipeline.run(frozen_source())

# this will freeze the whole schema, regardless of the decorator settings
pipeline.run(frozen_source(), schema_contract="freeze")

```

