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

## why? I have created a few JavaScript and typescript sqlite memory banks for cursor and I thought that this memory codebase was simple but effective so I decided to !vibe the whole thing is just !vibe 🐸 and when I had issues in cursors implementation of the built in project awareness and my local DB I immediately thought to password protect the database and put the password in the database and somehow this really surprised me. crypto hashes stored in sqlite made cursor like way way better.. added rules - detailed enough to get the ai to constantly add notes and then from the main notepad "team-notes.txt" the AI is instructed to summarize and find the best project structure details and context then use sqlite to store hashes for the compressed memory. the AI agents are all like 90 year olds with Alzheimer's but kinda developers so reminding them constantly of structure, dependencies and the os - container all the details and goals of the project along with user specific context makes them way more useful. this is my attempt at a secure private and potentially 🐔 blocking all the ai companies storing our data by making a secure parallel memory context system ... where you can swap between models and still have great results all because of context.. 



