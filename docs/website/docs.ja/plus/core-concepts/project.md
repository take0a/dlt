# Project

dlt+ プロジェクトは、開発者にデータワークフローコンポーネント（ソース、デスティネーション、パイプライン、変換、パラメータなど）を定義するための宣言的なアプローチを提供します。
このプロジェクトは、Python マニフェストファイル `dlt.yml` を中心とした独自の構造を採用しており、すべての dlt エンティティが体系的に定義および構成されます。
マニフェストファイルは、データパイプラインの信頼できる唯一の情報源として機能し、すべてのチームの連携を維持します。

プロジェクトレイアウトには、以下のコンポーネントが含まれます。

1. ソース、デスティネーション、パイプライン、変換などのデータプラットフォームエンティティと、それぞれの構成を指定する dlt マニフェストファイル (`dlt.yml`)
2. シークレットなどの情報を含む `.dlt` フォルダ。オープンソースの dlt と下位互換性があります。
3. ソースコードとテストを含む Python モジュール。モジュールのレイアウトは厳密にすることを推奨します（ソースコードは`sources/`フォルダ内など）。
4. パイプラインの作業ディレクトリとローカルの出力先ファイル（ファイルシステム、duckdbデータベースなど）が保存される`_data`フォルダ（`.git`からは除外）。

一般的なdlt+プロジェクトは以下の構造を持ちます。

```text
.
├── .dlt/                 # your dlt secrets
│   ├── dev.secrets.toml
│   └── secrets.toml
├── _data/             # local storage for your project, excluded from git
├── sources/              # your sources, contains the code for the arrow source
│   └── arrow.py
├── .gitignore
├── requirements.txt
└── dlt.yml               # the main project manifest
```

dlt+ プロジェクトの詳細については、[プロジェクト機能の説明](../features/projects.md) をご覧ください。

:::note
dlt+ プロジェクトを開始し、cli コマンドを使用して管理する方法を学ぶには、[チュートリアル](../getting-started/tutorial.md) をご覧ください。
:::
