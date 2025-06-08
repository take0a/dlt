---
title: Runners
description: Run pipelines in production
keywords: [runners, lambda, airflow]
---

# Runners

dlt+ を使用すると、コマンドラインから直接パイプラインを実行できるようになり、より早く本番環境に移行できるようになります。

```sh
dlt pipeline my_pipeline run
```

これらは、[プロファイル](../core-concepts/profiles.md)を使用してさまざまな環境で実行することもできます。

```sh
dlt project --profile prod my_pipeline run
```

Airflow、Dagster、Prefectなどの環境に特化したランナーの開発に取り組んでいます。ご興味をお持ちいただけましたら、[早期アクセスプログラム](https://info.dlthub.com/waiting-list)にぜひご参加ください。

