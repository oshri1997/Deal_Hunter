# Tests

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run specific test file
```bash
python -m pytest tests/test_config.py -v
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_helpers.py -v
python -m pytest tests/test_sanity.py -v
```

### Run with coverage
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Structure

- `test_config.py` - Configuration tests
- `test_scraper.py` - Scraper unit tests
- `test_helpers.py` - Helper functions tests
- `test_sanity.py` - End-to-end integration tests

## CI/CD

Tests run automatically on GitHub Actions for:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

See `.github/workflows/tests.yml` for configuration.
