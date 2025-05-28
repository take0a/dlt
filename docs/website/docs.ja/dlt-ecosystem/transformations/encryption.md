---
title: Data security and encryption
description: Transforming the data for encryption in transit, client-side encryption, and encryption at rest.
keywords: [transform, data security, encryption]
---

# データセキュリティと暗号化

現代のデータ環境では、機密情報をライフサイクル全体にわたって保護するための強力なセキュリティ対策が求められます。組織は、ますます巧妙化する脅威からデータを保護するために、包括的な暗号化戦略を導入する必要があります。

### ライフサイクル全体にわたる暗号化

データは、システム間を移動中（転送中）と保存中の両方で脆弱です。DLTは両方のニーズに対応します。

- **転送中のデータ**:

    転送中にデータが傍受または改ざんされる可能性があります。安全なプロトコル（SSL/TLSなど）や暗号化された接続文字列を使用することで、不正アクセスを防ぎ、機密性を確保できます。
    
- **クライアント側暗号化**:

    送信前にクライアント側でデータを暗号化することで、セキュリティがさらに強化されます。AWS Encryption SDK、Google Tink、Azure Key Vault などのライブラリを使用することで、組織はデータが送信元から送信される前に暗号化され、暗号化キーの管理を維持し、送信経路全体にわたって機密情報を保護できます。
    
- **保存データ / サーバーサイド暗号化**:

    ストレージシステムが侵害された場合でも、保存データの暗号化により不正アクセスを防止します。dltは、ディスク暗号化（BitLocker、FileVault、dm-crypt/LUKSなど）または保存先のサーバーサイド暗号化を活用して、ローカルマシンとクラウドの両方でデータを安全に保ちます。
    

この階層型アプローチにより、抽出から保存までのデータの移動のあらゆる段階を網羅した包括的な保護が保証されます。

## クライアント側暗号化

### なぜクライアント側暗号化が必要なのでしょうか?

クライアントサイド暗号化により、データが環境から送信される前に暗号化できます。これにより、以下のことが可能になります:

- **暗号化キーの完全な制御を維持** (多くの場合、AWS KMS、Google Cloud KMS、Azure Key Vault などの KMS ソリューションを通じて管理されます)。
- **データは転送中および送信先での保存中、送信先のセキュリティが侵害された場合でも保護された状態を維持** します。

### 一般的なクライアント側暗号化ツール

- AWS Encryption SDK
- Tink by Google
- Azure Key Vault & Blob Client-Side Encryption
- OpenSSL


## 転送中の暗号化とサーバー側の暗号化

### dlt の作業ディレクトリの暗号化パーティション

dlt はデータをローカルで抽出・処理してから出力先にロードするため、ローカルディスク上のファイルには機密データが含まれています。これらのファイルが存在するパーティションを暗号化することで、ローカルシステム上で保存されているデータが確実に保護されます。保存されているデータを保護するために、以下のシステムをご利用いただけます。

- **Windows**: BitLocker
- **macOS**: FileVault
- **Linux**: dm-crypt/LUKS, Loop-AES

### 転送中の暗号化

データが宛先へ転送される際に暗号化することも同様に重要です。dlt を使用すると、接続文字列を設定して暗号化を強制できます。ターゲットのデータベースまたはストレージに応じて、次のようなオプションがあります。

- すべての通信で TLS/SSL が使用されるように、**接続文字列** に `Encrypt=yes` と `encrypt=true` を追加する。
- クラウドベースの宛先には、HTTPS などの安全なプロトコルを使用する。

### サーバーサイド暗号化

サーバーサイド暗号化 (SSE) は、データが送信先に到着した時点で暗号化することで、クライアントサイド暗号化を補完します。人気のサービスには以下が含まれます。

- **Amazon S3 SSE**: SSE-S3 (AWS 管理のキーを使用) または SSE-KMS (AWS KMS のカスタマー管理のキーを使用) を提供します。
- **BigQuery**: カスタマー管理の暗号化キー (CMEK) のオプションを提供し、よりきめ細かなキー管理を可能にします。

## DLTにおける暗号化の管理

### 暗号化パイプラインの設定手順

1. **暗号化キーのプロビジョニング**: お好みのクラウドKMSまたはオンプレミスソリューションを使用して、暗号化キーを作成および管理します。
2. **クライアント側ライブラリとの統合**: 適切な暗号化SDK（例：AWS Encryption SDK）を環境にインストールして設定します。
3. **暗号化ロジックの組み込み**: dltリソース関数を変更し、機密フィールドを宛先にロードする前に暗号化します。
4. **テストと検証**: データが暗号化され、キーを使用して正しく復号できることを確認します。

