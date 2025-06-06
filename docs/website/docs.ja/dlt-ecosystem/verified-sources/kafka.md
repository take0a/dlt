---
title: Kafka
description: dlt verified source for Confluent Kafka
keywords: [kafka api, kafka verified source, kafka]
---
import Header from './_source-info-header.md';

# Kafka

<Header/>

[Kafka](https://www.confluent.io/) は、メッセージの発行者と購読者を含むログの形式で編成されたオープンソースの分散イベントストリーミングプラットフォームです。
Kafka `dlt` 検証済みソースは、Confluent Kafka API を使用して、選択した宛先にデータをロードします。
[パイプラインの例](https://github.com/dlt-hub/verified-sources/blob/master/sources/kafka_pipeline.py)を参照ください

ロードできるリソース:

| 名前              | 説明                                |
| ----------------- |--------------------------------------------|
| kafka_consumer    | Kafkaトピックからメッセージを抽出します        |

## セットアップガイド

### Kafka クラスターの資格情報を取得する

1. プロジェクトを微調整するには、[Kafka セットアップ](https://developer.confluent.io/get-started/python/#kafka-setup) に従ってください。
2. [構成](https://developer.confluent.io/get-started/python/#configuration)に従って、プロジェクトの資格情報を取得します。

### 検証済みソースを初期化する

データパイプラインを開始するには、次の手順に従ってください:

1. 次のコマンドを入力してください:

   ```sh
   dlt init kafka duckdb
   ```

   [このコマンド](../../reference/command-line-interface)は、Kafka を[ソース](../../general-usage/source)、[duckdb](../destinations/duckdb.md) を[宛先](../destinations)として[パイプラインの例](https://github.com/dlt-hub/verified-sources/blob/master/sources/kafka_pipeline.py)を初期化します。

2. 別の宛先を使用する場合は、`duckdb` を希望する[宛先](../destinations)の名前に置き換えてください。

3. このコマンドを実行すると、開始するために必要なファイルと構成設定を含む新しいディレクトリが作成されます。

詳細については、[ウォークスルー: 検証済みソースを追加する](../../walkthroughs/add-a-verified-source)をお読みください。

### 資格情報を追加する

1. `.dlt` フォルダには、`secrets.toml` というファイルがあります。アクセス トークンなどの機密情報を安全に保存する場所です。このファイルを安全に保管してください。

   サービスアカウント認証には次の形式を使用します:

```toml
[sources.kafka.credentials]
bootstrap_servers="web.address.gcp.confluent.cloud:9092"
group_id="test_group"
security_protocol="SASL_SSL"
sasl_mechanisms="PLAIN"
sasl_username="example_username"
sasl_password="example_secret"
```

2. [ドキュメント](../destinations/)に従って、選択した宛先の資格情報を入力します。

## パイプラインを実行する

1. パイプラインを実行する前に、次のコマンドを実行して必要な依存関係がすべてインストールされていることを確認してください:

   ```sh
   pip install -r requirements.txt
   ```

2. これでパイプラインを実行する準備ができました。開始するには、次のコマンドを実行します:

   ```sh
   python kafka_pipeline.py
   ```

3. パイプラインの実行が終了したら、次のコマンドを使用してすべてが正しくロードされたことを確認できます:

   ```sh
   dlt pipeline <pipeline_name> show
   ```

詳細については、[ウォークスルー: パイプラインを実行する](../../walkthroughs/run-a-pipeline)をお読みください。

:::info
トピックを作成してすぐに読み取りを開始すると、ブローカーがまだ同期されていない可能性があり、`dlt` がメッセージを読み取るオフセットが無効になる可能性があります。この場合、リソースはメッセージを返しません。保留中のメッセージは、次回の実行時 (またはブローカーが同期するとき) に受信されます。
:::

## ソースとリソース

`dlt`は[ソース](../../general-usage/source)と[リソース](../../general-usage/resource)の原則に基づいて動作します。

### `kafka_consumer` ソース

この関数は指定されたKafkaトピックからメッセージを取得します.

```py
@dlt.resource(name="kafka_messages", table_name=lambda msg: msg["_kafka"]["topic"])
def kafka_consumer(
    topics: Union[str, List[str]],
    credentials: Union[KafkaCredentials, Consumer] = dlt.secrets.value,
    msg_processor: Optional[Callable[[Message], Dict[str, Any]]] = default_msg_processor,
    batch_size: Optional[int] = 3000,
    batch_timeout: Optional[int] = 3,
    start_from: Optional[TAnyDateTime] = None,
) -> Iterable[TDataItem]:
   ...
```

`topics`: 抽出する Kafka トピックのリスト。

`credentials`: デフォルトでは、`secrets.toml` のデータで初期化されます。初期化された Kafka Consumer オブジェクトを渡すために明示的に使用できます。

`msg_processor`: 指定されたトピックから読み取られたすべてのメッセージを、宛先に保存する前に処理するために使用される関数です。カスタム プロセッサを渡すために明示的に使用できます。プロセッサの実装方法の例として、[デフォルトのプロセッサ](https://github.com/dlt-hub/verified-sources/blob/fe8ed7abd965d9a0ca76d100551e7b64a0b95744/sources/kafka/helpers.py#L14-L50)を参照してください。

`batch_size`: クラスターから一度に抽出するメッセージの数。パフォーマンスを微調整するために設定できます。

`batch_timeout`: 1 回のバッチ読み取り操作の最大タイムアウト (秒単位)。パフォーマンスを微調整するために設定できます。

`start_from`: メッセージの読み取り開始点となるタイムスタンプ。渡されると、`dlt` は Kafka クラスターに指定されたタイムスタンプの実際のオフセットを要求し、このオフセットからメッセージの読み取りを開始します。

## カスタマイズ

### 独自のパイプラインを作成する

1. パイプライン名、宛先、データセットを次のように指定してパイプラインを構成します:

   ```py
   pipeline = dlt.pipeline(
        pipeline_name="kafka",     # Use a custom name if desired
        destination="duckdb",      # Choose the appropriate destination (e.g., duckdb, redshift, post)
        dataset_name="kafka_data"  # Use a custom name if desired
   )
   ```

2. 複数のトピックを抽出する:

   ```py
   topics = ["topic1", "topic2", "topic3"]

   resource = kafka_consumer(topics)
   pipeline.run(resource, write_disposition="replace")
   ```

3. メッセージを抽出し、カスタムした方法で処理する:

   ```py
    def custom_msg_processor(msg: confluent_kafka.Message) -> Dict[str, Any]:
        return {
            "_kafka": {
                "topic": msg.topic(),  # required field
                "key": msg.key().decode("utf-8"),
                "partition": msg.partition(),
            },
            "data": msg.value().decode("utf-8"),
        }

    resource = kafka_consumer("topic", msg_processor=custom_msg_processor)
    pipeline.run(resource)
   ```

4. タイムスタンプからメッセージを抽出するには:

   ```py
    resource = kafka_consumer("topic", start_from=pendulum.DateTime(2023, 12, 15))
    pipeline.run(resource)
   ```

<!--@@@DLT_TUBA kafka-->

