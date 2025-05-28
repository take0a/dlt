---
title: Accessing loaded data
description: How to access your loaded datasets
keywords: [datasets, data, access]
---
import DocCardList from '@theme/DocCardList';

# ロードされたデータへのアクセス

パイプラインの実行が1回以上成功すると、ロードされたデータを様々な方法で確認したりアクセスしたりできます。

* シンプルな [`streamlit` アプリ](./streamlit.md) を使用すると、Web アプリでローカルにデータを表示できます。
* [Python インターフェース](./dataset.md) を使用すると、シンプルなデータセットオブジェクトまたは SQL インターフェースを使用して、Python タプル、`arrow` テーブル、または `pandas` データフレームとして Python でデータにアクセスできます。`DuckDB` を介してファイルシステムの宛先で SQL コマンドを実行したり、任意のテーブルから別のパイプラインにデータを転送したりすることもできます。
* [`ibis` インターフェース](./ibis-backend.md) を使用すると、ロードされたデータを強力な [ibis-framework](https://ibis-project.org/) ライブラリに渡すことができます。
* 最後に、[データの品質を監視し、確保するための](./data-quality-dashboard.md) アドバイスをいくつか紹介します。

# Learn more
<DocCardList />

