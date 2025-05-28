---
title: Transforming your data
description: How to transform your data
keywords: [datasets, data, access, transformations]
---
import DocCardList from '@theme/DocCardList';

# データの変換

パイプラインロード後にデータを変換する場合、以下の3つのオプションがあります。

* [dbt の使用](./dbt/dbt.md) - dlt は、統合を容易にする便利な dbt ラッパーを提供します。
* [`dlt` SQL クライアントの使用](./sql.md) - dlt は、SQL を使用して出力先のデータを直接変換するための SQL クライアントを公開します。
* [Python で DataFrame または Arrow テーブルを使用する](./python.md) - Python で Arrow テーブルと DataFrame を使用してデータを変換することもできます。

データをロードする前に前処理が必要な場合は、以下の戦略についてご確認ください。

* [列名を変更する](../../general-usage/customising-pipelines/renaming_columns)
* [列を仮名化する](../../general-usage/customising-pipelines/pseudonymizing_columns)
* [列を削除する](../../general-usage/customising-pipelines/removing_columns)

これは、PII（個人情報）やその他の機密データに関連するデータを削除する場合、ユースケースに不要な列を削除する場合、またはソースデータの特定のデータ型をサポートしていない出力先を使用する場合に特に役立ちます。


# Learn more
<DocCardList />

