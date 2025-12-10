#!/bin/bash
# Test runner script for AOSB Backend
# This script provides convenient test execution commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test summary counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_pytest_installed() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed"
        print_info "Install with: pip install pytest pytest-asyncio pytest-cov pytest-mock"
        exit 1
    fi
}

run_all_tests() {
    print_header "Running All Tests"
    check_pytest_installed
    pytest -v --tb=short
}

run_unit_tests() {
    print_header "Running Unit Tests (Extractor, Chunker, Embedder)"
    check_pytest_installed
    pytest -v -m unit --tb=short
}

run_integration_tests() {
    print_header "Running Integration Tests (API)"
    check_pytest_installed
    pytest -v -m integration --tb=short
}

run_extractor_tests() {
    print_header "Running Extractor Tests"
    check_pytest_installed
    pytest tests/test_extractor.py -v --tb=short
}

run_chunker_tests() {
    print_header "Running Chunker Tests"
    check_pytest_installed
    pytest tests/test_chunker.py -v --tb=short
}

run_embedder_tests() {
    print_header "Running Embedder Tests"
    check_pytest_installed
    pytest tests/test_embedder.py -v --tb=short
}

run_with_coverage() {
    print_header "Running Tests with Coverage Report"
    check_pytest_installed
    
    if ! python -c "import pytest_cov" 2>/dev/null; then
        print_error "pytest-cov is not installed"
        print_info "Install with: pip install pytest-cov"
        exit 1
    fi
    
    pytest --cov=backend --cov-report=html --cov-report=term-missing -v --tb=short
    print_success "Coverage report generated at htmlcov/index.html"
}

run_coverage_open() {
    run_with_coverage
    if command -v open &> /dev/null; then
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    else
        print_info "Open htmlcov/index.html in your browser"
    fi
}

run_watch_mode() {
    print_header "Running Tests in Watch Mode"
    
    if ! command -v ptw &> /dev/null; then
        print_error "pytest-watch is not installed"
        print_info "Install with: pip install pytest-watch"
        exit 1
    fi
    
    ptw
}

run_fast_tests() {
    print_header "Running Fast Tests (Excluding Slow Tests)"
    check_pytest_installed
    pytest -v -m "not slow" --tb=short
}

run_failed_tests() {
    print_header "Running Failed Tests"
    check_pytest_installed
    pytest -v --lf --tb=short
}

show_help() {
    cat << EOF
${BLUE}AOSB Backend Test Runner${NC}

Usage: ./run_tests.sh [COMMAND]

Commands:
    all             Run all tests (default)
    unit            Run unit tests only (extractor, chunker, embedder)
    integration     Run integration tests only (API)
    extractor       Run extractor module tests
    chunker         Run chunker module tests
    embedder        Run embedder module tests
    coverage        Run tests with coverage report
    coverage-open   Run tests with coverage and open HTML report
    watch           Run tests in watch mode (requires pytest-watch)
    fast            Run tests excluding slow tests
    failed          Run last failed tests
    help            Show this help message

Examples:
    ./run_tests.sh unit              # Run unit tests
    ./run_tests.sh coverage          # Run with coverage report
    ./run_tests.sh watch             # Run in watch mode
    ./run_tests.sh extractor         # Run extractor tests

Environment Variables:
    PYTEST_ARGS     Additional pytest arguments
                    Example: PYTEST_ARGS='-x -v' ./run_tests.sh all

Test Categories:
    - unit:             Unit tests for core components
    - integration:      API endpoint tests
    - slow:             Long-running tests
    - mock_external:    Tests with mocked external services
    - extractor:        Extractor module tests
    - chunker:          Chunker module tests
    - embedder:         Embedder module tests

Configuration:
    - pytest.ini:       Pytest configuration
    - conftest.py:      Shared fixtures and setup
    - TESTING.md:       Comprehensive testing guide

For more information, see TESTING.md
EOF
}

# Main script logic
main() {
    local command="${1:-all}"
    
    case $command in
        all)
            run_all_tests
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        extractor)
            run_extractor_tests
            ;;
        chunker)
            run_chunker_tests
            ;;
        embedder)
            run_embedder_tests
            ;;
        coverage)
            run_with_coverage
            ;;
        coverage-open)
            run_coverage_open
            ;;
        watch)
            run_watch_mode
            ;;
        fast)
            run_fast_tests
            ;;
        failed)
            run_failed_tests
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
