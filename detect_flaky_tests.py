#!/usr/bin/env python
"""
Flaky Test Detection Script for py3plex

This script runs the test suite multiple times to identify flaky tests
(tests that pass sometimes and fail sometimes) and provides detailed
analysis of the failures.

Usage:
    python detect_flaky_tests.py --runs 5 --output flaky_tests_report.json
    python detect_flaky_tests.py --runs 10 --test-subset tests/test_dsl_v2.py
    python detect_flaky_tests.py --runs 3 --parallel 4
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Set
import re


@dataclass
class TestRun:
    """Represents a single test run."""
    test_id: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    failure_message: Optional[str] = None


@dataclass
class TestStatistics:
    """Statistics for a test across multiple runs."""
    test_id: str
    total_runs: int
    passed: int
    failed: int
    skipped: int
    errors: int
    failure_messages: List[str]
    durations: List[float]
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_runs == 0:
            return 0.0
        return self.passed / self.total_runs
    
    @property
    def is_flaky(self) -> bool:
        """Determine if test is flaky (not consistently passing or failing)."""
        # A test is flaky if it has both passes and failures
        return self.passed > 0 and self.failed > 0
    
    @property
    def avg_duration(self) -> float:
        """Average duration across runs."""
        if not self.durations:
            return 0.0
        return sum(self.durations) / len(self.durations)


class FlakyTestDetector:
    """Detects flaky tests by running tests multiple times."""
    
    def __init__(self, runs: int = 5, test_path: str = "tests/", parallel: int = 1):
        self.runs = runs
        self.test_path = test_path
        self.parallel = parallel
        self.test_results: Dict[str, List[TestRun]] = defaultdict(list)
        
    def run_tests(self, run_number: int) -> Dict[str, TestRun]:
        """Run tests once and return results."""
        print(f"\n{'='*80}")
        print(f"Running test suite: Run {run_number + 1}/{self.runs}")
        print(f"{'='*80}\n")
        
        # Use pytest with JSON report
        cmd = [
            sys.executable, "-m", "pytest",
            self.test_path,
            "-v",
            "--tb=short",
            "-q",
            f"-n={self.parallel}" if self.parallel > 1 else "-n=auto",
            "--junit-xml=pytest_results.xml",
            "--strict-markers",
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per run
            )
            duration = time.time() - start_time
            
            # Parse output
            test_results = self._parse_pytest_output(result.stdout, result.stderr)
            
            print(f"\nRun {run_number + 1} completed in {duration:.2f}s")
            print(f"Exit code: {result.returncode}")
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print(f"  Run {run_number + 1} timed out after 600s")
            return {}
        except Exception as e:
            print(f" Run {run_number + 1} failed with error: {e}")
            return {}
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, TestRun]:
        """Parse pytest output to extract test results."""
        results = {}
        
        # Pattern to match pytest output lines
        # Example: tests/test_file.py::TestClass::test_method PASSED
        # Example: tests/test_file.py::test_function FAILED
        pattern = r'([\w/\.\-]+\.py::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)\s*(\[.*?\])?\s*(?:\(([\d\.]+)s\))?'
        
        for line in stdout.split('\n'):
            match = re.search(pattern, line)
            if match:
                test_id = match.group(1)
                status = match.group(2).lower()
                duration_str = match.group(4)
                duration = float(duration_str) if duration_str else 0.0
                
                # Extract failure message from following lines if failed
                failure_msg = None
                if status == 'failed':
                    # Look for assertion errors or exception info
                    failure_msg = self._extract_failure_message(stdout, test_id)
                
                results[test_id] = TestRun(
                    test_id=test_id,
                    status=status,
                    duration=duration,
                    failure_message=failure_msg
                )
        
        return results
    
    def _extract_failure_message(self, output: str, test_id: str) -> Optional[str]:
        """Extract failure message for a failed test."""
        # Simple extraction - look for lines after the test failure
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if test_id in line and 'FAILED' in line:
                # Get next few lines as failure message
                msg_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].startswith('___') or lines[j].startswith('==='):
                        break
                    msg_lines.append(lines[j])
                return '\n'.join(msg_lines[:5])  # First 5 lines
        return None
    
    def detect_flaky_tests(self) -> List[TestStatistics]:
        """Run tests multiple times and detect flaky tests."""
        print(f" Starting flaky test detection")
        print(f"   Runs: {self.runs}")
        print(f"   Test path: {self.test_path}")
        print(f"   Parallel workers: {self.parallel}")
        
        # Run tests multiple times
        for run_num in range(self.runs):
            run_results = self.run_tests(run_num)
            
            # Store results
            for test_id, test_run in run_results.items():
                self.test_results[test_id].append(test_run)
        
        # Analyze results
        return self._analyze_results()
    
    def _analyze_results(self) -> List[TestStatistics]:
        """Analyze test results to identify flaky tests."""
        statistics = []
        
        for test_id, runs in self.test_results.items():
            passed = sum(1 for r in runs if r.status == 'passed')
            failed = sum(1 for r in runs if r.status == 'failed')
            skipped = sum(1 for r in runs if r.status == 'skipped')
            errors = sum(1 for r in runs if r.status == 'error')
            
            failure_messages = [r.failure_message for r in runs if r.failure_message]
            durations = [r.duration for r in runs if r.duration > 0]
            
            stats = TestStatistics(
                test_id=test_id,
                total_runs=len(runs),
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                failure_messages=failure_messages,
                durations=durations
            )
            
            statistics.append(stats)
        
        return statistics
    
    def generate_report(self, statistics: List[TestStatistics], output_file: str):
        """Generate a report of flaky tests."""
        # Separate flaky and stable tests
        flaky_tests = [s for s in statistics if s.is_flaky]
        stable_passed = [s for s in statistics if s.passed == s.total_runs]
        stable_failed = [s for s in statistics if s.failed == s.total_runs]
        
        print("\n" + "="*80)
        print("FLAKY TEST DETECTION REPORT")
        print("="*80)
        
        print(f"\n Overall Statistics:")
        print(f"   Total unique tests: {len(statistics)}")
        print(f"   Flaky tests: {len(flaky_tests)}")
        print(f"   Stable passing: {len(stable_passed)}")
        print(f"   Stable failing: {len(stable_failed)}")
        print(f"   Flaky rate: {len(flaky_tests)/len(statistics)*100:.2f}%")
        
        if flaky_tests:
            print(f"\n  FLAKY TESTS ({len(flaky_tests)}):")
            print("-" * 80)
            
            # Sort by pass rate (most flaky first)
            flaky_tests.sort(key=lambda x: abs(0.5 - x.pass_rate))
            
            for i, test in enumerate(flaky_tests[:20], 1):  # Show top 20
                print(f"\n{i}. {test.test_id}")
                print(f"   Pass rate: {test.pass_rate*100:.1f}% ({test.passed}/{test.total_runs})")
                print(f"   Failed: {test.failed}, Errors: {test.errors}, Skipped: {test.skipped}")
                print(f"   Avg duration: {test.avg_duration:.3f}s")
                
                if test.failure_messages:
                    print(f"   Sample failure: {test.failure_messages[0][:100]}...")
        
        # Save JSON report
        report_data = {
            "runs": self.runs,
            "test_path": self.test_path,
            "total_tests": len(statistics),
            "flaky_tests_count": len(flaky_tests),
            "flaky_rate": len(flaky_tests)/len(statistics) if statistics else 0,
            "flaky_tests": [
                {
                    "test_id": s.test_id,
                    "pass_rate": s.pass_rate,
                    "passed": s.passed,
                    "failed": s.failed,
                    "skipped": s.skipped,
                    "errors": s.errors,
                    "avg_duration": s.avg_duration,
                    "failure_messages": s.failure_messages[:3]  # Include only first 3
                }
                for s in flaky_tests
            ],
            "stable_failing": [
                {
                    "test_id": s.test_id,
                    "failure_messages": s.failure_messages[:1]
                }
                for s in stable_failed[:10]  # Include first 10
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n Full report saved to: {output_file}")
        
        # Generate recommendations
        self._generate_recommendations(flaky_tests)
    
    def _generate_recommendations(self, flaky_tests: List[TestStatistics]):
        """Generate recommendations for fixing flaky tests."""
        if not flaky_tests:
            print("\n No flaky tests detected!")
            return
        
        print("\n" + "="*80)
        print("RECOMMENDATIONS FOR FIXING FLAKY TESTS")
        print("="*80)
        
        print("\n1. Common causes of flaky tests:")
        print("   - Missing random seeds in tests using random/numpy.random")
        print("   - Race conditions in parallel tests")
        print("   - Timing-dependent assertions")
        print("   - Unordered collection comparisons (sets, dicts)")
        print("   - Filesystem state dependencies")
        print("   - Network/external resource dependencies")
        
        print("\n2. Recommended actions:")
        print("   - Add @pytest.mark.flaky decorator to known flaky tests")
        print("   - Install pytest-rerunfailures: pip install pytest-rerunfailures")
        print("   - Set random seeds explicitly in tests")
        print("   - Use freezegun for time-dependent tests")
        print("   - Mock external dependencies")
        print("   - Sort collections before comparison")
        
        print("\n3. Example fix for random seed issues:")
        print("   ```python")
        print("   import random")
        print("   import numpy as np")
        print("   ")
        print("   def test_with_randomness():")
        print("       random.seed(42)  # Set seed")
        print("       np.random.seed(42)  # Set numpy seed")
        print("       # test code here")
        print("   ```")


def main():
    parser = argparse.ArgumentParser(
        description="Detect flaky tests in py3plex test suite"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of times to run the test suite (default: 5)"
    )
    parser.add_argument(
        "--test-subset",
        type=str,
        default="tests/",
        help="Path to test subset to check (default: tests/)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="flaky_tests_report.json",
        help="Output file for JSON report (default: flaky_tests_report.json)"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1, use -1 for auto)"
    )
    
    args = parser.parse_args()
    
    # Create detector
    detector = FlakyTestDetector(
        runs=args.runs,
        test_path=args.test_subset,
        parallel=args.parallel
    )
    
    # Detect flaky tests
    statistics = detector.detect_flaky_tests()
    
    # Generate report
    detector.generate_report(statistics, args.output)
    
    # Exit with error if flaky tests found
    flaky_count = sum(1 for s in statistics if s.is_flaky)
    if flaky_count > 0:
        print(f"\n Found {flaky_count} flaky tests")
        sys.exit(1)
    else:
        print("\n No flaky tests detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
