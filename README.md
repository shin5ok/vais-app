# Vertex AI Search Web Application

Vertex AI Searchを活用したシンプルなチャットUIアプリケーション

## Setup

```bash
# Install dependencies
make install

# Run development server
make dev
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_SEARCH_DATASTORE_ID=your-datastore-id
VERTEX_AI_SEARCH_LOCATION=global
```

## Deploy

ローカルに Docker をインストールする必要はありません。Cloud Run のソースデプロイ機能を使用して、Google Cloud Buildpacks によりクラウド上でビルドが実行されます。

```bash
# Cloud Run にソースデプロイ (IAP有効化、組み込みドメイン*.run.appを使用)
make deploy
```

> [!IMPORTANT]
> **初回デプロイ時の注意点**
> 組織に紐付いていないプロジェクトの場合、IAP の初回 OAuth 同意画面の設定は GCP コンソールから手動で行う必要があります。警告が出た場合は Cloud Run コンソール → セキュリティタブ → IAP を先に有効化してください。

## IAP Access Management

```bash
# 個別ユーザーへのアクセス付与
make grant-iap-access IAP_MEMBER=user:alice@your-org.com

# 設定状態の確認
make check-iap
```
