#!/usr/bin/env python3
"""
Test Runner - Easy access to all test suites
Provides convenient interface to run individual test suites or master validation
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test_suite(test_name: str) -> int:
    """Run a specific test suite and return exit code."""
    test_file = Path(__file__).parent / "tests" / f"test_{test_name}.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print(f"🧪 Running {test_name} test suite...")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, str(test_file)
        ], cwd=str(Path(__file__).parent))
        
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
        return 1

def show_help():
    """Show usage information."""
    print("Test Runner - Local RAG System")
    print("=" * 40)
    print()
    print("Usage: python run_tests.py [test_name]")
    print()
    print("Available tests:")
    print("  system_health    - Infrastructure, containers, databases (11 tests)")
    print("  api_streaming    - API endpoints, communication (11 tests)")
    print("  user_interface   - Browser experience, workflows (9 tests)")
    print("  master_validation - All tests + orchestration (recommended)")
    print()
    print("Examples:")
    print("  python run_tests.py master_validation  # Run all tests")
    print("  python run_tests.py system_health      # Infrastructure only")
    print("  python run_tests.py --all              # Run all individual suites")
    print("  python run_tests.py --help             # Show this help")

def run_all_individual_suites() -> None:
    """Run all individual test suites."""
    suites = ["system_health", "api_streaming", "user_interface"]
    
    print("🧪 Running All Individual Test Suites")
    print("=" * 50)
    
    results = {}
    for suite in suites:
        print(f"\n{'='*20} {suite.upper().replace('_', ' ')} {'='*20}")
        exit_code = run_test_suite(suite)
        results[suite] = exit_code == 0
    
    print("\n" + "=" * 50)
    print("📊 INDIVIDUAL SUITES SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for suite, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {suite.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed}/{total} suites passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All individual test suites passed!")
    else:
        print("⚠️ Some test suites failed - check individual results above")

def main():
    """Main test runner."""
    if len(sys.argv) == 1:
        # No arguments - show help
        show_help()
        return
    
    arg = sys.argv[1].lower()
    
    if arg in ["--help", "-h", "help"]:
        show_help()
        return
    elif arg == "--all":
        run_all_individual_suites()
        return
    elif arg in ["system_health", "api_streaming", "user_interface", "master_validation"]:
        exit_code = run_test_suite(arg)
        sys.exit(exit_code)
    else:
        print(f"❌ Unknown test: {arg}")
        print()
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()