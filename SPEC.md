# Vertex AI Search Web Application

## 概要
Vertex AI Search を活用したシンプルなチャットUIを持つWebアプリケーション

## 技術スタック
- **Backend**: Python 3.12, FastAPI
- **Frontend**: HTMX + HTML/CSS
- **Infrastructure**: Cloud Run
- **Search Engine**: Vertex AI Search
- **認証・認可**: Cloud IAP (Identity-Aware Proxy)

## 機能要件
1. シンプルなチャットUI（Google Workspace Gemini App風）
2. 継続的な会話セッション
3. Vertex AI Search との連携
4. マークダウン形式の回答をHTMLとしてレンダリング
5. 回答の引用元（citations）リンクを表示

## 非機能要件
- `make dev` でローカル開発環境起動
- `make deploy` で Cloud Run へソースデプロイ（Google Cloud Buildpacks使用）
- `make setup-iap` で Cloud IAP の設定（初回のみ）
- Dev Container による共通開発環境の提供
- **アクセス制御**: Cloud IAP により、セキュアなアクセス環境を提供（Cloud Run 組み込みドメインを利用）

## アクセス制御
- Cloud Run の IAP (Identity-Aware Proxy) を使用してアクセス制御
- `--no-allow-unauthenticated` でパブリックアクセスを禁止
- IAP バックエンドサービスにより、OAuth 2.0 認証を要求
- 個別ユーザーやグループに対し `roles/iap.httpsResourceAccessor` を手動付与して許可する

## 環境変数
| 変数名 | 説明 |
|--------|------|
| GOOGLE_CLOUD_PROJECT | GCPプロジェクトID |
| VERTEX_AI_SEARCH_DATASTORE_ID | Vertex AI Search データストアID |
| VERTEX_AI_SEARCH_LOCATION | ロケーション (default: global) |

## Makefile ターゲット
| ターゲット | 説明 |
|-----------|------|
| `make install` | 依存パッケージのインストール |
| `make dev` | ローカル開発サーバ起動 |
| `make test` | テスト実行 |
| `make build` | Dockerイメージビルド |
| `make deploy` | Cloud Run へソースデプロイ。Google Cloud Buildpacksを使用してクラウド上でビルド |
| `make setup-iap` | IAP の初回セットアップ（OAuth同意画面・バックエンド設定） |
| `make grant-iap-access` | IAP アクセス権限付与 |
| `make clean` | 一時ファイル削除 |

## 設定ファイル
### config/prompts.yaml
要約生成用のシステムプロンプトと設定を管理

```yaml
summary:
  preamble: |
    システムプロンプトをここに記述
  result_count: 5        # 要約に使用する検索結果数
  include_citations: true # 引用を含めるか
```

## API エンドポイント
| Method | Path | 説明 |
|--------|------|------|
| GET | / | メインページ |
| POST | /chat | チャットメッセージ送信 |
| DELETE | /chat | 会話履歴クリア |
