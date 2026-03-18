# 現在の絶対パスを取得
CURRENT_DIR := $(shell pwd)

# パスの末尾が "/.devcontainer" であれば削除してプロジェクトルートを特定
# (sed を使って末尾の /.devcontainer を除去します)
PROJECT_PATH := $(shell echo "$(CURRENT_DIR)" | sed 's|/\.devcontainer$$||')

# DevContainer が付与するラベルを使って ID を取得
CONTAINER_IDS := $(shell docker ps -aq --filter "label=devcontainer.local_folder=$(PROJECT_PATH)")
IMAGE_IDS := $(shell docker images -q --filter "label=devcontainer.local_folder=$(PROJECT_PATH)")

.PHONY: help status stop rm-container rm-image clean build all-clean all-build

build: ## Dockerfile からイメージをビルド
	@echo "Building image for $(PROJECT_PATH)..."
	docker build -t dev-container --label "devcontainer.local_folder=$(PROJECT_PATH)" .

all-build: all-clean ## 全てを再ビルド (キャッシュなし)
	@echo "Rebuilding image for $(PROJECT_PATH) without cache..."
	docker build --no-cache -t dev-container --label "devcontainer.local_folder=$(PROJECT_PATH)" .

all-clean: clean ## 全てを削除

help: ## ヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

status: ## 認識されているプロジェクトパスとIDを表示
	@echo "Detected Project Root: $(PROJECT_PATH)"
	@if [ -z "$(CONTAINER_IDS)" ]; then echo "Container IDs: (None)"; else echo "Container IDs: $(CONTAINER_IDS)"; fi
	@if [ -z "$(IMAGE_IDS)" ]; then echo "Image IDs:     (None)"; else echo "Image IDs:     $(IMAGE_IDS)"; fi

stop: ## コンテナを停止
	@if [ -n "$(CONTAINER_IDS)" ]; then \
		echo "Stopping containers..."; \
		docker stop $(CONTAINER_IDS); \
	else \
		echo "No containers to stop."; \
	fi

rm-container: stop ## コンテナを停止して削除
	@if [ -n "$(CONTAINER_IDS)" ]; then \
		echo "Removing containers..."; \
		docker rm $(CONTAINER_IDS); \
	else \
		echo "No containers to remove."; \
	fi

rm-image: ## イメージを削除
	@if [ -n "$(IMAGE_IDS)" ]; then \
		echo "Removing images..."; \
		docker rmi -f $(IMAGE_IDS); \
	else \
		echo "No images to remove."; \
	fi

clean: rm-container rm-image ## コンテナとイメージをすべて削除
