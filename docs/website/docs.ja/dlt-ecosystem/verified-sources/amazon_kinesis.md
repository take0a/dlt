---
title: Amazon Kinesis
description: dlt verified source for Amazon Kinesis
keywords: [amazon kinesis, verified source]
---
import Header from './_source-info-header.md';

# Amazon Kinesis

<Header/>

[Amazon Kinesis](https://docs.aws.amazon.com/streams/latest/dev/key-concepts.html) は、リアルタイムのデータストリーミングと分析のためのクラウドベースのサービスであり、大量のデータストリームをリアルタイムで処理および分析できます。

AWS Kinesis [検証済みソース](https://github.com/dlt-hub/verified-sources/tree/master/sources/kinesis) は、Kinesis ストリームから希望する[宛先](../../dlt-ecosystem/destinations/)にメッセージを読み込みます。

この検証済みソースを使用してロードできるリソースは:

| 名前              | 説明                                     |
|------------------|------------------------------------------|
| kinesis_stream   | 指定されたストリームからメッセージを読み込む |


:::tip
パイプラインの例は[こちら](https://github.com/dlt-hub/verified-sources/blob/master/sources/kinesis_pipeline.py)で確認できます。
:::

## セットアップガイド

### 資格情報を取得する

この検証済みソースを使用するには、AWS の `アクセスキー` と `シークレットアクセスキー`が必要です。これらは次のように取得できます:

1. AWS マネジメントコンソールにサインインします。
1. IAM (Identity and Access Management) ダッシュボードに移動します。
1. 「ユーザー」メニューから、IAM ユーザー名を選択します。
1. 「セキュリティ資格情報」タブをクリックします。
1. 「アクセスキーの作成」を選択します。
1. 後で使用するために、アクセスキー ID とシークレットアクセスキーをダウンロードまたはコピーします。

:::info
ここで説明されている AWS UI は変更される可能性があります。完全なガイドはこちらの[リンク](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)から入手できます。
:::

### 検証済みソースを初期化する

データパイプラインを開始するには、次の手順に従ってください:

1. 次のコマンドを入力してください:

   ```sh
   dlt init kinesis duckdb
   ```

   [このコマンド](../../reference/command-line-interface)は、Kinesisを[ソース](../../general-usage/source)、[duckdb](../destinations/duckdb.md)を[宛先](../destinations)として[パイプラインの例](https://github.com/dlt-hub/verified-sources/blob/master/sources/kinesis_pipeline.py)を初期化します。

1. 別の宛先を使用する場合は、`duckdb` を希望する[宛先](../destinations)の名前に置き換えてください。

1. このコマンドを実行すると、開始するために必要なファイルと構成設定を含む新しいディレクトリが作成されます。

詳細については、[検証済みのソースを追加する](../../walkthroughs/add-a-verified-source)をお読みください。

### 資格情報を追加する

1. `.dlt` フォルダには `secrets.toml` というファイルがあります。アクセストークンなどの機密情報を安全に保存する場所です。このファイルを安全に保管してください。サービスアカウント認証の形式は次のとおりです:

   ```toml
   # Put your secret values and credentials here.
   # Note: Do not share this file and do not push it to GitHub!
   [sources.kinesis.credentials]
   aws_access_key_id="AKIA********"
   aws_secret_access_key="K+o5mj********"
   region_name="please set me up!" # aws region name
   ```

1. オプションで、`stream_name` を設定できます。`.dlt/config.toml` を更新します:

   ```toml
   [sources.kinesis]
   stream_name = "please set me up!" # Stream name (Optional).
   ```

1. `aws_access_key_id` と `aws_secret_access_key` の値を [上記でコピーしたもの](#grab-credentials) に置き換えます。これにより、検証済みのソースが Kinesis リソースに安全にアクセスできるようになります。

1. 次に、[宛先](../destinations/duckdb)の指示に従って、選択した宛先の資格情報を追加します。これにより、データが最終的な宛先に適切にルーティングされるようになります。

詳細については、[資格情報](../../general-usage/credentials)をご覧ください。

## パイプラインを実行する

1. パイプラインを実行する前に、次のコマンドを実行して必要な依存関係がすべてインストールされていることを確認してください:

   ```sh
   pip install -r requirements.txt
   ```

2. これでパイプラインを実行する準備ができました。開始するには、次のコマンドを実行します:

   ```sh
   python kinesis_pipeline.py
   ```

3. パイプラインの実行が終了したら、次のコマンドを使用してすべてが正しくロードされたことを確認できます:

   ```sh
   dlt pipeline <pipeline_name> show
   ```

   たとえば、上記のパイプラインの例の `pipeline_name` は `kinesis_pipeline` です。代わりに任意のカスタム名を使用することもできます。

詳細については、[パイプラインを実行する](../../walkthroughs/run-a-pipeline)を参照してください。

## ソースとリソース

`dlt`は[ソース](../../general-usage/source)と[リソース](../../general-usage/resource)の原則に基づいて動作します。

### `kinesis_stream` リソース

このリソースは Kinesis ストリームを読み取り、メッセージを生成します。[インクリメンタルロード](../../general-usage/incremental-loading) をサポートし、デフォルトでメッセージを JSON として解析します。

```py
@dlt.resource(
    name=lambda args: args["stream_name"],
    primary_key="_kinesis_msg_id",
    standalone=True,
)
def kinesis_stream(
    stream_name: str = dlt.config.value,
    credentials: AwsCredentials = dlt.secrets.value,
    last_msg: Optional[dlt.sources.incremental[StrStr]] = dlt.sources.incremental(
        "_kinesis", last_value_func=max_sequence_by_shard
    ),
    initial_at_timestamp: TAnyDateTime = 0.0,
    max_number_of_messages: int = None,
    milliseconds_behind_latest: int = 1000,
    parse_json: bool = True,
    chunk_size: int = 1000,
) -> Iterable[TDataItem]:
    ...
```

`stream_name`: Kinesis ストリームの名前。指定されていない場合のデフォルトは config/secrets になります。

`credentials`: Kinesis アクセスの認証情報。指定されていない場合は、シークレットまたはローカル認証情報を使用します。

`last_msg`: インクリメンタルロードのための shard_id からメッセージ シーケンスへのマッピング。

`initial_at_timestamp`: AT_TIMESTAMP または LATEST イテレータの開始タイムスタンプ。デフォルトは 0 です。

`max_number_of_messages`:実行あたりの最大メッセージ数。chunk_size を超える場合があります。デフォルトは None (制限なし)。

`milliseconds_behind_latest`: シャードトップから遅れるミリ秒。デフォルトは 1000 です。

`parse_json`: True の場合、メッセージを JSON として解析します。デフォルトは False。

`chunk_size`: リクエストごとに取得されるレコード数。デフォルトは 1000 です。

### どのように動くか？

ストリーム名と他のいくつかのオプションを渡すことで、リソース `kinesis_stream` を作成します。リソースの名前はストリームと同じになります。このリソースを反復処理すると (または `pipeline.run` レコードに渡すと)、要求されたストリーム内のすべてのシャードについて Kinesis にクエリが実行されます。各シャードに対して、メッセージを読み取るためのイテレータが作成されます:

1. `initial_at_timestamp` が存在する場合、リソースはこのタイムスタンプ以降のすべてのメッセージを読み取ります。
2. `initial_at_timestamp` が 0 の場合、ストリームの先端にあるメッセージのみが読み取られます。
3. 初期タイムスタンプが指定されていない場合は、 (TRIM HORIZON から)すべてのメッセージが取得されます。

リソースはシャードごとにすべてのメッセージシーケンスを状態に保存します。リソースを再度実行すると、メッセージが段階的にロードされます:

1. メッセージがあったすべてのシャードについては、最後のメッセージの後のメッセージのみが取得されます。
2. メッセージがないシャード (または新しいシャード) の場合、最後の実行時間を使用してメッセージが取得されます。

返されるメッセージの数を制限したり、JSON メッセージを自動的に解析したりするなどの追加オプションについては、`kinesis_stream` の [docstring](https://github.com/dlt-hub/verified-sources/blob/master/sources/kinesis/__init__.py#L31-L46) を確認してください。

### Kinesis メッセージ形式

メッセージ内の `_kinesis` ディクショナリには、シャード ID、シーケンス、パーティション キーなどを含むメッセージ エンベロープが格納されます。メッセージには、主キーである `_kinesis_msg_id` が含まれます。これは、(シャード ID + メッセージ シーケンス番号) のハッシュです。`parse_json` を True (デフォルト) に設定すると、データ フィールドが解析されます。False の場合は、`data` がバイトとして返されます。

## カスタマイズ

### 独自のパイプラインを作成する

独自のパイプラインを作成する場合は、この検証済みソースのソースおよびリソースメソッドを活用できます。

1. 次のようにパイプライン名、宛先、データセットを指定して[パイプライン](../../general-usage/pipeline)を設定します:

   ```py
   pipeline = dlt.pipeline(
       pipeline_name="kinesis_pipeline",  # Use a custom name if desired
       destination="duckdb",  # Choose the appropriate destination (e.g., duckdb, redshift, post)
       dataset_name="kinesis"  # Use a custom name if desired
   )
   ```

1. 過去1時間のストリームからメッセージを読み込むには:

   ```py
   # The resource below will take its name from the stream name,
   # it can be used multiple times. By default, it assumes that data is JSON and parses it,
   # here we disable that to just get bytes in data elements of the message.
   kinesis_stream_data = kinesis_stream(
       "kinesis_source_name",
       parse_json=False,
       initial_at_timestamp=pendulum.now().subtract(hours=1),
   )
   info = pipeline.run(kinesis_stream_data)
   print(info)
   ```

1. インクリメンタル Kinesis ストリームの場合、新しいメッセージのみを取得する:

   ```py
   # Running pipeline will get only new messages.
   info = pipeline.run(kinesis_stream_data)
   message_counts = pipeline.last_trace.last_normalize_info.row_counts
   if "kinesis_source_name" not in message_counts:
       print("No messages in kinesis")
   else:
       print(pipeline.last_trace.last_normalize_info)
   ```

1. シンプルなデコーダーでJSONを解析する:

   ```py
   def _maybe_parse_json(item: TDataItem) -> TDataItem:
       try:
           item.update(json.loadb(item["data"]))
       except Exception:
           pass
       return item

   info = pipeline.run(kinesis_stream_data.add_map(_maybe_parse_json))
   print(info)
   ```

1. パイプラインを使用せずにKinesisメッセージを読み取り、どこかに送信する:

   ```py
   from dlt.common.configuration.container import Container
   from dlt.common.pipeline import StateInjectableContext

   STATE_FILE = "kinesis_source_name.state.json"

   # Load the state if it exists.
   if os.path.exists(STATE_FILE):
       with open(STATE_FILE, "rb") as rf:
           state = json.typed_loadb(rf.read())
   else:
       # Provide new state.
       state = {}

   with Container().injectable_context(
       StateInjectableContext(state=state)
   ) as managed_state:
       # dlt resources/source is just an iterator.
       for message in kinesis_stream_data:
           # Here you can send the message somewhere.
           print(message)
           # Save state after each message to have full transaction load.
           # DynamoDB is also OK.
           with open(STATE_FILE, "wb") as wf:
               json.typed_dump(managed_state.state, wf)
           print(managed_state.state)
   ```

<!--@@@DLT_TUBA kinesis-->

