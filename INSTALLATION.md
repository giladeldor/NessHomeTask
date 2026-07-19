# Installation & Setup Guide

## Prerequisites

- **Python**: 3.10 or later
- **Poetry**: Package manager (v1.2+)
- **Git**: Version control
- **FFmpeg** (optional): For advanced media processing

### System Requirements
- **OS**: macOS, Linux, or Windows
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB for dependencies + model files
- **GPU**: Optional (CUDA for faster image processing)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/knowledge-management-system.git
cd knowledge-management-system
```

### 2. Install Dependencies
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 3. Setup Environment
```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables**:
```env
# Required for image analysis via OpenAI (skip if using local BLIP only)
OPENAI_API_KEY=sk-...

# Optional: Google Gemini fallback
GEMINI_API_KEY=...

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./data/knowledge_base.db

# Logging
LOG_LEVEL=INFO
```

### 4. Initialize Database
```bash
poetry run python -m src.core.database
```

### 5. Run Server
```bash
poetry run python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Access the application**:
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Detailed Setup

### Option A: Local Development (SQLite)

Best for getting started quickly.

```bash
# 1. Install dependencies
poetry install

# 2. Create data directories
mkdir -p data logs uploads

# 3. Initialize database
poetry run python -c "from src.core.database import init_db; init_db()"

# 4. Run development server
poetry run python -m uvicorn src.app.main:app --reload

# 5. Seed sample data (optional)
poetry run python scripts/seed_sample_data.py
```

**Pros**:
- Simple setup
- No external database needed
- Good for testing

**Cons**:
- SQLite limitations for concurrent users
- Not suitable for production

### Option B: Docker Setup

Best for consistency and production-like environment.

```bash
# 1. Build Docker image
docker build -t kms .

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Run with Docker Compose
docker-compose up

# 4. Access application
# http://localhost:8000
```

**Using Docker Compose**:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build --no-cache
```

### Option C: Production Setup (PostgreSQL)

Best for production deployments.

```bash
# 1. Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# 2. Create database
createdb knowledge_db
createuser -d postgres

# 3. Update .env
DATABASE_URL=postgresql://postgres:password@localhost/knowledge_db

# 4. Install dependencies
poetry install --with production

# 5. Initialize database
poetry run python -m src.core.database

# 6. Run production server
poetry run gunicorn src.app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Dependency Management

### Add New Dependency
```bash
poetry add package-name
```

### Add Development Dependency
```bash
poetry add --group dev package-name
```

### Update Dependencies
```bash
poetry update
```

### Lock Dependencies
```bash
poetry lock
```

### View Installed Packages
```bash
poetry show
```

## Configuration

### Environment Variables

```bash
# Application
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
UPLOAD_DIR=./uploads        # File upload directory
DATABASE_URL=...            # Database connection string

# APIs
OPENAI_API_KEY=...          # OpenAI API key for image analysis
GEMINI_API_KEY=...          # Google Gemini API key (optional)

# Features
MAX_FILE_SIZE=10485760      # Max upload size (10MB)
ALLOWED_EXTENSIONS=txt,pdf,doc,docx,jpg,png,gif,webp
```

### Configuration File
Edit `src/core/config.py` to add new settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add your settings here
    my_setting: str = "default_value"
    
    class Config:
        env_file = ".env"
```

## Running Tests

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Test File
```bash
poetry run pytest tests/test_local_vision.py
```

### Run with Coverage
```bash
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Run Specific Test Category
```bash
poetry run pytest -m unit          # Unit tests
poetry run pytest -m integration   # Integration tests
poetry run pytest -m api          # API tests
```

See [TESTING.md](TESTING.md) for more details.

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/my-feature
```

### 2. Install Pre-commit Hooks (optional)
```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

### 3. Format Code
```bash
# Format with Black
poetry run black src tests

# Sort imports with isort
poetry run isort src tests
```

### 4. Lint Code
```bash
# Check with Pylint
poetry run pylint src

# Type checking with mypy
poetry run mypy src
```

### 5. Run Tests
```bash
poetry run pytest
```

### 6. Commit Changes
```bash
git add .
git commit -m "feat: add my feature"
```

### 7. Push and Create PR
```bash
git push origin feature/my-feature
```

## Troubleshooting

### Issue: "Permission denied" on macOS
```bash
# Grant execute permission
chmod +x scripts/setup.sh
```

### Issue: Port 8000 already in use
```bash
# Use different port
poetry run python -m uvicorn src.app.main:app --port 8001

# Or kill process on port 8000
lsof -ti :8000 | xargs kill -9
```

### Issue: BLIP model download fails
```bash
# Download manually and cache
poetry run python -c "
from transformers import BlipProcessor, BlipForConditionalGeneration
BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')
BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base')
"
```

### Issue: Database locked (SQLite)
```bash
# Close all connections
pkill -f "uvicorn"

# Remove database
rm data/knowledge_base.db

# Reinitialize
poetry run python -c "from src.core.database import init_db; init_db()"
```

### Issue: OpenAI API quota exceeded
The system automatically falls back to local BLIP vision processing. No action needed.

### Issue: Out of memory with BLIP
BLIP model is memory-intensive (~500MB). Ensure system has adequate RAM:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
```

## Performance Optimization

### Database Optimization
```sql
-- Add indexes for faster searches
CREATE INDEX idx_asset_filename ON asset(filename);
CREATE INDEX idx_metadata_description ON metadata(description);
```

### Enable Query Caching
Add Redis configuration to `src/core/config.py`:
```python
REDIS_URL = "redis://localhost:6379"
```

### Async Request Processing
Already implemented with background threads. For Celery:
```bash
poetry add celery redis
```

## Monitoring

### View Logs
```bash
# Real-time logs
tail -f logs/app.log

# Search logs
grep "ERROR" logs/app.log
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Database Health
```bash
poetry run python -c "
from src.core.database import SessionLocal
db = SessionLocal()
print('Database connection OK')
db.close()
"
```

## Upgrading

### Upgrade Dependencies
```bash
# Update all dependencies
poetry update

# Update specific package
poetry update package-name

# Preview changes
poetry update --dry-run
```

### Database Migration
When schema changes:
```bash
# Backup database
cp data/knowledge_base.db data/knowledge_base.db.backup

# Run migrations
poetry run alembic upgrade head
```

## Uninstallation

### Remove Virtual Environment
```bash
poetry env remove python3.12
```

### Remove Project
```bash
rm -rf knowledge-management-system
```

## Support

For issues and questions:
1. Check [TESTING.md](TESTING.md) for test-related issues
2. See [API.md](API.md) for API documentation
3. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
4. Create GitHub issue with details
5. Contact development team

## Next Steps

After installation:
1. Run tests to verify setup: `poetry run pytest`
2. Upload sample files via Web UI
3. Test search functionality
4. Review API documentation at `/api/docs`
5. Check logs in `logs/app.log`
