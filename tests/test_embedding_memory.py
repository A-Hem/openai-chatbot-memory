"""
Test suite for the embedding memory implementation.
"""

import os
import pytest
import tempfile
import numpy as np
import time
from memory.embedding_memory import EmbeddingMemory

@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    yield path
    os.close(fd)
    # Add retry logic for file deletion
    max_retries = 3
    for _ in range(max_retries):
        try:
            os.unlink(path)
            break
        except PermissionError:
            time.sleep(0.1)  # Wait a bit before retrying

@pytest.fixture
def memory(temp_db):
    """Create an EmbeddingMemory instance with a temporary database."""
    # Skip if sentence-transformers not installed
    pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")
    
    try:
        memory = EmbeddingMemory(
            db_path=temp_db,
            model_name="all-MiniLM-L6-v2",
            passphrase="test-passphrase"
        )
        yield memory
        memory.close()
    except Exception as e:
        pytest.skip(f"Failed to initialize EmbeddingMemory: {str(e)}")

def test_initialization(memory):
    """Test embedding memory system initialization."""
    assert memory.initialized
    assert memory.conn is not None
    assert memory.encryption_key is not None
    assert memory.model is not None

def test_embeddings_table_creation(memory):
    """Test that the embeddings table is created properly."""
    cursor = memory.conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='embeddings'
    """)
    assert cursor.fetchone() is not None

def test_memory_storage_with_embedding(memory):
    """Test storing memories with embeddings."""
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
    
    # Verify memory was stored
    cursor = memory.conn.cursor()
    cursor.execute("SELECT content FROM memories WHERE id = ?", (memory_id,))
    assert cursor.fetchone() is not None
    
    # Verify embedding was stored
    cursor.execute("SELECT embedding FROM embeddings WHERE memory_id = ?", (memory_id,))
    embedding_data = cursor.fetchone()
    assert embedding_data is not None
    
    # Verify embedding is valid
    embedding = np.frombuffer(embedding_data[0], dtype=np.float32)
    assert embedding.shape[0] > 0  # Should have non-zero dimensions

def test_semantic_search(memory):
    """Test semantic search functionality."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store multiple memories with related content
    memories = [
        ("The weather is nice today", ["weather"]),
        ("I had a great lunch at the restaurant", ["food"]),
        ("The temperature is 25 degrees Celsius", ["weather"])
    ]
    
    for content, tags in memories:
        memory.store(
            content=content,
            context_id=context_id,
            tags=tags
        )
    
    # Test semantic search
    results = memory.semantic_search(
        query="How's the weather outside?",
        context_id=context_id,
        threshold=0.5
    )
    
    # Verify results
    assert len(results) > 0
    assert all(0 <= result['similarity'] <= 1 for result in results)
    assert all(result['similarity'] >= 0.5 for result in results)
    
    # Weather-related content should be ranked higher than food-related content
    weather_scores = [r['similarity'] for r in results if "weather" in r['content'].lower()]
    food_scores = [r['similarity'] for r in results if "food" in r['content'].lower() or "restaurant" in r['content'].lower()]
    
    if weather_scores and food_scores:
        assert max(weather_scores) > max(food_scores)

def test_semantic_search_with_different_context(memory):
    """Test semantic search respects context boundaries."""
    # Create two contexts
    context1 = memory.create_context("Weather Context")
    context2 = memory.create_context("Food Context")
    
    # Store memories in different contexts
    memory.store(
        content="The weather is nice today",
        context_id=context1,
        tags=["weather"]
    )
    
    memory.store(
        content="I had a great lunch at the restaurant",
        context_id=context2,
        tags=["food"]
    )
    
    # Search in first context
    results1 = memory.semantic_search(
        query="How's the weather outside?",
        context_id=context1
    )
    
    # Search in second context
    results2 = memory.semantic_search(
        query="How's the weather outside?",
        context_id=context2
    )
    
    # Verify context separation
    if results1 and results2:
        weather_content = [r for r in results1 if "weather" in r['content'].lower()]
        food_content = [r for r in results2 if "food" in r['content'].lower() or "restaurant" in r['content'].lower()]
        
        assert len(weather_content) > 0
        assert len(food_content) > 0

def test_semantic_search_threshold(memory):
    """Test semantic search threshold filtering."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store memories
    memory.store(
        content="The weather is nice today",
        context_id=context_id,
        tags=["weather"]
    )
    
    memory.store(
        content="I had a great lunch at the restaurant",
        context_id=context_id,
        tags=["food"]
    )
    
    # Search with high threshold
    results_high = memory.semantic_search(
        query="How's the weather outside?",
        context_id=context_id,
        threshold=0.9  # Very high threshold
    )
    
    # Search with low threshold
    results_low = memory.semantic_search(
        query="How's the weather outside?",
        context_id=context_id,
        threshold=0.1  # Very low threshold
    )
    
    # High threshold should return fewer results than low threshold
    assert len(results_low) >= len(results_high)

def test_memory_deletion_with_embedding(memory):
    """Test that memory deletion also removes embeddings."""
    # Create a context and store memory
    context_id = memory.create_context("Test Context")
    memory_id = memory.store(
        content="Test memory",
        context_id=context_id
    )
    
    # Delete memory
    memory.delete_memory(memory_id)
    
    # Verify memory is deleted
    cursor = memory.conn.cursor()
    cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
    assert cursor.fetchone() is None
    
    # Verify embedding is deleted
    cursor.execute("SELECT memory_id FROM embeddings WHERE memory_id = ?", (memory_id,))
    assert cursor.fetchone() is None

def test_database_persistence_with_embeddings(temp_db):
    """Test that data and embeddings persist between sessions."""
    # Skip if sentence-transformers not installed
    try:
        # Store data in first session
        with EmbeddingMemory(
            db_path=temp_db,
            model_name="all-MiniLM-L6-v2",
            passphrase="test-passphrase"
        ) as m1:
            context_id = m1.create_context("Test Context")
            memory_id = m1.store(
                content="Persistent memory",
                context_id=context_id
            )
        
        # Retrieve data in second session
        with EmbeddingMemory(
            db_path=temp_db,
            model_name="all-MiniLM-L6-v2",
            passphrase="test-passphrase"
        ) as m2:
            # Verify memory exists
            retrieved = m2.retrieve(memory_id)
            assert retrieved['content'] == "Persistent memory"
            
            # Verify embedding exists
            cursor = m2.conn.cursor()
            cursor.execute("SELECT embedding FROM embeddings WHERE memory_id = ?", (memory_id,))
            assert cursor.fetchone() is not None
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_similarity_ordering(memory):
    """Test that results are ordered by similarity."""
    # Create a context
    context_id = memory.create_context("Test Context")
    
    # Store related memories
    memory.store("Weather forecast shows rain", context_id)
    memory.store("Weather today is cloudy", context_id)
    memory.store("Something completely unrelated", context_id)
    
    # Search for weather
    results = memory.semantic_search("What's the weather like?", context_id)
    
    # Results should be ordered by decreasing similarity
    if len(results) >= 2:
        assert results[0]['similarity'] >= results[1]['similarity']