---
title: Destination
description: Declare and configure destinations to which to load data
keywords: [destination, load data, configure destination, name destination]
---

# 宛先

[宛先](glossary.md#destination) は、`dlt` がスキーマの現在のバージョンを作成および維持し、データを読み込む場所です。宛先には、データベース、データレイク、ベクター ストア、ファイルなど、さまざまな形式があります。`dlt` は、パイプラインの作成時に宣言するモジュールを介してこの多様性に対応します。

すぐに使用できる [組み込みの宛先](../dlt-ecosystem/destinations/) のセットを提供しています。

## 宛先タイプを宣言する

`dlt.pipeline` を使用してパイプライン インスタンスを作成するときは、宛先タイプを宣言することをお勧めします。これにより、`run` メソッドはローカル パイプラインの状態を宛先と同期し、`extract` および `normalize` は互換性のあるロード パッケージとスキーマを作成できます。宛先を `run` メソッドと `load` メソッドに渡すこともできます。

* 宛先の**省略形**を使用する
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::shorthand-->

上記では、**filesystem** 組み込みの宛先を使用します。組み込みの場合のみ、省略型を使用できます。

* 完全な**宛先ファクトリタイプ**を使用する
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::class_type-->

上記では、モジュール `dlt.destinations` からファクトリ タイプ `filesystem` を提供することで、組み込みの **filesystem** 宛先を使用しています。[外部モジュールからの宛先](#declare-external-destination)も渡すことができます。

* **宛先ファクトリ** をインポート
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::class-->

上記では、**filesystem** の宛先ファクトリをインポートし、パイプラインに渡します。

上記のすべての例では、デフォルトのパラメータを使用して同じ宛先クラスを作成し、[configuration](credentials/index.md) から必要な構成とシークレットの値を取得します。これらは同等です。

### 明示的なパラメータと名前を宛先に渡す

**宛先ファクトリ** を自分でインスタンス化して明示的に設定することができます。これを行うと、[ソース](source.md) と同じように宛先を操作します。
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::instance-->

上記では、`filesystem` 宛先ファクトリをインポートしてインスタンス化します。バケットの明示的な URL を渡し、宛先に `production_az_bucket` という名前を付けます。

宛先に名前が付けられていない場合は、その短縮形 (Python ファクトリ名) が宛先名として機能します。同じタイプの宛先の複数の個別の構成が必要な場合 (つまり、開発、ステージング、および本番環境のストレージ バケットの認証情報を同じ構成ファイルで管理する場合) は、宛先に明示的に名前を付けます。宛先名は [ロード情報](../running-in-production/running.md#inspect-and-save-the-load-info-and-trace) およびパイプライン トレースにも保存されるため、より説明的な名前 (たとえば、`filesystem` 以外) が必要な場合にもそれらを使用します。

## 宛先を設定する

資格情報やその他の必要なパラメータを、TOML ファイル、環境変数、またはその他の [設定プロバイダ](credentials/setup) を介して構成に渡すことをお勧めします。これにより、たとえば、デプロイ後に本番環境への切り替えが簡単になります。

以下のように[デフォルトの設定セクションレイアウト](credentials/setup#structure-of-secrets.toml-and-config.toml)を使用することをお勧めします。:
<!--@@@DLT_SNIPPET ./snippets/destination-toml.toml::default_layout-->

または環境変数を介して:

```sh
DESTINATION__FILESYSTEM__BUCKET_URL=az://dlt-azure-bucket
DESTINATION__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_NAME=dltdata
DESTINATION__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_KEY="storage key"
```

名前付き宛先の場合は、設定セクションでその名前を使用します。
<!--@@@DLT_SNIPPET ./snippets/destination-toml.toml::name_layout-->

[`dlt init` コマンド](../walkthroughs/add-a-verified-source.md) を使用してデータ ソースを作成または追加すると、`dlt` によって選択した宛先のサンプル構成が作成されることに注意してください。

### 明示的な資格情報を渡す

宛先ファクトリインスタンスを作成するときに、資格情報を明示的に渡すことができます。これは、現在非推奨となっている `dlt.pipeline` および `pipeline.load` メソッドの `credentials` 引数を置き換えます。必要な資格情報オブジェクト、その辞書表現、または以下のようにサポートされているネイティブ形式を渡すことができます:
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::config_explicit-->


:::tip
部分的な認証情報を作成して渡すと、`dlt` が不足しているデータを入力します。以下では、パスワードなしで PostgreSQL 接続文字列を渡し、それが環境変数 (または他の [config provider](credentials/setup)) に存在することを期待しています。
<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::config_partial-->


<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::config_partial_spec-->


[さまざまな組み込み資格情報タイプ](credentials/complex_types)の使用方法をお読みください。
:::

### 宛先の機能を検査する

[宛先の機能](../walkthroughs/create-new-destination.md#3-set-the-destination-capabilities) は、`dlt` に、特定の宛先で何ができるか、何ができないかを伝えます。たとえば、どのファイル形式をロードできるか、クエリまたは識別子の最大長はどれくらいかを伝えます。宛先の機能を次のように検査します。:

```py
import dlt
pipeline = dlt.pipeline("snowflake_test", destination="snowflake")
print(dict(pipeline.destination.capabilities()))
```

### 追加のパラメータを渡して宛先の機能を変更する

宛先ファクトリは、事前構成や宛先の機能の変更に使用される追加のパラメータを受け入れます。

```py
import dlt
duck_ = dlt.destinations.duckdb(naming_convention="duck_case", recommended_file_size=120000)
print(dict(duck_.capabilities()))
```

上記の例では、宛先の機能の `naming_convention` と `recommended_file_size` を上書きしています。

### パイプラインで複数の宛先を構成する

パイプライン内で複数の宛先を設定するには、「secrets.toml」ファイルで各宛先の認証情報を提供する必要があります。この例では、`destination_one` という名前の BigQuery 宛先を設定する方法を示します:

```toml
[destination.destination_one]
location = "US"
[destination.destination_one.credentials]
project_id = "please set me up!"
private_key = "please set me up!"
client_email = "please set me up!"
```

この宛先をパイプラインで次のように使用できます:

```py
import dlt
from dlt.common.destination import Destination

# Configure the pipeline to use the "destination_one" BigQuery destination
pipeline = dlt.pipeline(
    pipeline_name='pipeline',
    destination=Destination.from_reference(
        "bigquery",
        destination_name="destination_one"
    ),
    dataset_name='dataset_name'
)
```

同様に、同じドライバーまたは異なるドライバーに複数の目的地を割り当てることもできます。

## 宛先にアクセスする

データをロードする際、`dlt` は2つのケースで宛先にアクセスします:

1. `run` メソッドの開始時に、パイプラインの状態を宛先と同期します。(または、`pipeline.sync_destination` を明示的に呼び出します。)
2. `pipeline.load` メソッドで、スキーマを移行し、ロードパッケージをロードします。

`dlt` は、[sql_client](../dlt-ecosystem/transformations/sql.md) をインスタンス化するときにも宛先にアクセスします。

:::note
`dlt` は、アクセスが必要ない場合、宛先の依存関係をインポートしたり、宛先の構成にアクセスしたりしません。ステップが別々のプロセスまたはコンテナで実行されるマルチステージ パイプラインを構築できます。`extract` および `normalize` ステップでは、宛先の依存関係、構成、および実際の接続は必要ありません。

<!--@@@DLT_SNIPPET ./snippets/destination-snippets.py::late_destination_access-->

:::

## `dlt` がテーブル、列、その他の識別子を作成する方法を制御する

`dlt` は、[命名規則](naming-convention.md) を使用して、ソース データで見つかった識別子を宛先の識別子 (テーブル名や列名など) にマッピングします。これにより、文字セット、識別子の長さ、およびその他のプロパティが、指定された宛先で処理できるものに適合することが保証されます。たとえば、[デフォルトの命名規則 (**スネーク ケース**)](naming-convention.md#default-naming-convention-snake_case) は、ソース (JSON ドキュメント フィールド) 内のすべての名前を、大文字と小文字を区別しないスネーク ケースの識別子に変換します。

各宛先は、優先命名規則、大文字と小文字を区別する識別子のサポート、および大文字と小文字を区別しない識別子が従う大文字と小文字の変換関数を宣言します。たとえば:

1. Redshift - デフォルトでは、大文字と小文字を区別する識別子をサポートせず、すべてを小文字に変換します。
2. Snowflake - 大文字と小文字を区別する識別子をサポートし、大文字になった識別子は大文字と小文字を区別しないものとみなします (これがデフォルトの大文字小文字の変換です)。
3. DuckDb - 大文字と小文字を区別する識別子をサポートしていませんが、大文字と小文字を区別しないため、情報スキーマ内の元の大文字と小文字が保持されます。
4. Athena - 大文字と小文字を区別する識別子をサポートしておらず、すべてを小文字に変換します。
5. BigQuery - すべての識別子は大文字と小文字を区別します。大文字と小文字の区別をしないモードは、ケース フォールディングでは利用できません(が、データセット レベルで有効にすることはできます)。

命名規則は[さまざまな方法](naming-convention.md#configure-naming-convention)で変更できます。以下では、Snowflakeの宛先の優先命名規則を`sql_cs`に設定して、Snowflakeを大文字と小文字を区別するモードに切り替えます:

```py
import dlt
snow_ = dlt.destinations.snowflake(naming_convention="sql_cs_v1")
```

命名規則を設定すると、作成されるすべての新しいスキーマ (つまり、最初のパイプライン実行時) に影響し、既存のすべての識別子が再正規化されます。

:::caution
`dlt` は、宛先で既に作成されているテーブル内の識別子の再正規化を防ぎます。データを削除するには、[refresh](pipeline.md#refresh-pipeline-data-and-state) モードを使用します。この動作は、[configuration](naming-convention.md#avoid-identifier-collisions) で無効にすることもできます。
:::

:::note
大文字と小文字を区別する識別子をサポートしているが、大文字と小文字を区別しない識別子を有効にするために大文字と小文字の折りたたみ規則を使用する宛先は、デフォルトで大文字と小文字を区別しないモードに設定されています。例: Postgres、Snowflake、Oracle。
:::

:::caution
大文字と小文字を区別しない宛先で大文字と小文字を区別する命名規則を使用する場合、`dlt` は:
1. 大文字と小文字の変換により識別子の衝突が検出された場合は、ロードが失敗します。
2. 宛先によって大文字と小文字の変換が適用されている場合は警告します。
:::

### 大文字と小文字を区別する識別子のサポートを有効にする

選択した宛先は、大文字と小文字を区別する識別子を受け入れるように構成できます。たとえば、**mssql** データベースで大文字と小文字を区別する照合を設定し、それを `dlt` に通知することができます。

```py
from dlt.destinations import mssql
dest_ = mssql(has_case_sensitive_identifiers=True, naming_convention="sql_cs_v1")
```

上記では、名前の衝突を心配することなく、大文字と小文字を区別する命名規則を安全に使用できます。

大文字と小文字の区別を設定できますが、**宛先機能の設定は現在サポートされていません**。

```toml
[destination.mssql]
has_case_sensitive_identifiers=true
```

:::note
ほとんどの場合、上記のフラグを設定すると、`dlt` に対して、宛先で大文字と小文字を区別するオプションを切り替えたことを示すだけです。`dlt` はそれを行いません。詳細については、宛先のドキュメントを参照してください。
:::

## 新しい宛先を作成する

新しい宛先を実装するには2つの方法があります:

1. `@dlt.destination` デコレータを使用して、[シンク関数を実装](../dlt-ecosystem/destinations/destination.md)できます。これは、データを REST API にプッシュバックするリバース ETL 宛先を実装するのに最適な方法です。
2. ロード ジョブとスキーマの移行を完全に制御できる [完全な宛先](../walkthroughs/create-new-destination.md) を実装できます。

