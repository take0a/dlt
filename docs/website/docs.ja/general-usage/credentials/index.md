---
title: 資格情報とパイプラインを構成する
description: How to configure dlt pipelines and set up credentials
keywords: [credentials, secrets.toml, secrets, config, configuration, environment variables]
---
import DocCardList from '@theme/DocCardList';

`dlt` の構成メカニズムは、コードとは別に外部システムへの資格情報やその他の設定を定義する柔軟で安全な方法を提供します。

## 主な機能

1. **シークレットと構成をコードから分離** - 構成システムの主な役割は、機密情報をソースコードから排除することです。

2. **組み込み認証情報** - `dlt` は、デフォルト/マシン認証情報アクセスを備えた、一般的なシステムのほとんどを組み込みサポートしています。

3. **自動生成構成** - `@dlt.source`、`@dlt.resource`、`@dlt.destination` で修飾された関数の場合、`dlt` は適切な構成仕様を自動的に生成し、組み込みの構成と認証情報のように動作します。

4. **包括的な構成可能性** - パイプライン、ノーマライザー、ローダー、ロギングなど、`dlt` のほぼすべての側面が構成可能であるため、コードを変更することなく動作を変更できます。この機能により、実行時にパフォーマンスの最適化やその他の調整が可能になります。

<DocCardList />
