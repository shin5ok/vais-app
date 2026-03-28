.PHONY: dev deploy build test install clean setup-iap grant-iap-access revoke-iap-access check-iap

PROJECT_ID      ?= $(shell gcloud config get-value project)
PROJECT_NUMBER  ?= $(shell gcloud projects describe $(PROJECT_ID) --format="value(projectNumber)")
REGION          ?= asia-northeast1
SERVICE_NAME    ?= vais-app
IMAGE_NAME      ?= gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)

install:
	uv sync

dev:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

test:
	uv run pytest -v

build:
	docker build -t $(IMAGE_NAME) .

## deploy: Cloud Run にソースデプロイし IAP を有効化する
deploy:
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--platform managed \
		--region $(REGION) \
		--no-allow-unauthenticated \
		--iap \
		--command="uvicorn src.main:app --host 0.0.0.0 --port 8080" \
		--set-env-vars "GOOGLE_CLOUD_PROJECT=$(PROJECT_ID)"
	@echo "Granting invoker permission to IAP service agent..."
	gcloud run services add-iam-policy-binding $(SERVICE_NAME) \
		--region=$(REGION) \
		--member="serviceAccount:service-$(PROJECT_NUMBER)@gcp-sa-iap.iam.gserviceaccount.com" \
		--role=roles/run.invoker
	@echo ""
	@echo "✅ Deployed with IAP enabled using Buildpacks on the built-in domain."
	@echo "   Use 'make grant-iap-access IAP_MEMBER=user:user@example.com' to grant access."
	@echo "   Run 'make check-iap' to verify IAP status."

## grant-iap-access: 個別ユーザーに IAP アクセス権限を付与する
##   使い方: make grant-iap-access IAP_MEMBER=user:alice@your-org.com
grant-iap-access:
	@[ -n "$(IAP_MEMBER)" ] || (echo "ERROR: IAP_MEMBER is required. e.g. make grant-iap-access IAP_MEMBER=user:alice@your-org.com" && exit 1)
	gcloud iap web add-iam-policy-binding \
		--member="$(IAP_MEMBER)" \
		--role=roles/iap.httpsResourceAccessor \
		--region=$(REGION) \
		--resource-type=cloud-run \
		--service=$(SERVICE_NAME)

## revoke-iap-access: 個別ユーザーの IAP アクセス権限を削除する
##   使い方: make revoke-iap-access IAP_MEMBER=user:alice@your-org.com
revoke-iap-access:
	@[ -n "$(IAP_MEMBER)" ] || (echo "ERROR: IAP_MEMBER is required. e.g. make revoke-iap-access IAP_MEMBER=user:alice@your-org.com" && exit 1)
	gcloud iap web remove-iam-policy-binding \
		--member="$(IAP_MEMBER)" \
		--role=roles/iap.httpsResourceAccessor \
		--region=$(REGION) \
		--resource-type=cloud-run \
		--service=$(SERVICE_NAME)

## check-iap: IAP の設定状態を確認する
check-iap:
	@echo "=== IAP Status for $(SERVICE_NAME) ==="
	gcloud run services describe $(SERVICE_NAME) \
		--region=$(REGION) \
		--format="yaml(iap)"
	@echo ""
	@echo "=== IAP IAM Policy ==="
	gcloud iap web get-iam-policy \
		--region=$(REGION) \
		--resource-type=cloud-run \
		--service=$(SERVICE_NAME)

clean:
	rm -rf __pycache__ .pytest_cache .venv
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
