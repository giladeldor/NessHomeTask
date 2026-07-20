# Knowledge Management System

Knowledge Management System is a FastAPI-based application for uploading files, extracting document text, generating AI metadata, and searching assets through a simple web interface and REST API.

## What the project does

- Upload text documents, PDFs, Word files, and images.
- Extract and store text from supported document formats.
- Generate descriptions, tags, and keywords using AI integrations.
- Search assets by filename, content, tags, keywords, and extracted text.
- Expose a REST API with Swagger and ReDoc documentation.

## Tech stack

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy + Alembic
- SQLite by default for local use
- Poetry for dependency management
- Docker and Docker Compose for containerized runs
- Render configuration for cloud deployment

## Project structure

```text
src/
  app/            # FastAPI entry point, routes, and static UI
  api/            # API schemas and request/response models
  services/       # Business logic for uploads, search, and metadata
  repositories/   # Database access layer
  integrations/   # OpenAI and local vision clients
  utils/          # Validation and text extraction helpers
tests/            # Pytest suite
uploads/          # Uploaded files
scripts/          # Startup and helper scripts
data/             # Local database and runtime files
```

# Architecture Documentation

## System Overview

Knowledge Management System is a FastAPI-based document management and search platform with AI-powered metadata extraction.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Web UI)                         │
│                    (HTML/JS/Bootstrap)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Routes (routes/)                                │  │
│  │  • Upload, Download, List, Delete, Search            │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │Services│    │Utilities │    │Integrations│
    └────────┘    └──────────┘    └──────────┘
        │
        ├─► asset_service
        ├─► ai_service
        ├─► search_service
        │
        ▼
    ┌─────────────────────────────────────────┐
    │    Repositories (Database Layer)         │
    │    • AssetRepository                     │
    │    • MetadataRepository                  │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │    SQLAlchemy ORM                        │
    │    • Asset Model                         │
    │    • Metadata Model                      │
    └─────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────┐
    │    SQLite Database                       │
    │    (Upgradeable to PostgreSQL)           │
    └─────────────────────────────────────────┘
```


## Quick start

1. Install dependencies:

   ```bash
   poetry install
   ```

2. Create an environment file:

   ```bash
   copy .env.example .env
   ```

   If .env.example is absent, create .env manually and include the required variables.

3. Run database migrations:

   ```bash
   poetry run alembic upgrade head
   ```

4. Start the API:

   ```bash
   poetry run uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. Open the app:

   - Web UI: http://localhost:8000/
   - API root: http://localhost:8000/api
   - Swagger docs: http://localhost:8000/api/docs
   - Health check: http://localhost:8000/api/health

## Docker and container deployment

### Build and run locally

```bash
docker compose up --build
```

Or:

```bash
docker-compose up --build
```

The app is exposed on port 8000.

### Stop the container

```bash
docker compose down
```

### Render deployment

The repository includes a Render configuration file for deployment. The service is set up to use:

- Build command: poetry install
- Start command: bash scripts/start.sh
- Health check: /api/health
- Persistent disks for uploads and data

## Environment variables

Common variables used by the app and deployment setup:

- OPENAI_API_KEY
- DATABASE_URL (defaults to sqlite:///./data/knowledge_base.db in local deployment)
- UPLOAD_DIR (defaults to /app/uploads)
- MAX_FILE_SIZE (defaults to 10485760)
- AI_TIMEOUT (defaults to 25)
- DEBUG (defaults to false)

## API overview

Base URL:

```text
http://localhost:8000/api
```

### Main endpoints

- GET /api/health
- POST /api/upload
- GET /api/assets
- GET /api/assets/{asset_id}
- GET /api/assets/{asset_id}/download
- DELETE /api/assets/{asset_id}
- GET /api/search

### Example requests

Upload a file:

```bash
curl -X POST http://localhost:8000/api/upload -F "file=@document.pdf"
```

Search for content:

```bash
curl "http://localhost:8000/api/search?q=machine+learning"
```

Download an uploaded asset:

```bash
curl http://localhost:8000/api/assets/1/download --output downloaded_file.pdf
```

## Architecture overview

### API layer

Handles HTTP requests and responses for uploads, downloads, listing, deletion, and search.

### Service layer

Contains the core business logic for file validation, storage, metadata generation, text extraction, and search orchestration.

### Repository layer

Provides database access for assets and metadata using SQLAlchemy models.

### Integration layer

Connects the application to AI providers and local vision services. The implementation first tries AI metadata generation and falls back to a local model when needed.

### Database layer

Uses SQLAlchemy with SQLite by default. Alembic is included for migrations.

## Testing

Run the test suite locally:

```bash
poetry run pytest -q
```