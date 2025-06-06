---
title: Incremental loading
description: Introduction to incremental loading with dlt
keywords: [incremental loading, loading methods, append, merge]
---

# インクリメンタルローディング

インクリメンタルローディングとは、すでにロードされている古いレコードではなく、新しいデータまたは変更されたデータのみをロードする操作です。これにより、低レイテンシで低コストのデータ転送が可能になります。

インクリメンタルなパイプラインの課題は、ロードの状態 (つまり、どの増分がロードされたか、どの増分がロードされるか) を追跡しないと、問題が発生する可能性があることです。状態の詳細については、[こちら](state.md) を参照してください。

## 書き込み処理の選択

### ３つの書き込み処理:

- **Full load**: 宛先データセットを、この実行でソースが生成したものに置き換えます。これを実現するには、リソースで `write_disposition='replace'` を使用します。詳細については、[フルロードのドキュメント](./full-loading.md)を参照してください。

- **Append**: 新しいデータを宛先に追加します。`write_disposition='append'` を使用します。

- **Merge**: `merge_key` を使用して新しいデータを宛先にマージしたり、`primary_key` を使用して新しいデータを重複排除/アップサートしたりします。

### How to choose the right write disposition

<div style={{textAlign: 'center'}}>
![write disposition flowchart](https://storage.googleapis.com/dlt-blog-images/flowchart_for_scd2.png)
</div>

選択する「書き込み処理」は、データセットとその抽出方法によって異なります。

使用すべき「書き込み処理」を見つけるには、まず「データはステートフルかステートレスか」と自問する必要があります。ステートフル データの状態は変更される可能性があります (ユーザーのプロファイルなど)。ステートレス データは変更できません (ページ ビューなどの記録されたイベントなど)。

ステートレス データは更新する必要がないため、追加するだけで済みます。

ステートフル データの場合、2 番目の質問が来ます - ソースから増分的に抽出できますか? できる場合は、[ゆっくり変化するディメンション (タイプ 2)](./merge-loading.md#scd2-strategy) を使用する必要があります。これにより、時間の経過に伴うデータの変更の履歴レコードを維持できます。

そうでない場合は、データセット全体を置き換える必要があります。ただし、「昨日以降に追加または変更されたすべてのユーザー」のように、データを段階的に要求できる場合は、マージ書き込み処理を使用して既存のデータセットに変更を適用するだけで済みます。

## Incremental loading strategies

dlt provides several approaches to incremental loading:

1. [Merge strategies](./merge-loading.md#merge-strategies) - Choose between delete-insert, SCD2, and upsert approaches to incrementally update your data
2. [Cursor-based incremental loading](./incremental/cursor.md) - Track changes using a cursor field (like timestamp or ID)
3. [Lag / Attribution window](./incremental/lag.md) - Refresh data within a specific time window
4. [Advanced state management](./incremental/advanced-state.md) - Custom state tracking


## 完全なリフレッシュを行う

`merge` および `append` パイプラインの完全な更新を強制することができます:

1. `merge` の場合、宛先のデータは削除され、新しくロードされます。現在、完全更新中にデータの重複排除は行われません。
1. `dlt.sources.incremental` の場合、データは削除され、最初からロードされます。増分の状態は初期値にリセットされます。

例:

```py
p = dlt.pipeline(destination="bigquery", dataset_name="dataset_name")
# Do a full refresh
p.run(merge_source(), write_disposition="replace")
# Do a full refresh of just one table
p.run(merge_source().with_resources("merge_table"), write_disposition="replace")
# Run a normal merge
p.run(merge_source())
```

書き込み処理を `replace` に渡すと、パイプラインの実行中に `repo_events` 内のすべてのリソースの書き込み処理が変更されます。

## Next steps

- [Cursor-based incremental loading](./incremental/cursor.md) - Use timestamps or IDs to track changes
- [Advanced state management](./incremental/advanced-state.md) - Advanced techniques for state tracking
- [Walkthroughs: Add incremental configuration to SQL resources](../walkthroughs/add-incremental-configuration.md) - Step-by-step examples
- [Troubleshooting incremental loading](./incremental/troubleshooting.md) - Common issues and how to fix them
