#!/bin/bash

# Script to run tests for the openai-chatbot-memory project

# Create test directories if they don't exist
mkdir -p tests/tmp

# Make sure we have all requirements
pip install -r requirements.txt

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to run a command and print status
run_test() {
    echo -e "${YELLOW}Running: $1${NC}"
    if $1; then
        echo -e "${GREEN}✓ Passed${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Run all tests
if [ "$1" == "all" ]; then
    run_test "python -m pytest"
    exit $?
fi

# Run specific test file
if [ -n "$1" ]; then
    run_test "python -m pytest $1"
    exit $?
fi

# Run specific test modules
echo -e "${YELLOW}Running critical tests...${NC}"

run_test "python -m pytest tests/test_hashing.py -v" || exit 1
run_test "python -m pytest tests/test_secure_memory.py -v" || exit 1
run_test "python -m pytest tests/test_embedding_memory.py -v"

echo -e "\n${YELLOW}To run all tests, use: ./run_tests.sh all${NC}"
echo -e "${YELLOW}To run a specific test, use: ./run_tests.sh tests/test_file.py${NC}" 