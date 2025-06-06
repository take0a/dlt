---
title: "Local transformations"
description: Run local transformations with dlt+ Cache
keywords: ["dlt+", "transformations", "cache", "dbt"]
---
import DocCardList from '@theme/DocCardList';

dlt+ の一部として、ローカル変換 [cache](../../core-concepts/cache.md) を提供しています。これは、データ変換のためのステージングレイヤーであり、ウェアハウス内ですべてのデータを実行することなく、データパイプラインのテスト、検証、デバッグを行うことができます。ローカル変換を使用すると、次のことが可能になります。

* 変換をローカルで実行することで、ウェアハウスクエリを待つ必要がなくなります。
* ロード前にスキーマを検証し、不一致を早期に検出できます。
* インメモリ実行によりコンピューティングの無駄が防止されるため、クラウドコストを発生させずにテストできます。

ローカル変換は DuckDB、Arrow、dbt 上に構築されているため、既存のスタックで動作します。

:::caution
ローカル変換機能は現在、早期アクセス段階です。
本番環境でご利用いただく前に、一般アクセスが開始されるまでお待ちいただくことをお勧めします。
:::

<DocCardList />

