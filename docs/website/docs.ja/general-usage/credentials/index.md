---
title: Configuration and Secrets
description: How to configure dlt pipelines and set up credentials
keywords: [credentials, secrets.toml, secrets, config, configuration, environment variables]
---
import DocCardList from '@theme/DocCardList';

`dlt` パイプラインは通常、設定と認証情報を必要とします。これらは [様々な方法](./setup) で設定できます。

1. 環境変数
2. 設定ファイル (`secrets.toml` および `config.toml`)
3. キーマネージャーとキーボールト

`dlt` は、柔軟な [命名規則](./setup/#naming-convention) に基づいて、設定とシークレットを自動的に抽出します。そして、これらの値をコード内の必要な場所に [挿入](./advanced/#injection-mechanism) します。

# Learn details about

<DocCardList />

