---
title: Amazon Redshift
description: Amazon Redshift `dlt` destination
keywords: [redshift, destination, data warehouse]
---

# Amazon Redshift

## Redshift と dlt をインストールする

**Redshift 依存関係を持つ dlt ライブラリをインストールするには:**

```sh
pip install "dlt[redshift]"
```

## セットアップガイド

### 1. dlt プロジェクトを初期化する

まず、新しい dlt プロジェクトを次のように初期化します:

```sh
dlt init chess redshift
```

> 💡 このコマンドは、chess をソース、Redshift を宛先としてパイプラインを初期化します。

上記のコマンドは、`.dlt/secrets.toml` や Redshift の要件ファイルなど、いくつかのファイルとディレクトリを生成します。要件ファイルで指定された必要な依存関係は、次のように実行することでインストールできます:

```sh
pip install -r requirements.txt
```

または、`pip install "dlt[redshift]"` を使用すると、`dlt` ライブラリと、Amazon Redshift を宛先として使用するために必要な依存関係がインストールされます。

### 2. Redshift クラスターのセットアップ

Redshift にデータをロードするには、Redshift クラスターを作成し、クラスターに関連付けられた VPC インバウンド ルールを通じて IP アドレスへのアクセスを有効にする必要があります。詳細については GPT-4 アシスタントに問い合わせることをお勧めしますが、以下にプロセスの概要を示します:

1. 既存のクラスターを使用することも、新しいクラスターを作成することもできます。
2. 新しいクラスターを作成するには、「プロビジョニングされたクラスターダッシュボード」に移動し、「クラスターの作成」をクリックします。
3. 「クラスター識別子」、「ノード タイプ」、「管理者ユーザー名」、「管理者パスワード」、「データベース名」などの必要な詳細を指定します。
4. 「ネットワークとセキュリティ」セクションでは、クラスターの VPC (仮想プライベートクラウド) を設定できます。AWS 上の VPC の受信ルールに IP アドレスを追加することを忘れないでください。

### 3. 資格情報を追加する

1. 次に、以下に示すように、`.dlt/secrets.toml` ファイルに Redshift 認証情報を設定します:

    ```toml
    [destination.redshift.credentials]
    database = "please set me up!" # Copy your database name here
    password = "please set me up!" # Keep your Redshift db instance password here
    username = "please set me up!" # Keep your Redshift db instance username here
    host = "please set me up!" # Copy your Redshift host from cluster endpoint here
    port = 5439
    connect_timeout = 15 # Enter the timeout value
    ```

2. 「ホスト」は、「一般設定」で指定されたクラスターエンドポイントから派生します。例:

    ```sh
    # If the endpoint is:
    redshift-cluster-1.cv3cmsy7t4il.us-east-1.redshift.amazonaws.com:5439/your_database_name
    # Then the host is:
    redshift-cluster-1.cv3cmsy7t4il.us-east-1.redshift.amazonaws.com
    ```

3. `connect_timeout` は、パイプラインがタイムアウトするまで待機する分数です。

