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

```bash
make deploy
```
