# Testing Guide

## Overview
This project uses pytest for unit and integration testing with comprehensive coverage of all major components.

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test File
```bash
pytest tests/test_local_vision.py
```

### Specific Test Class
```bash
pytest tests/test_local_vision.py::TestLocalVisionClient
```

### Specific Test Method
```bash
pytest tests/test_local_vision.py::TestLocalVisionClient::test_initialization
```

### With Coverage Report
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Run Only Fast Tests (exclude slow)
```bash
pytest -m "not slow"
```

### Run Specific Category
```bash
pytest -m unit      # Unit tests only
pytest -m integration  # Integration tests only
pytest -m api      # API tests only
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_local_vision.py     # Local BLIP vision tests
├── test_ai_service.py       # AI service tests
├── test_asset_service.py    # Asset management tests
├── test_text_extractor.py   # Text extraction tests
├── test_search_service.py   # Search functionality tests
├── test_api_endpoints.py    # API endpoint tests
└── test_database.py         # Database operation tests
```

## Available Fixtures

### Database Fixtures
- `test_db_path`: Temporary test database path
- `test_db_session`: SQLAlchemy session for testing
- `asset_repository`: AssetRepository instance
- `test_asset`: Sample asset object
- `test_metadata`: Sample metadata object

### File Fixtures
- `sample_image_path`: Temporary test image file
- `sample_text_file`: Temporary test text file
- `sample_pdf_file`: Temporary test PDF file

### Service Fixtures
- `ai_service`: AIService instance
- `search_service`: SearchService instance
- `client`: FastAPI TestClient

## Writing New Tests

### Example Unit Test
```python
def test_example_functionality(sample_text_file: Path) -> None:
    """Test example functionality."""
    result = some_function(sample_text_file)
    assert result is not None
    assert result == expected_value
```

### Example Integration Test
```python
@pytest.mark.integration
def test_full_workflow(client: TestClient, sample_image_path: Path) -> None:
    """Test complete upload and search workflow."""
    # Upload file
    response = client.post("/api/upload", files={"file": open(sample_image_path, "rb")})
    assert response.status_code == 200
    
    # Search
    search_response = client.get("/api/search?q=test")
    assert search_response.status_code == 200
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality() -> None:
    pass

@pytest.mark.integration
def test_integration_workflow() -> None:
    pass

@pytest.mark.slow
def test_slow_operation() -> None:
    pass

@pytest.mark.api
def test_api_endpoint() -> None:
    pass
```

## Coverage Goals

Target minimum coverage:
- **Overall**: 80%
- **Core Services**: 90%
- **Database Layer**: 85%
- **API Endpoints**: 80%

View coverage report:
```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Open report
open htmlcov/index.html
```

## Mocking and Patching

Mock external APIs to avoid costs:

```python
from unittest.mock import patch, MagicMock

def test_with_mocked_api(ai_service):
    with patch.object(ai_service.client, 'generate_metadata_for_image') as mock:
        mock.return_value = {"description": "test"}
        result = ai_service.generate_metadata(file_path, "image")
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Scheduled daily runs

See `.github/workflows/tests.yml` for CI/CD configuration.

## Debugging Failed Tests

```bash
# Show print statements
pytest -s

# Drop to debugger on failure
pytest --pdb

# Verbose output
pytest -vv

# Show local variables on failure
pytest -l
```

## Performance Testing

For slow operations:

```bash
pytest --durations=10  # Show slowest 10 tests
pytest --durations=0   # Show all test durations
```
