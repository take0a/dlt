---
title: Setup
description: Define and execute local transformations
---

dlt+ は、ローカルでスピンアップされたキャッシュを使用してデータの変換を実行するための強力なメカニズムを提供します。
実行前にキャッシュを自動的に作成・管理し、実行後にキャッシュをクリーンアップします。

変換は、[キャッシュ](../../core-concepts/cache.md) に保存されたデータを変更する関数で構成されます。これらの変換は、以下を使用して実装できます。

* [dbt モデル](./dbt-transformations.md)
* [🧪 Python ユーザー定義関数](./python-transformations.md)

キャッシュと変換を組み合わせることで、dlt 経由で読み込まれたデータを効率的に処理し、新しい宛先に移動できます。

:::caution
ローカル変換は現在、特定のユースケースに限定されており、ファイルシステムベースの宛先に保存されたデータとのみ互換性があります:

* [Iceberg](../../ecosystem/iceberg.md)
* [Delta](../../ecosystem/delta.md)
* [Cloud storage and filesystem](../../../dlt-ecosystem/destinations/filesystem.md)

[キャッシュを定義する](#defining-the-cache) ときは、ファイルシステムベースの保存先にあるデータセットを指定するようにしてください。
:::

この機能を使用するには、以下の手順に従ってください:

1. [`dlt.yml` ファイルの設定](#configure-dltyml-file): キャッシュを定義し、変換を指定します。
2. [スキャフォールディングの生成](#generate-scaffolding): 変換テンプレートを自動的に作成します。
3. [変換の変更](#modify-transformations): 生成された Python 関数または dbt モデルを更新します。
4. [変換の実行](#run-transformations): データに対して変換を実行します。

## `dlt.yml` ファイルの設定

`dlt.yml` ファイルで変換を設定する前に、キャッシュが定義されていることを確認する必要があります。

### キャッシュの定義

キャッシュを定義する方法の詳細な手順は、[キャッシュのコアコンセプト](../../core-concepts/cache.md#define-the-cache)に記載されています。
以下に例を示します:

```yaml
caches:
  github_events_cache:
    inputs:
      - dataset: github_events_dataset
        tables:
          items: items
    outputs:
      - dataset: github_events_dataset
        tables:
          items: items
          items_aggregated: items_aggregated
```

:::caution
キャッシュの入力データセットがファイルシステムベースの保存先 ([Iceberg](../../ecosystem/iceberg.md)、[Delta](../../ecosystem/delta.md)、または [クラウド ストレージとファイルシステム](../../../dlt-ecosystem/destinations/filesystem.md)) にあることを確認してください。
:::

### 変換の定義

`dlt.yml` で、以下のパラメータを使用して変換を指定します。

* 変換の一意の識別子。
* エンジン – 以下から選択します。
  * Python ベースの変換の場合は `arrow`
  * dbt ベースの変換の場合は `dbt`
* キャッシュ – 変換が実行されるキャッシュ。

例:

```yaml
transformations:
  github_events_transformations:
    engine: dbt
    cache: github_events_cache
```

## スキャフォールディングの生成

DLTパイプラインに基づいて変換スキャフォールディングを作成するには：

1. DLTパイプラインを少なくとも1回実行します。これにより、DLTにデータセットスキーマが確実に含まれます。
2. 次のCLIコマンドを実行します。

```sh
dlt transformation <transformation-name> render-t-layer
```

これにより、`./transformations` フォルダ内に変換ファイルが生成されます。
エンジンによって異なります。

* Python 変換の場合: 変換関数を含む Python スクリプト ([詳細はこちら](./python-transformations.md))
* dbt 変換の場合: dbt モデル ([詳細はこちら](./dbt-transformations.md))

生成される各変換には、`dlt_load_id` を介して増分読み込み状態を管理するためのモデルが含まれます。

## 変換の変更

生成された変換を更新し、目的の動作を反映する新しい変換を作成できます。
生成されたモデルと同様に、増分アプローチを維持することをお勧めします。

## 変換の実行

dlt+ は、変換を実行するための包括的な CLI サポートを提供します。
利用可能なコマンドの全リストは、[コマンドラインインターフェース](../../reference.md) で確認できます。

定義された変換を実行するには、[次のコマンド](../../reference.md#dlt-transformation-run) を使用します。

```sh
dlt transformation <transformation_name> run
```

このコマンドは、ローカル キャッシュにデータを入力し、定義された変換を適用し、変換されたテーブルを指定された宛先にフラッシュします。

