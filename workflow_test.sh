#!/bin/bash
# Script to simulate GitHub Actions workflow locally

set -e  # Exit on any error

# Colors for better output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Running workflow test locally ====${NC}"

# Function to run a step and check result
run_step() {
  local step_name=$1
  local command=$2
  
  echo -e "\n${YELLOW}STEP: ${step_name}${NC}"
  echo -e "${YELLOW}COMMAND: ${command}${NC}"
  
  if eval $command; then
    echo -e "${GREEN}✓ Step passed${NC}"
  else
    echo -e "${RED}✗ Step failed${NC}"
    exit 1
  fi
}

# Create test directories
run_step "Create test directories" "mkdir -p tests/tmp"

# Install dependencies if needed
if [ "$1" == "install" ]; then
  run_step "Install dependencies" "pip install pytest pytest-cov"
  run_step "Install torch" "pip install torch"
  run_step "Install sentence-transformers" "pip install sentence-transformers"
  run_step "Install requirements" "pip install -r requirements.txt"
fi

# Debug environment
run_step "Debug environment" "pip list | grep -E 'pytest|torch|sentence-transformers|cryptography|argon2|passlib|numpy'"

# Set environment variables
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run security module tests first
run_step "Run security module tests" "python -m pytest tests/test_hashing.py -v"

# Run memory module tests
run_step "Run memory module tests" "python -m pytest tests/test_secure_memory.py -v"

# Run embedding module tests (allow failure)
echo -e "\n${YELLOW}STEP: Run embedding module tests${NC}"
echo -e "${YELLOW}COMMAND: python -m pytest tests/test_embedding_memory.py -v${NC}"
if python -m pytest tests/test_embedding_memory.py -v; then
  echo -e "${GREEN}✓ Step passed${NC}"
else
  echo -e "${YELLOW}⚠ Some embedding tests skipped or failed (this is allowed)${NC}"
fi

# Run coverage report
run_step "Run coverage report" "python -m pytest tests/ --cov=security --cov=memory --cov-report=term"

echo -e "\n${GREEN}==== All workflow tests completed successfully ====${NC}" 