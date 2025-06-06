---
title: Profiles
keywords: [dlt+, profiles]
---

プロファイルとは、特定のユースケース向けに定義された設定とシークレットのセットです。
プロファイルは、環境ごとに異なる設定を管理する手段を提供します。

プロファイルは、`dlt.yml` の `profiles` セクションで定義されます。

```yaml
profiles:
  # profiles allow you to configure different settings for different environments
  dev:
    sources:
      my_arrow_source:
        row_count: 100
    runtime:
      log_level: DEBUG
  prod:
    sources:
      my_arrow_source:
        row_count: 200
    runtime:
      log_level: INFO
    destinations:
      my_duckdb_destination:
        credentials: my_data_prod.duckdb
```

すべてのプロジェクトには、デフォルトで `dev` と `tests` という 2 つの暗黙的なプロファイルが含まれています。
プロファイルが指定されていない場合は、デフォルトで `dev` プロファイルが読み込まれます。
プロジェクトで実行されるすべての CLI コマンドは `--profile` オプションをサポートしており、必要なプロファイルを指定できます。
例えば、

```sh
dlt project --profile dev my_pipeline run
dlt dataset --profile prod my_duckdb_destination_dataset row-counts
```

## プロファイルでの設定ファイルの使用

プロファイルのすべての設定とシークレットは、[dlt OSS ドキュメント](../../general-usage/credentials/)に記載されているように、TOML ファイルに配置することもできます。
各プロファイルには独自の `secrets.toml` ファイルを作成でき、このファイルはそのプロファイルがアクティブな場合にのみ読み込まれます。

例えば、`.dlt` 以下に 2 つのシークレットファイルがある場合:

```sh
.
├── .dlt/                 # your dlt settings including profile settings
│   ├── config.toml
│   ├── dev.secrets.toml
│   └── tests.secrets.toml
```

次のように、異なるプロファイルを使用してパイプラインを実行できます:

```sh
dlt pipeline --profile dev my_pipeline run
dlt pipeline --profile tests my_pipeline run
```

:::caution
YAML ファイルと TOML ファイルの間には、今後修正される予定の以下の不整合がありますのでご注意ください。

* YAML の `destinations` セクションは、TOML ファイルでは `destination` と単数形になっています。
* `tmp_dir` などのプロジェクト変数は、TOML ファイルでは使用できません。
:::

## プロファイルのピン留め

プロファイルをローカルにピン留めし、指定したプロファイル名をデフォルトにすることができます。
これは、例えばプロジェクトを本番環境やステージング環境にデプロイする場合に便利です。

```sh
dlt profile prod pin
```

`prod` プロファイルをピン留めします。これ以降、すべての Python スクリプトと CLI コマンドはこれをデフォルトとして認識し、自動的に切り替えます。
プロファイルのピン留めは `.dlt/profile-name` ファイルに保存されます。
ピン留めを解除するには、このファイルを削除します。デフォルトの `.gitignore` により、このファイルの追加がブロックされていることに注意してください。

### `dlt.yml` ファイルと TOML ファイルの設定

dlt+ プロジェクトでは、シークレットではない設定はすべて `dlt.yml` に保存し、シークレットは `.dlt/secrets.toml` にのみ保存するのがベストプラクティスです。
これにより、機密データは必要なプロファイルまたは環境でのみ利用可能になります。

上記の例では、デモ目的のため、シークレットではない値の一部を `.dlt/secrets.toml` に移動していますが、これは推奨される方法ではありません。
