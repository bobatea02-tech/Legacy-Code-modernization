# Legacy Code Modernizer

A secure and robust repository ingestion system for processing legacy code archives.

## Features

### Repository Ingestion Module

The core ingestion module (`app/ingestion/ingestor.py`) provides:

- **Security**: Zip Slip protection against path traversal attacks
- **Validation**: Configurable limits for archive size, file size, and file count
- **Language Detection**: Automatic detection of source file types (.java, .c, .cbl, etc.)
- **Smart Filtering**: Ignores binary files, hidden files, and build directories
- **Encoding Normalization**: Automatic detection and conversion to UTF-8
- **Reproducibility**: SHA256 hashing for file integrity and caching
- **Cross-Platform**: Works on Windows and Linux with proper path handling

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Required settings:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Usage

### Basic Ingestion

```python
from app.ingestion import RepositoryIngestor

# Use context manager for automatic cleanup
with RepositoryIngestor() as ingestor:
    files = ingestor.ingest_zip("path/to/repository.zip")
    
    for file_meta in files:
        print(f"{file_meta.relative_path} ({file_meta.language})")
```

### Custom Configuration

```python
from app.ingestion import RepositoryIngestor, IngestionConfig

# Create custom config
config = IngestionConfig()
config.MAX_ARCHIVE_SIZE_MB = 100
config.MAX_FILE_SIZE_MB = 5
config.MAX_FILE_COUNT = 1000

# Add custom language support
config.LANGUAGE_EXTENSIONS['.py'] = 'python'
config.LANGUAGE_EXTENSIONS['.js'] = 'javascript'

with RepositoryIngestor(config=config) as ingestor:
    files = ingestor.ingest_zip("path/to/repository.zip")
```

See `examples/ingestor_usage.py` for more examples.

## Project Structure

```
.
├── app/
│   ├── core/              # Core configuration and logging
│   │   ├── config.py      # Pydantic settings management
│   │   └── logging.py     # Loguru-based logging
│   └── ingestion/         # Repository ingestion module
│       ├── ingestor.py    # Main ingestion logic
│       └── __init__.py
├── tests/
│   └── test_ingestor.py   # Comprehensive test suite
├── examples/
│   └── ingestor_usage.py  # Usage examples
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md
```

## Testing

Run the test suite:

```bash
pytest tests/test_ingestor.py -v
```

All tests include:
- Basic ingestion workflow
- Language detection
- Security (path traversal protection)
- File size limits
- Ignored directories and files
- SHA256 determinism
- Cleanup verification

## Security Features

### Zip Slip Protection

The ingestion module validates all ZIP archive members before extraction to prevent path traversal attacks:

```python
# This will raise PathTraversalError
malicious_zip = "archive_with_../../etc/passwd.zip"
ingestor.ingest_zip(malicious_zip)  # Raises PathTraversalError
```

### Size Limits

Configurable limits prevent resource exhaustion:
- Archive size: 500MB (default)
- Individual file size: 10MB (default)
- Total file count: 10,000 (default)

## API (Coming Soon)

FastAPI-based REST API for code translation and analysis.

## License

MIT
