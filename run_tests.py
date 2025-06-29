#!/usr/bin/env python3
"""
Comprehensive test runner for The Oracle I Ching App

This script runs all tests and provides detailed reporting including:
- Unit tests
- Integration tests
- Performance tests
- Coverage reporting
- Profiling information
"""

import unittest
import sys
import os
import time
import cProfile
import pstats
import io
from contextlib import redirect_stdout

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests_with_coverage():
    """Run all tests with coverage reporting"""
    try:
        import coverage

        # Start coverage
        cov = coverage.Coverage(source=['models', 'logic', 'app'])
        cov.start()

        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = 'tests'
        suite = loader.discover(start_dir, pattern='test_*.py')

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)

        # Stop coverage and generate report
        cov.stop()
        cov.save()

        print("\n" + "="*60)
        print("COVERAGE REPORT")
        print("="*60)
        cov.report(show_missing=True)

        # Generate HTML coverage report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")

        return result.wasSuccessful()

    except ImportError:
        print("Coverage package not installed. Running tests without coverage...")
        return run_tests_without_coverage()

def run_tests_without_coverage():
    """Run all tests without coverage reporting"""
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_performance_profile():
    """Run performance profiling on key components"""
    print("\n" + "="*60)
    print("PERFORMANCE PROFILING")
    print("="*60)

    # Profile I Ching casting
    print("\nProfiling I Ching hexagram casting...")
    pr = cProfile.Profile()
    pr.enable()

    try:
        from logic.iching import cast_hexagrams
        for _ in range(100):
            cast_hexagrams()
    except Exception as e:
        print(f"Error in I Ching profiling: {e}")

    pr.disable()

    # Print profiling results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)  # Top 10 functions
    print(s.getvalue())

    # Profile User operations
    print("\nProfiling User operations...")
    pr2 = cProfile.Profile()
    pr2.enable()

    try:
        from models.user import User
        import tempfile

        # Create temporary database for profiling
        test_db_fd, test_db_path = tempfile.mkstemp()

        # Profile user operations
        for i in range(50):
            user = User(f"user{i}", "hash", "1990-01-01", "Test bio")
            user.db_file = test_db_path
            user.save()
            retrieved = User.get_by_username(f"user{i}")

        os.close(test_db_fd)
        os.unlink(test_db_path)

    except Exception as e:
        print(f"Error in User profiling: {e}")

    pr2.disable()

    s2 = io.StringIO()
    ps2 = pstats.Stats(pr2, stream=s2).sort_stats('cumulative')
    ps2.print_stats(10)
    print(s2.getvalue())

def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")

    missing_deps = []

    try:
        import flask
        print("✓ Flask")
    except ImportError:
        missing_deps.append("flask")
        print("✗ Flask")

    try:
        import openai
        print("✓ OpenAI")
    except ImportError:
        missing_deps.append("openai")
        print("✗ OpenAI")

    try:
        import werkzeug
        print("✓ Werkzeug")
    except ImportError:
        missing_deps.append("werkzeug")
        print("✗ Werkzeug")

    try:
        import markdown
        print("✓ Markdown")
    except ImportError:
        missing_deps.append("markdown")
        print("✗ Markdown")

    try:
        import docarray
        print("✓ DocArray")
    except ImportError:
        missing_deps.append("docarray")
        print("✗ DocArray")

    try:
        import coverage
        print("✓ Coverage (optional)")
    except ImportError:
        print("- Coverage (optional - install with: pip install coverage)")

    if missing_deps:
        print(f"\nMissing required dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install " + " ".join(missing_deps))
        return False

    print("\nAll required dependencies are available!")
    return True

def run_quick_smoke_tests():
    """Run quick smoke tests to verify basic functionality"""
    print("\n" + "="*60)
    print("SMOKE TESTS")
    print("="*60)

    errors = []

    # Test 1: Import all modules
    try:
        from models.user import User
        from models.history import History, HistoryEntry
        from logic.iching import Reading, cast_hexagrams
        import app
        print("✓ All modules import successfully")
    except Exception as e:
        errors.append(f"Module import failed: {e}")
        print(f"✗ Module import failed: {e}")

    # Test 2: Basic User operations
    try:
        import tempfile
        test_db_fd, test_db_path = tempfile.mkstemp()

        user = User("smoketest", "hash", "1990-01-01", "Smoke test")
        user.db_file = test_db_path
        success = user.save()

        os.close(test_db_fd)
        os.unlink(test_db_path)

        if success:
            print("✓ User operations work")
        else:
            errors.append("User save operation failed")
            print("✗ User save operation failed")
    except Exception as e:
        errors.append(f"User operations failed: {e}")
        print(f"✗ User operations failed: {e}")

    # Test 3: I Ching casting
    try:
        reading = cast_hexagrams()
        if reading and hasattr(reading, 'Current'):
            print("✓ I Ching casting works")
        else:
            errors.append("I Ching casting returned invalid result")
            print("✗ I Ching casting returned invalid result")
    except Exception as e:
        errors.append(f"I Ching casting failed: {e}")
        print(f"✗ I Ching casting failed: {e}")

    # Test 4: Flask app creation
    try:
        test_app = app.app
        if test_app:
            print("✓ Flask app creation works")
        else:
            errors.append("Flask app creation failed")
            print("✗ Flask app creation failed")
    except Exception as e:
        errors.append(f"Flask app creation failed: {e}")
        print(f"✗ Flask app creation failed: {e}")

    if errors:
        print(f"\nSmoke tests found {len(errors)} issues:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✓ All smoke tests passed!")
        return True

def main():
    """Main test runner function"""
    print("="*60)
    print("THE ORACLE I CHING APP - TEST SUITE")
    print("="*60)

    start_time = time.time()

    # Check dependencies first
    if not check_dependencies():
        print("\nPlease install missing dependencies before running tests.")
        sys.exit(1)

    # Run smoke tests
    if not run_quick_smoke_tests():
        print("\nSmoke tests failed. Please fix basic issues before running full test suite.")
        sys.exit(1)

    # Parse command line arguments
    run_coverage = '--coverage' in sys.argv or '-c' in sys.argv
    run_profile = '--profile' in sys.argv or '-p' in sys.argv
    quick_only = '--quick' in sys.argv or '-q' in sys.argv

    if quick_only:
        print("\nQuick mode: Only running smoke tests.")
        end_time = time.time()
        print(f"\nTotal time: {end_time - start_time:.2f} seconds")
        sys.exit(0)

    # Run main test suite
    print("\n" + "="*60)
    print("RUNNING FULL TEST SUITE")
    print("="*60)

    if run_coverage:
        success = run_tests_with_coverage()
    else:
        success = run_tests_without_coverage()

    # Run performance profiling if requested
    if run_profile:
        run_performance_profile()

    end_time = time.time()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    # Show usage if help requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python run_tests.py [options]")
        print("\nOptions:")
        print("  --coverage, -c    Run tests with coverage reporting")
        print("  --profile, -p     Run performance profiling")
        print("  --quick, -q       Run only smoke tests (quick)")
        print("  --help, -h        Show this help message")
        print("\nExamples:")
        print("  python run_tests.py                    # Run all tests")
        print("  python run_tests.py --coverage         # Run with coverage")
        print("  python run_tests.py --profile          # Run with profiling")
        print("  python run_tests.py --coverage --profile  # Run with both")
        print("  python run_tests.py --quick            # Quick smoke tests only")
        sys.exit(0)

    main()
