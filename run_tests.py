#!/usr/bin/env python3
"""
ArthSetu — Unified Automated Test Runner
Runs all unit and integration test suites with formatted results.

Usage:
    python run_tests.py
    python run_tests.py --verbose
"""

from __future__ import annotations

import sys
import time
import unittest


def main() -> int:
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    print("=" * 70)
    print("  🏦 ArthSetu Automated Test Suite")
    print("  Evaluating Multi-Agent DAG, Cedar Policy Firewall & AWS Integrations")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_*.py")

    total_tests = suite.countTestCases()
    print(f"\n📦 Discovered {total_tests} automated tests across test modules.\n")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("  📊 Test Execution Summary")
    print("=" * 70)
    print(f"  • Total Tests Run : {result.testsRun}")
    print(f"  • Passed          : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  • Failures        : {len(result.failures)}")
    print(f"  • Errors          : {len(result.errors)}")
    print(f"  • Execution Time  : {elapsed:.2f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print("  ✅ ALL TESTS PASSED PERFECTLY!\n")
        return 0
    else:
        print("  ❌ SOME TESTS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
