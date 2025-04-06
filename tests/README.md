# OpenAI Chatbot Memory - Tests

This directory contains tests for the OpenAI Chatbot Memory project.

## Running Tests

To run the tests, you need to have pytest installed:

```bash
pip install -r ../requirements.txt
```

Then you can run all tests with:

```bash
pytest
```

Or run specific test files:

```bash
pytest test_encryption.py
pytest test_secure_memory.py
pytest test_embedding_memory.py
```

## Test Structure

- **test_encryption.py**: Tests for the encryption utilities
- **test_secure_memory.py**: Tests for the secure memory system
- **test_embedding_memory.py**: Tests for the vector embedding system

## Test Coverage

The tests cover:

1. **Encryption functionality**:
   - Key generation and validation
   - Encryption and decryption roundtrip
   - Error handling for invalid keys or corrupted data

2. **Secure Memory functionality**:
   - Database initialization and schema
   - Context creation and management
   - Memory storage and retrieval
   - Password protection and validation
   - Memory search functionality

3. **Embedding Memory functionality**:
   - Vector embedding generation and storage
   - Semantic search capabilities
   - Context boundaries in search results
   - Similarity threshold filtering
   - Result ordering by similarity score

## Troubleshooting

### Missing Dependencies

If you encounter import errors, make sure you have installed all dependencies:

```bash
pip install -r ../requirements.txt
```

### Sentence Transformers Issues

If you have issues with sentence-transformers, especially on Apple Silicon (M1/M2):

1. Install PyTorch directly from their website instructions
2. Then install sentence-transformers:

```bash
pip install sentence-transformers
```

### Database Access Errors

If you encounter database access errors, ensure that:

1. The tests have write permissions to the temporary directory
2. There are no other processes locking the database files