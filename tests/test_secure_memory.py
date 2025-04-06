"""
Test suite for the secure memory implementation.
"""

import os
import pytest
import tempfile
import json
import sqlite3
from datetime import datetime
from memory.secure_memory import SecureMemory

@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def memory(temp_db):
    """Create a SecureMemory instance with a temporary database."""
    memory = SecureMemory(db_path=temp_db, passphrase="test-passphrase")
    yield memory
    memory.close()

def test_initialization(memory):
    """Test memory system initialization."""
    assert memory.initialized
    assert memory.conn is not None
    assert memory.encryption_key is not None

def test_context_creation(memory):
    """Test context creation and retrieval."""
    # Create a context
    context_id = memory.create_context(
        name="Test Context",
        description="Test description"
    )
    
    # Verify context exists
    contexts = memory.get_contexts()
    assert len(contexts) == 1
    assert contexts[0]['id'] == context_id
    assert contexts[0]['name'] == "Test Context"
    assert contexts[0]['description'] == "Test description"

def test_memory_storage_and_retrieval(memory):
    """Test storing and retrieving memories."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store a memory
    content = "This is a test memory"
    memory_id = memory.store(
        content=content,
        context_id=context_id,
        importance=8,
        tags=["test", "memory"]
    )
    
    # Retrieve the memory
    retrieved = memory.retrieve(memory_id)
    
    # Verify content
    assert retrieved['content'] == content
    assert retrieved['importance'] == 8
    assert sorted(retrieved['tags']) == sorted(["test", "memory"])
    assert isinstance(retrieved['created_at'], str)

def test_memory_encryption(memory):
    """Test that memories are properly encrypted."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store a memory
    content = "Sensitive information"
    memory_id = memory.store(content=content, context_id=context_id)
    
    # Check raw database content
    cursor = memory.conn.cursor()
    cursor.execute("SELECT content FROM memories WHERE id = ?", (memory_id,))
    encrypted_data = cursor.fetchone()[0]
    
    # Verify content is encrypted (not plain text)
    assert content.encode() not in encrypted_data

def test_memory_search(memory):
    """Test memory search functionality."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store multiple memories
    memories = [
        ("First test memory", ["test", "first"]),
        ("Second test memory", ["test", "second"]),
        ("Different content", ["other"])
    ]
    
    for content, tags in memories:
        memory.store(
            content=content,
            context_id=context_id,
            tags=tags
        )
    
    # Search for memories
    results = memory.search("test", context_id=context_id)
    assert len(results) == 2
    assert all("test" in result['content'] for result in results)
    
    # Search with different context
    other_context = memory.create_context("Other Context")
    memory.store("Test in other context", other_context)
    results = memory.search("test", context_id=context_id)
    assert len(results) == 2  # Should only find memories in specified context

def test_tag_search(memory):
    """Test searching memories by tags."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store memories with different tags
    memory.store("Memory with tag1", context_id, tags=["tag1"])
    memory.store("Memory with tag2", context_id, tags=["tag2"])
    memory.store("Memory with both tags", context_id, tags=["tag1", "tag2"])
    
    # Search by tag
    results = memory.search(context_id=context_id, tags=["tag1"])
    assert len(results) == 2
    assert all("tag1" in result['tags'] for result in results)
    
    # Search by multiple tags
    results = memory.search(context_id=context_id, tags=["tag1", "tag2"])
    assert len(results) == 1
    assert "both tags" in results[0]['content']

def test_importance_update(memory):
    """Test updating memory importance."""
    # Create a context and store memory
    context_id = memory.create_context("Test Context")
    memory_id = memory.store(
        content="Test memory",
        context_id=context_id,
        importance=5
    )
    
    # Update importance
    memory.update_importance(memory_id, 8)
    
    # Verify update
    retrieved = memory.retrieve(memory_id)
    assert retrieved['importance'] == 8

def test_tag_management(memory):
    """Test adding and managing tags."""
    # Create a context and store memory
    context_id = memory.create_context("Test Context")
    memory_id = memory.store(
        content="Test memory",
        context_id=context_id,
        tags=["initial"]
    )
    
    # Add more tags
    memory.add_tags(memory_id, ["additional", "tags"])
    
    # Verify tags
    retrieved = memory.retrieve(memory_id)
    assert "initial" in retrieved['tags']
    assert "additional" in retrieved['tags']
    assert "tags" in retrieved['tags']

def test_memory_deletion(memory):
    """Test memory deletion."""
    # Create a context and store memory
    context_id = memory.create_context("Test Context")
    memory_id = memory.store(
        content="Test memory",
        context_id=context_id
    )
    
    # Delete memory
    memory.delete_memory(memory_id)
    
    # Verify deletion
    with pytest.raises(ValueError):
        memory.retrieve(memory_id)

def test_context_manager(temp_db):
    """Test context manager functionality."""
    with SecureMemory(db_path=temp_db, passphrase="test-passphrase") as m:
        # Create a context
        context_id = m.create_context("Test Context")
        
        # Store a memory
        memory_id = m.store(
            content="Test memory",
            context_id=context_id
        )
        
        # Verify memory exists
        retrieved = m.retrieve(memory_id)
        assert retrieved['content'] == "Test memory"
    
    # Verify connection is closed after context exit
    assert not m.initialized

def test_invalid_operations(memory):
    """Test handling of invalid operations."""
    # Test retrieving non-existent memory
    with pytest.raises(ValueError):
        memory.retrieve(999)
    
    # Test storing in non-existent context
    with pytest.raises(ValueError):
        memory.store("Test", "non-existent-context")
    
    # Test adding tags to non-existent memory
    with pytest.raises(ValueError):
        memory.add_tags(999, ["test"])

def test_database_persistence(temp_db):
    """Test that data persists between sessions."""
    # Store data in first session
    with SecureMemory(db_path=temp_db, passphrase="test-passphrase") as m1:
        context_id = m1.create_context("Test Context")
        memory_id = m1.store(
            content="Persistent memory",
            context_id=context_id
        )
    
    # Retrieve data in second session
    with SecureMemory(db_path=temp_db, passphrase="test-passphrase") as m2:
        retrieved = m2.retrieve(memory_id)
        assert retrieved['content'] == "Persistent memory"

def test_wrong_passphrase(temp_db):
    """Test that using wrong passphrase fails."""
    # Create database with one passphrase
    with SecureMemory(db_path=temp_db, passphrase="correct-passphrase") as m:
        m.create_context("Test Context")
    
    # Try to open with wrong passphrase
    with pytest.raises(ValueError, match="Invalid passphrase"):
        SecureMemory(db_path=temp_db, passphrase="wrong-passphrase")

def test_clear_context(memory):
    """Test clearing all memories in a context."""
    # Create context and add memories
    context_id = memory.create_context("Test Context")
    memory.store("Memory 1", context_id)
    memory.store("Memory 2", context_id)
    
    # Verify memories exist
    results = memory.search(context_id=context_id)
    assert len(results) == 2
    
    # Clear context
    deleted = memory.clear_context(context_id)
    assert deleted == 2
    
    # Verify memories are gone
    results = memory.search(context_id=context_id)
    assert len(results) == 0