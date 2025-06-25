
## スキーマ設定
スキーマの `settings` セクションでは、データからテーブルと列を推論する方法に影響するさまざまなグローバルルールを定義できます。

### テーブル除外フィルターとテーブル包含フィルター
テーブルに包含フィルターと除外フィルターを定義することはできますが、Pythonでソースデータを変換・フィルタリングする方がはるかに効果的です。現在の実装は奇妙でありながら、非常に強力です。つまり、正規表現を使って列やテーブル全体を除外し、その正規表現に正規化された値の系統を入力として指定できます。
Example
```yaml
event_user:
    columns: {}
    write_disposition: append
    filters:
      excludes:
      - re:^parse_data
      includes:
      - re:^parse_data__(intent|entities|message_id$|text$)
```

これにより、`event_user` テーブルの子テーブルと列のうち、`parse_data` で始まるものはすべて除外されますが、名前に `intent` と `entities` が含まれる子テーブル、および列名が `message_id` と `text` で終わるすべてのテーブルは含まれます。

⛔ 系統が実装されると、除外フィルターと包含フィルターがそれらでも機能するようになります。現時点では、これらのフィルターを使用しないことをお勧めします。

## スキーマファイルの操作
`dlt` は、スキーマのインポートフォルダとエクスポートフォルダを設定することで、スキーマファイルの操作を自動化します。設定は、構成プロバイダ (`config.toml` など) または `dlt.pipeline(import_schema_path, export_schema_path)` 設定から行えます。例:
```python
dlt.pipeline(import_schema_path="schemas/import", export_schema_path="schemas/export")
```
プロジェクトのルートフォルダに次のフォルダ構造を作成します
```
schemas
    |---import/
    |---export/
```

これにより、パイプラインのスキーマが `yml` 形式でユーザーに公開されます。

1. 新しいパイプラインが作成され、ソース関数が初めて抽出されると、新しいスキーマがパイプラインに追加されます。このスキーマは、ソース抽出関数に存在するグローバルヒントとリソースヒントから作成されます。**データに依存しません（これは正規化ステージで発生します）。**
2. 作成された新しいスキーマはすべて、`import` フォルダに保存され（まだ存在しない場合）、今後のすべてのパイプライン実行の初期バージョンとして使用されます。
3. スキーマが `import` フォルダに保存されると、**ユーザーのみが書き込み可能になります**。
4. そのフォルダ内のスキーマへの変更は検出され、次回の実行時にパイプラインに自動的に反映されます（実際には、`Pipeline` オブジェクトへの呼び出しごとに同期が行われます）。つまり、ユーザーが更新すると、`import` フォルダ内のスキーマによって、データからのすべての自動更新がリセットされます。
4. それ以外の場合、**スキーマは正規化段階で自動的に進化**し、各更新は`export`フォルダに保存されます。exportフォルダは**dltのみ書き込み可能**で、スキーマの実際のビューを提供します。
5. `export`フォルダと`import`フォルダは同じでも構いません。その場合、進化したスキーマは自動的に初期スキーマとして「承認」されます。


## コード内でのスキーマ操作
`dlt` ユーザーは、コード内で変更するために任意のパイプラインスキーマを「チェックアウト」できます。

> ⛔ コード内のテーブル、列、その他のヒントを操作するための便利な API はありません。スキーマは型付き辞書であり、現時点ではこれが唯一の方法です。

`dlt` は、`run`、`extract`、`normalize`、`load` メソッドの呼び出し時に、すべてのスキーマ変更を「コミット」します。

例:

```python
# extract some to "table" resource using default schema
p = dlt.pipeline(destination=redshift)
p.extract([1,2,3,4], name="table")
# get live schema
schema = p.default_schema
# we want the list data to be text, not integer
schema.tables["table"]["columns"]["value"] = schema_utils.new_column("value", "text")
# `run` will apply schema changes and run the normalizer and loader for already extracted data
p.run()
```

> `normalize` ステージでは、特定のバージョンのデータとスキーマを含むスタンドアロンのロードパッケージが作成されます。これらのパッケージは、もちろん「ライブ」スキーマの変更の影響を受けません。
