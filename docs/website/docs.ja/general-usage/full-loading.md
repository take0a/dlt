---
title: Full loading
description: Full loading with dlt
keywords: [full loading, loading methods, replace]
---
# フルロード

フルロードとは、テーブルのデータを完全に再ロードする操作です。
既存のデータはすべて削除され、今回の実行でソースが生成したデータに置き換えられます。
フルロードの実行中に選択されていないリソースは、宛先のデータを置き換えません。

## フルロードの実行

1 つ以上のリソースに対してフルロードを実行するには、そのリソースに対して `write_disposition='replace'` を選択します:

```py
p = dlt.pipeline(destination="bigquery", dataset_name="github")
issues = []
reactions = ["%2B1", "-1", "smile", "tada", "thinking_face", "heart", "rocket", "eyes"]
for reaction in reactions:
    for page_no in range(1, 3):
      page = requests.get(f"https://api.github.com/repos/{REPO_NAME}/issues?state=all&sort=reactions-{reaction}&per_page=100&page={page_no}", headers=headers)
      print(f"Got page for {reaction} page {page_no}, requests left", page.headers["x-ratelimit-remaining"])
      issues.extend(page.json())
p.run(issues, write_disposition="replace", primary_key="id", table_name="issues")
```

## フルロードに適した置換戦略の選択

dlt は、テーブルへのフルロードを実行するために、`truncate-and-insert`、`insert-from-staging`、`staging-optimized` という 3 つの異なる戦略を実装しています。
これらの戦略の具体的な動作は、利用可能な保存先によって異なります。

`config.toml` ファイルの設定で戦略を選択できます。
戦略を選択しない場合、dlt はデフォルトで `truncate-and-insert` を使用します。

```toml
[destination]
# Set the optimized replace strategy
replace_strategy = "staging-optimized"
```

### `truncate-and-insert` 戦略

`truncate-and-insert` 置換戦略はデフォルトであり、3 つの戦略の中で最も高速です。
この設定でデータをロードすると、ロード開始時に宛先テーブルが切り捨てられ、新しいデータが連続して挿入されますが、同じトランザクション内ではありません。
この戦略の欠点は、ロードが完了するまでしばらくの間、テーブルにデータが存在しないことです。
ロード実行中にロードが失敗すると、一部のテーブルには新しいデータが追加され、他のテーブルにはデータがない状態になる可能性があります。
このような不完全なロードは、[_dlt_loads テーブル](destination-tables.md#load-packages-and-load-ids) で、置換されたテーブルの _dlt_load_id のロード ID が含まれているかどうかを確認することで検出できます。
データのダウンタイムを回避したい場合は、他の戦略のいずれかを使用してください。

### `insert-from-staging` 戦略

`insert-from-staging` 戦略は、3 つの戦略の中で最も低速です。
この戦略では、すべての新しいデータが最終的な宛先テーブルとは別のステージングテーブルにロードされ、その後、1 回のトランザクションで新しいデータの切り捨てと挿入が行われます。
また、ネストされたテーブルとルートテーブル間の一貫性が常に維持されます。
ダウンタイムなしで宛先データセットの一貫性が求められる場合で、`optimized` 戦略が適さない場合は、この戦略を使用してください。
この戦略は、すべての宛先で同じように動作します。

### `staging-optimized` 戦略

`staging-optimized` 戦略は `insert-from-staging` のすべての利点を備えていますが、一部の出力先で読み込みを高速化するために、特定の最適化を実装しています。
この戦略には、場合によっては出力先テーブルが削除され、再作成されるというデメリットがあります。つまり、これらのテーブルに設定したビューやその他の制約もテーブルとともに削除されます。
出力先テーブルを保持する必要がある設定の場合は、`staging-optimized` 戦略を使用しないでください。
テーブルの削除は問題にならないものの、`insert-from-staging` の利点とパフォーマンス（およびコスト）の削減が必要な場合は、この戦略を使用する必要があります。
`staging-optimized` 戦略は、出力先によって動作が異なります。

* Postgres: 新しいデータがステージングテーブルに読み込まれた後、出力先テーブルは削除され、ステージングテーブルに置き換えられます。データを移動する必要がないため、この戦略は `truncate-and-insert` とほぼ同程度の速度です。
* BigQuery: 新しいデータをステージングテーブルにロードした後、宛先テーブルは削除され、ステージングテーブルから [clone コマンド](https://cloud.google.com/bigquery/docs/table-clones-create) を使用して再作成されます。これは、別のテーブルのデータから独立した 2 番目のテーブルを低コストで高速に作成する方法です。詳しくは、[BigQuery でのテーブルのクローン作成](https://cloud.google.com/bigquery/docs/table-clones-intro) をご覧ください。
* Snowflake: 新しいデータをステージングテーブルにロードした後、宛先テーブルは削除され、ステージングテーブルから [clone コマンド](https://docs.snowflake.com/en/sql-reference/sql/create-clone) を使用して再作成されます。これは、別のテーブルのデータから独立した 2 番目のテーブルを低コストで高速に作成する方法です。 [Snowflakeでのテーブルクローン作成](https://docs.snowflake.com/en/user-guide/object-clone)の詳細については、こちらをご覧ください。

その他のすべての[destinations](../dlt-ecosystem/destinations/index.md)については、それぞれのドキュメントページを参照して、`staging-optimized`戦略が実装されているかどうか、またどのように実装されているかを確認してください。
実装されていない場合、`dlt`は`insert-from-staging`戦略にフォールバックします。

