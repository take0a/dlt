---
title: Running
description: Running a dlt pipeline in production
keywords: [running, production, tips]
---

# 実行

本番環境でパイプラインを実行する際は、スクリプトにいくつか追加することを検討してください。ここでは、以下のスクリプトを出発点として使用します。

```py
import dlt

if __name__ == "__main__":
    pipeline = dlt.pipeline(pipeline_name="chess_pipeline", destination='duckdb', dataset_name="games_data")
    # get data for a few famous players
    data = chess_source(['magnuscarlsen', 'vincentkeymer', 'dommarajugukesh', 'rpragchess'], start_month="2022/11", end_month="2022/12")
    load_info = pipeline.run(data)
```

## ロード情報とトレースを確認し、保存します。

`load_info` には、最近ロードされたデータに関する有用な情報が多数含まれています。
パイプラインとデータセット名、出力先情報（シークレットなし）、ロードされたパッケージのリストが含まれます。
パッケージ情報には、状態（`COMPLETED/PROCESSED`）、すべてのジョブのリスト（ステータス、ファイルサイズ、タイプを含む）、そして失敗したジョブの場合は出力先からのエラーメッセージが含まれます。

```py
    # see when load was started
    print(load_info.started_at)
    # print the information on the first load package and all jobs inside
    print(load_info.load_packages[0])
    # print the information on the first completed job in the first load package
    print(load_info.load_packages[0].jobs["completed_jobs"][0])
```

`load_info` は以下のように宛先にロードされる場合もあります:

```py
    # we reuse the pipeline instance below and load to the same dataset as data
    pipeline.run([load_info], table_name="_load_info")
```

パイプラインからランタイムトレースを取得することもできます。これには、`extract`、`normalize`、`load` ステップのタイミング情報に加え、すべての設定値とシークレット値とその取得元に関する詳細情報が含まれます。
以下のようにトレース情報を表示およびロードできます。コードエディタを使用して、`trace` オブジェクトをさらに詳しく調べてください。
`normalize` ステップ情報には、正規化されてロードされたデータのテーブルごとの行数が含まれます。

```py
    # print human-friendly trace information
    print(pipeline.last_trace)
    # save trace to destination, sensitive data will be removed
    pipeline.run([pipeline.last_trace], table_name="_trace")
```

You can also access the last `extract`, `normalize`, and `load` infos directly:

```py
    # print human-friendly extract information
    print(pipeline.last_trace.last_extract_info)
    # print human-friendly normalization information
    print(pipeline.last_trace.last_normalize_info)
    # access row counts dictionary of normalize info
    print(pipeline.last_trace.last_normalize_info.row_counts)
    # print human-friendly load information
    print(pipeline.last_trace.last_load_info)
```

