#!/usr/bin/env python3
"""
Simple test runner for py3plex tests with timeout awareness.
This script runs available tests and provides a clear test report with progress updates.
"""

import os
import sys
import traceback
import importlib.util
import time
import signal
from pathlib import Path

class TimeoutHandler:
    """Handle test timeouts gracefully."""
    def __init__(self, timeout):
        self.timeout = timeout
        self.timed_out = False
        
    def timeout_handler(self, signum, frame):
        self.timed_out = True
        raise TimeoutError(f"Test execution timed out after {self.timeout} seconds")
    
    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):  # Unix only
            signal.signal(signal.SIGALRM, self.timeout_handler)
            signal.alarm(self.timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):  # Unix only
            signal.alarm(0)

def run_test_file(test_file_path, timeout=300):
    """Run a single test file and return results with timeout protection."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file_path}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        with TimeoutHandler(timeout):
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
            
            print(f"⏱️  Loading test module... (timeout: {timeout}s)")
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
                print(f"🔍 Found {len(test_classes)} unittest TestCase classes")
                # Run unittest-based tests
                loader = unittest.TestLoader()
                suite = unittest.TestSuite()
                
                for test_class in test_classes:
                    class_tests = loader.loadTestsFromTestCase(test_class)
                    suite.addTests(class_tests)
                
                # Custom test result to capture output
                class CustomTestResult(unittest.TextTestResult):
                    def __init__(self, stream, descriptions, verbosity):
                        super().__init__(stream, descriptions, verbosity)
                        self.success_count = 0
                        
                    def addSuccess(self, test):
                        super().addSuccess(test)
                        self.success_count += 1
                        
                # Run the tests with progress updates
                print(f"⚡ Running {suite.countTestCases()} unittest tests...")
                runner = unittest.TextTestRunner(resultclass=CustomTestResult, verbosity=1)
                result = runner.run(suite)
                
                elapsed = time.time() - start_time
                print(f"⏱️  Test execution took {elapsed:.2f} seconds")
                
                if result.wasSuccessful():
                    print(f"\n🎉 All {result.testsRun} unittest tests PASSED!")
                    return True
                else:
                    print(f"\n💥 {len(result.failures + result.errors)}/{result.testsRun} unittest tests FAILED!")
                    return False
                    
            elif test_functions:
                # Run simple function-based tests
                print(f"🔍 Found {len(test_functions)} test function(s)")
                failed_tests = 0
                for i, test_func in enumerate(test_functions, 1):
                    try:
                        print(f"\n➤ Running {test_func.__name__} ({i}/{len(test_functions)})...")
                        test_func()
                        print(f"✅ {test_func.__name__} PASSED")
                    except Exception as e:
                        print(f"❌ {test_func.__name__} FAILED: {e}")
                        traceback.print_exc()
                        failed_tests += 1
            
                elapsed = time.time() - start_time
                print(f"⏱️  Test execution took {elapsed:.2f} seconds")
                
                if failed_tests == 0:
                    print(f"\n🎉 All {len(test_functions)} tests PASSED!")
                    return True
                else:
                    print(f"\n💥 {failed_tests}/{len(test_functions)} tests FAILED!")
                    return False
            else:
                # If no test functions found, try running main() if it exists
                print("🔍 No standard test functions found")
                if hasattr(test_module, '__name__') and test_module.__name__ == "__main__":
                    # The file has a main section, let's run it by executing as script
                    print("📝 Executing as script...")
                    exec(open(test_file_path).read())
                else:
                    print("⚠️  No test functions found and no main execution block")
                    return False
            
            elapsed = time.time() - start_time
            print(f"⏱️  Total execution took {elapsed:.2f} seconds")
            return True
            
    except TimeoutError as e:
        elapsed = time.time() - start_time
        print(f"⏰ {e} (after {elapsed:.2f} seconds)")
        return "timeout"
        
    except ModuleNotFoundError as e:
        print(f"⚠️  Dependency missing: {e}")
        print("   This test requires additional dependencies to be installed.")
        print("   Run: pip install -e . to install all dependencies")
        return "skipped"
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed to run test file after {elapsed:.2f} seconds: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test runner with timeout management."""
    print("🧪 Py3plex Test Runner")
    print("=" * 60)
    
    start_time = time.time()
    
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
    
    # Run each test file with individual timeouts
    passed_files = 0
    failed_files = 0
    skipped_files = 0
    timeout_files = 0
    
    for i, test_file in enumerate(test_files, 1):
        try:
            print(f"\n🚀 Progress: {i}/{len(test_files)} files")
            # Adjust timeout based on test file (some need more time)
            if "multilayer_centrality" in test_file.name:
                timeout = 180  # 3 minutes for complex centrality tests
            elif "core_functionality" in test_file.name:
                timeout = 240  # 4 minutes for visualization tests
            else:
                timeout = 120  # 2 minutes for simple tests
                
            result = run_test_file(test_file, timeout)
            if result is True:
                passed_files += 1
            elif result == "skipped":
                skipped_files += 1
            elif result == "timeout":
                timeout_files += 1
            else:
                failed_files += 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Test run interrupted by user")
            break
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test files found: {len(test_files)}")
    print(f"✅ Passed: {passed_files}")
    print(f"❌ Failed: {failed_files}")
    print(f"⚠️  Skipped: {skipped_files}")
    print(f"⏰ Timed out: {timeout_files}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    
    if failed_files == 0 and timeout_files == 0:
        print("\n🎉 All tests completed successfully!")
        return 0
    elif timeout_files > 0:
        print(f"\n⚠️  Some tests timed out - this may indicate network or performance issues")
        return 2  # Different exit code for timeouts
    else:
        print(f"\n💥 Some tests failed - check the output above for details")
        return 1
if __name__ == "__main__":
    sys.exit(main())