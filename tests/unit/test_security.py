"""
Unit tests for security check functions
"""

import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '')))

from scripts.security_check import check_api_keys, check_dependencies, check_file_permissions

class TestSecurityChecks(unittest.TestCase):
    """Test security check functions."""
    
    def test_api_key_check(self):
        """Test the API key check function."""
        # This should return 0 or a positive number
        result = check_api_keys()
        self.assertIsInstance(result, int, "API key check should return an integer")
        self.assertGreaterEqual(result, 0, "API key check should return a non-negative number")
    
    def test_dependency_check(self):
        """Test the dependency check function."""
        # This might return -1 if safety is not installed
        result = check_dependencies()
        self.assertIsInstance(result, int, "Dependency check should return an integer")
    
    def test_file_permission_check(self):
        """Test the file permission check function."""
        # This should return 0 or a positive number
        result = check_file_permissions()
        self.assertIsInstance(result, int, "File permission check should return an integer")
        self.assertGreaterEqual(result, 0, "File permission check should return a non-negative number")

if __name__ == '__main__':
    unittest.main()
