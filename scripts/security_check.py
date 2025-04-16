#!/usr/bin/env python
"""
Security check script for Jyra
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

try:
    from jyra.utils.logger import setup_logger
except ImportError:
    # Fallback logger if jyra module is not available
    import logging

    def setup_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

logger = setup_logger(__name__)


def check_api_keys():
    """
    Check for exposed API keys in the codebase.
    """
    logger.info("Checking for exposed API keys...")

    # Patterns to look for
    patterns = [
        r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
        r'token\s*=\s*["\']([^"\']+)["\']',
        r'secret\s*=\s*["\']([^"\']+)["\']',
        r'password\s*=\s*["\']([^"\']+)["\']',
        r'GEMINI_API_KEY\s*=\s*["\']([^"\']+)["\']',
        r'TELEGRAM_TOKEN\s*=\s*["\']([^"\']+)["\']'
    ]

    # Files to exclude
    exclude_files = [
        '.env',
        '.env.example',
        'security_check.py'
    ]

    # Directories to exclude
    exclude_dirs = [
        '.git',
        'venv',
        '__pycache__',
        'data/cache'
    ]

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith('.py') and file not in exclude_files:
                python_files.append(os.path.join(root, file))

    # Check each file
    issues_found = 0
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                content = f.read()

                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Check if it's an environment variable reference
                        if 'os.environ.get' in content[max(0, match.start() - 20):match.start()]:
                            continue

                        # Check if it's a placeholder
                        value = match.group(1)
                        if value in ['your_api_key', 'your_token', 'your_secret', 'your_password', 'YOUR_API_KEY']:
                            continue

                        logger.warning(
                            f"Potential API key/secret found in {file_path}: {match.group(0)}")
                        issues_found += 1
            except Exception as e:
                logger.error(f"Error reading {file_path}: {str(e)}")

    if issues_found == 0:
        logger.info("No API keys found in the codebase.")
    else:
        logger.warning(
            f"Found {issues_found} potential API keys/secrets in the codebase.")

    return issues_found


def check_dependencies():
    """
    Check for vulnerable dependencies.
    """
    logger.info("Checking for vulnerable dependencies...")

    try:
        # Run safety check
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )

        # Write the output to a temporary file
        with open("pip_list.json", "w") as f:
            f.write(result.stdout)

        # Run safety check on the file
        safety_result = subprocess.run(
            ["safety", "check", "--file=pip_list.json", "--output=text"],
            capture_output=True,
            text=True
        )

        # Clean up
        os.remove("pip_list.json")

        # Check if vulnerabilities were found
        if safety_result.returncode == 0:
            logger.info("No vulnerable dependencies found.")
            return 0
        else:
            # Count the number of vulnerabilities
            vulnerabilities = safety_result.stdout.count("vulnerability found")
            logger.warning(f"Found {vulnerabilities} vulnerable dependencies:")
            logger.warning(safety_result.stdout)
            return vulnerabilities
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        logger.info(
            "To check for vulnerable dependencies, install safety: pip install safety")
        return -1


def check_file_permissions():
    """
    Check for insecure file permissions.
    """
    logger.info("Checking file permissions...")

    # Files that should be restricted
    sensitive_files = [
        '.env',
        'data/jyra.db'
    ]

    issues_found = 0

    # Check based on platform
    if sys.platform == 'win32':
        logger.info("Running Windows-specific permission checks...")

        # On Windows, just check if the files exist and are readable by everyone
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                try:
                    # Try to open the file to check if it's readable
                    with open(file_path, 'r') as _:
                        # If we can read it, check if it should be protected
                        if file_path == '.env':
                            logger.warning(
                                f"File {file_path} exists and is readable by everyone")
                            logger.warning(
                                f"  Fix: On Windows, right-click the file, select Properties > Security > Advanced,")
                            logger.warning(
                                f"        and restrict permissions to only your user account.")
                            issues_found += 1
                        else:
                            logger.info(
                                f"File {file_path} exists and is readable")
                except PermissionError:
                    logger.info(
                        f"File {file_path} exists but is not readable (good)")
                except Exception as e:
                    logger.warning(f"Error checking {file_path}: {str(e)}")
    else:
        # Unix permission checks
        logger.info("Running Unix-specific permission checks...")
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                permissions = os.stat(file_path).st_mode & 0o777
                if permissions & 0o077:  # Check if group or others have any permissions
                    logger.warning(
                        f"Insecure permissions ({oct(permissions)}) on {file_path}")
                    logger.warning(
                        f"  Fix: On Unix, run 'chmod 600 {file_path}' to restrict permissions.")
                    issues_found += 1
                else:
                    logger.info(
                        f"File {file_path} has secure permissions: {oct(permissions)}")

    # Report results
    if issues_found == 0:
        logger.info("No insecure file permissions found.")
    else:
        logger.warning(
            f"Found {issues_found} files with insecure permissions.")

    return issues_found


if __name__ == "__main__":
    print("Running security checks for Jyra AI Roleplay Bot...")

    api_key_issues = check_api_keys()
    dependency_issues = check_dependencies()
    permission_issues = check_file_permissions()

    total_issues = api_key_issues + \
        (dependency_issues if dependency_issues > 0 else 0) + permission_issues

    if total_issues == 0:
        print("\n✅ All security checks passed!")
        sys.exit(0)
    else:
        print(
            f"\n⚠️ Found {total_issues} security issues. Please review the logs.")
        sys.exit(1)
