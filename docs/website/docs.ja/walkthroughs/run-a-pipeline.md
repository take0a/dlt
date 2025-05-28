---
title: Run a pipeline
description: How to run a pipeline
keywords: [how to, run a pipeline]
---

# パイプラインを実行する

以下の手順に従って、パイプラインスクリプトを実行し、読み込まれたデータとテーブルを確認し、パイプラインの状態を検査し、最も一般的な問題をトレースして対処します。

## 1. パイプラインスクリプトの作成と実行

[新しいパイプラインを作成](create-a-pipeline) または [ソースを追加して検証](add-a-verified-source) したら、それを使用してデータをロードします。
[chess.com](https://www.chess.com) API からデータをロードする以下の例のようなパイプラインスクリプトを作成（または[カスタマイズ](add-a-verified-source#3-customize-or-write-a-pipeline-script)）する必要があります。

```py
import dlt

if __name__ == "__main__":
    pipeline = dlt.pipeline(pipeline_name="chess_pipeline", destination='duckdb', dataset_name="games_data")
    # get data for a few famous players
    data = chess_source(['magnuscarlsen', 'rpragchess'], start_month="2022/11", end_month="2022/12")
    load_info = pipeline.run(data)
```

`run` メソッドは、チェス API からデータを[抽出](../reference/explainers/how-dlt-works.md#extract)し、テーブルに[正規化](../reference/explainers/how-dlt-works.md#normalize)した後、1つまたは複数のロードパッケージの形式で `duckdb` に[ロード](../reference/explainers/how-dlt-works.md#load)します。
`run` メソッドは `load_info` オブジェクトを返します。このオブジェクトを出力すると、パイプライン名とデータセット名、ロードパッケージの ID、そしてオプションで失敗したジョブの情報が表示されます。スクリプトに次の行を追加してください。

```py
print(load_info)
```

これがプリントされて:

```text
Pipeline chess_pipeline completed in 1.80 seconds
1 load package(s) were loaded to destination duckdb and into dataset games_data
The duckdb destination used duckdb:////home/user-name/src/dlt_tests/dlt-cmd-test-3/chess_pipeline.duckdb location to store data
Load package 1679931001.985323 is COMPLETED and contains no failed jobs
```

## 2. 読み込み中の進行状況を確認する

チェスのゲームデータを1年間分読み込みたいが、時間がかかるとします。パイプラインの動作を確認するには、プログレスバーやコンソールログを有効にできます。
Pythonのプログレスバーライブラリ、Pythonロガー、またはテキストコンソールのほとんどをサポートしています。
例として、スクリプトを変更して1年間分のチェスのゲームデータを取得してみましょう。

```py
data = chess_source(['magnuscarlsen', 'rpragchess'], start_month="2021/11", end_month="2022/12")
```

[enlighten](https://github.com/Rockhopper-Technologies/enlighten)をインストールします。Enlightenは、ログメッセージと組み合わせることができるプログレスバーを表示します:

```sh
pip install enlighten
```

`PROGRESS` 環境変数をライブラリ名に設定してスクリプトを実行します:

```sh
PROGRESS=enlighten python chess_pipeline.py
```

他に使用できるライブラリとしては、[tqdm](https://github.com/tqdm/tqdm)、[alive_progress](https://github.com/rsalmei/alive-progress) などがあります。
定期的にコンソールに進行状況を出力するには、名前を `log` に設定します:

```sh
PROGRESS=log python chess_pipeline.py
```

[コード内でプログレス バーを自由に構成できます](../general-usage/pipeline.md#display-the-loading-progress)。

## 3. データとテーブルを確認する

スクリプトと同じフォルダから次のコマンドを実行すると、生成されたテーブルとデータを簡単に確認したり、どのテーブルに何行がロードされたかを確認したり、SQLクエリを実行したりできます。

```sh
dlt pipeline chess_pipeline show
```

これにより、Streamlit アプリが起動し、ブラウザで開くことができます:

```text
Found pipeline chess_pipeline in /home/user-name/.dlt/pipelines

Collecting usage statistics. To deactivate, set browser.gatherUsageStats to False.


  You can now view your Streamlit app in your browser.

  Network URL: http://192.168.131.137:8501
  External URL: http://46.142.217.118:8501
```

## 4. ロードプロセスの検査

`dlt` は、**ロードパッケージ** の形式でデータをロードします。各パッケージには、特定のテーブルのデータを含む複数のジョブが含まれています。
パッケージは **load_id** で識別されます。このIDは上記の出力で確認できます。また、次のコマンドを実行して取得することもできます:

```sh
dlt pipeline chess_pipeline info
```

パッケージを検査し、ジョブのリストを取得し、失敗したジョブの場合は関連するエラー メッセージを取得できます。

- 最新のロード パッケージ情報を参照してください:
  ```sh
  dlt pipeline chess_pipeline load-package
  ```
- 指定されたロード ID のパッケージ情報を表示します。
  ```sh
  dlt pipeline chess_pipeline load-package 1679931001.985323
  ```
- また、パッケージで導入されたスキーマの変更も参照してください。
  ```sh
  dlt pipeline -v chess_pipeline load-package
  ```

`dlt` は最新のデータロードのトレースを保存します。
このトレースには、パイプライン処理ステップ（`extract`、`normalize`、`load`）に関する情報が含まれます。
また、最新の `load_info` も表示されます。

```sh
dlt pipeline chess_pipeline trace
```

パイプラインスクリプトでこれらの情報すべてにアクセスし、`load_info` を保存して宛先までトレースするなどできます。
詳細については、[本番環境での実行](../running-in-production/running.md#inspect-and-save-the-load-info-and-trace)を参照してください。

## ノートブックで dlt を実行する

### Colab
他の依存関係と同様に、`dlt` をインストールする必要があります:

```sh
!pip install dlt
```

**Secrets** サイドバーを使用してシークレットを設定できます。
`secrets.toml` という名前の変数を作成し、`.dlt` フォルダにある **toml** ファイルの内容をそこに貼り付けるだけです。
`config.toml` 変数もサポートしています。

:::note
`dlt` はシークレットを自動的にリロードしません。
上記の変数の内容を追加/変更した場合は、Colab オプションでインタープリターを再起動してください。
:::


## トラブルシューティング

何か問題が発生した場合はどうなりますか？
ほとんどの場合、`dlt` `run` コマンドは例外を発生させます。
私たちは、例外メッセージを分かりやすくするために多大な努力を払っています。
それらを読むことが、問題解決の第一歩です。
ご不明な点がございましたら、[こちら](https://github.com/dlt-hub/dlt/issues/new) からお知らせください。

### シークレットまたは設定値が不足しています

最もよく発生する例外は以下のようになります。
ここでは、PostgreSQLにデータをロードするために「chess_pipeline.py」スクリプトを変更していますが、パスワードは提供していません。

```sh
CREDENTIALS="postgres://loader@localhost:5432/dlt_data" python chess_pipeline.py
...
dlt.common.configuration.exceptions.ConfigFieldMissingException: Following fields are missing: ['password'] in configuration with spec PostgresCredentials
    for field "password" config providers and keys were tried in the following order:
        In Environment Variables key CHESS_PIPELINE__DESTINATION__POSTGRES__CREDENTIALS__PASSWORD was not found.
        In Environment Variables key CHESS_PIPELINE__DESTINATION__CREDENTIALS__PASSWORD was not found.
        In Environment Variables key CHESS_PIPELINE__CREDENTIALS__PASSWORD was not found.
        In secrets.toml key chess_games.destination.postgres.credentials.password was not found.
        In secrets.toml key chess_games.destination.credentials.password was not found.
        In secrets.toml key chess_games.credentials.password was not found.
        In Environment Variables key DESTINATION__POSTGRES__CREDENTIALS__PASSWORD was not found.
        In Environment Variables key DESTINATION__CREDENTIALS__PASSWORD was not found.
        In Environment Variables key CREDENTIALS__PASSWORD was not found.
        In secrets.toml key destination.postgres.credentials.password was not found.
        In secrets.toml key destination.credentials.password was not found.
        In secrets.toml key credentials.password was not found.
Please refer to https://dlthub.com/docs/general-usage/credentials/ for more information
```

この例外は何を示していますか？

1. `password` フィールドがありません（「次のフィールドがありません: \['password'\]」）。
1. `dlt` は `secrets.toml` と環境変数でパスワードを検索しようとしました。
1. `dlt` は、より正確なものからより一般的なものまで、パスワードを保存できる複数の場所またはキーを試しました。

How to fix that?

最も簡単な方法は、例外メッセージの最後の行を確認することです:

`In secrets.toml key credentials.password was not found.`

提案されたキーを使用して、`secrets.toml` に `password` を追加するだけです:

```toml
credentials.password="loader"
```

> 💡 スクリプトは、保存されているフォルダから実行してください。
> 例えば、`python chess_demo/chess.py` は `chess_demo` フォルダからスクリプトを実行しますが、現在の作業ディレクトリは上記のフォルダです。
> これにより、`dlt` が `chess_demo/.dlt/secrets.toml` を見つけて認証情報を入力するのを防ぐことができます。

### APIまたはデータベース接続の失敗、およびその他の例外

`dlt` は、特定のステップの実行中に発生した問題を通知するために、`PipelineStepFailed` 例外を発生させます。
これらの例外はコードでキャッチできます。

```py
from dlt.pipeline.exceptions import PipelineStepFailed

try:
    pipeline.run(data)
except PipelineStepFailed as step_failed:
    print(f"We failed at step: {step_failed.step} with step info {step_failed.step_info}")
    raise
```

または、`trace` コマンドを使用して最後の例外を確認してください。ここでは、PostgreSQL のパスワードを間違って入力しました。

```sh
dlt pipeline chess_pipeline trace
```

```text
Found pipeline chess_pipeline in /home/user-name/.dlt/pipelines
Run started at 2023-03-28T09:13:56.277016+00:00 and FAILED in 0.01 seconds with 1 steps.
Step run FAILED in 0.01 seconds.
Failed due to: connection to server at "localhost" (127.0.0.1), port 5432 failed: FATAL:  password authentication failed for user "loader"
```

### ロードパッケージ内の失敗したジョブ

まれに、ロードパッケージ内の一部のジョブが失敗し、`dlt` がプロセスを再試行してもロードできない場合があります。
その場合、ジョブは失敗としてマークされ、追加情報が提供されます。
なお、([特に設定されていない場合](../running-in-production//running.md#failed-jobs))、`dlt` は**失敗したジョブに対して例外を発生し、パッケージを中止します**。
中止されたパッケージは再試行できません。

```text
Step run COMPLETED in 14.21 seconds.
Pipeline chess_pipeline completed in 35.21 seconds
1 load package(s) were loaded to destination dummy and into dataset None
The dummy destination used /dev/null location to store data
Load package 1679996953.776288 is COMPLETED and contains 4 FAILED job(s)!
```

次は何をすればいいですか？

次のコマンドでさらに詳しく調べてください:

```sh
dlt pipeline chess_pipeline failed-jobs
```

次の出力を得て:

```text
Found pipeline chess_pipeline in /home/user-name/.dlt/pipelines
Checking failed jobs in load id '1679996953.776288'
JOB: players_games.80eb41650c.0.jsonl(players_games)
JOB file type: jsonl
JOB file path: /home/user-name/.dlt/pipelines/chess_pipeline/load/loaded/1679996953.776288/failed_jobs/players_games.80eb41650c.0.jsonl
a random fail occurred
```

 `a random fail occurred`（コンソール上で赤字で表示）は、出力先からのエラーメッセージです。
何が問題だったかが分かります。

ジョブが失敗した原因として最も可能性が高いのは、**ジョブファイル内のデータ**です。
**ジョブファイルパス**を使用して、ファイルの内容を確認できます。

## さらに詳しい情報

- [本番環境向けにスクリプトを強化](../running-in-production/running.md) することで、アラート、再試行、ログ記録を簡単に追加でき、問題発生時に的確な情報を得ることができます。
- [このパイプラインを GitHub Actions でデプロイ](deploy-a-pipeline/deploy-with-github-actions) することで、パイプラインスクリプトがスケジュールに従って自動的に実行されるようになります。

