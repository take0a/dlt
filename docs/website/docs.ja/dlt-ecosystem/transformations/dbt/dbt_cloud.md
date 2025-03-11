---
title: Transforming the Data with dbt Cloud
description: Transforming the data loaded by a dlt pipeline with dbt Cloud
keywords: [transform, sql]
---

# dbt クラウドのクライアントとヘルパー関数

:::tip dlt+
dbt モデルを自動的に生成したい場合は、[dlt+](../../../plus/features/transformations/dbt-transformations.md) を参照してください。
:::

## APIクライアント

dbt Cloud Client は、dbt Cloud API (バージョン 2) と対話するように設計された Python クラスです。
ジョブ実行のトリガーやジョブ実行ステータスの取得など、dbt Cloud でさまざまな操作を実行するためのメソッドを提供します。

```py
from dlt.helpers.dbt_cloud import DBTCloudClientV2

# Initialize the client
client = DBTCloudClientV2(api_token="YOUR_API_TOKEN", account_id="YOUR_ACCOUNT_ID")

# Example: Trigger a job run
job_run_id = client.trigger_job_run(job_id=1234, data={"cause": "Triggered via API"})
print(f"Job run triggered successfully. Run ID: {job_run_id}")

# Example: Get run status
run_status = client.get_run_status(run_id=job_run_id)
print(f"Job run status: {run_status['status_humanized']}")
```

## ヘルパー関数

これらの Python 関数は、dbt Cloud API と対話するためのインターフェースを提供します。
これにより、dbt Cloud でのジョブ実行のトリガーと監視のプロセスが簡素化されます。

### `run_dbt_cloud_job()`

この関数は、指定された構成を使用して dbt Cloud でジョブの実行をトリガーします。
さまざまなカスタマイズオプションをサポートし、ジョブのステータスを監視できます。

```py
from dlt.helpers.dbt_cloud import run_dbt_cloud_job

# Trigger a job run with default configuration
status = run_dbt_cloud_job()

# Trigger a job run with additional data
additional_data = {
    "git_sha": "abcd1234",
    "schema_override": "custom_schema",
    # ... other parameters
}
status = run_dbt_cloud_job(job_id=1234, data=additional_data, wait_for_outcome=True)
```

### `get_dbt_cloud_run_status()`

すでにジョブ実行を開始していて、実行 ID を持っている場合は、`get_dbt_cloud_run_status` 関数を使用できます。

この関数は、特定の dbt Cloud ジョブ実行に関する完全な情報を取得します。
実行が完了するまで待機するオプションもサポートしています。

```py
from dlt.helpers.dbt_cloud import get_dbt_cloud_run_status

# Retrieve status for a specific run
status = get_dbt_cloud_run_status(run_id=1234, wait_for_outcome=True)
```

## 資格情報を設定する

### secrets.toml

dlt をローカルで使用する場合は、`.dlt/secrets.toml` メソッドを使用して資格情報を設定することをお勧めします。

`dlt init` コマンドを使用した場合、`.dlt` フォルダーはすでに作成されています。
それ以外の場合は、作業ディレクトリに `.dlt` フォルダーを作成し、その中に `secrets.toml` ファイルを作成します。

ここには、アクセス トークンなどの機密情報が安全に保存されます。このファイルを安全に保管してください。

dbt Cloud API認証には次の形式を使用します:

```toml
[dbt_cloud]
api_token = "set me up!" # required for authentication
account_id = "set me up!" # required for both helper functions
job_id = "set me up!" # optional only for the run_dbt_cloud_job function (you can pass this explicitly as an argument to the function)
run_id = "set me up!" # optional for the get_dbt_cloud_run_status function (you can pass this explicitly as an argument to the function)
```

### 環境変数

dlt は環境からの資格情報の読み取りをサポートします。

dlt が環境変数からこれを読み取ろうとする場合、異なる命名規則が使用されます。

環境変数の場合、すべての名前は大文字で表記され、セクションは二重のアンダースコア「__」で区切られます。

上記の機密情報を環境変数に置く必要がある場合:

```sh
DBT_CLOUD__API_TOKEN
DBT_CLOUD__ACCOUNT_ID
DBT_CLOUD__JOB_ID
```

詳細については、[資格情報](../../../general-usage/credentials)のドキュメントをお読みください。