[コマンドライン](../reference/command-line-interface.md#dlt-pipeline)を使用してパイプラインを検査できることに注意してください。

### スキーマの変更を検査、保存、アラートする

パッケージ情報では、パッケージのロード中に宛先に作成されたすべてのテーブルと列のリストも確認できます。
以下のコードは、すべてのテーブルとスキーマを表示します。
これらのオブジェクトは型付き辞書であることに注意してください。コードエディタを使用して詳細を確認してください。

```py
    # print all the new tables/columns in
    for package in load_info.load_packages:
        for table_name, table in package.schema_update.items():
            print(f"Table {table_name}: {table.get('description')}")
            for column_name, column in table["columns"].items():
                print(f"\tcolumn {column_name}: {column['data_type']}")
```

新しいテーブルと列スキーマのみを出力先に保存できます。
上記の `load_info` を保存するコードは、このデータも保存することに注意してください。

```py
    # save just the new tables
    table_updates = [p.asdict()["tables"] for p in load_info.load_packages]
    pipeline.run(table_updates, table_name="_new_tables")
```

## 残されるデータ

デフォルトでは、`dlt` はロードされたパッケージをそのまま残します。これにより、ロード後に完全にクエリと検査を実行できます。
この動作は、正常に完了したジョブがロードされたパッケージから削除されるように変更できます。
その場合、パイプラインが正常に動作するために、最小限のデータのみが残されます。
`config.toml` では次のようになります:

```toml
[load]
delete_completed_jobs=true
```

また、デフォルトでは、`dlt` は [ステージングデータセット](../dlt-ecosystem/staging.md#staging-dataset) にデータを残します。これは、マージロードと置換ロードで重複排除に使用されます。これをクリアするには、`config.toml` に次の行を追加します。

```toml
[load]
truncate_staging_dataset=true
```

## Slack を使ったメッセージ送信

`dlt` は、Slack メッセージの送信に関する基本的なサポートを提供します。Slack の受信フックは、[secrets.toml または環境変数](../general-usage/credentials/setup) で設定できます。
**Slack の受信フックはシークレットとして扱われ、GitHub リポジトリにプッシュされるとすぐにブロックされます** のでご注意ください。`secrets.toml` では、次のようになります。

```toml
[runtime]
slack_incoming_hook="https://hooks.slack.com/services/T04DHMAF13Q/B04E7B1MQ1H/TDHEI123WUEE"
```

or

```sh
RUNTIME__SLACK_INCOMING_HOOK="https://hooks.slack.com/services/T04DHMAF13Q/B04E7B1MQ1H/TDHEI123WUEE"
```

その後、設定されたフックはパイプラインオブジェクトを介して利用できるようになります。
Slackメッセージを送信するための便利なメソッドも提供しています:

```py
from dlt.common.runtime.slack import send_slack_message

send_slack_message(pipeline.runtime_config.slack_incoming_hook, message)

```

## Sentry トレースを有効にする

例外とランタイムのトレースを Sentry 経由で有効にできます (../running-in-production/tracing.md)。

## ログレベルと形式を設定する

ログレベルを設定し、ログをJSON形式に切り替えることができます。

```toml
[runtime]
log_level="INFO"
log_format="JSON"
```

`log_level` は [Python 標準のログレベル名](https://docs.python.org/3/library/logging.html#logging-levels) を受け入れます。

- デフォルトのログレベルは `WARNING` です。
- `INFO` ログレベルは、本番環境での問題を診断する際に役立ちます。
- `CRITICAL` はログを無効にします。
- `DEBUG` は本番環境では使用しないでください。

`log_format` は以下を受け入れます。

- `json` は JSON 形式でログを取得します。
- [Python 標準のログ形式指定子](https://docs.python.org/3/library/logging.html#logrecord-attributes)。

他の設定と同様に、TOML ファイルの代わりに環境変数を使用できます。

- `RUNTIME__LOG_LEVEL` はログレベルを設定します。
- `LOG_FORMAT` はログ形式を設定します。

`dlt` は **dlt** という名前のロガーにログを記録します。`dlt` ロガーは通常の Python ロガーを使用するため、必要に応じてハンドラーを設定できます。

例えば、ファイルにログを出力するには、次のようにします。

```py
import logging

# Create a logger
logger = logging.getLogger('dlt')

# Set the log level
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler('dlt.log')

# Add the handler to the logger
logger.addHandler(handler)
```
You can intercept logs by using [loguru](https://loguru.readthedocs.io/en/stable/api/logger.html). To do so, follow the instructions below:

```py
import logging
import sys

import dlt
from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):

    @loguru_logger.catch(default=True, onerror=lambda _: sys.exit(1))
    def emit(self, record):
        # Get the corresponding Loguru level if it exists.
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the caller from where the logged message originated.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logger_dlt = logging.getLogger("dlt")
logger_dlt.addHandler(InterceptHandler())

loguru_logger.add("dlt_loguru.log")
```

## 例外、失敗したジョブを処理し、パイプラインを再試行します。

パイプラインのいずれかのステップが失敗すると、`PipelineStepFailed` 型の例外が発生します。
この例外には、パイプラインのステップ名、パイプラインオブジェクト自体、およびステップ情報（`LoadInfo`）が含まれます。これは、問題が発生した場所に関する一般的な情報を提供します。
ほとんどの場合、標準的な Python 例外チェーン (`__context__`) を使用して、原因となっている例外を取得できます。また、そうすべきです。

`__context__` には 2 種類の例外があります。

1. **ターミナル例外** は、介入なしにはエラー状態が回復しないため、**再試行すべきではない** 例外です。
例としては、設定値やシークレット値の不足、ほとんどの `40x` HTTP エラー、いくつかのデータベースエラー（テーブルなどのリレーションの不足など）などが挙げられます。各出力先には、`dlt` が保持しようとするターミナル例外のセットが独自に存在します。
2. **一時例外** は、再試行される可能性のある例外です。

以下のコードは、ある例外タイプと別の例外タイプを区別しています。この処理を自動的に行う再試行戦略ヘルパーが提供されていることに注意してください。

```py
from dlt.common.exceptions import TerminalException

def check(ex: Exception):
    if isinstance(ex, TerminalException) or (ex.__context__ is not None and isinstance(ex.__context__, TerminalException)):
        return False
    return True
```

### 失敗したジョブ

パッケージ内のジョブが**ターミナルで失敗**した場合、そのジョブは `failed_jobs` フォルダに移動さ​​れ、そのステータスが割り当てられます。
デフォルトでは**例外が発生し**、最初の失敗したジョブで、ロードパッケージは `LoadClientJobFailed`（ターミナル例外）で中止されます。
このようなパッケージは完了しますが、そのロードIDは `_dlt_loads` テーブルに追加されません。
並行して実行されていたすべてのジョブは、例外が発生する前に完了しています。
dlt 状態が存在する場合、`dlt` からは参照できません。
この動作を無効にする `config.toml` の例を以下に示します。

```toml
# I hope you know what you are doing by setting this to false
load.raise_on_failed_jobs=false
```

失敗したジョブで dlt がターミナル例外を発生させないようにしたい場合は、次のようにロード情報をチェックして失敗したジョブを手動で確認し、例外を発生させることができます:

```py
# returns True if there are failed jobs in any of the load packages
print(load_info.has_failed_jobs)
# raises terminal exception if there are any failed jobs
load_info.raise_on_failed_jobs()
```

:::caution
特定の書き込み処理は、データを不可逆的に変更することに注意してください。
1. デフォルトの `truncate-and-insert` [戦略](../general-usage/full-loading.md) を使用した `replace` 書き込み処理は、ロード前にテーブルを切り詰めます。
2. `merge` 書き込み処理は、ステージングデータセットのテーブルを宛先データセットにマージします。これは、このテーブル（およびネストされたテーブル）のすべてのデータがロードされた場合にのみ実行されます。

部分的にロードされたパッケージに対処するには、次の操作を実行できます。
1. 一時的なエラーが発生した場合は、ロード手順を再試行します。
2. ステージングデータセットで replace 戦略を使用し、テーブル（およびすべてのネストされたテーブル）のデータが完全にロードされ、アトミック操作（可能な場合）が実行できた場合にのみ replace を実行します。
3. "append" 書き込み処理のみを使用します。ロードパッケージが失敗した場合は、`_dlt_load_id` を使用して未処理のデータをすべて削除できます。
4. 「ステージング追加」を使用します (主キーとマージ キーを定義せずに `merge` 配置)。

:::


### `run` メソッドの内部動作

パイプラインステップに再試行を追加する前に、`run` メソッドの実際の動作を確認してください。

1. `run` メソッドはまず `sync_destination` メソッドを使用して、パイプラインの状態とスキーマを同期先と同期します。
当然のことながら、この時点では同期先への接続が確立されています（接続に失敗して再試行される場合もあります）。
2. 次に、前回の実行で取得したデータが完全に処理されていることを確認します。処理されていない場合、`run` メソッドは正規化し、保留中のデータ項目をロードして **終了** します。
3. 保留中のデータがない場合、`data` 引数から新しいデータが抽出され、正規化されてロードされます。

### 再試行ヘルパーと `tenacity`

デフォルトでは、`dlt` はパイプラインのどのステップも再試行しません。
これは、同梱のヘルパーと [tenacity](https://tenacity.readthedocs.io/en/latest/) ライブラリによって処理されます。
以下のスニペットは、`retry_load` 戦略を使用して `load` ステージを再試行し、他のステップ (`extract`、`normalize`) とターミナル例外に対してバックオフまたは例外の再発生を定義します。

```py
from tenacity import stop_after_attempt, retry_if_exception, Retrying, retry, wait_exponential
from dlt.common.runtime.slack import send_slack_message
from dlt.pipeline.helpers import retry_load

if __name__ == "__main__":
    pipeline = dlt.pipeline(pipeline_name="chess_pipeline", destination='duckdb', dataset_name="games_data")
    # get data for a few famous players
    data = chess_source(['magnuscarlsen', 'rpragchess'], start_month="2022/11", end_month="2022/12")
    try:

        for attempt in Retrying(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1.5, min=4, max=10), retry=retry_if_exception(retry_load()), reraise=True):
            with attempt:
                load_info = pipeline.run(data)
                send_slack_message(pipeline.runtime_config.slack_incoming_hook, "HOORAY 😄")
    except Exception:
        # we get here after all the retries
        send_slack_message(pipeline.runtime_config.slack_incoming_hook, "BOOO 🤯")
        raise
```

`tenacity` を使って関数をデコレートすることもできます。この例では、`extract` でさらに再試行を行っています:

```py
if __name__ == "__main__":
    pipeline = dlt.pipeline(pipeline_name="chess_pipeline", destination='duckdb', dataset_name="games_data")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1.5, min=4, max=10), retry=retry_if_exception(retry_load(("extract", "load"))), reraise=True)
    def load():
        data = chess_source(['magnuscarlsen', 'vincentkeymer', 'dommarajugukesh', 'rpragchess'], start_month="2022/11", end_month="2022/12")
        return pipeline.run(data)

    load_info = load()
```

