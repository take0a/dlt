---
title: Adjust a schema
description: How to adjust a schema
keywords: [how to, adjust a schema]
---

# スキーマの調整

パイプラインを[作成](create-a-pipeline.md)して[実行](run-a-pipeline.md)する際に、`dlt` によって生成された[スキーマ](../general-usage/schema.md)を手動で確認して変更する必要がある場合があります。
手順は次のとおりです。

## 1. 実行ごとにスキーマをエクスポートします。

`dlt.pipeline` に `export_schema_path` 引数を指定して、スキーマを保存するエクスポートフォルダを設定します。
`dlt` が変更内容を読み取るインポートフォルダを設定するには、`import_schema_path` 引数を指定します。

[パイプラインの実行](run-a-pipeline.md) の例に従って、以下の手順を実行します。

```py
dlt.pipeline(
    import_schema_path="schemas/import",
    export_schema_path="schemas/export",
    pipeline_name="chess_pipeline",
    destination='duckdb',
    dataset_name="games_data"
)
```

プロジェクト ルート フォルダーに次のフォルダー構造が作成されます。

```text
schemas
    |---import/
    |---export/
```

`dlt.pipeline` 関数でパスを指定する代わりに、`config.toml` ファイルの先頭でパスを設定することもできます。

```toml
export_schema_path="schemas/export"
import_schema_path="schemas/import"
```

## 2. パイプラインを実行してスキーマを確認します。

スキーマを確認するには、パイプラインを再度実行する必要があります。`schemas` ディレクトリと `import`/`export` ディレクトリが作成されます。
各ディレクトリには、YAML ファイル（例：`chess.schema.yaml`）があります。

エクスポート フォルダ内のエクスポート スキーマを確認します。これは、データから推論され、出力先（例：`duckdb`）にロードするために使用されたスキーマです。

## 3. インポートスキーマを変更する

次に、インポートフォルダ内のインポートスキーマを確認します。このスキーマには、`chess` ソースで明示的に宣言されたテーブル、列、ヒントのみが含まれています。
このスキーマを使用して変更を加えます。通常は、エクスポートスキーマから関連するスニペットを貼り付けて変更します。
インポートスキーマは可能な限りシンプルに保ち、残りの処理は `dlt` に任せましょう。

💡 スキーマのインポートの仕組み

1. 新しいパイプラインが作成され、ソース関数が初めて抽出されると、新しいスキーマがパイプラインに追加されます。
  このスキーマは、ソース抽出関数内のグローバルヒントとリソースヒントから作成されます。
2. 新しいスキーマはすべて、`import` フォルダに保存され（まだ存在しない場合）、今後のすべてのパイプライン実行の初期バージョンとして使用されます。
3. `import` フォルダにスキーマが追加されると、**ユーザーのみが書き込み可能** になります。
4. そのフォルダ内のスキーマへの変更は、次回の実行時に自動的に検出され、パイプラインに反映されます。
  つまり、ユーザーが更新すると、`import` フォルダ内のスキーマは、データからのすべての自動更新を元に戻します。

次の手順では、さまざまな実験を行います。実験が完了するまでは、`dev_mode=True` を設定するように警告されます。

:::caution
dlt は、テーブル作成後に既存の列を**変更しません**。新しい列を追加することはできますが、既存の列への変更（データ型の変更やヒントの追加など）は自動的には反映されません。

