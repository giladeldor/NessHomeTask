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

## Directory Structure

```
NessHomeTask/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   └── routes/              # API endpoint handlers
│   │       ├── __init__.py
│   │       ├── api.py
│   │       ├── health.py
│   │       ├── assets.py
│   │       └── search.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database setup
│   │   ├── logging_config.py    # Logging configuration
│   │   └── exceptions.py        # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   └── asset.py             # SQLAlchemy models
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── asset_repository.py  # Database access layer
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_service.py     # File upload & processing
│   │   ├── ai_service.py        # AI metadata generation
│   │   └── search_service.py    # Search functionality
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── openai_client.py     # OpenAI API client
│   │   ├── local_vision.py      # BLIP vision model
│   │   └── gemini_client.py     # Google Gemini client (fallback)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request/response models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_validator.py    # File validation utilities
│   │   ├── text_extractor.py    # Text extraction from documents
│   │   ├── helpers.py           # Helper functions
│   │   └── decorators.py        # Custom decorators
│   └── api/
│       ├── __init__.py
│       └── schemas.py           # API schemas
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_local_vision.py
│   ├── test_ai_service.py
│   ├── test_asset_service.py
│   ├── test_text_extractor.py
│   ├── test_search_service.py
│   ├── test_api_endpoints.py
│   └── test_database.py
├── data/
│   └── knowledge_base.db        # SQLite database
├── logs/
│   └── app.log                  # Application logs
├── uploads/
│   └── *.pdf, *.txt, *.jpg      # Uploaded files
├── pyproject.toml               # Poetry dependency configuration
├── docker-compose.yml           # Docker Compose setup
├── Dockerfile                   # Docker image definition
├── pytest.ini                   # Pytest configuration
├── TESTING.md                   # Testing documentation
├── API.md                        # API documentation
├── ARCHITECTURE.md              # This file
├── INSTALLATION.md              # Installation guide
└── README.md                    # Project overview
```

## Component Details

### 1. API Layer (src/app/)

**Responsibility**: Handle HTTP requests and responses

**Components**:
- `main.py`: FastAPI app initialization, middleware, event handlers
- `routes/`: Endpoint handlers for upload, search, download operations
- `schemas.py`: Pydantic models for request/response validation

**Key Features**:
- Async request handling
- Automatic OpenAPI documentation
- Error handling with custom exceptions
- CORS and security headers

### 2. Service Layer (src/services/)

**Responsibility**: Business logic implementation

**Services**:

#### AssetService
- Handles file uploads
- Manages file storage
- Spawns background threads for metadata generation
- Implements text extraction backfill
- Implements image metadata backfill

#### AIService
- Orchestrates AI metadata generation
- Attempts OpenAI first for images
- Falls back to local BLIP vision if OpenAI fails
- Extracts and processes text content
- Manages metadata storage

#### SearchService
- Implements full-text search
- Queries against filename, description, tags, keywords, extracted_text
- Supports pagination
- Case-insensitive matching

### 3. Repository Layer (src/repositories/)

**Responsibility**: Database abstraction

**AssetRepository**:
- CRUD operations on assets
- Metadata management
- Search queries
- Database sessions

### 4. Integration Layer (src/integrations/)

**Responsibility**: External service clients

**Clients**:
- `OpenAIClient`: GPT-4 Vision for image analysis
- `LocalVisionClient`: BLIP for local image analysis (no API calls)
- `GeminiClient`: Google Gemini backup (fallback)

### 5. Utilities (src/utils/)

**Responsibility**: Reusable helper functions

**Utilities**:
- `TextExtractor`: Extract text from PDF, DOCX, TXT files
- `FileValidator`: Validate file types and sizes
- `Helpers`: JSON conversion, filename sanitization
- `Decorators`: Timing, logging decorators

### 6. Database Layer (src/core/)

**Responsibility**: Database configuration and models

**Components**:
- `database.py`: SQLAlchemy setup, session management
- `config.py`: Environment-based configuration
- `models/`: ORM models (Asset, Metadata)

## Data Flow

### File Upload Flow
```
1. User uploads file via /api/upload
2. File validated (type, size)
3. File saved to disk/storage
4. Asset record created in DB
5. Response returned immediately
6. Background thread spawned for metadata:
   a. Extract text (if applicable)
   b. Try OpenAI for AI metadata
   c. Fall back to BLIP if OpenAI fails
   d. Store metadata in DB
```

### Search Flow
```
1. User searches via /api/search?q=term
2. Query transmitted to SearchService
3. ILIKE query runs against multiple columns:
   - filename
   - description
   - tags
   - keywords
   - extracted_text
4. Results paginated and returned
5. Frontend displays with relevance indicators
```

