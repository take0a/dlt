---
title: "Data quality 🧪"
description: Validate your data and control its quality
keywords: ["dlt+", "data quality", "contracts"]
---

:::caution
🚧 この機能は現在開発中です。早期テスターに​​ご興味をお持ちですか？[dlt+早期アクセスにご参加ください](https://info.dlthub.com/waiting-list)。
:::

dlt+を使用すると、YAMLレベルまたはPydanticモデルを使用してデータ検証ルールを定義できます。これにより、取り込み段階でデータが期待される品質基準を満たしていることが保証されます。

## 例: YAML での品質コントラクトの定義

品質コントラクトを指定することで、期待値の範囲や null 値許容など、データに制約を適用できます。

```yaml
engine_version: 10
name: scd_type_3
tables:
  customers:
    columns:
      category:
        data_type: bigint
        nullable: false
        quality_contracts:
          expect_column_max_to_be_between:
            min_value: 1
            max_value: 100
```

## 主な機能

dlt+ を使用すると、次のことが可能になります。

* YAML 設定または Pydantic モデルを使用して、データテストと品質契約を定義します。
* 行レベルとバッチレベルの両方の検証を適用します。
* 分布、境界、期待値に制約を適用します。

これらの機能を拡張していく予定ですので、今後のアップデートにご期待ください。 🚀

