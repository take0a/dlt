---
title: Add a verified source
description: How to create a pipeline from a verified source
keywords: [how to, add a verified source]
---

# 検証済みのソースを追加する

以下の手順に従って、`dlt` ユーザーが提供した[検証済みソース](../general-usage/glossary.md#verified-source)から[パイプライン](../general-usage/glossary.md#pipeline)を作成します。

以下の手順を実行する前に、[`dlt`](../reference/installation.md) がインストールされていることを確認してください。

## 1. プロジェクトの初期化

`dlt`プロジェクト用の新しい空のディレクトリを作成するには、次のコマンドを実行します:

```sh
mkdir various_pipelines
cd various_pipelines
```

利用可能なソースを一覧表示して、名前と説明を表示します:

```sh
dlt init --list-sources
```

ここで、ソース名（例：`pipedrive`）と宛先（例：`bigquery`）のいずれかを選択します:

```sh
dlt init pipedrive bigquery
```

このコマンドは、`pipedrive`フォルダをコピーして`.dlt`フォルダを作成し、パイプラインプロジェクトを作成します:

```text
├── .dlt
│   ├── config.toml
│   └── secrets.toml
├── pipedrive
│   └── helpers
│   └── __init__.py
│   └── settings.py
│   └── typing.py
├── .gitignore
├── pipedrive_pipeline.py
└── requirements.txt
```

コマンドを実行した後、依存関係をインストールする方法についてはコマンド出力を読んでください:

```text
Verified source pipedrive was added to your project!
* See the usage examples and code snippets to copy from pipedrive_pipeline.py
* Add credentials for bigquery and other secrets in .dlt/secrets.toml
* Add the required dependencies to pyproject.toml:
  dlt[bigquery]>=0.3.1
  If the dlt dependency is already added, make sure you install the extra for bigquery to it
  If you are using poetry you may issue the following command:
  poetry add dlt -E bigquery

* Read https://dlthub.com/docs/walkthroughs/create-a-pipeline for more information
```

したがって、`pip install -r requirements.txt` を使用して依存パッケージを必ずインストールしてください。オンラインオーケストレーターにデプロイする場合は、オーケストレーターでサポートされている方法で requirements.txt から依存パッケージをインストールできます。

最後に、パイプラインを実行し、secrets.toml に資格情報を入力するか、サポートされている場所に資格情報を配置します。

## 2. 資格情報の追加

ローカルまたはオーケストレーターで追加するには、次のガイド [資格情報](add_credentials) を参照してください。

## 3. パイプラインスクリプトをカスタマイズまたは作成する

パイプラインを初期化すると、サンプル ファイル `pipedrive_pipeline.py` が作成されます。

これは開発者が提案するパイプラインの使用方法なので、出発点として使用できます。この場合、すべてのデータをロードするメソッドを実行するか、どのエンドポイントをロードするかを選択できます。

このファイルを提案として使用し、代わりに独自のファイルを作成することもできます。

## 4. 検証済みのソースをハッキングする

既存の検証済みソースをその場で変更できます。

- その変更がこのソースを使用するすべての人にとって一般的に役立つ場合は、PR を介して貢献することを検討してください。こうすることで、テストとメンテナンスを確実に行うことができます。
- その変更が一般に共有されていない場合は、それを維持するための責任はあなたにあります。可能であれば、独自のカスタマイズをモジュール化して、ソースのメンテナンスの際にコミュニティ リポジトリから更新されたソースをプルし続けることができるようにすることをお勧めします。

## 5. プロジェクトにソースを追加する

```sh
dlt init chess duckdb
```

別の検証済みソースを追加するには、最初のパイプラインと同じ場所で　`dlt init` コマンドを実行するだけです:

- 共有ファイルは更新されます (secrets, config).
- 新しいソース用に新しいフォルダーが作成されます。
- 2 番目のソースの依存モジュールをインストールすることを忘れないでください。

## 6. 検証済みのソースを最新バージョンに更新する

検証済みのソースを最新のオンラインバージョンに更新するには、親フォルダで同じinitコマンドを実行するだけです:

```sh
dlt init pipedrive bigquery
```

## 7. 上級: ブランチ、ローカルフォルダー、または Git リポジトリで dlt init を使用する

このコマンドの詳細情報を確認するには、--help を使用します:

```sh
dlt init --help
```

`verified-sources`リポジトリのブランチからデプロイするには、以下を使用します:

```sh
dlt init source destination --branch <branch_name>
```

別のリポジトリからデプロイするには、verified-sourcesリポジトリをフォークし、次のように新しいリポジトリURLを指定します。`dlt-hub`をフォーク名に置き換えます:

```sh
dlt init pipedrive bigquery --location "https://github.com/dlt-hub/verified-sources"
```
