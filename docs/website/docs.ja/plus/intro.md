---
title: Introduction
description: Introduction to dlt+
---

import Link from '../_plus_admonition.md';

<Link/>

# dlt+ とは？

![dlt+](/img/slot-machine-gif.gif)

dlt+は、大規模な本番環境でdltパイプラインを実行するためのフレームワークです。これは、オープンソースのデータロードツール（dlt）の商用拡張です。dlt+の機能には以下が含まれます:

* [Project](../plus/features/projects.md): チームメンバーがソース、宛先、パイプラインを簡単に定義できる宣言型 YAML インターフェース。
* [Local transformations](../plus/features/transformations/index.md): ローカル キャッシュとスキーマの適用、デバッグ ツール、既存のデータ ワークフローとの統合を組み合わせた、データ変換用のステージング レイヤー。
* [Data quality & tests](../plus/features/quality/tests.md)
* [Iceberg support](../plus/ecosystem/iceberg.md)
* [Secure data access and sharing](../plus/features/data-access.md)
* [AI workflows](../plus/features/ai.md): データエンジニアリングチームを強化するエージェント。

dlt+ を使い始めるには、pip (Python 3.9-3.12) を使用してライブラリをインストールします:

```sh
pip install dlt-plus
```

:::caution
dlt+ を実行するにはライセンスが必要です。試用をご希望の場合は、[待機リスト](https://info.dlthub.com/waiting-list)にご登録ください。
:::

