#!/usr/bin/env python
"""
Cache cleanup script for Jyra.

This script removes old cache files based on age or total cache size.
"""

import os
import time
import argparse
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path("data/cache")
# Default age threshold in days
DEFAULT_AGE_THRESHOLD = 7
# Default size threshold in MB
DEFAULT_SIZE_THRESHOLD = 100


def get_file_age_days(file_path):
    """Get the age of a file in days."""
    file_time = os.path.getmtime(file_path)
    current_time = time.time()
    return (current_time - file_time) / (60 * 60 * 24)


def get_directory_size_mb(directory):
    """Get the size of a directory in megabytes."""
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size / (1024 * 1024)  # Convert to MB


def cleanup_cache(cache_dir=DEFAULT_CACHE_DIR, age_threshold=DEFAULT_AGE_THRESHOLD,
                 size_threshold=DEFAULT_SIZE_THRESHOLD, dry_run=False):
    """
    Clean up cache files based on age and size thresholds.
    
    Args:
        cache_dir (Path): Path to the cache directory
        age_threshold (int): Age threshold in days
        size_threshold (int): Size threshold in MB
        dry_run (bool): If True, don't actually delete files
    
    Returns:
        tuple: (number of files deleted, space freed in MB)
    """
    if not os.path.exists(cache_dir):
        logger.warning(f"Cache directory {cache_dir} does not exist.")
        return 0, 0
    
    # Check if we need to clean up based on total size
    current_size = get_directory_size_mb(cache_dir)
    logger.info(f"Current cache size: {current_size:.2f} MB (threshold: {size_threshold} MB)")
    
    files_to_delete = []
    
    # First, identify files older than the age threshold
    for file_path in Path(cache_dir).glob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            age_days = get_file_age_days(file_path)
            if age_days > age_threshold:
                files_to_delete.append((file_path, age_days, os.path.getsize(file_path) / (1024 * 1024)))
    
    # Sort files by age (oldest first)
    files_to_delete.sort(key=lambda x: x[1], reverse=True)
    
    # If we're still over the size threshold, add more files until we're under
    if current_size > size_threshold:
        remaining_files = [f for f in Path(cache_dir).glob("*") 
                          if f.is_file() and not f.name.startswith('.') and f not in [x[0] for x in files_to_delete]]
        
        # Sort by age (oldest first)
        remaining_files.sort(key=lambda f: os.path.getmtime(f))
        
        # Add files until we're under the threshold
        size_to_free = current_size - size_threshold
        size_freed = sum(x[2] for x in files_to_delete)
        
        for file_path in remaining_files:
            if size_freed >= size_to_free:
                break
                
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            age_days = get_file_age_days(file_path)
            files_to_delete.append((file_path, age_days, file_size_mb))
            size_freed += file_size_mb
    
    # Delete the files
    files_deleted = 0
    space_freed = 0
    
    for file_path, age_days, file_size_mb in files_to_delete:
        if dry_run:
            logger.info(f"Would delete: {file_path.name} (Age: {age_days:.1f} days, Size: {file_size_mb:.2f} MB)")
        else:
            try:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path.name} (Age: {age_days:.1f} days, Size: {file_size_mb:.2f} MB)")
                files_deleted += 1
                space_freed += file_size_mb
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {str(e)}")
    
    if dry_run:
        logger.info(f"Dry run: Would delete {len(files_to_delete)} files, freeing {sum(x[2] for x in files_to_delete):.2f} MB")
    else:
        logger.info(f"Deleted {files_deleted} files, freed {space_freed:.2f} MB")
    
    return files_deleted, space_freed


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clean up Jyra cache files")
    parser.add_argument("--cache-dir", type=str, default=str(DEFAULT_CACHE_DIR),
                        help=f"Cache directory (default: {DEFAULT_CACHE_DIR})")
    parser.add_argument("--age", type=int, default=DEFAULT_AGE_THRESHOLD,
                        help=f"Age threshold in days (default: {DEFAULT_AGE_THRESHOLD})")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE_THRESHOLD,
                        help=f"Size threshold in MB (default: {DEFAULT_SIZE_THRESHOLD})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually delete files, just show what would be deleted")
    
    args = parser.parse_args()
    
    cleanup_cache(
        cache_dir=Path(args.cache_dir),
        age_threshold=args.age,
        size_threshold=args.size,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
