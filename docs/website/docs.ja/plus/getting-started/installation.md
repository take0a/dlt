---
title: Installation
description: Installation information for dlt+
---

:::info サポートされているPythonのバージョン

dlt+ は現在、Python バージョン 3.9 ～ 3.12 をサポートしています。

:::

## クイックスタート

`dlt-plus` パッケージをインストールするには、次のコマンドを実行します:

```sh
pip install dlt-plus
```

続行する前に、[ライセンス](#licensing) の説明に従って有効なライセンスをインストールしてください。

## 環境の設定

### Python 環境の設定

Python 環境が設定されているかどうかを確認します:

```sh
python --version
pip --version
```

異なるバージョンの Python がインストールされている場合、または pip が不足している場合は、以下の手順に従って Python バージョンを更新するか、または `pip` をインストールしてください。

<Tabs values={[{"label": "Ubuntu", "value": "ubuntu"}, {"label": "macOS", "value": "macos"}, {"label": "Windows", "value": "windows"}]} groupId="operating-systems" defaultValue="ubuntu">
<TabItem value="ubuntu">

`apt` を使って Python 3.10 をインストールできます。

```sh
sudo apt update
sudo apt install python3.10
pip install uv
```

  </TabItem>
  <TabItem value="macos">

macOSでは、[Homebrew](https://brew.sh)を使用してPython 3.10をインストールできます。

```sh
brew update
brew install python@3.10
pip install uv
```

  </TabItem>
  <TabItem value="windows">

[Python 3.10 (64ビット版) for Windows](https://www.python.org/downloads/windows/) をインストールした後、 `pip` をインストールできます。

```sh
C:\> pip3 install -U pip
C:\> pip3 install uv
```

  </TabItem>
</Tabs>

### Virtual environment

Python プロジェクトを作成する際は、[仮想環境](https://docs.python.org/3/library/venv.html) 内で作業することをお勧めします。これにより、現在のプロジェクトのすべての依存関係が、他のプロジェクトのパッケージから分離されます。

<Tabs values={[{"label": "Ubuntu", "value": "ubuntu"}, {"label": "macOS", "value": "macos"}, {"label": "Windows", "value": "windows"}]} groupId="operating-systems" defaultValue="ubuntu">

  <TabItem value="ubuntu">

作業フォルダに新しい仮想環境を作成します。
これにより、仮想環境が保存される `./venv` ディレクトリが作成されます。

```sh
uv venv --python 3.10
```

仮想環境をアクティブ化します。

```sh
source .venv/bin/activate
```

  </TabItem>
  <TabItem value="macos">

作業フォルダに新しい仮想環境を作成します。
これにより、仮想環境が保存される `./venv` ディレクトリが作成されます。

```sh
uv venv --python 3.10
```

仮想環境をアクティブ化します。

```sh
source .venv/bin/activate
```

  </TabItem>
  <TabItem value="windows">

作業フォルダに新しい仮想環境を作成します。
これにより、仮想環境が保存される `./venv` ディレクトリが作成されます:

```bat
C:\> uv venv --python 3.10
```

仮想環境をアクティブ化します:

```bat
C:\> .\venv\Scripts\activate
```

  </TabItem>
</Tabs>

### dlt+ をインストール

次のコマンドを実行することで、仮想環境に dlt+ をインストールできます:

```sh
# install the newest dlt version or upgrade the existing version to the newest one
uv pip install -U dlt-plus
```

続行する前に、[ライセンス](#licensing) の説明に従って有効なライセンスをインストールしてください。

## Licensing

有効なライセンスを取得したら、次のいずれかの方法で dlt+ で利用できるようにすることができます。

1. **環境変数**: ライセンス キーを環境変数として設定します。

```sh
export RUNTIME__LICENSE="eyJhbGciOiJSUz...vKSjbEc==="
```

2. **Secrets ファイル**: ライセンスキーを `secrets.toml` ファイルに追加します。プロジェクトレベルの `secrets.toml` ファイル（`./.dlt/secrets.toml` 内）またはグローバルの `secrets.toml` ファイル（`~/.dlt/secrets.toml` 内）のいずれかを使用できます。

```toml
[runtime]
license="eyJhbGciOiJSUz...vKSjbEc==="
```

3. **`dlt.yml`**: ユーザー定義の環境変数を参照して、[プロジェクト マニフェスト ファイル](../features/projects.md) にライセンス キーを直接追加します。

```yaml
runtime:
  license: { env.MY_ENV_CONTAINING_LICENSE_KEY }
```

次のコマンドを実行すると、ライセンスが正しくインストールされ、有効であることを確認できます:

```sh
$ dlt license show
```

当社のライセンス条項については、[こちら](https://dlthub.com/legal/dlt-plus-eula) をご覧ください。
