---
title: Deploy with Dagster
description: How to deploy a pipeline with Dagster
keywords: [how to, deploy a pipeline, Dagster]
---

# Dagsterでデプロイ

## Dagsterの紹介

Dagster は、テーブル、データセット、機械学習モデル、レポートなどのデータ資産の開発と保守用に設計されたオーケストレーターです。Dagster は、これらのプロセスの信頼性を確保し、ソフトウェア定義資産 (SDA) を使用して複雑なデータ管理を簡素化し、コードの再利用性を高め、データの理解を深めることに重点を置いています。

詳細については、Dagster の[ドキュメント](https://docs.dagster.io/getting-started?_gl=1*19ikq9*_ga*NTMwNTUxNDAzLjE3MDg5Mjc4OTk.*_ga_84VRQZG7TV*MTcwOTkwNDY3MS4zLjEuMTcwOTkwNTYzNi41Ny4wLjA.*_gcl_au*OTM3OTU1ODMwLjE3MDg5Mjc5MDA.)
を参照してください。

### Dagster Cloud の機能

Dagster Cloud は、サーバーレスまたはハイブリッドのデプロイメント オプションを備えたエンタープライズ レベルのオーケストレーション サービスを提供します。ネイティブ ブランチと組み込みの CI/CD を組み込んで、開発者エクスペリエンスを優先します。
インフラストラクチャ管理の手間をかけずに、スケーラブルでコスト効率の高い運用を実現します。

### Dagster の展開オプション: **サーバーレス** と **ハイブリッド**

*サーバーレス* オプションはオーケストレーションエンジンを完全にホストしますが、*ハイブリッド* モデルはコンピューティング リソースを使用する柔軟性を提供し、Dagster がコントロール プレーンを管理して、運用オーバーヘッドを削減し、セキュリティを確保します。

詳細については、Dagster Cloud [ドキュメント](https://dagster.io/cloud)を参照してください。

### Dagster を無料で利用する

Dagster は 30 日間の無料トライアルを提供しており、その期間中にパイプライン オーケストレーション、データ品質チェック、埋め込み ELT などの機能を試すことができます。オープン ソースを使用するか、トライアルにサインアップして Dagster を試すことができます。

## `dlt` を使用したデータ パイプラインの構築

**パイプラインオーケストレーションとして `dlt` はどのように Dagster と統合されるのか？**

`dlt` はパイプライン オーケストレーションのために Dagster と統合され、データ パイプラインの構築、拡張、管理のための合理化されたプロセスを提供します。これにより、開発者はデータの抽出とロードを処理するための `dlt` の機能と、データ パイプラインを効率的に管理および監視するための Dagster のオーケストレーション機能を活用することができます。

Dagster は [dlt とのネイティブ統合](https://docs.dagster.io/integrations/embedded-elt/dlt) をサポートしています。この統合の仕組みに関するガイドはこちらです。

### Dagster での `dlt` パイプラインのオーケストレーション

ここでは、Dagster を使用して `dlt` パイプラインをオーケストレーションし、リポジトリから GitHub の問題データを取り込み、それを DuckDB にロードするパイプラインを作成するための簡潔なガイドを紹介します。

完全なサンプルコードは、[このリポジトリ](https://github.com/dlt-hub/dlthub-education/blob/main/workshops/workshop_august_2024/part2/deployment/deploy_dagster/README.md)にあります。

**手順は次のとおりです:**

1. pip を使用して Dagster と組み込み ELT パッケージをインストールします:

    ```sh
    pip install dagster dagster-embedded-elt
    ```

1. Dagster プロジェクトを設定します:

      ```sh
      mkdir dagster_github_issues
      cd dagster_github_issues
      dagster project scaffold --name github-issues
      ```

      ![image](https://github.com/user-attachments/assets/f9002de1-bcdf-49f4-941b-abd59ea7968d)

1. Dagster プロジェクトで、`github_source` フォルダーに dlt パイプラインを定義します。

   **注意**: dlt Dagster ヘルパーは dlt ソースでのみ機能します。リソースは常にソースにグループ化する必要があります。

     ```py
     import dlt
     ...
     @dlt.resource(
         table_name="issues",
         write_disposition="merge",
         primary_key="id",
     )
     def get_issues(
             updated_at=dlt.sources.incremental("updated_at", initial_value="1970-01-01T00:00:00Z")
     ):
         url = (
             f"{BASE_URL}?since={updated_at.last_value}&per_page=100&sort=updated"
             "&direction=desc&state=open"
         )
         yield pagination(url)

     @dlt.source
     def github_source():
         return get_issues()
     ```
 
 1. `dlt_assets` 定義を作成します。

    `@dlt_assets` デコレータは、`dlt_source` および `dlt_pipeline` パラメータを受け取ります。この例では、`github_source` ソースを使用し、GitHub から DuckDB にデータを取り込むための `dlt_pipeline` を作成しました。

    アセットを定義する方法の例を次に示します (`github_source/assets.py`):

      ```py
      import dlt
      from dagster import AssetExecutionContext
      from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
      from .github_pipeline import github_source

      @dlt_assets(
          dlt_source=github_source(),
          dlt_pipeline=dlt.pipeline(
              pipeline_name="github_issues",
              dataset_name="github",
              destination="duckdb",
              progress="log",
          ),
          name="github",
          group_name="github",
      )
      def dagster_github_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
          yield from dlt.run(context=context)
      ```

    詳細については、[Dagster のドキュメント](https://docs.dagster.io/_apidocs/libraries/dagster-embedded-elt#dagster_embedded_elt.dlt.dlt_assets)を参照してください。

 1. 定義オブジェクトを作成します。

    最後のステップは、アセットとリソースを [Definitions](https://docs.dagster.io/_apidocs/definitions#dagster.Definitions) オブジェクト (`github_source/definitions.py`) に含めることです。これにより、Dagster ツールは定義したすべてのものを読み込むことができます:

     ```py
     import assets
     from dagster import Definitions, load_assets_from_modules
     from dagster_embedded_elt.dlt import DagsterDltResource

     dlt_resource = DagsterDltResource()
     all_assets = load_assets_from_modules([assets])

     defs = Definitions(
         assets=all_assets,
         resources={
             "dlt": dlt_resource,
         },
     )
     ```

1. Web サーバーをローカルで実行します:

    1. 次のコマンドを使用して、必要な依存関係をインストールします:

       ```sh
       pip install -e ".[dev]"
       ```

       -e を使用して、依存関係を [編集可能モード](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) でインストールします。これにより、コードを変更したときに変更が自動的に適用されます。

    2. プロジェクトを実行します:

       ```sh
       dagster dev
       ```

    3. Dagster UI にアクセスするには、Web ブラウザーで localhost:3000 に移動します:

       ![image](https://github.com/user-attachments/assets/97b74b86-df94-47e5-8ae2-de7cc47f56d8)

1. パイプラインを実行します。

   Dagster のインスタンスが実行中になったので、データ パイプラインを実行できます。

   パイプラインを実行するには、**Assets** に移動し、右上の **Materialize** ボタンをクリックします。Dagster では、マテリアライズとは、アセットに関連付けられたコードを実行して出力を生成することを指します。

   ![image](https://github.com/user-attachments/assets/79416fb7-8362-4640-b205-e59aa7ac785c)

   コマンドラインに次のログが表示されます:

   ![image](https://github.com/user-attachments/assets/f0e3bec8-f702-46a6-b69f-194a1dacf625)

   実際の運用環境での dlt の例をご覧になりたいですか? [Dagster Open Platform](https://github.com/dagster-io/dagster-open-platform) プロジェクトで、Dagster 社内で dlt がどのように使用されているかを確認してください。


:::info
Dagster と dlt の統合の全体像については、[ドキュメント](https://docs.dagster.io/integrations/embedded-elt/dlt) を参照してください。このドキュメントでは、GitHub データを取り込んで Snowflake に保存するための詳細な概要と手順が説明されています。同様のアプローチを使用してパイプラインを構築できます。
:::

### よくある質問

- **`secrets.toml` および `config.toml` ファイルを含む生成された `.dlt` フォルダーを削除できますか?**

  はい。dlt は環境変数と互換性があるため、Dagster と dlt の両方に必要なシークレットにこれを使用できます。

- **複数のソースを扱っています。これらのアセットを最適にグループ化するにはどうすればよいでしょうか？**

  複数のソースを扱うときに Dagster でアセットを効果的にグループ化するには、`@dlt_assets` デコレータで `group_name` パラメータを使用します。これにより、Dagster UI で特定のソースまたはテーマに関連するアセットを整理して視覚化できます。以下に簡略化した例を示します:

  ```py
  import dlt
  from dagster_embedded_elt.dlt import dlt_assets
  from dlt_sources.google_analytics import google_analytics

  # Define assets for the first Google Analytics source
  @dlt_assets(
      dlt_source=google_analytics(),
      dlt_pipeline=dlt.pipeline(
        pipeline_name="google_analytics_pipeline_1",
        destination="bigquery",
        dataset_name="google_analytics_data_1"
      ),
      group_name='Google_Analytics'
  )
  def google_analytics_assets_1(context, dlt):
      yield from dlt.run(context=context)

  # Define assets for the second Google Analytics source
  @dlt_assets(
      dlt_source=google_analytics(),
      dlt_pipeline=dlt.pipeline(
        pipeline_name="google_analytics_pipeline_2",
        destination="bigquery",
        dataset_name="google_analytics_data_2"
      ),
      group_name='Google_Analytics'
  )
  def google_analytics_assets_2(context, dlt):
      yield from dlt.run(context=context)
  ```

- **パーティション分割されたテーブルに対して、Dagster で `bigquery_adapter` と `@dlt_assets` を使用するにはどうすればよいですか？**

  Dagster でパーティション分割されたテーブルに対して `bigquery_adapter` を `@dlt_assets` とともに使用するには、リソース設定を変更して、パーティション パラメータを持つ `bigquery_adapter` を含めます。簡単な例を次に示します:

  ```py
  import dlt
  from google.analytics import BetaAnalyticsDataClient
  from dlt.destinations.adapters import bigquery_adapter
  from dagster import dlt_asset

  @dlt_asset
  def google_analytics_asset(context):
      # Configuration (replace with your actual values or parameters)
      queries = [
          {"dimensions": ["dimension1"], "metrics": ["metric1"], "resource_name": "resource1"}
      ]
      property_id = "your_property_id"
      start_date = "2024-01-01"
      rows_per_page = 1000
      credentials = your_credentials

      # Initialize Google Analytics client
      client = BetaAnalyticsDataClient(credentials=credentials.to_native_credentials())

      # Fetch metadata
      metadata = get_metadata(client=client, property_id=property_id)
      resource_list = [metadata | metrics_table, metadata | dimensions_table]

      # Configure and add resources to the list
      for query in queries:
          dimensions = query["dimensions"]
          if "date" not in dimensions:
              dimensions.append("date") # type: ignore[attr-defined]

          resource_name: str = query["resource_name"] # type: ignore[assignment]
          resource_list.append(
              bigquery_adapter(
                  dlt.resource(data, name=resource_name, write_disposition="append")(
                      client=client,
                      rows_per_page=rows_per_page,
                      property_id=property_id,
                      dimensions=dimensions,
                      metrics=query["metrics"],
                      resource_name=resource_name,
                      start_date=start_date,
                      last_date=dlt.sources.incremental("date"),
                  ),
                  partition="date"
              )
          )

      return resource_list
  ```

### 追加リソース

- Dagster Cloud へのデプロイの詳細については、[Dagster Cloud ドキュメント](https://docs.dagster.cloud/) をご覧ください。

- Dagster と dlt の統合の詳細については、以下をご覧ください:
  [dlt & Dagster](https://docs.dagster.io/integrations/embedded-elt/dlt)
  [Embedded ELT Documentation](https://docs.dagster.io/_apidocs/libraries/dagster-embedded-elt#dagster_embedded_elt.dlt.dlt_assets).

- Dagster 上でオーケストレーションされた一般的な構成可能な `dlt` リソース:
  [dlt resource](https://github.com/dagster-io/dagster-open-platform/blob/5030ff6828e2b001a557c6864f279c3b476b0ca0/dagster_open_platform/resources/dlt_resource.py#L29).

- Dagster で `dlt` パイプラインを構成します:
  [dlt pipelines](https://github.com/dagster-io/dagster-open-platform/tree/5030ff6828e2b001a557c6864f279c3b476b0ca0/dagster_open_platform/assets/dlt_pipelines).

- MongoDB ソースをアセット ファクトリとして構成します:

   Dagster は、データベースの各コレクションを個別のアセットに変換できる [@multi_asset](https://github.com/dlt-hub/dlt-dagster-demo/blob/21a8d18b6f0424f40f2eed5030989306af8b8edb/mongodb_dlt/mongodb_dlt/assets/__init__.py#L18) 宣言の機能を提供します。これにより、障害が発生した場合にパイプラインを簡単にデバッグでき、コレクションが互いに独立します。

:::note
これらの一部は外部リポジトリであり、変更される可能性があります。
:::

