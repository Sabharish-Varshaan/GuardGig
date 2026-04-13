"""
GuardGig Backend Test Suite - Comprehensive Test Runner

This script runs all backend tests and generates a detailed report:
- Authentication & User Flow
- Policy Management
- Payment Processing (Razorpay)
- Trigger Logic (Weather)
- Claim Generation & Payouts
- Fraud Detection
- Metrics & Actuarial
- Scheduler & Background Jobs
- Edge Cases & Adversarial Tests

Usage:
    python run_all_tests.py              # Run all tests with reporting
    python run_all_tests.py -v           # Verbose output
    python run_all_tests.py --html       # Generate HTML report
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re


class TestRunner:
    """Run all tests and collect results"""

    def __init__(self, test_dir: str = "tests"):
        self.test_dir = Path(test_dir)
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "duration": 0,
            "tests": {},
            "summary": ""
        }
        self.test_modules = [
            "test_auth.py",
            "test_policy.py",
            "test_payment.py",
            "test_trigger.py",
            "test_claims.py",
            "test_fraud.py",
            "test_metrics.py",
            "test_scheduler.py",
            "test_edge_cases.py",
        ]

    def run_all_tests(self, verbose: bool = False, html_report: bool = False) -> bool:
        """Run all test modules"""
        print("\n" + "="*80)
        print(" " * 20 + "GUARDGIG BACKEND TEST SUITE")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Directory: {self.test_dir}")
        print("="*80 + "\n")

        all_passed = True

        for module in self.test_modules:
            module_path = self.test_dir / module
            if module_path.exists():
                print(f"\n{'─'*80}")
                print(f"Running: {module}")
                print('─'*80)
                
                passed = self._run_module(module_path, verbose)
                if not passed:
                    all_passed = False

        # Print final report
        self._print_final_report(html_report)
        
        return all_passed

    def _run_module(self, module_path: Path, verbose: bool) -> bool:
        """Run a single test module"""
        try:
            # Use pytest to run the module
            cmd = ["python", "-m", "pytest", str(module_path), "-v", "--tb=short"]
            
            if verbose:
                cmd.append("-vv")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse output
            output = result.stdout + result.stderr
            
            # Extract test count
            match = re.search(r"(\d+) passed", output)
            if match:
                self.results["passed"] += int(match.group(1))

            match = re.search(r"(\d+) failed", output)
            if match:
                self.results["failed"] += int(match.group(1))

            match = re.search(r"(\d+) error", output)
            if match:
                self.results["errors"] += int(match.group(1))

            self.results["tests"][module_path.name] = {
                "passed": True if result.returncode == 0 else False,
                "output": output[:500]  # First 500 chars
            }

            if verbose:
                print(output)
            
            if result.returncode == 0:
                print(f"✓ {module_path.name} - PASSED")
                return True
            else:
                print(f"✗ {module_path.name} - FAILED")
                print(output[:300])  # Show error snippet
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ {module_path.name} - TIMEOUT")
            self.results["failed"] += 1
            return False
        except Exception as e:
            print(f"✗ {module_path.name} - ERROR: {e}")
            self.results["errors"] += 1
            return False

    def run_tests_standalone(self) -> None:
        """Run tests without pytest, using test class methods directly"""
        print("\n" + "="*80)
        print(" " * 20 + "GUARDGIG BACKEND TEST SUITE (Standalone)")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        # Import and run tests manually
        try:
            # Test Authentication
            from tests.test_auth import TestAuthenticationFlow, TestTokenValidation
            print("\n[MODULE] test_auth.py")
            print("─" * 80)
            self._run_test_class(TestAuthenticationFlow)

        except ImportError as e:
            print(f"Warning: Could not import test modules: {e}")
            print("Install required packages with: pip install -r requirements.txt")

    def _run_test_class(self, test_class):
        """Run all test methods in a class"""
        instance = test_class()
        test_count = 0
        passed_count = 0

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                test_count += 1
                try:
                    method = getattr(instance, method_name)
                    method()  # Run test
                    passed_count += 1
                    self.results["passed"] += 1
                    print(f"  ✓ {method_name}")
                except AssertionError as e:
                    self.results["failed"] += 1
                    print(f"  ✗ {method_name}: {e}")
                except Exception as e:
                    self.results["errors"] += 1
                    print(f"  ✗ {method_name}: ERROR: {e}")

        self.results["total"] += test_count
        return passed_count == test_count

    def _print_final_report(self, html_report: bool = False) -> None:
        """Print final test report"""
        # Calculate totals
        total = self.results["passed"] + self.results["failed"] + self.results["errors"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        print("\n" + "="*80)
        print(" " * 25 + "TEST SUMMARY REPORT")
        print("="*80)
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"  Total Tests Run:        {total}")
        print(f"  ✓ Passed:              {self.results['passed']}")
        print(f"  ✗ Failed:              {self.results['failed']}")
        print(f"  ⚠ Errors:              {self.results['errors']}")
        print(f"  ⊘ Skipped:             {self.results['skipped']}")
        print()
        print(f"  Success Rate:          {pass_rate:.1f}%")
        print()

        # Module breakdown
        if self.results["tests"]:
            print("MODULE RESULTS:")
            print("─" * 80)
            for module, info in self.results["tests"].items():
                status = "✓ PASS" if info["passed"] else "✗ FAIL"
                print(f"  {status:10} {module}")
        
        print("="*80)

        # Generate HTML report if requested
        if html_report:
            self._generate_html_report()

        # Exit code
        exit_code = 0 if self.results["failed"] == 0 and self.results["errors"] == 0 else 1
        print(f"\nExit Code: {exit_code}")
        sys.exit(exit_code)

    def _generate_html_report(self) -> None:
        """Generate HTML test report"""
        html_file = "test_report.html"
        
        total = self.results["passed"] + self.results["failed"] + self.results["errors"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GuardGig Backend Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin-right: 40px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ color: #666; font-size: 12px; }}
        .status-pass {{ color: #27ae60; }}
        .status-fail {{ color: #e74c3c; }}
        .status-error {{ color: #f39c12; }}
        .modules {{ background: white; padding: 20px; border-radius: 5px; }}
        .module-item {{ padding: 10px; margin: 5px 0; border-left: 4px solid #95a5a6; }}
        .module-pass {{ border-left-color: #27ae60; }}
        .module-fail {{ border-left-color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #ecf0f1; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GuardGig Backend Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="metric">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value status-pass">{self.results['passed']}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric">
            <div class="metric-value status-fail">{self.results['failed']}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric">
            <div class="metric-value status-error">{self.results['errors']}</div>
            <div class="metric-label">Errors</div>
        </div>
        <div class="metric">
            <div class="metric-value">{pass_rate:.1f}%</div>
            <div class="metric-label">Pass Rate</div>
        </div>
    </div>
    
    <div class="modules">
        <h2>Module Results</h2>
        <table>
            <tr><th>Module</th><th>Status</th><th>Details</th></tr>
"""

        for module, info in self.results["tests"].items():
            status = "PASS" if info["passed"] else "FAIL"
            status_class = "module-pass" if info["passed"] else "module-fail"
            html_content += f"""
            <tr class="{status_class}">
                <td>{module}</td>
                <td>{status}</td>
                <td><small>{info['output']}</small></td>
            </tr>
"""

        html_content += """
        </table>
    </div>
</body>
</html>
"""

        with open(html_file, "w") as f:
            f.write(html_content)
        
        print(f"\nHTML Report generated: {html_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GuardGig Backend Test Suite Runner"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report"
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run tests without pytest (for basic test execution)"
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Test directory (default: tests)"
    )

    args = parser.parse_args()

    runner = TestRunner(test_dir=args.test_dir)

    if args.standalone:
        runner.run_tests_standalone()
    else:
        runner.run_all_tests(
            verbose=args.verbose,
            html_report=args.html
        )


if __name__ == "__main__":
    main()
