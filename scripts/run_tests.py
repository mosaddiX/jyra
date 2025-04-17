#!/usr/bin/env python
"""
Test runner for Jyra AI Roleplay Bot
"""

import os
import sys
import argparse
import unittest
import importlib
import coverage


def run_tests(test_type=None, verbose=False, use_coverage=False):
    """
    Run the tests using unittest instead of pytest.

    Args:
        test_type (str): Type of tests to run (unit, integration, or all)
        verbose (bool): Whether to show verbose output
        use_coverage (bool): Whether to generate coverage report
    """
    # Add the current directory to the Python path
    current_dir = os.path.abspath(os.path.dirname(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Set up test discovery
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # Manually load test modules instead of using discover
    if test_type == "unit" or test_type == "all":
        print("Loading unit tests...")
        unit_test_dir = os.path.join(current_dir, "tests", "unit")
        if os.path.exists(unit_test_dir):
            for file in os.listdir(unit_test_dir):
                if file.startswith("test_") and file.endswith(".py"):
                    module_name = f"tests.unit.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        tests = test_loader.loadTestsFromModule(module)
                        test_suite.addTests(tests)
                        print(f"  Loaded {module_name}")
                    except Exception as e:
                        print(f"  Error loading {module_name}: {str(e)}")
        else:
            print(f"  Unit test directory not found: {unit_test_dir}")

    if test_type == "integration" or test_type == "all":
        print("Loading integration tests...")
        integration_test_dir = os.path.join(
            current_dir, "tests", "integration")
        if os.path.exists(integration_test_dir):
            for file in os.listdir(integration_test_dir):
                if file.startswith("test_") and file.endswith(".py"):
                    module_name = f"tests.integration.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        tests = test_loader.loadTestsFromModule(module)
                        test_suite.addTests(tests)
                        print(f"  Loaded {module_name}")
                    except Exception as e:
                        print(f"  Error loading {module_name}: {str(e)}")
        else:
            print(
                f"  Integration test directory not found: {integration_test_dir}")

    # Set up test runner
    verbosity = 2 if verbose else 1
    test_runner = unittest.TextTestRunner(verbosity=verbosity)

    # Run with coverage if requested
    if use_coverage:
        cov = coverage.Coverage(source=["jyra"])
        cov.start()
        result = test_runner.run(test_suite)
        cov.stop()
        cov.save()

        print("\nCoverage Report:")
        cov.report()
        cov.html_report(directory="htmlcov")
        print(f"HTML coverage report generated in 'htmlcov' directory")
    else:
        result = test_runner.run(test_suite)

    # Return success if all tests passed
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run tests for Jyra AI Roleplay Bot")
    parser.add_argument("--type", choices=["unit", "integration", "all"], default="all",
                        help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show verbose output")
    parser.add_argument("--coverage", "-c", action="store_true",
                        help="Generate coverage report")

    args = parser.parse_args()

    # Run the tests
    sys.exit(run_tests(args.type, args.verbose, args.coverage))
