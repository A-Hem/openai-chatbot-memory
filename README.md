# OpenAI Chatbot Memory

A self-hosted memory system for AI chatbots with privacy features.

## Features

- Secure local memory storage with end-to-end encryption
- Contextual memory management with vector similarity search
- Password protection with Argon2id hashing
- Extensible architecture for custom memory storage implementations

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/openai-chatbot-memory.git
cd openai-chatbot-memory

# Install dependencies
pip install -r requirements.txt
```

## Testing

The project uses pytest for testing. We have separate test suites for different components:

- `test_hashing.py`: Tests for the security hashing module
- `test_secure_memory.py`: Tests for the secure memory implementation
- `test_embedding_memory.py`: Tests for the vector embedding memory system

### Running Tests

You can run the tests using the provided script:

```bash
# Make the script executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh all

# Run specific test file
./run_tests.sh tests/test_secure_memory.py
```

Or you can run pytest directly:

```bash
# Run all tests
python -m pytest

# Run specific test file with verbosity
python -m pytest tests/test_hashing.py -v
```

### Workflow Testing

For workflow testing (similar to CI environment):

```bash
# Make the script executable
chmod +x workflow_test.sh

# Run workflow test
./workflow_test.sh

# Run workflow test with dependency installation
./workflow_test.sh install
```

## Project Structure

```
openai-chatbot-memory/
├── memory/                  # Memory management modules
│   ├── __init__.py
│   ├── secure_memory.py     # Core secure memory implementation
│   └── embedding_memory.py  # Vector similarity memory extension
├── security/                # Security utilities
│   ├── __init__.py
│   ├── encryption.py        # Encryption utilities
│   └── hashing.py           # Password hashing utilities
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_hashing.py
│   ├── test_secure_memory.py
│   └── test_embedding_memory.py
├── requirements.txt         # Project dependencies
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── run_tests.sh             # Test runner script
```

## License

MIT
