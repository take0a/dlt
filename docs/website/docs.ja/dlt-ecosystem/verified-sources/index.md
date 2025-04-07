---
title: Sources
description: Available sources
keywords: ['source']
---
import Link from '../../_book-onboarding-call.md';
import {useCurrentSidebarCategory} from '@docusaurus/theme-common';
import DocCardList from '@theme/DocCardList';

`dlt` を本番環境で使用する予定で、リストに載っていないソースが必要ですか? 喜んで構築をお手伝いします: <Link/>.

### コアソース

<DocCardList items={useCurrentSidebarCategory().items.filter(
item => item.label === '30+ SQL Databases' || item.label === 'REST APIs' || item.label === 'Cloud storage and filesystem'
)} />

### 検証済みのソース

`dlt` チームとコミュニティによって開発および保守されている検証済みのソースのコレクションから選択してください。各ソースは実際の API に対して厳密にテストされており、簡単にカスタマイズできるように Python コードとして提供されています。

:::tip
ソース実装が見つからない場合は、簡単に独自に作成できます。方法については、[リソース ページ](../../general-usage/resource) をご覧ください。
:::

<DocCardList items={useCurrentSidebarCategory().items.filter(
item => item.label !== '30+ SQL Databases' && item.label !== 'REST APIs' && item.label !== 'Cloud storage and filesystem'
)} />

### コアソースと検証済みソースの違いは何ですか?

[コアソース](#core-sources) と [検証済みソース](#verified-sources) の主な違いは、その構造にあります。
コアソースは汎用コレクションであるため、さまざまなシステムに接続できます。たとえば、[SQL データベース ソース](sql_database) は、SQLAlchemy をサポートする任意のデータベースに接続できます。

テレメトリによると、コアソースはユーザーの間で最も広く使用されています。

また、コア ソースは `dlt` コア ライブラリに統合されているのに対し、検証済みソースは別の [リポジトリ](https://github.com/dlt-hub/verified-sources) で管理されていることにも注意してください。
検証済みソースを使用するには、`dlt` init コマンドを実行して、検証済みソース コードを作業ディレクトリにダウンロードする必要があります。


### Get help

* ソースが見つかりませんか? [新しい検証済みソースをリクエストしてください。](https://github.com/dlt-hub/verified-sources/issues/new?template=source-request.md)
* エンドポイントまたは機能が不足していますか? [リクエストまたは貢献](https://github.com/dlt-hub/verified-sources/issues/new?template=extend-a-source.md)
* [Slack コミュニティに参加](https://dlthub.com/community)して、技術ヘルプチャネルで質問してください。