以下は、dltでデータをロードする前に、AWS KMSを使用してネストされたデータ構造内の特定のフィールドを暗号化する方法を示した例です。同じ原則は、Google TinkやAzure Key Vaultなどの他の暗号化ライブラリにも適用できます。

:::note
デモ用に、スクリプトには「KMS_KEY_ARN」、「aws_access_key_id」、「aws_secret_access_key」が含まれています。ただし、これらを dlt `secrets.toml` または安全な保管庫に保存するのがベストプラクティスです。
:::

```py
import boto3
import dlt
import aws_encryption_sdk
from aws_encryption_sdk import CommitmentPolicy
from aws_encryption_sdk.key_providers.kms import KMSMasterKey

# Define the KMS Key ARN
KMS_KEY_ARN = (
    "arn:aws:kms:<region>:<number>:key/<key>"
)

# Create a boto3 client for AWS KMS
kms_client = boto3.client(
    "kms",
    region_name="<region-name>",
    aws_access_key_id="your aws access key",
    aws_secret_access_key="your aws secret key",
)

# Create the KMS Master Key
master_key = KMSMasterKey(key_id=KMS_KEY_ARN, client=kms_client)

# Instantiate the AWS Encryption SDK client
client = aws_encryption_sdk.EncryptionSDKClient(
    commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_REQUIRE_DECRYPT
)

#Encryption function
def encryption_func(record):
    """
    Encrypts the 'security_key' for each child in a given record.
    """
    for child in record.get("children", []):
        # Convert the security key to bytes for encryption
        key_to_encrypt = str(child["security_key"]).encode("utf-8")
        try:
            # Encrypt the security key using the provided master key
            ciphertext, _ = client.encrypt(
                source=key_to_encrypt, key_provider=master_key
            )
            # Replace the plain key with the encrypted data in hex format
            child["security_key"] = ciphertext.hex()
        except Exception as e:
            print(
                f"Failed to encrypt security key for child_id {child['child_id']}: {e}"
            )
            raise
    return record


# Define the raw data structure
raw_data = [
    {
        "parent_id": 1,
        "parent_name": "Alice",
        "children": [
            {"child_id": 1, "child_name": "Child 1", "security_key": 12345},
            {"child_id": 2, "child_name": "Child 2", "security_key": 67891},
        ],
    },
    {
        "parent_id": 2,
        "parent_name": "Bob",
        "children": [
            {"child_id": 3, "child_name": "Child 3", "security_key": 999111}
        ],
    },
]

#dlt resource
@dlt.resource(name="data_test", write_disposition={"disposition": "replace"})
def data_source():
    yield from raw_data


if __name__ == "__main__":
    # Apply the encryption transformation using add_map
    data_encrypted = data_source().add_map(encryption_func)

    # Configure and run the pipeline
    pipeline = dlt.pipeline(
        pipeline_name="pipeline",
        destination="duckdb",
        dataset_name="dataset",
    )
    load_info = pipeline.run(data_encrypted)
    print(load_info)
```

このコードでは、次の処理が行われます。

- AWS Encryption SDK を使用して、dlt でデータをロードする前に `security_key` フィールドを暗号化します。
- このパターンを適用して、他の機密フィールドを暗号化したり、異なる暗号化ライブラリを統合したりできます。
- クライアント側の暗号化には、さまざまな暗号化方式を使用できます。

## セキュリティのベストプラクティス

**1. クライアント側とサーバー側の暗号化を組み合わせる**

セキュリティを最大限に高めるには、クライアント側でデータを暗号化し、送信先でもサーバー側の暗号化を有効にします。これにより、セキュリティレイヤーの1つが機能しなくなったり、構成が誤っていたりしても、データのセキュリティが確保されます。

**2. 鍵の管理とローテーション**

AWS KMS、Google Cloud KMS、Azure Key Vault などの専用の鍵管理サービス (KMS) を使用して、暗号化鍵を保存および管理します。鍵は定期的にローテーションし、厳格なアクセス制御を実施します。

**3. インフラストラクチャのセキュリティ保護**

dlt がデータを抽出および処理するローカルディスクまたはパーティションを暗号化し、システムに保存されているデータが保護されるようにします (例: BitLocker、FileVault、dm-crypt/LUKS)。

**4. 監視と監査**

異常なアクセスパターンを監視する機能を実装し、監査用に詳細なログを保持します。AWS CloudTrail や Azure Monitor などのサービスを利用すれば、誰がいつ鍵にアクセスしたかに関する分析情報を得ることができます。

**5.検証とテスト**

ステージング環境またはQA環境で、暗号化および復号化ワークフローを定期的にテストしてください。バックアップからデータを復元できること、暗号化プロセスによってボトルネックやエラーが発生しないことを確認してください。
