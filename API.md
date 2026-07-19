# API Documentation

## Overview
Knowledge Management System API provides endpoints for uploading, organizing, and searching documents with AI-powered metadata extraction.

**Base URL**: `http://localhost:8000/api`

## Interactive API Docs
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Authentication
Currently, the API does not require authentication. In production, implement:
- API Key authentication
- OAuth 2.0 with bearer tokens
- JWT tokens

## Endpoints

### Health Check

#### GET /health
Check if the service is running.

**Response**:
```json
{
  "status": "healthy"
}
```

---

### Assets

#### GET /assets
List all assets in the system.

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 50)

**Response**:
```json
[
  {
    "id": 1,
    "filename": "document.pdf",
    "file_type": "text",
    "file_size": 25000,
    "created_at": "2026-07-19T10:30:00",
    "updated_at": "2026-07-19T10:30:00",
    "metadata": {
      "description": "A PDF document",
      "tags": ["document", "pdf"],
      "keywords": ["text", "content"],
      "extracted_text": "Document content..."
    }
  }
]
```

---

#### GET /assets/{asset_id}
Get details of a specific asset.

**Path Parameters**:
- `asset_id` (int): ID of the asset

**Response**:
```json
{
  "id": 1,
  "filename": "document.pdf",
  "file_type": "text",
  "file_size": 25000,
  "created_at": "2026-07-19T10:30:00",
  "updated_at": "2026-07-19T10:30:00",
  "metadata": {
    "description": "A PDF document",
    "tags": ["document", "pdf"],
    "keywords": ["text", "content"],
    "extracted_text": "Document content..."
  }
}
```

**Error Responses**:
- `404`: Asset not found

---

#### POST /upload
Upload a new file.

**Request**:
- Content-Type: multipart/form-data
- Body:
  - `file` (file): The file to upload (max 10MB)

**Supported Formats**:
- Text: `.txt`
- Documents: `.pdf`, `.doc`, `.docx`
- Images: `.jpg`, `.png`, `.gif`, `.webp`

**Response**:
```json
{
  "id": 2,
  "filename": "new_document.pdf",
  "file_type": "text",
  "file_size": 50000,
  "message": "File uploaded successfully. Metadata generation in progress."
}
```

**Error Responses**:
- `400`: Invalid file format
- `413`: File too large
- `422`: Validation error

---

#### DELETE /assets/{asset_id}
Delete an asset and its metadata.

**Path Parameters**:
- `asset_id` (int): ID of the asset to delete

**Response**:
```json
{
  "message": "Asset deleted successfully",
  "id": 1
}
```

**Error Responses**:
- `404`: Asset not found

---

#### GET /assets/{asset_id}/download
Download an asset file.

**Path Parameters**:
- `asset_id` (int): ID of the asset

**Response**:
- Binary file content with appropriate Content-Type header

**Error Responses**:
- `404`: Asset not found

---

### Search

#### GET /search
Search for assets by filename, description, tags, keywords, or extracted text content.

**Query Parameters**:
- `q` (string): Search query (required)
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 50)

**Response**:
```json
[
  {
    "id": 1,
    "filename": "document.pdf",
    "file_type": "text",
    "file_size": 25000,
    "created_at": "2026-07-19T10:30:00",
    "metadata": {
      "description": "A PDF document containing search term",
      "tags": ["document", "pdf"],
      "keywords": ["text", "search"],
      "extracted_text": "Document content..."
    }
  }
]
```

**Examples**:

Search by filename:
```
GET /search?q=invoice
```

Search by content (images and documents):
```
GET /search?q=mountain+landscape
```

Search with pagination:
```
GET /search?q=python&page=2&per_page=25
```

---

## Data Types

### Asset
```json
{
  "id": "integer (unique)",
  "filename": "string",
  "file_type": "string (text|image)",
  "file_size": "integer (bytes)",
  "file_path": "string (internal use)",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```

### Metadata
```json
{
  "id": "integer",
  "asset_id": "integer (foreign key)",
  "description": "string (1-2 sentences)",
  "tags": "JSON array of strings",
  "keywords": "JSON array of strings",
  "extracted_text": "string (for text files only)"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `413`: Payload Too Large
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

## Rate Limiting
Currently unlimited. In production, implement rate limiting:
- Per-IP limits
- Per-user limits
- Burst limits

## CORS
Currently allows all origins. Configure in production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Examples

### Upload and Search Workflow

```bash
# 1. Upload a file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# Response: {"id": 5, "filename": "document.pdf", ...}

# 2. Search for content
curl "http://localhost:8000/api/search?q=machine+learning"

# 3. Get asset details
curl http://localhost:8000/api/assets/5

# 4. Download file
curl http://localhost:8000/api/assets/5/download --output document.pdf
```

### Using Python Requests

```python
import requests

# Upload
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/upload', files=files)
asset_id = response.json()['id']

# Search
response = requests.get('http://localhost:8000/api/search', 
                       params={'q': 'search term'})
results = response.json()

# Download
response = requests.get(f'http://localhost:8000/api/assets/{asset_id}/download')
with open('downloaded_file.pdf', 'wb') as f:
    f.write(response.content)
```

## Metadata Generation

### Text Files
- Extracted text content indexed
- Automatically analyzed for keywords
- No external API calls

### Images
- Local BLIP vision model analyzes content
- Generates description, tags, and keywords
- No external API costs (runs locally)

### PDF Documents
- Text extracted using pdfplumber
- Full-text search enabled
- Optional metadata generation

## Performance

### Upload Speed
- Returns immediately after file save
- Metadata generation happens in background
- No blocking on AI processing

### Search Speed
- Full-text search: <100ms for typical database
- Results include relevance scoring
- Pagination for large result sets

### Image Processing
- ~3-5 seconds per image with BLIP
- Runs in background thread
- No impact on upload response time
