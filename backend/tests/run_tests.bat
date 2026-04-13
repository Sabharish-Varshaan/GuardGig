@echo off
REM Quick Start Guide for GuardGig Backend Test Suite (Windows)

echo.
echo ==========================================
echo GuardGig Backend Test Suite - Quick Start
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version

REM Navigate to backend directory
cd ..
echo Working directory: %cd%
echo.

REM Install test dependencies
echo Installing test dependencies...
pip install -q -r requirements.txt
pip install -q pytest pytest-asyncio pytest-cov pytest-html

REM Create test output directory
if not exist "test_results" mkdir test_results

echo.
echo ==========================================
echo Running All Tests
echo ==========================================
echo.

REM Run all tests with coverage
python -m pytest tests/ ^
    -v ^
    --tb=short ^
    --cov=app ^
    --cov-report=html:test_results/coverage ^
    --cov-report=term-missing ^
    --html=test_results/report.html ^
    --self-contained-html

REM Capture exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo Test Results
    echo ==========================================
    echo Coverage Report: test_results/coverage/index.html
    echo HTML Report: test_results/report.html
    echo.
    echo ✓ All tests passed!
) else (
    echo.
    echo ✗ Some tests failed
)

exit /b %ERRORLEVEL%
