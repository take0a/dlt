---
title: Postgres replication
description: dlt verified source for Postgres replication
keywords: [postgres, postgres replication, database replication]
---
import Header from './_source-info-header.md';

# Postgres replication

<Header/>

[Postgres](https://www.postgresql.org/) は、最も人気のあるリレーショナル データベース管理システムの 1 つです。この検証済みソースは、Postgres レプリケーション機能を使用してテーブルを効率的に処理します (このプロセスは、多くの場合、*Change Data Capture* または CDC と呼ばれます)。[論理デコード](https://www.postgresql.org/docs/current/logicaldecoding.html)と標準の組み込み`pgoutput` [出力プラグイン](https://www.postgresql.org/docs/current/logicaldecoding-output-plugin.html)を使用します。

この検証済みソースを使用してロードできるリソースは:

| 名前                 | 説明                                     |
| -------------------- | ----------------------------------------------- |
| replication_resource | レプリケーションスロットから公開されたメッセージをロードする |

:::info
Postgres レプリケーションソースは現在、[scd2 マージ戦略](../../general-usage/incremental-loading#scd2-strategy) を**サポートしていません。**
:::

## セットアップガイド

### ユーザーの設定

Postgresユーザーを設定するには、次の手順に従います:

1. Postgresユーザーには `LOGIN` 属性と `REPLICATION` 属性が割り当てられている必要があります:
    
    ```sql
    CREATE ROLE replication_user WITH LOGIN REPLICATION;
    ```
    
2. また、データベースに対する `GRANT` 権限も必要です:
    
    ```sql
    GRANT CREATE ON DATABASE dlt_data TO replication_user;
    ```

### RDS を設定する

RDS で Postgres ユーザーを設定するには、次の手順に従います:

1. [パラメータグループ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PostgreSQL.Replication.ReadReplicas.html)を介して RDS Postgres インスタンスのレプリケーションを有効にする必要があります。

2. `WITH LOGIN REPLICATION;` は RDS では機能しません。代わりに、:
    
    ```sql
    GRANT rds_replication TO replication_user;
    ```
    
3. 接続パラメータを設定して非SSL接続にフォールバックしないでください:
    
   ```toml
   sources.pg_replication.credentials="postgresql://loader:password@host.rds.amazonaws.com:5432/dlt_data?sslmode=require&connect_timeout=300"
   ```

### 検証済みソースを初期化する

データパイプラインを開始するには、次の手順に従ってください:

1. 次のコマンドを入力してください:
    
   ```sh
   dlt init pg_replication duckdb
   ```
    
   [パイプラインの例](https://github.com/dlt-hub/verified-sources/blob/master/sources/pg_replication_pipeline.py)を、Postgres レプリケーションを[ソース](../../general-usage/source)、[DuckDB](../../dlt-ecosystem/destinations/duckdb) を[宛先](../../dlt-ecosystem/destinations)として初期化します。
    
    
2. 別の宛先を使用する場合は、`duckdb` を希望する [宛先](../../dlt-ecosystem/destinations) の名前に置き換えるだけです。
    
3. このソースは`sql_database`ソースを使用します。次のように初期化できます:
    
   ```sh
   dlt init sql_database duckdb
   ```
   :::note
   重要なのは、ユーザーが初期ロードを実行する場合、具体的には `persist_snapshots` が `True` に設定されている場合にのみ必要になることです。
   :::
    
4. これら 2 つのコマンドを実行すると、開始するために必要なファイルと構成設定を含む新しいディレクトリが作成されます。
   
   詳細については、[検証済みソースを追加する方法](../../walkthroughs/add-a-verified-source) のガイドをお読みください。

   :::note
   `secrets.toml` の `[sql.sources.credentials]` セクションは必須ではないため省略できます。
   :::

### 資格情報を追加する

1. `.dlt` フォルダには、`secrets.toml` というファイルがあります。アクセス トークンなどの機密情報を安全に保存する場所です。このファイルを安全に保管してください。
    
   `secrets.toml`は次のようになります:
    
   ```toml
   [sources.pg_replication.credentials]
   drivername = "postgresql" # please set me up!
   database = "database" # please set me up!
   password = "password" # please set me up!
   username = "username" # please set me up!
   host = "host" # please set me up!
   port = 0 # please set me up! 
   ```
    
2. 資格情報は上記のように設定できます。または、次のように `secrets.toml` ファイルで資格情報を提供することもできます:
    
   ```toml
   sources.pg_replication.credentials="postgresql://username@password.host:port/database"
   ```

3. 最後に、[宛先](../../dlt-ecosystem/destinations/)の指示に従って、選択した宛先の資格情報を追加します。これにより、データが適切にルーティングされるようになります。

詳細については、[構成セクション](../../general-usage/credentials) を参照してください。

## パイプラインを実行する

1. パイプラインを実行する前に、次のコマンドを実行して必要な依存関係がすべてインストールされていることを確認してください:

   ```sh
   pip install -r requirements.txt
   ```

2. これでパイプラインを実行する準備ができました。開始するには、次のコマンドを実行します。:

   ```sh
   python pg_replication_pipeline.py
   ```

3. パイプラインの実行が終了したら、次のコマンドを使用してすべてが正しくロードされたことを確認できます:

   ```sh
   dlt pipeline <pipeline_name> show
   ```

   たとえば、上記のパイプライン例の `pipeline_name` は `pg_replication_pipeline` ですが、代わりに任意のカスタム名を使用することもできます。

   詳細については、[パイプラインの実行方法](../../walkthroughs/run-a-pipeline) のガイドをお読みください。

## ソースとリソース

`dlt` は、[ソース](../../general-usage/source) と [リソース](../../general-usage/resource) の原則に基づいて動作します。

### `replication_resource` リソース

このリソースは、1 つ以上の Postgres テーブルの変更に関するデータ項目を生成します。

```py
@dlt.resource(
    name=lambda args: args["slot_name"] + "_" + args["pub_name"],
)
def replication_resource(
    slot_name: str,
    pub_name: str,
    credentials: ConnectionStringCredentials = dlt.secrets.value,
    include_columns: Optional[Dict[str, Sequence[str]]] = None,
    columns: Optional[Dict[str, TTableSchemaColumns]] = None,
    target_batch_size: int = 1000,
    flush_slot: bool = True,
) -> Iterable[Union[TDataItem, DataItemWithMeta]]:
    ...
```

`slot_name`: メッセージを消費するレプリケーションスロット名。

`pub_name`: メッセージを生成するスロット名。

`include_columns`: 生成されたデータ項目に含める列名のシーケンスにテーブル名をマップします。シーケンスに含まれない列は除外されます。指定しない場合は、すべての列が含まれます。

`columns`: テーブル名を列ヒントにマップし、複製されたテーブルに適用します。

`target_batch_size`: バッチで生成されるデータ項目の希望数。メモリ内のデータ項目を制限するために使用できます。

`flush_slot`:  処理されたメッセージがレプリケーション スロットから破棄されるかどうか。推奨値は「True」です。

## カスタマイズ

独自のパイプラインを作成する場合は、この検証済みソースのソースおよびリソース メソッドを活用できます。

1. ソースパイプラインを次のように定義します:
    
   ```py
   # Defining source pipeline
   src_pl = dlt.pipeline(
       pipeline_name="source_pipeline",
       destination="postgres",
       dataset_name="source_dataset",
       dev_mode=True,
   )
   ```

   `pg_replication_pipeline.py` ファイルで利用可能な `get_postgres_pipeline()` 関数を設定して使用することで、同じ機能を実現できます。

   :::note IMPORTANT
    Postgres データベースからの大規模なデータセットを扱う場合、ソース パイプラインの関連性を考慮することが重要です。テスト目的では、ソース パイプラインを使用してデータ フローを試してみると便利です。ただし、実稼働環境では、Postgres データベースを変更する別のプロセスが存在する可能性があります。このような場合、ユーザーは通常、宛先パイプラインを定義するだけで済みます。
   :::
    
2. 同様に、宛先パイプラインを定義します。
    
   ```py
   dest_pl = dlt.pipeline(
       pipeline_name="pg_replication_pipeline",
       destination='duckdb',
       dataset_name="replicate_single_table",
       dev_mode=True,
   )
   ```
    
3. スロット名とパブリケーション名を次のように定義します:
    
   ```py
   slot_name = "example_slot"
   pub_name = "example_pub"
   ```
    
4. レプリケーションを初期化するには、`init_replication` 関数を使用できます。ユーザーはこの関数を使用して、`dlt` に Postgres を設定させ、レプリケーションの準備を整えることができます。
    
   ```py
   # requires the Postgres user to have the REPLICATION attribute assigned
   init_replication(  
       slot_name=slot_name,
       pub_name=pub_name,
       schema_name=src_pl.dataset_name,
       table_names="my_source_table",
       reset=True,
   )
   ```
    
   :::note
   スキーマ全体を複製する場合は、`init_replication` 関数の `table_names` 引数を省略できます。
   :::

5. 初期ロード中にデータを宛先にスナップショットするには、次のように `persist_snapshots=True` 引数を使用します:

   ```py
   snapshot = init_replication(  # requires the Postgres user to have the REPLICATION attribute assigned
        slot_name=slot_name,
        pub_name=pub_name,
        schema_name=src_pl.dataset_name,
        table_names="my_source_table",
        persist_snapshots=True,  # persist snapshot table(s) and let function return resource(s) for initial load
        reset=True,
    )
   ```

6. このスナップショットを宛先にロードするには、宛先パイプラインを次のように実行します:
    
   ```py
   dest_pl.run(snapshot)
   ```
    
7. ソースに変更を加えた後、`replication_resource`を使用して変更を宛先に複製し、パイプラインを次のように実行できます:
    
   ```py
   # Create a resource that generates items for each change in the source table
   changes = replication_resource(slot_name, pub_name)
 
   # Run the pipeline as
   dest_pl.run(changes)
   ```
    
8. 選択した列を含むテーブルを複製するには、次のように `include_columns` 引数を使用します:
    
   ```py
   # requires the Postgres user to have the REPLICATION attribute assigned
   initial_load = init_replication(  
       slot_name=slot_name,
       pub_name=pub_name,
       schema_name=src_pl.dataset_name,
       table_names="my_source_table",
       include_columns={
           "my_source_table": ("column1", "column2")
       },
       reset=True,
   )
   ```
    
   同様に、選択した列の変更を複製するには、`replication_resource` 関数で `table_names` および `include_columns` 引数を使用できます。
