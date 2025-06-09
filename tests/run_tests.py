import unittest
import sys
import coverage
from datetime import datetime

def run_tests():
    """Run all tests with coverage reporting."""
    # Start coverage measurement
    cov = coverage.Coverage()
    cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Stop coverage measurement
    cov.stop()
    cov.save()

    # Print coverage report
    print("\n" + "="*50)
    print("Coverage Report")
    print("="*50)
    cov.report()

    # Generate HTML coverage report
    cov.html_report(directory='coverage_html')

    # Print summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    # Print detailed failure information
    if result.failures:
        print("\n" + "="*50)
        print("Failures")
        print("="*50)
        for failure in result.failures:
            print(f"\n{failure[0]}")
            print(failure[1])

    if result.errors:
        print("\n" + "="*50)
        print("Errors")
        print("="*50)
        for error in result.errors:
            print(f"\n{error[0]}")
            print(error[1])

    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    print(f"Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(run_tests()) 