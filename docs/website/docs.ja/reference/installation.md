---
title: Installation
description: How to install dlt
keywords: [installation, environment, pip install]
---

# インストール

## 環境の設定

### 1. **Python 3.9-3.13** を使用していること、`pip` がインストールされていることを確認する

```sh
python --version
pip --version
```

別のバージョンの Python がインストールされている場合、または pip がない場合は、以下の手順に従って Python バージョンを更新し、`pip` をインストールしてください。

<Tabs values={[{"label": "Ubuntu", "value": "ubuntu"}, {"label": "macOS", "value": "macos"}, {"label": "Windows", "value": "windows"}]}  groupId="operating-systems" defaultValue="ubuntu">
  <TabItem value="ubuntu">

`apt` を使用して Python 3.10 をインストールできます。

```sh
sudo apt update
sudo apt install python3.10
sudo apt install python3.10-venv
```

  </TabItem>
  <TabItem value="macos">

macOS では、[Homebrew](https://brew.sh) を使用して Python 3.10 をインストールできます。

```sh
brew update
brew install python@3.10
```

  </TabItem>
  <TabItem value="windows">

[Windows 用の Python 3.10 (64 ビット版)](https://www.python.org/downloads/windows/)をインストールしたら、`pip` をインストールできます。

```sh
C:\> pip3 install -U pip
```

  </TabItem>
</Tabs>

### 2. Pythonプロジェクト用の仮想環境をセットアップしてアクティブ化する

Python プロジェクトを作成するときは、[仮想環境](https://docs.python.org/3/library/venv.html)内で作業することをお勧めします。これにより、現在のプロジェクトのすべての依存関係が他のプロジェクトのパッケージから分離されます。

<Tabs values={[{"label": "Ubuntu", "value": "ubuntu"}, {"label": "macOS", "value": "macos"}, {"label": "Windows", "value": "windows"}]}  groupId="operating-systems" defaultValue="ubuntu">

  <TabItem value="ubuntu">

作業フォルダに新しい仮想環境を作成します。これにより、仮想環境が保存される `./env` ディレクトリが作成されます:

```sh
python -m venv ./env
```

仮想環境をアクティブ化します:

```sh
source ./env/bin/activate
```

  </TabItem>
  <TabItem value="macos">

作業フォルダに新しい仮想環境を作成します。これにより、仮想環境が保存される `./env` ディレクトリが作成されます:

```sh
python -m venv ./env
```

仮想環境をアクティブ化します:

```sh
source ./env/bin/activate
```

  </TabItem>
  <TabItem value="windows">

作業フォルダに新しい仮想環境を作成します。これにより、仮想環境が保存される `./env` ディレクトリが作成されます:

```bat
C:\> python -m venv ./env
```

仮想環境をアクティブ化します:

```bat
C:\> .\env\Scripts\activate
```

  </TabItem>
</Tabs>

### 3. `dlt`ライブラリをインストールする

仮想環境に `dlt` の最新バージョンをインストールまたはアップグレードするには、次のコマンドを実行します:

```sh
pip install -U dlt
```

以下に、追加のインストール例をいくつか示します:

DuckDB サポート付きの dlt をインストールするには:
```sh
pip install "dlt[duckdb]"
```

特定のバージョンの dlt をインストールするには (たとえば、0.5.0 より前のバージョン):
```sh
pip install "dlt<0.5.0"
```

### 3.1. Pixi または Conda で dlt をインストールする

`pixi` を使用して dlt をインストールするには:

```sh
pixi add dlt
```

`conda` を使用して dlt をインストールするには:

```sh
conda install -c conda-forge dlt
```

### 4. 完了！

これで、`dlt` を使って最初のパイプラインを構築する準備が整いました。始めるには、これらのチュートリアルをご覧ください:

- [REST API からデータをロードする](../tutorial/rest-api)
- [SQL データベースからデータをロードする](../tutorial/sql-database)
- [クラウドストレージまたはファイルシステムからデータをロードする](../tutorial/filesystem)

もしくは、[dlt を使用したカスタムデータパイプライン](../tutorial/load-data-from-an-api.md)を構築する方法に関する詳細なチュートリアルをお読みください。

