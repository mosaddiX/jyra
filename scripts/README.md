# Jyra Utility Scripts

This directory contains utility scripts for maintaining and managing the Jyra AI Companion.

## Maintenance Scripts

- `cleanup_cache.py` - Clean up old cache files based on age and size thresholds
- `clear_cache.py` - Clear all cache files
- `optimize_db.py` - Optimize the SQLite database
- `security_check.py` - Run security checks on the codebase
- `update_memory_schema.py` - Update the memory database schema

## Database Scripts

- `update_admin_field.py` - Update the admin field in the users table
- `update_db_schema.py` - Update the database schema
- `update_memory_db.py` - Update the memory database

## Testing Scripts

- `run_maintenance.py` - Run maintenance tasks
- `run_tests.py` - Run the test suite

## Usage

Most scripts can be run directly from the command line:

```bash
python scripts/script_name.py [arguments]
```

For example:

```bash
python scripts/cleanup_cache.py --age 7 --size 100
```

Use the `--help` flag to see available options for each script:

```bash
python scripts/cleanup_cache.py --help
```
