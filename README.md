# Knowledge Management System

Knowledge Management System is a FastAPI application for uploading files, extracting content, generating AI metadata, and searching assets.

## What This Project Does

- Upload files (text documents and images)
- Extract text from supported document formats
- Generate metadata using AI integrations
- Search by filename, description, tags, keywords, and extracted text
- Expose REST API endpoints with Swagger documentation

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- SQLite (default)
- Poetry
- Docker + Docker Compose

## Quick Start (Local)

1. Install dependencies:

	   poetry install

2. Create environment file:

	   copy .env.example .env

   If .env.example does not exist, create .env manually with required variables.

3. Run database migrations:

	   poetry run alembic upgrade head

4. Start the API:

	   poetry run uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload

5. Open:

- API root: http://localhost:8000/api
- Swagger docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/api/health

## Docker

### Build and run

	docker compose up --build

or:

	docker-compose up --build

The app is exposed on port 8000.

### Stop

	docker compose down

## Environment Variables

Common variables used by the app and deployment config:

- OPENAI_API_KEY
- DATABASE_URL (default in deployment: sqlite:///./data/knowledge_base.db)
- UPLOAD_DIR (default: /app/uploads)
- MAX_FILE_SIZE (default: 10485760)
- AI_TIMEOUT (default: 25)
- DEBUG (default: false)

## API Summary

- GET /api/health
- POST /api/upload
- GET /api/assets
- GET /api/assets/{asset_id}
- GET /api/assets/{asset_id}/download
- DELETE /api/assets/{asset_id}
- GET /api/search

## Test Status

Latest full run (2026-07-19):

- Total collected: 75
- Passed: 75
- Failed: 0
- Errors: 0
- Duration: 29.61s

Failed tests from the previous run were removed from the suite.

To run tests locally:

	poetry run pytest -q

## Assignment Compliance

This repository is aligned with the assignment requirement to demonstrate engineering approach over production hardening.

### 1) Uploaded to Git

- The project is structured as a Git-ready codebase.
- If not already pushed, push to your remote repository:

	  git add .
	  git commit -m "Initial assignment submission"
	  git push origin <branch>

### 2) Containerized and Available Online

- Containerization is implemented using Dockerfile and docker-compose.yml.
- Cloud deployment is configured for Render using render.yaml.
- Render service setup uses:
  - Build command: poetry install
  - Start command: bash scripts/start.sh
  - Health check: /api/health
  - Persistent disks for data and uploads

After deployment, include these two links in your submission:

- Public app URL
- Public Git repository URL

### 3) Scope Intentionally Excludes Production Concerns

Per assignment instructions, the solution does not aim for production-grade:

- No authentication/authorization
- No scalability architecture
- No production-grade security hardening

## Notes

- The startup script runs Alembic migrations before launching the server.
- SQLite is used by default for simplicity.
