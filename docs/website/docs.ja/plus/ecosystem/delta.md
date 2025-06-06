---
title: "Destination: Delta"
description: Delta destination
keywords: [delta, delta lake]
---

# Delta

Delta の保存先は、dlt の [ファイルシステム保存先](../../dlt-ecosystem/destinations/filesystem.md) に基づいています。
ファイルシステム保存先のすべての設定オプションも同様に設定できます。

:::caution
dlt+ は内部的に [deltalake ライブラリ](https://pypi.org/project/deltalake/) を使用して Delta テーブルを書き込みます。
1 つのテーブルに大量のデータをロードする場合、基盤となる Rust 実装が大量のメモリを消費することに注意してください。
これは既知の問題であり、メンテナーは積極的に解決に取り組んでいます。
進捗状況は [こちら](https://github.com/delta-io/delta-rs/pull/2289) で確認できます。
問題が解決するまでは、複数の小さな増分パイプライン実行を行うことで、メモリ消費を軽減できます。
:::

## セットアップ

必要な依存関係がインストールされていることを確認してください:

```sh
pip install deltalake
pip install pyarrow>=2.0.18
```

次のコマンドを使用して、現在の作業ディレクトリ内の dlt+ プロジェクトを初期化します:

```sh
# replace sql_database with the source of your choice
dlt project init sql_database delta
```

これにより、`dlt.yml` に Delta 宛先が作成され、宛先を設定できます:

```yaml
destinations:
  delta_destination:
    type: delta
    bucket_url: "s3://your_bucket" # replace with bucket url
```

資格情報は `secrets.toml` で定義できます:

<Tabs
  groupId="filesystem-type"
  defaultValue="aws"
  values={[
    {"label": "AWS S3", "value": "aws"},
    {"label": "GCS/GDrive", "value": "gcp"},
    {"label": "Azure", "value": "azure"},
    {"label": "SFTP", "value": "sftp"},
]}>

<TabItem value="aws">

```toml
# secrets.toml
[destination.delta.credentials]
aws_access_key_id="Please set me up!"
aws_secret_access_key="Please set me up!"
```
</TabItem>

<TabItem value="azure">

```toml
# secrets.toml
[destination.delta.credentials]
azure_storage_account_name="Please set me up!"
azure_storage_account_key="Please set me up!"
```
</TabItem>

<TabItem value="gcp">

:::caution
Google Cloud Storage では、[サービス アカウント](../../dlt-ecosystem/destinations/bigquery#setup-guide) と [アプリケーションのデフォルト認証情報](../../dlt-ecosystem/destinations/bigquery#using-default-credentials) の認証方法のみがサポートされています。
:::

```toml
# secrets.toml
[destination.delta.credentials]
client_email="Please set me up!"
private_key="Please set me up!"
project_id="Please set me up!"
```
</TabItem>

<TabItem value="sftp">

各認証方法のSFTP認証情報の設定方法については、[SFTPセクション](../../dlt-ecosystem/destinations/filesystem#sftp)を参照してください。
たとえば、キーベース認証の場合、ソースを次のように設定できます。

```toml
# secrets.toml
[destination.delta.credentials]
sftp_username = "foo"
sftp_key_filename = "/path/to/id_rsa"     # Replace with the path to your private key file
sftp_key_passphrase = "your_passphrase"   # Optional: passphrase for your private key
```
</TabItem>

</Tabs>


Delta の宛先は、Python では次のように定義することもできます:

```py
pipeline = dlt.pipeline("loads_delta", destination="delta")
```

## 書き込み処理

Delta 出力先は、書き込み処理を次のように処理します。
- `append` - 該当するテーブルに属するファイルがデータセットフォルダに追加されます。
- `replace` - 該当するテーブルに属するすべてのファイルがデータセットフォルダから削除され、現在のファイルセットが追加されます。
- `merge` - `upsert` [マージ戦略](../../general-usage/merge-loading.md#upsert-strategy) でのみ使用できます。

:::caution
Delta 宛先の `upsert` マージ戦略は **実験的** です。
:::

`merge` 書き込み処理は、ソース/リソース レベルで次のように構成できます:

<Tabs values={[{"label": "dlt.yml", "value": "yaml"}, {"label": "Python", "value": "python"}]}  groupId="language" defaultValue="yaml">
  <TabItem value="yaml">

```yaml
sources:
  my_source:
    type: sources.my_source
    with_args:
      write_disposition:
        disposition: merge
        strategy: upsert
```
  </TabItem>
  <TabItem value="python">

```py
@dlt.resource(
    primary_key="id",  # merge_key also works; primary_key and merge_key may be used together
    write_disposition={"disposition": "merge", "strategy": "upsert"},
)
def my_resource():
    yield [
        {"id": 1, "foo": "foo"},
        {"id": 2, "foo": "bar"}
    ]
...

pipeline = dlt.pipeline("loads_delta", destination="delta")

```
</TabItem>
</Tabs>

または `pipeline.run` レベルで: <!-- can this also be defined in the yaml??-->

```py
pipeline.run(write_disposition={"disposition": "merge", "strategy": "upsert"})
```

## パーティショニング

デルタテーブルは、ソース/リソースレベルで1つ以上のパーティション列ヒントを指定することにより、パーティション分割（[Hive スタイルのパーティショニング](https://delta.io/blog/pros-cons-hive-style-partionining/)を使用）できます。

<Tabs values={[{"label": "dlt.yml", "value": "yaml"}, {"label": "Python", "value": "python"}]}  groupId="language" defaultValue="yaml">
  <TabItem value="yaml">

  ```yaml
  sources:
    my_source:
      type: sources.my_source
      with_args:
        columns:
          foo:
            partition: True
  ```

  </TabItem>
  <TabItem value="python">

  ```py
  @dlt.resource(
    columns={"_dlt_load_id": {"partition": True}}
  )
  def my_resource():
      ...

  pipeline = dlt.pipeline("loads_delta", destination="delta")
  ```

  </TabItem>
</Tabs>

:::caution
パーティションの進化 (テーブルの作成後にパーティション列を変更すること) は現在サポートされていません。
:::

## テーブルアクセスヘルパー関数

`get_delta_tables` ヘルパー関数を使用して、ネイティブの [DeltaTable](https://delta-io.github.io/delta-rs/api/delta_table/) オブジェクトにアクセスできます。

```py
from dlt.common.libs.deltalake import get_delta_tables

...

# get dictionary of DeltaTable objects
delta_tables = get_delta_tables(pipeline)

# execute operations on DeltaTable objects
delta_tables["my_delta_table"].optimize.compact()
delta_tables["another_delta_table"].optimize.z_order(["col_a", "col_b"])
# delta_tables["my_delta_table"].vacuum()
# etc.
```

## テーブル形式

Delta 出力先は、読み込むすべてのリソースに自動的に `delta` テーブル形式を割り当てます。
リソースレベルで `table_format` をネイティブに設定することで、ファイルの保存にフォールバックすることもできます。

  ```py
  @dlt.resource(
    table_format="native"
  )
  def my_resource():
      ...

  pipeline = dlt.pipeline("loads_delta", destination="delta")
  ```

## ストレージオプションと設定

`destination.filesystem.deltalake_storage_options` と `destination.filesystem.deltalake_configuration` の両方を設定することで、ストレージオプションと設定を渡すことができます。

```toml
[destination.filesystem]
deltalake_configuration = '{"delta.enableChangeDataFeed": "true", "delta.minWriterVersion": "7"}'
deltalake_storage_options = '{"AWS_S3_LOCKING_PROVIDER": "dynamodb", "DELTA_DYNAMO_TABLE_NAME": "custom_table_name"}'
```

dlt は、これらを `deltalake` ライブラリの `write_deltalake` メソッドに引数として渡します（`deltalake_configuration` は `configuration` に、`deltalake_storage_options` は `storage_options` にマッピングされます）。
使用可能なオプションについては、[ドキュメント](https://delta-io.github.io/delta-rs/api/delta_writer/#deltalake.write_deltalake) を参照してください。

ここで資格情報を指定する必要はありません。
dlt は、必要な資格情報と指定されたオプションをマージしてから、`storage_options` として渡します。

:::warning
`s3` を使用する場合は、ロック動作を [設定](https://delta-io.github.io/delta-rs/usage/writing/writing-to-s3-with-locking-provider/) するためのストレージ オプションを指定する必要があります。
:::
