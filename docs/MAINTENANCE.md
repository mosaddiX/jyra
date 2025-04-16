# Jyra AI Companion Maintenance Guide

This document provides instructions for maintaining and optimizing the Jyra AI Companion.

## Table of Contents
- [Testing](#testing)
- [Database Optimization](#database-optimization)
- [Cache Management](#cache-management)
- [Security Checks](#security-checks)
- [Scheduled Maintenance](#scheduled-maintenance)

## Testing

Jyra includes a test suite to ensure basic functionality is working correctly.

### Running Tests

To run the tests:

```bash
# Make sure you're in the project root directory
cd /path/to/jyra

# Install coverage package if needed
pip install coverage

# Run unit tests
python run_tests.py --type unit --verbose

# Run integration tests (requires API keys)
python run_tests.py --type integration --verbose

# Run all tests with coverage report
python run_tests.py --coverage
```

### Test Types

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test how components work together
- **Coverage Reports**: Show which parts of the code are tested

### Note on Test Coverage

The current test suite provides basic coverage of core functionality. Most tests are designed to verify that components can be imported and basic functions work correctly. For more comprehensive testing, additional test cases should be added.

### Test Organization

Tests are organized into the following directories:

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions

Key test files include:

- `tests/unit/test_basic.py` - Basic functionality tests
- `tests/unit/test_security.py` - Security check tests
- `tests/integration/test_ffmpeg.py` - FFmpeg functionality tests
- `tests/integration/test_gemini_ai.py` - Gemini AI integration tests
- `tests/integration/test_sentiment_analyzer.py` - Sentiment analysis tests

## Database Optimization

The database can become fragmented over time, leading to slower performance. Regular optimization helps maintain performance.

### Running Database Optimization

```bash
# Make sure you're in the project root directory
cd /path/to/jyra

# Basic optimization
python -m scripts.optimize_db

# Clean up old conversations (older than 30 days)
python -m scripts.optimize_db --cleanup --days 30
```

### What It Does

- **VACUUM**: Rebuilds the database file to reduce fragmentation
- **ANALYZE**: Updates statistics used by the query planner
- **Cleanup**: Removes old conversation data to reduce database size

## Cache Management

Jyra uses caching to reduce API calls and improve response time. The cache should be cleared periodically to free up disk space.

### Managing the Cache

```bash
# Make sure you're in the project root directory
cd /path/to/jyra

# Clear cache entries older than 24 hours
python -m scripts.clear_cache --age 24

# Force clear all cache entries
python -m scripts.clear_cache --force
```

### Cache Settings

The cache settings can be adjusted in the `jyra/ai/models/gemini_direct.py` file:

- **Cache Location**: `data/cache`
- **Default Max Age**: 3600 seconds (1 hour)
- **Cache Eligibility**: Responses with temperature between 0.6 and 0.8

## Security Checks

Regular security checks help identify potential vulnerabilities in the codebase.

### Running Security Checks

```bash
# Make sure you're in the project root directory
cd /path/to/jyra

# Run all security checks
python -m scripts.security_check
```

### What It Checks

- **API Keys**: Looks for exposed API keys in the codebase
- **Dependencies**: Checks for vulnerable dependencies using safety
- **File Permissions**: Ensures sensitive files have proper permissions

## Scheduled Maintenance

For optimal performance, schedule the following maintenance tasks:

### Daily
- Clear cache entries older than 24 hours:
  ```bash
  python -m scripts.clear_cache --age 24
  ```

### Weekly
- Run security checks:
  ```bash
  python -m scripts.security_check
  ```
- Run tests to ensure everything is working:
  ```bash
  python -m pytest
  ```

### Monthly
- Optimize the database and clean up old conversations:
  ```bash
  python run_maintenance.py optimize_db --cleanup --days 30
  ```
- Update dependencies:
  ```bash
  pip install -U -r requirements.txt
  ```

## Troubleshooting

### Common Issues

#### ModuleNotFoundError: No module named 'jyra'
Make sure you're running the scripts from the project root directory, or add the project root to your Python path:

```bash
# Option 1: Run from project root
cd /path/to/jyra
python -m scripts.script_name

# Option 2: Add to Python path
export PYTHONPATH=/path/to/jyra:$PYTHONPATH  # Linux/Mac
set PYTHONPATH=C:\path\to\jyra;%PYTHONPATH%  # Windows
```

#### Database Locked
If you get a "database is locked" error, make sure no other process is using the database:

```bash
# Check for running processes
ps aux | grep jyra  # Linux/Mac
tasklist | findstr python  # Windows
```

#### API Rate Limits
If you're hitting API rate limits, adjust the caching settings to reduce API calls:

1. Increase the cache max age in `GeminiAI.__init__`
2. Implement rate limiting as described in the code comments