YAML スキーマファイルを変更する場合は、データセットを削除するか、`dev_mode=True` を有効にするか、Pipeline の [更新オプション](../general-usage/pipeline#refresh-pipeline-data-and-state) のいずれかを使用して変更を適用する必要があります。
```py
dlt.pipeline(
    import_schema_path="schemas/import",
    export_schema_path="schemas/export",
    pipeline_name="chess_pipeline",
    destination='duckdb',
    dataset_name="games_data",
    dev_mode=True,
)
```
:::

### データ型を変更する

エクスポートスキーマを見ると、`p​​layers_games` の `end_time` 列のデータ型が `text` になっているのがわかりますが、実際にはタイムスタンプであることが分かっています。これを変更して、正常に動作するか確認してみましょう。

列をコピーします:

```yaml
end_time:
  nullable: true
  data_type: text
```

エクスポートからインポートスキーマに変更し、データ型を変更します:

```yaml
players_games:
  columns:
    end_time:
      nullable: true
      data_type: timestamp
```

パイプラインスクリプトを再度実行し、エクスポートスキーマに変更が反映されていることを確認します。
次に、[Streamlitアプリを起動](../general-usage/dataset-access/streamlit)して、変更されたデータを確認します。

:::note
YAML ファイル内のテーブルや列の名前を変更しないでください。`dlt` はデータからそれらを推測するため、スキーマが再作成されます。
リソースがロードされる前に、Python で [スキーマを調整](../general-usage/resource.md#set-table-name-and-adjust-schema) できます。
:::

### 列の順序変更

データセット内の列の順序を変更するには、以下の手順に従います。

1. 初回実行: パイプラインを実行して、インポートスキーマとエクスポートスキーマを取得します。
1. エクスポートスキーマの変更: エクスポートスキーマの列の順序を必要に応じて調整します。
1. インポートスキーマの同期: 一貫性を保つために、これらの変更がインポートスキーマに反映されていることを確認します。
1. データセットの削除: 再ロードの準備として、既存のデータセットを削除します。
1. データの再ロード: データを再ロードします。これで、インポートYAMLで指定された新しい列の順序がデータセットに反映されるはずです。

これらの手順により、データセット内の列の順序が仕様と一致します。

**列の順序を変更する別の方法** は、`add_map` 関数を使用することです。たとえば、「column1」、「column2」、「column3」を並べ替えるには、次の手順に従います。

```py
# Define the data source and reorder columns using add_map
my_resource = resource().add_map(lambda row: {
    'column3': row['column3'],
    'column1': row['column1'],
    'column2': row['column2']
})

# Run the pipeline
load_info = pipeline.run(my_resource)
```

この例では、`add_map` 関数は新しいマッピングを定義して列の順序を変更します。
Lambda 関数は、キーと値のペアを並べ替えることで、目的の順序を指定します。
パイプラインが実行されると、列が新しい順序でデータが読み込まれます。

### フラット化された辞書からネストされたテーブルや列を生成する代わりに、JSON としてデータをロードします。

エクスポートスキーマでは、白と黒のプレイヤーのプロパティが次のようにフラット化されていることがわかります。

```yaml
white__rating:
  nullable: true
  data_type: bigint
white__result:
  nullable: true
  data_type: text
white__aid:
  nullable: true
  data_type: text
```

何らかの理由で、単一のJSON（または構造体）列を扱いたい場合、`white`列を`json`として宣言するだけで、`dlt`はそれをフラット化しない（リストの場合はネストされたテーブルに変換しない）ように指示します。`black`列についても同様にします。

```yaml
players_games:
  columns:
    end_time:
      nullable: true
      data_type: timestamp
    white:
      nullable: false
      data_type: json
    black:
      nullable: false
      data_type: json
```

パイプライン スクリプトを再度実行すると、JSON 式を使用して `black` 列と `white` 列をクエリできるようになります。

### パフォーマンスに関するヒントを追加する

ローカルでの実験が終了し、データを `duckdb` ではなく `BigQuery` にロードしたいとします。
クエリコストを削減するために、データをパーティション分割したいと考えています。
先ほど修正した `end_time` 列が適切な候補のようです。

```yaml
players_games:
  columns:
    end_time:
      nullable: false
      data_type: timestamp
      partition: true
    white:
      nullable: false
      data_type: json
    black:
      nullable: false
      data_type: json
```

## 4. インポートスキーマはそのままにしておいてください。

インポートフォルダをgitに追加してプッシュするだけです。クローン時に自動的に使用されます。
または、[インポートスキーマをソースにバンドル](../general-usage/schema.md#attaching-schemas-to-sources)することもできます。

