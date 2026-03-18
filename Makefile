.PHONY: dev deploy build test install clean

PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= asia-northeast1
SERVICE_NAME ?= vais-app
IMAGE_NAME ?= gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)

install:
	uv sync

dev:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

test:
	uv run pytest -v

build:
	docker build -t $(IMAGE_NAME) .

deploy: build
	docker push $(IMAGE_NAME)
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE_NAME) \
		--platform managed \
		--region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars "GOOGLE_CLOUD_PROJECT=$(PROJECT_ID)"

clean:
	rm -rf __pycache__ .pytest_cache .venv
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
