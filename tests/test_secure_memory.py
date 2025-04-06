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
def temp_db(sqlite_db):
    """Create a temporary database file."""
    return sqlite_db

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
    cursor = memory.conn.cursor()
    cursor.execute("SELECT name, description FROM contexts WHERE id = ?", (context_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "Test Context"
    assert row[1] == "Test description"
    
    # Verify get_contexts works
    contexts = memory.get_contexts()
    assert len(contexts) >= 1
    assert any(c['id'] == context_id for c in contexts)

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
    assert retrieved['tags'] == ["test", "memory"]
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
    """Test searching memories by tag."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store memories with different tags
    memory.store("Memory with tag A", context_id, tags=["A", "common"])
    memory.store("Memory with tag B", context_id, tags=["B", "common"])
    
    # Search by tag
    results = memory.search("Memory", context_id=context_id, tags=["A"])
    assert len(results) == 1
    assert "tag A" in results[0]['content']
    
    # Search with multiple tags
    results = memory.search("Memory", context_id=context_id, tags=["common"])
    assert len(results) == 2

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
    memory.add_tags(memory_id, ["additional", "initial"])  # 'initial' should not be duplicated
    
    # Verify tags
    retrieved = memory.retrieve(memory_id)
    assert set(retrieved['tags']) == {"initial", "additional"}

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

def test_context_manager(memory):
    """Test context manager functionality."""
    with SecureMemory(db_path=memory.db_path, passphrase="test-passphrase") as m:
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
    
    # Verify connection is closed
    assert not m.initialized

def test_invalid_operations(memory):
    """Test handling of invalid operations."""
    # Test retrieving non-existent memory
    with pytest.raises(ValueError):
        memory.retrieve(999)
    
    # Test storing in non-existent context
    with pytest.raises(ValueError):
        memory.store("Test", "non-existent-context")
    
    # Test updating non-existent memory
    with pytest.raises(Exception):  # Could be IntegrityError or other exception
        memory.update_importance(999, 8)
    
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
    """Test that the wrong passphrase fails properly."""
    # Create DB with one passphrase
    with SecureMemory(db_path=temp_db, passphrase="correct-passphrase") as m1:
        m1.create_context("Test Context")
    
    # Try to open with wrong passphrase
    with pytest.raises(ValueError, match="Failed to decrypt"):
        SecureMemory(db_path=temp_db, passphrase="wrong-passphrase")

def test_clear_context(memory):
    """Test clearing a context."""
    # Create a context and store memories
    context_id = memory.create_context("Test Context")
    memory.store("Memory 1", context_id)
    memory.store("Memory 2", context_id)
    
    # Search to verify memories exist
    results = memory.search("Memory", context_id=context_id)
    assert len(results) == 2
    
    # Clear the context
    memory.clear_context(context_id)
    
    # Verify context is cleared
    contexts = memory.get_contexts()
    assert not any(c['id'] == context_id for c in contexts)
    
    # Create new context with same name to verify search is empty
    new_context_id = memory.create_context("Test Context")
    results = memory.search("Memory", context_id=new_context_id)
    assert len(results) == 0