### Image Analysis Flow
```
1. Image uploaded or backfill triggered
2. AIService.generate_metadata() called
3. Try OpenAI Vision API:
   a. Success: return description + tags + keywords
   b. Failure (quota, error): go to step 4
4. Fall back to LocalVisionClient (BLIP):
   a. Load BLIP model (cached after first load)
   b. Analyze image
   c. Return description + tags + keywords
5. Store in Metadata.description, Metadata.tags, Metadata.keywords
6. Image now searchable by content
```

## Asynchronous Processing

### Background Threads
- Metadata generation doesn't block upload
- Text extraction runs in parallel for existing files
- Image analysis runs at startup if needed

### Threading Model
```python
threading.Thread(target=background_function, daemon=True).start()
```

### Database Sessions
Each background thread creates its own session:
```python
db = SessionLocal()  # New session per thread
# ... operations ...
db.close()
```

## Logging Architecture

**Levels**: DEBUG, INFO, WARNING, ERROR

**Sinks**:
- Console output (for development)
- File rotation (5MB, 3 backups) at `logs/app.log`

**Configured Loggers**:
- `src.app.main`: API lifecycle
- `src.services.*`: Service operations
- `src.repositories.*`: Database operations
- `src.integrations.*`: External service calls

**Library Silencing**:
- `pdfminer`, `pdfplumber`: PDF processing noise
- `uvicorn.access`: HTTP access logs (use separate config)
- `sqlalchemy.engine`: SQL debugging (enable with SQL_DEBUG env var)
- `httpx`, `openai`: Client verbosity

## Error Handling

### Custom Exceptions (src/core/exceptions.py)
```python
class AIServiceError(Exception): pass
class FileProcessingError(Exception): pass
```

### HTTP Error Responses
- 400: Bad request (validation error)
- 404: Resource not found
- 413: Payload too large
- 422: Unprocessable entity
- 500: Server error

### Graceful Degradation
- OpenAI fails → Fall back to BLIP
- BLIP fails → Store asset without metadata
- File extraction fails → Continue without extracted_text

## Performance Considerations

### Upload Speed
- Non-blocking: response in <1 second
- Background processing: ~5-30 seconds
- Metadata stored asynchronously

### Search Speed
- ILIKE queries: ~50-200ms (SQLite)
- Indexed columns recommended for production
- PostgreSQL: 10-50ms for large datasets

### Memory Management
- BLIP model: ~500MB loaded once at startup
- Cached singleton: reused for all requests
- Image processing: efficient batch handling

### Scaling Recommendations
1. **Database**: Switch to PostgreSQL with full-text search
2. **Storage**: Use S3/GCS for files, keep paths in DB
3. **Async Tasks**: Use Celery/RQ for long-running jobs
4. **Caching**: Add Redis for search results
5. **Load Balancing**: Multiple Uvicorn instances

## Security Considerations

### Current State
- No authentication (add JWT/OAuth2)
- CORS allows all origins (restrict in production)
- No rate limiting (implement per-IP/user)
- API keys in environment variables (use secrets manager)

### Recommendations
1. Add API key authentication
2. Implement JWT token-based auth
3. Add CORS restrictions
4. Add rate limiting
5. Validate file content (not just extension)
6. Encrypt sensitive metadata
7. Add audit logging

## Testing Strategy

### Unit Tests (tests/test_*.py)
- Test individual components in isolation
- Use mocks for external dependencies
- Fast execution (<1 second each)

### Integration Tests
- Test component interactions
- Use test database
- Test API endpoints end-to-end

### Test Fixtures (conftest.py)
- Reusable test data
- Database setup/teardown
- File fixtures for testing

## Monitoring & Observability

### Logging
- Comprehensive logging at service level
- Structured JSON logging possible
- Log rotation to prevent disk bloat

### Metrics to Track
- File upload count/size
- Search query patterns
- Metadata generation time
- Error rates by component
- Database query performance

### Health Checks
- `/api/health` endpoint
- Database connectivity check
- Disk space availability
- Memory usage monitoring

## Deployment

### Development
```bash
poetry run python -m uvicorn src.app.main:app --reload
```

### Production (Docker)
```bash
docker build -t kms .
docker run -p 8000:8000 -e OPENAI_API_KEY=... kms
```

### Database
- **Dev**: SQLite in-memory or file
- **Prod**: PostgreSQL with SSL

### Environment Variables
```
DATABASE_URL=postgresql://user:pass@host/db
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
LOG_LEVEL=INFO
```

## Future Enhancements

1. **Advanced Search**
   - Faceted search (by file type, date, etc.)
   - Full-text search with TF-IDF ranking
   - Semantic search with embeddings

2. **Collaboration**
   - User accounts and permissions
   - Shared folders
   - Comments and annotations

3. **AI Features**
   - Document summarization
   - Named entity extraction
   - Document classification
   - Multi-language support

4. **Performance**
   - Elasticsearch integration
   - Message queue (RabbitMQ/Kafka)
   - Distributed processing
   - Caching layer (Redis)

5. **Analytics**
   - User activity tracking
   - Popular search terms
   - Document usage statistics
   - Performance metrics dashboard
