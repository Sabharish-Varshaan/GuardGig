#!/bin/bash
# Quick Start Guide for GuardGig Backend Test Suite

echo "=========================================="
echo "GuardGig Backend Test Suite - Quick Start"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python --version || python3 --version

# Navigate to backend directory
cd "$(dirname "$0")/../" || exit 1
echo "Working directory: $(pwd)"
echo ""

# Install test dependencies
echo "Installing test dependencies..."
pip install -q -r requirements.txt
pip install -q pytest pytest-asyncio pytest-cov pytest-html

# Create test output directory
mkdir -p test_results

echo ""
echo "=========================================="
echo "Running All Tests"
echo "=========================================="
echo ""

# Run all tests with coverage
python -m pytest tests/ \
    -v \
    --tb=short \
    --cov=app \
    --cov-report=html:test_results/coverage \
    --cov-report=term-missing \
    --html=test_results/report.html \
    --self-contained-html

# Capture exit code
EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo "Coverage Report: test_results/coverage/index.html"
echo "HTML Report: test_results/report.html"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
