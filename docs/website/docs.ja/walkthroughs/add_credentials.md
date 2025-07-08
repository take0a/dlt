---
title: 資格情報を追加する方法
description: ローカルおよび本番環境で認証情報を追加する方法
keywords: [credentials, secrets.toml, environment variables]
---

# 資格情報を追加する方法

## ローカルでの認証情報の追加

パイプラインをローカルで使用する場合は、`.dlt/secrets.toml` メソッドを使用することをお勧めします。

これを行うには、dlt secrets ファイルを開き、ソース名と認証情報をスクリプト内のものと一致させます。例:

```toml
[sources.pipedrive]
pipedrive_api_key = "pipedrive_api_key" # please set me up!

[destination.bigquery]
location = "US"

[destination.bigquery.credentials]
project_id = "project_id" # please set me up!
private_key = "private_key" # please set me up!
client_email = "client_email" # please set me up!
```

:::note
TOML ファイル内のキーは大文字と小文字が区別され、セクションはピリオド (`.`) で区切られます。
:::

宛先の認証情報については、[各宛先のドキュメントページ](../dlt-ecosystem/destinations) を参照して認証情報を作成および設定してください。

検証済みソースの認証情報については、各ソースの[セットアップガイド](../dlt-ecosystem/verified-sources) を参照して認証情報の取得方法を確認してください。

ソースと宛先の認証情報を取得したら、上記のファイルに追加して保存してください。

[認証情報の設定](../general-usage/credentials) の詳細については、こちらをご覧ください。

## デプロイメントへの認証情報の追加

デプロイメントに認証情報を追加するには、

- いずれかの `dlt deploy` コマンドを使用します。
- または、[コード経由で認証情報を渡す](../general-usage/credentials/advanced#configure-destination-credentials-in-code) または [環境経由で認証情報を渡す](../general-usage/credentials/setup#environment-variables) 手順に従ってください。

### 環境変数からの認証情報の読み取り

`dlt` は、環境変数からの認証情報の読み取りをサポートしています。例えば、`.dlt/secrets.toml` は次のようになります。

```toml
[sources.pipedrive]
pipedrive_api_key = "pipedrive_api_key" # please set me up!

[destination.bigquery]
location = "US"

[destination.bigquery.credentials]
project_id = "project_id" # please set me up!
private_key = "private_key" # please set me up!
client_email = "client_email" # please set me up!
```

dlt が環境変数からこれを読み取ろうとする場合、異なる命名規則が使用されます。

環境変数の場合、名前はすべて大文字で始まり、セクションは二重のアンダースコア "__" で区切られます。

例えば、上記のシークレットについては、環境変数で次のように設定する必要があります。

```sh
SOURCES__PIPEDRIVE__PIPEDRIVE_API_KEY
DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID
DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY
DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL
DESTINATION__BIGQUERY__LOCATION
```

## Google Cloud Secret Manager からの認証情報の取得

`dlt` は、Google Cloud Secret Manager からの認証情報の読み取りをサポートしています。
この機能を有効にするには、以下のアクセス権限を持つ認証情報を提供する必要があります。
* 特定のシークレットを読み取るための **roles/secretmanager.secretAccessor**
* 利用可能なシークレットを一覧表示する **roles/secretmanager.secretViewer** (オプションですが、強く推奨)

設定例:
```toml
[providers]
enable_google_secrets=true

[providers.google_secrets]
only_secrets=false
only_toml_fragments=false
list_secrets=true

[providers.google_secrets.credentials]
"project_id" = "<project_id>"
"private_key" = "-----BEGIN PRIVATE KEY-----\n....\n-----END PRIVATE KEY-----\n"
"client_email" = "....gserviceaccount.com"
```

### シークレットの一覧表示とToMLフラグメントの使用によるバックエンドへの呼び出し回数の削減
`list_secrets` を有効にして、可能なキーの一覧を取得し、バックエンドへの呼び出し回数を削減することをお勧めします。
また、呼び出し回数を削減するため、単一の値ではなく、構成フラグメントを保存することをお勧めします。
Vaultプロバイダーは、このようなフラグメントを取得し、それらを即座に完全な構成に統合することができます。

例えば、以下を定義できます。

**destination** シークレット：宛先の認証情報を保持します。
```toml
[destination]
postgres.credentials="postgresql://loader:***@host:5432/postgres"

[destination.bigquery.credentials]
"project_id" = "<project_id>"
"private_key" = "-----BEGIN PRIVATE KEY-----\n....\n-----END PRIVATE KEY-----\n"
"client_email" = "....gserviceaccount.com"
```

または、ファイルシステムの資格情報のみを保存するには **destination-filesystem** を使用します。
```toml
[destination.filesystem]
bucket_url="s3://bucket/path"
[destination.filesystem.credentials]
# s3 (same as athena)
region_name="eu-central-1"
aws_access_key_id="..."
aws_secret_access_key="..."
```

ソースについても同様です。つまり、**sources-mongodb** は mongo の資格情報を保存します。
```toml
[sources.mongodb]
connection_url="mongodb+srv://temp_writer:***/dlt_data?authSource=admin&replicaSet=db-mongodb&tls=true"
```

単一の値を保存することもできます。その場合、Google Vault は環境変数プロバイダと同様に動作します。
```sh
sources-pipedrive-pipedrive_api_key
destination-bigquery-credentials-project_id
destination-bigquery-credentials-private_key
destination-bigquery-credentials-client_email
destination-bigquery-location
```
明らかに、これには Secrets バックエンドへの複数の呼び出しが必要になります。

:::caution
Vaultプロバイダーは取得したすべてのキーを内部的にキャッシュし、（プロセスが再起動されるまで）それらのシークレットを再度取得しません。これにより、バックエンドへの呼び出し回数（コスト発生）が削減されますが、実行時に変更が反映されなくなります。
:::

### シークレットの一覧表示権限なしでシークレットにアクセスする
以下の設定により、シークレットの一覧表示をスキップしながら、バックエンド呼び出しの回数を最小限に抑えることができます。
```toml
[providers.google_secrets]
only_secrets=true
only_toml_fragments=true
list_secrets=false
```

Vault は、単一の値を取得せずに、シークレット値 (資格情報、`dlt.secrets.value` でマークされた引数) と、上記のセクションで説明した toml フラグメントのみを取得します。


:::caution
`dlt` は単一の値について複数の場所を調査するため、`only_toml_fragments` を無効にすると、Secrets バックエンドへの呼び出しが大量に発生する可能性があります。
:::

## 他のボールトタイプからの認証情報の取得
`VaultDocProvider` のサブクラスを作成し、シークレットを取得するメソッドと（オプションで）シークレットを一覧表示するメソッドを実装します。次に、[サブクラスをカスタムプロバイダーとして登録します](../examples/custom_config_provider)。
