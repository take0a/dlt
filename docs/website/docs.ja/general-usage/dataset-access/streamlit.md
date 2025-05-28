---
title: Viewing your data with Streamlit
description: Viewing your data with streamlit
keywords: [data, dataset, streamlit]
---

# Streamlit でデータを表示する

パイプラインをローカルで実行したら、読み込んだデータを表示するウェブアプリを起動できます。このためには、`streamlit` パッケージがインストールされている必要があります。

:::tip
Streamlit アプリは、`dlt` でサポートされているすべての出力先で動作するわけではありません。
SQL クライアントを提供する出力先のみが動作します。
ファイルシステムの出力先は、[ファイルシステム SQL クライアント](./sql-client#the-filesystem-sql-client) を介してサポートされており、ほとんどの場合動作します。
ベクターデータベースは一般的にサポートされていません。
:::

## 前提条件

Streamlit をインストールするには、次のコマンドを実行します:

```sh
pip install streamlit
```

*注意*: PythonのバージョンはCライブラリのサポートがインストールされている必要があります。確認するには、以下を実行してください。

```sh
`python -c "import _ctypes"`
```

これが失敗した場合は、[libffi](https://sourceware.org/libffi/) パッケージ (debian/ubuntu/Windows の場合は `libffi-dev`、macOS の場合は `libffi`) をインストールする必要があります。その後、Python バージョンも再インストールする必要があるかもしれません。


## Streamlit アプリの起動

パイプライン名を指定して、`show` [CLI コマンド](../../reference/command-line-interface.md#dlt-pipeline-show) を使用できます。

```sh
dlt pipeline {pipeline_name} show
```

Python コードで定義したパイプライン名を `pipeline_name` 引数で指定します。不明な場合は、`dlt pipeline --list` コマンドを使用してすべてのパイプラインを一覧表示できます。

## 認証情報

`dlt` は `.dlt` フォルダ内の `secrets.toml` と `config.toml` を検索します。

`secrets.toml` が見つからない場合は、`.streamlit` フォルダ内の `secrets.toml` を使用します。

ローカルで実行する場合は、通常の `.dlt` フォルダを維持してください。

streamlit クラウドで実行する場合は、`dlt` `secrets.toml` の内容を `streamlit` の secrets に貼り付けてください。

## データの調査

スキーマとデータの調査ができるようになりました。左側のサイドバーで以下の項目を切り替えられます。

* Exploring your data (default);
* Information about your loads.


## さらに詳しい情報

Python で `dlt` を対話形式またはノートブックで実行する場合は、[Python でロードしたデータにアクセスする](./dataset.md) ガイドをお読みください。