`psycopg2` ライブラリや [SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/engines.html#postgresql) で使用されるものと同様のデータベース接続文字列を渡すこともできます。上記の資格情報は次のようになります:

```toml
# Keep it at the top of your TOML file, before any section starts
destination.redshift.credentials="redshift://loader:<password>@localhost/dlt_data?connect_timeout=15"
```

:::note
PostgreSQL ベースのセットアップには PostgreSQL ドライバーを使用し、ネイティブ Redshift には Amazon Redshift ドライバーを使用します。[ドキュメントを参照](https://docs.aws.amazon.com/redshift/latest/dg/c_redshift-postgres-jdbc.html)。
:::

## 書き込み処理

すべての [書き込み処理](../../general-usage/incremental-loading#choosing-a-write-disposition) がサポートされています。

## サポートされているファイル形式

デフォルトでは[SQL Insert](../file-formats/insert-format)が使用されます。

ステージングが有効になっている場合:

* [JSONL](../file-formats/jsonl.md) は、デフォルトです。
* [Parquet](../file-formats/parquet.md) は、サポートされます。

:::caution
- **Redshift は JSON ファイルから `VARBYTE` 列をロードできません**。 `dlt` では、このようなジョブが永久に失敗します。バイナリをロードするには Parquet に切り替えてください。

- **Redshift は JSON または Parquet ファイルから `TIME` 列をロードできません**。 `dlt` はこのようなジョブを永久に失敗します。時間列をロードするために `insert_values` を直接実行するように切り替えます。

- **Redshift は JSON ファイルから圧縮タイプを検出できません**。 `dlt` は、JSONL ファイルが gzip 圧縮されていると想定します (これがデフォルトです)。

- **Redshift は Parquet を使用して JSON 型を文字列として SUPER に読み込みます**。 JSONL 形式を使用して JSON を SUPER にネイティブに保存するか、`PARSE_JSON` を使用して SUPER 列を変換します。
:::

## サポートされている列のヒント

Amazon Redshiftは次の列ヒントをサポートしています:

- `cluster` - このヒントは、テーブル分散を表す Redshift 用語です。これを列に適用すると、その列は「DISTKEY」となり、クエリと結合のパフォーマンスに影響します。詳細については、次の [ドキュメント](https://docs.aws.amazon.com/redshift/latest/dg/c_best-practices-best-dist-key.html) を確認してください。
- `sort` - このヒントは、ディスク上の行を物理的に順序付けるための SORTKEY を作成します。これは、Redshift でのクエリと結合の速度を向上させるために使用されます。詳細については、[ソートキーのドキュメント](https://docs.aws.amazon.com/redshift/latest/dg/c_best-practices-sort-key.html) をお読みください。

### テーブルと列の識別子

Redshift は**デフォルトで**、大文字と小文字を区別しない識別子を使用し、INFORMATION SCHEMA に保存される**すべての識別子を小文字にします**。[大文字と小文字を区別する命名規則](../../general-usage/naming-convention.md#case-sensitive-and-insensitive-destinations) は使用しないでください。いずれにしても大文字と小文字は削除され、識別子の衝突が発生するリスクがあります。これは `dlt` によって検出され、ロード プロセスが失敗します。

[Redshift を大文字と小文字を区別するモードにする](https://docs.aws.amazon.com/redshift/latest/dg/r_enable_case_sensitive_identifier.html)ことができます。大文字と小文字を区別する命名規則を使用するには、次のように宛先を設定します:

```toml
[destination.redshift]
has_case_sensitive_identifiers=true
```

## ステージングサポート

Redshift は、ファイルのステージング先として s3 をサポートしています。`dlt` は parquet 形式のファイルを s3 にアップロードし、そのデータを直接 db にコピーするように Redshift に要求します。bucket_url と認証情報を使用して s3 バケットを設定する方法については、[S3 ドキュメント](./filesystem.md#aws-s3) を参照してください。`dlt` Redshift ローダーは、特に指定がない限り、s3 に提供された AWS 認証情報を使用して s3 バケットにアクセスします (以下の構成オプションを参照)。parquet ファイルの代わりに、ステージング ファイル形式として jsonl を指定することもできます。これを行うには、パイプラインの `run` コマンドの `loader_file_format` 引数を `jsonl` に設定します。

:::note
If the S3 bucket is in a different region than your Redshift cluster:
- You must set `region_name` in `[destination.filesystem.credentials]` in your `config.toml` file to ensure proper access
- For Parquet files, cross-region COPY operations are not supported by Redshift, so the region setting will be ignored
:::

## 識別子名と大文字と小文字の区別

* 最大127文字
* 大文字と小文字を区別しない
* 識別子を小文字で保存します
* 大文字と小文字を区別するモードがあり、有効になっている場合は、[宛先ファクトリで大文字と小文字の区別を有効にする](../../general-usage/destination.md#control-how-dlt-creates-table-column-and-other-identifiers)必要があります。

### 認証IAMロール

AWS ステージング認証情報を転送せずに s3 からロードし、Redshift に接続された IAM ロールで認証する場合は、[Redshift ドキュメント](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html) に従って、Redshift クラスターにリンクされた s3 へのアクセス権を持つロールを作成し、IAM ロールを使用するように宛先設定を変更します。

```toml
[destination]
staging_iam_role="arn:aws:iam::..."
```

### Redshift/S3 ステージングのサンプルコード

```py
# Create a dlt pipeline that will load
# chess player data to the Redshift destination
# via staging on S3
pipeline = dlt.pipeline(
    pipeline_name='chess_pipeline',
    destination='redshift',
    staging='filesystem', # add this to activate the staging location
    dataset_name='player_data'
)
```

## 追加の宛先オプション

### dbt サポート

- この宛先は、[dbt-redshift](https://github.com/dbt-labs/dbt-redshift) を介して [dbt と統合](../transformations/dbt) します。資格情報とタイムアウト設定は `dbt` と自動的に共有されます。

### `dlt` の状態の同期

- この宛先は、[dlt state sync.](../../general-usage/state#syncing-state-with-destination) を完全にサポートしています。

## サポートされているローダーファイル形式

Redshift でサポートされているローダー ファイル形式は、`sql` と `insert_values` (デフォルト) です。ステージング ロケーションを使用する場合、Redshift は Parquet と JSONL をサポートします。

<!--@@@DLT_TUBA redshift-->

