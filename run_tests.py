#!/usr/bin/env python3
"""
Simple test runner for py3plex tests.
This script runs available tests and provides a clear test report.
"""

import os
import sys
import traceback
import importlib.util
from pathlib import Path

def run_test_file(test_file_path):
    """Run a single test file and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file_path}")
    print(f"{'='*60}")
    
    try:
        # Load the test module
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        
        # Add the test directory to the path so imports work
        test_dir = os.path.dirname(test_file_path)
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)
        
        # Add the repository root to path for py3plex imports
        repo_root = os.path.dirname(os.path.abspath(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        
        # Execute the test module
        spec.loader.exec_module(test_module)
        
        # Check for unittest TestCase classes
        import unittest
        test_classes = []
        test_functions = []
        
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                test_classes.append(obj)
            elif name.startswith('test_') and callable(obj):
                test_functions.append(obj)
        
        if test_classes:
            # Run unittest-based tests
            print(f"Found {len(test_classes)} test class(es)")
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            
            for test_class in test_classes:
                class_tests = loader.loadTestsFromTestCase(test_class)
                suite.addTests(class_tests)
            
            # Custom test result to capture output
            class CustomTestResult(unittest.TextTestResult):
                def __init__(self, stream, verbosity):
                    super().__init__(stream, verbosity)
                    self.success_count = 0
                    
                def addSuccess(self, test):
                    super().addSuccess(test)
                    self.success_count += 1
                    
            # Run the tests
            runner = unittest.TextTestRunner(resultclass=CustomTestResult, verbosity=1)
            result = runner.run(suite)
            
            if result.wasSuccessful():
                print(f"\n🎉 All {result.testsRun} unittest tests PASSED!")
                return True
            else:
                print(f"\n💥 {len(result.failures + result.errors)}/{result.testsRun} unittest tests FAILED!")
                return False
                
        elif test_functions:
            # Run simple function-based tests
            print(f"Found {len(test_functions)} test function(s)")
            failed_tests = 0
            for test_func in test_functions:
                try:
                    print(f"\n➤ Running {test_func.__name__}...")
                    test_func()
                    print(f"✅ {test_func.__name__} PASSED")
                except Exception as e:
                    print(f"❌ {test_func.__name__} FAILED: {e}")
                    traceback.print_exc()
                    failed_tests += 1
            
            if failed_tests == 0:
                print(f"\n🎉 All {len(test_functions)} tests PASSED!")
                return True
            else:
                print(f"\n💥 {failed_tests}/{len(test_functions)} tests FAILED!")
                return False
        else:
            # If no test functions found, try running main() if it exists
            if hasattr(test_module, '__name__') and test_module.__name__ == "__main__":
                # The file has a main section, let's run it by executing as script
                print("No test functions found, executing as script...")
                exec(open(test_file_path).read())
            else:
                print("No test functions found and no main execution block")
                return False
        
        return True
        
    except ModuleNotFoundError as e:
        print(f"⚠️  Dependency missing: {e}")
        print("   This test requires additional dependencies to be installed.")
        print("   Run: pip install -e . to install all dependencies")
        return "skipped"
        
    except Exception as e:
        print(f"❌ Failed to run test file: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("🧪 Py3plex Test Runner")
    print("=" * 60)
    
    # Find test files
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print(f"❌ No test files found in: {test_dir}")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  📄 {test_file.name}")
    
    # Run each test file
    passed_files = 0
    failed_files = 0
    skipped_files = 0
    
    for test_file in test_files:
        try:
            result = run_test_file(test_file)
            if result is True:
                passed_files += 1
            elif result == "skipped":
                skipped_files += 1
            else:
                failed_files += 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Test run interrupted by user")
            break
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test files found: {len(test_files)}")
    print(f"✅ Passed: {passed_files}")
    print(f"❌ Failed: {failed_files}")
    print(f"⚠️  Skipped (deps missing): {skipped_files}")
    
    if failed_files == 0 and passed_files > 0:
        print("\n🎉 All runnable tests completed successfully!")
        if skipped_files > 0:
            print(f"💡 {skipped_files} test(s) skipped due to missing dependencies")
        return 0
    elif passed_files > 0:
        print(f"\n✅ {passed_files} test(s) passed, but {failed_files} failed")
        return 1
    else:
        print(f"\n💥 No tests could be run successfully!")
        return 1

if __name__ == "__main__":
    sys.exit(main())