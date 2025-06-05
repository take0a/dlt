---
title: Staging
description: Configure an S3 or GCS bucket for staging before copying into the destination
keywords: [staging, destination]
---

# ステージング

ステージングの目的は、データをデータベースエンジンに近づけることで、宛先（最終）データセットの変更をより迅速かつエラーなく行うことです。
`dlt` は、要求に応じて2つのステージング領域を作成します。

1. **ステージングデータセット**。[マージロードと置換ロード](../general-usage/incremental-loading.md#merge-incremental-loading)で重複排除と宛先とのデータのマージに使用されます。
2. **ステージングストレージ**。通常はS3/GCPバケットで、宛先にロードされる前に[ローダーファイル](file-formats/)がコピーされます。

## ステージングデータセット

`dlt` は、ロードされたリソースの書き込み処理でステージングデータセットが必要な場合に作成します。
メインデータセットとまったく同じように、必要なテーブルを作成して移行します。
ステージングテーブルのデータは、ロードステップの開始時に、そのステップに参加するテーブルに対してのみ切り捨てられます。
このようなステージングデータセットの名前は、`dlt.pipeline` に渡されるデータセットと同じで、名前に `_staging` サフィックスが付きます。
また、独自のステージングデータセットパターンを指定したり、構成されたすべてのデータセットで同一の固定名を使用したりすることもできます。

```toml
[destination.postgres]
staging_dataset_name_layout="staging_%s"
```

上記のエントリは、パターンを `staging_` プレフィックスに切り替えます。たとえば、**github_data** という名前のデータセットの場合、`dlt` は **staging_github_data** を作成します。

静的なステージングデータセット名を設定するには、次のようにします（宛先ファクトリーを使用します）。

```py
import dlt

dest_ = dlt.destinations.postgres(staging_dataset_name_layout="_dlt_staging")
```

`dest_` を宛先として使用するすべてのパイプラインは、**staging_dataset** を使用してステージングテーブルを保存します。
パイプラインが互いのテーブルを上書きしていないことを確認してください。

### ステージングデータセットを自動的にクリーンアップします

`dlt` は、ロード終了時にステージングデータセット内のテーブルを切り捨てません。
ロード後に残るデータには抽出されたすべてのデータが含まれており、デバッグに役立つ場合があります。
切り捨てる場合は、`config.toml` に次の行を追加してください。

```toml
[load]
truncate_staging_dataset=true
```

## ステージングストレージ

`dlt` は、最初の宛先 (`staging`) がローカルファイルシステムからリモートストレージへのファイルのアップロードを担当する、宛先の連鎖を可能にします。
その後、2 番目の宛先に対して、通常はリモートストレージから宛先にファイルをコピーする後続ジョブを生成します。

現在、ステージングとして使用できる宛先は [ファイルシステム](destinations/filesystem.md) のみです。
以下の宛先がリモートファイルをコピーできます。

1. [Azure Synapse](destinations/synapse#staging-support)
2. [Athena](destinations/athena#staging-support)
3. [Bigquery](destinations/bigquery.md#staging-support)
4. [Dremio](destinations/dremio#staging-support)
5. [Redshift](destinations/redshift.md#staging-support)
6. [Snowflake](destinations/snowflake.md#staging-support)

### 使用方法

基本的には、2つの出力先を設定し、それらを `dlt.pipeline` に渡す必要があります。
以下では、[Parquet](./file-formats/parquet) ファイルを使用して `filesystem` ステージングを使用し、`redshift` 出力先にロードします。

1. **S3 バケットとファイルシステムのステージングを設定します。**

    [ファイルシステムの保存先に関するドキュメント](destinations/filesystem.md)のガイドに従ってください。
    ステージングをスタンドアロンの保存先としてテストし、ファイルが目的の場所に確実に保存されることを確認してください。
    これで、`secrets.toml` に、`filesystem` 設定が適切に保存されているはずです。

    ```toml
    [destination.filesystem]
    bucket_url = "s3://[your_bucket_name]" # replace with your bucket name

    [destination.filesystem.credentials]
    aws_access_key_id = "please set me up!" # copy the access key here
    aws_secret_access_key = "please set me up!" # copy the secret access key here
    ```

2. **Redshift の宛先を設定します。**

    [Redshift の宛先ドキュメント](destinations/redshift.md)のガイドに従ってください。`secrets.toml` に以下を追加してください。

    ```toml
    # Keep it at the top of your TOML file, before any section starts
    destination.redshift.credentials="redshift://loader:<password>@localhost/dlt_data?connect_timeout=15"
    ```

3. **Redshift クラスターがステージングバケットにアクセスできるようにします。**

    デフォルトでは、`dlt` は `filesystem` に設定された認証情報を `Redshift` COPY コマンドに転送します。
    これで問題がなければ、次のステップに進みます。

4. **ステージングを宛先にチェーンし、Parquet ファイル形式をリクエストします。**

    `dlt.pipeline` に `staging` 引数を渡します。
    これは宛先の `argument` と同様に機能します。

    ```py
    # Create a dlt pipeline that will load
    # chess player data to the redshift destination
    # via staging on S3
    pipeline = dlt.pipeline(
        pipeline_name='chess_pipeline',
        destination='redshift',
        staging='filesystem', # add this to activate the staging location
        dataset_name='player_data'
    )
    ```

    `dlt` はステージングファイルに適したローダーファイル形式を自動的に選択します。以下では、Parquet ファイル形式を明示的に指定しています（方法を示すため）。

    ```py
    info = pipeline.run(chess_source(), loader_file_format="parquet")
    ```

5. **パイプラインスクリプトを実行します。**

    パイプラインスクリプトを通常どおり実行します。

:::tip
`dlt` は、ロードが完了した後、ロードされたファイルをステージング ストレージから削除しませんが、以前にロードされたファイルを切り捨てることに注意してください。
:::

### ステージングファイルの切り捨てを防ぐ方法

`dlt` は、ステージングストレージにデータをロードする前に、以前にロードしたファイルを切り捨てます。
これを防止し、ロードされたファイルの履歴全体を保持するには、次のパラメータを使用します。

```toml
[destination.redshift]
truncate_tables_on_staging_destination_before_load=false
```

:::caution
[Athena](destinations/athena#staging-support) 宛先は、`replace` merge_disposition を持つ非アイスバーグテーブルのみを切​​り捨てます。
したがって、パラメータ `truncate_tables_on_staging_destination_before_load` は、これらのテーブルに対応するファイルの切り捨てのみを制御します。
:::

