---
title: 'Moving from local to production'
description: Share a local dataset by moving it to BigQuery
keywords: [how to, share a dataset]
---

# ローカルから本番環境への移行

以前のハウツーガイドでは、パイプラインの作成と実行にローカルスタックを使用していました。
これにより、クラウドアカウントや認証情報の設定、そして多くの場合費用といった煩わしさから解放されました。
ローカル「ウェアハウス」として、高速で機能が豊富で、どこでも動作する `duckdb` を選択しました。
しかし、ある時点で本番環境に移行したり、結果を同僚と共有したりする必要が生じるかもしれません。ローカルの `duckdb` ファイルだけでは不十分です！
[既に用意している chess.com API 用のデータセット](run-a-pipeline.md) を BigQuery に移行してみましょう。

## 1. 「destination」引数を「bigquery」に置き換えます

```py
import dlt

if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="chess_pipeline",
        destination='bigquery',
        dataset_name="games_data"
    )
    # get data for a few famous players
    data = chess_source(
        data=['magnuscarlsen', 'rpragchess'],
        start_month="2022/11",
        end_month="2022/12"
    )
    load_info = pipeline.run(data)
```

コードの変更はこれで完了です。スクリプトを実行すると、`dlt` によって `duckdb` と同じデータセットが BigQuery 内に作成されます。

## 2. BigQuery へのアクセスを有効にし、認証情報を取得します。

`dlt` が BigQuery にデータを書き込めるようにするには、[こちらの手順](../dlt-ecosystem/destinations/bigquery.md)に従ってください。

## 3. secrets.toml に認証情報を追加する

前の手順で取得した認証情報を使用して、`secrets.toml` ファイルに次のセクションを追加してください。

```toml
[destination.bigquery]
location = "US"

[destination.bigquery.credentials]
project_id = "project_id" # please set me up!
private_key = "private_key" # please set me up!
client_email = "client_email" # please set me up!
```

## 4. パイプラインを再度実行する

```sh
python chess_pipeline.py
```

例外が見つかった場合は、次のセクションに進んでください。

## 5. 例外のトラブルシューティング

### Credentials missing: ConfigFieldMissingException

この例外は、`dlt` が BigQuery 認証情報を見つけられない場合に表示されます。
以下の例外では、認証情報（「project_id」、「private_key」、「client_email」）がすべて欠落しています。
この例外には、実行されたすべての構成ルックアップのリストも表示されます。[ここでは、このようなリストの読み方を説明します](run-a-pipeline.md#missing-secret-or-configuration-values)。

```text
dlt.common.configuration.exceptions.ConfigFieldMissingException: Following fields are missing: ['project_id', 'private_key', 'client_email'] in configuration with spec GcpServiceAccountCredentials
    for field "project_id" config providers and keys were tried in the following order:
        In Environment Variables key CHESS__DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID was not found.
        In Environment Variables key CHESS__DESTINATION__CREDENTIALS__PROJECT_ID was not found.
```

例外が発生する最も一般的なケースは次のとおりです。

1. シークレットが `secrets.toml` に存在しない。
1. シークレットが間違ったセクションに配置されている。例えば、以下のコードは動作しません。
  ```toml
  [destination.bigquery] # 'credentials' missed
  project_id = "project_id"
  ```
1. パイプラインスクリプトを、保存されているフォルダとは**異なる**フォルダから実行しています。例えば、`python chess_demo/chess_pipeline.py` は `chess_demo` フォルダからスクリプトを実行しますが、現在の作業ディレクトリは上記のフォルダです。
これにより、`dlt` が `chess_demo/.dlt/secrets.toml` を見つけて認証情報を入力することができなくなります。

### secrets.toml にプレースホルダが残っています

ここで、BigQuery は `private_key` の形式が正しくないというエラーを表示します。
これは、`secrets.toml` 内のプレースホルダを実際の値に置き換え忘れた場合によく発生します。

```text
<class 'dlt.destinations.exceptions.DestinationConnectionError'>
Connection with BigQuerySqlClient to dataset name games_data failed. Please check if you configured the credentials at all and provided the right credentials values. You can also be denied access, or your internet connection may be down. The actual reason given is: No key could be detected.
```

### BigQuery が有効になっていません

[BigQuery API を有効にする必要があります。](https://console.cloud.google.com/apis/dashboard)

```text
<class 'google.api_core.exceptions.Forbidden'>
403 POST https://bigquery.googleapis.com/bigquery/v2/projects/bq-walkthrough/jobs?prettyPrint=false: BigQuery API has not been used in project 364286133232 before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/bigquery.googleapis.com/overview?project=364286133232 then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.

Location: EU
Job ID: a5f84253-3c10-428b-b2c8-1a09b22af9b2
 [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Google developers console API activation', 'url': 'https://console.developers.google.com/apis/api/bigquery.googleapis.com/overview?project=364286133232'}]}, {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'SERVICE_DISABLED', 'domain': 'googleapis.com', 'metadata': {'service': 'bigquery.googleapis.com', 'consumer': 'projects/364286133232'}}]
```

### ジョブを作成する権限がありません

[宛先ページ](../dlt-ecosystem/destinations/bigquery.md)に記載されているように、「BigQuery ジョブユーザー」を追加してください。

```text
<class 'google.api_core.exceptions.Forbidden'>
403 POST https://bigquery.googleapis.com/bigquery/v2/projects/bq-walkthrough/jobs?prettyPrint=false: Access Denied: Project bq-walkthrough: User does not have bigquery.jobs.create permission in project bq-walkthrough.

Location: EU
Job ID: c1476d2c-883c-43f7-a5fe-73db195e7bcd
```

### データのクエリ/書き込み権限がありません

[移行先ページ](../dlt-ecosystem/destinations/bigquery.md) に記載されているように、「BigQuery データエディタ」を追加してください。

```text
<class 'dlt.destinations.exceptions.DatabaseTransientException'>
403 Access Denied: Table bq-walkthrough:games_data._dlt_loads: User does not have permission to query table bq-walkthrough:games_data._dlt_loads, or perhaps it does not exist in location EU.

Location: EU
Job ID: 299a92a3-7761-45dd-a433-79fdeb0c1a46
```

### 課金機能の欠如 / BigQuery がサンドボックスモードの場合

プロジェクトで課金が有効になっていない場合、`dlt` は BigQuery をサポートしません。
スタックトレースに以下の警告が表示される場合：

```text
<class 'dlt.destinations.exceptions.DatabaseTransientException'>
403 Billing has not been enabled for this project. Enable billing at https://console.cloud.google.com/billing. DML queries are not allowed in the free tier. Set up a billing account to remove this restriction.
```

or

```text
2023-06-08 16:16:26,769|[WARNING]|8096|dlt|load.py|complete_jobs:198|Job for players_games_83b8ac9e98_4_jsonl retried in load 1686233775.932288 with message {"error_result":{"reason":"billingNotEnabled","message":"Billing has not been enabled for this project. Enable billing at https://console.cloud.google.com/billing. Table expiration time must be less than 60 days while in sandbox mode."},"errors":[{"reason":"billingNotEnabled","message":"Billing has not been enabled for this project. Enable billing at https://console.cloud.google.com/billing. Table expiration time must be less than 60 days while in sandbox mode."}],"job_start":"2023-06-08T14:16:26.850000Z","job_end":"2023-06-08T14:16:26.850000Z","job_id":"players_games_83b8ac9e98_4_jsonl"}
```

課金を有効にする必要があります。

