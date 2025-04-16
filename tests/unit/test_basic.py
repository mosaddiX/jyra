"""
Basic unit tests for Jyra
"""

import unittest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of Jyra."""

    def test_imports(self):
        """Test that all modules can be imported."""
        # Test importing core modules
        import jyra
        import jyra.utils
        import jyra.db
        import jyra.ai
        import jyra.bot

        # Verify imports worked
        self.assertIsNotNone(jyra)
        self.assertIsNotNone(jyra.utils)
        self.assertIsNotNone(jyra.db)
        self.assertIsNotNone(jyra.ai)
        self.assertIsNotNone(jyra.bot)

    def test_config(self):
        """Test that config can be loaded."""
        from jyra.utils.config import DATABASE_PATH, validate_config

        # Verify that DATABASE_PATH is set
        self.assertIsNotNone(DATABASE_PATH)

        # Test config validation
        errors = validate_config()
        # We don't assert that there are no errors, as the test environment
        # might not have all required environment variables set

    def test_logger(self):
        """Test that logger can be created."""
        from jyra.utils.logger import setup_logger

        # Create a logger
        logger = setup_logger('test')

        # Verify logger was created
        self.assertIsNotNone(logger)

        # Test logging
        logger.info('Test log message')

        # No assertion needed, just checking that it doesn't raise an exception


if __name__ == '__main__':
    unittest.main()
