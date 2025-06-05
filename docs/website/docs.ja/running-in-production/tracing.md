---
title: Tracing
description: Rich information on executed dlt pipelines
keywords: [tracing, sentry, opt in]
---

# トレース

`dlt` ユーザーは、[Sentry](https://sentry.io) DSN を設定することで、実行されたパイプラインに関する豊富な情報（発生したエラーや例外など）を受け取ることができます。
**Sentry トレースはデフォルトで無効になっています。**

### 送信タイミングと送信内容

例外トレースは、以下の場合に送信されます。

- Python ロガー（`dlt` を含む）がエラーをログに記録した場合。
- Python ロガー（`dlt` を含む）が警告をログに記録した場合（`dlt` のログレベルが `WARNING` 以下の場合のみ有効）。
- 未処理の例外が発生した場合。

トランザクショントレースは、`pipeline.run` が呼び出されたときに送信されます。[抽出、正規化、ロード](../reference/explainers/how-dlt-works.md) の各ステップが完了したときに情報を送信します。

Sentry で利用可能なデータにより、バグの検出と文書化が容易になり、ボトルネックの特定やデータの抽出、正規化、ロードのプロファイル作成が容易になります。

`dlt` は、Sentry データに一連の追加タグ（パイプライン名、宛先名など）を追加します。

Sentryの[ドキュメント](https://docs.sentry.io/platforms/python/data-collected/)を参照してください。

### パイプライントレースを有効にする

Sentry を有効にするには、`config.toml` で [DSN](https://docs.sentry.io/product/sentry-basics/dsn-explainer/) を設定する必要があります。

```toml
[runtime]

sentry_dsn="https:///<...>"
```

あるいは、環境変数を使用することもできます:

```sh
RUNTIME__SENTRY_DSN="https:///<...>"
```

Sentryクライアントは、`dlt.pipeline()`で最初のパイプラインを作成した後に設定されます。必要に応じて、`sentry_sdk` initを再度使用してください。

> 💡 `dlt` does not have Sentry client as a dependency. Remember to install it with `pip install sentry-sdk`.

## すべてのトレースを無効にする

`dlt` を使用すると、匿名テレメトリと Sentry を含むパイプラインのトレースを完全に無効にできます。`config.toml` を使用する場合:

```toml
enable_runtime_trace=false
```

