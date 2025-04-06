"""
embedding_memory.py - Vector-based memory storage with semantic search

This module implements a vector-based memory storage system that uses
sentence-transformers for semantic search capabilities. It extends the
base secure memory system with vector embeddings and similarity search.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from .secure_memory import SecureMemory

class EmbeddingMemory(SecureMemory):
    """
    Vector-based memory storage with semantic search capabilities.
    
    This class extends SecureMemory to add vector embeddings and semantic
    search functionality using sentence-transformers.
    """
    
    def __init__(self, db_path: str, model_name: str = "all-MiniLM-L6-v2",
                 passphrase: str = None, key_path: str = None):
        """
        Initialize embedding memory system.
        
        Args:
            db_path: Path to SQLite database file
            model_name: Name of the sentence-transformer model to use
            passphrase: Optional passphrase for encryption
            key_path: Optional path to encryption key file
        """
        super().__init__(db_path, passphrase, key_path)
        
        # Initialize the sentence transformer model
        self.model = SentenceTransformer(model_name)
        
        # Create embeddings table if it doesn't exist
        self._create_embeddings_table()
    
    def _create_embeddings_table(self) -> None:
        """Create the embeddings table for storing vector embeddings."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                memory_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)
        
        self.conn.commit()
    
    def store(self, content: str, context_id: str,
              importance: int = 5, tags: List[str] = None) -> int:
        """
        Store a memory with its vector embedding.
        
        Args:
            content: Content to store
            context_id: Context ID to associate with memory
            importance: Importance score (1-10)
            tags: Optional tags for categorization
            
        Returns:
            Memory ID
        """
        # Store the memory using parent class
        memory_id = super().store(content, context_id, importance, tags)
        
        # Generate and store the embedding
        embedding = self.model.encode(content)
        
        # Store embedding in database
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO embeddings (memory_id, embedding) VALUES (?, ?)",
            (memory_id, embedding.tobytes())
        )
        
        self.conn.commit()
        return memory_id
    
    def semantic_search(self, query: str, context_id: str = None,
                       limit: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search for memories using semantic similarity.
        
        Args:
            query: Search query
            context_id: Optional context ID to search within
            limit: Maximum number of results
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching memories with similarity scores
        """
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Build SQL query
        sql = """
            SELECT m.id, m.content, m.importance, m.tags, m.created_at, e.embedding
            FROM memories m
            JOIN embeddings e ON m.id = e.memory_id
        """
        params = []
        
        if context_id:
            sql += " WHERE m.context_id = ?"
            params.append(context_id)
        
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            # Extract memory data
            memory_id = row[0]
            content = row[1]
            importance = row[2]
            tags = row[3]
            created_at = row[4]
            embedding_bytes = row[5]
            
            # Convert embedding bytes to numpy array
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= threshold:
                results.append({
                    'id': memory_id,
                    'content': content,
                    'importance': importance,
                    'tags': tags,
                    'created_at': created_at,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and importance
        results.sort(key=lambda x: (x['similarity'], x['importance']), reverse=True)
        
        return results[:limit]
    
    def delete_memory(self, memory_id: int) -> None:
        """
        Delete a memory and its embedding.
        
        Args:
            memory_id: ID of the memory to delete
        """
        cursor = self.conn.cursor()
        
        # Delete embedding first (due to foreign key constraint)
        cursor.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))
        
        # Delete memory using parent class
        super().delete_memory(memory_id)
        
        self.conn.commit()

    def batch_store(self, memories: List[Dict[str, Any]], context_id: str) -> List[int]:
        """
        Store multiple memories efficiently in a single transaction.
        
        Args:
            memories: List of dictionaries containing memory data:
                     [{'content': str, 'importance': int, 'tags': List[str]}]
            context_id: Context ID to associate with memories
            
        Returns:
            List[int]: List of memory IDs for stored memories
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        memory_ids = []
        cursor = self.conn.cursor()
        
        try:
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Process each memory
            for memory_data in memories:
                content = memory_data['content']
                importance = memory_data.get('importance', 5)
                tags = memory_data.get('tags', [])
                
                # Store base memory
                memory_id = super().store(content, context_id, importance, tags)
                
                # Generate and store embedding
                embedding = self.model.encode(content)
                cursor.execute(
                    "INSERT INTO embeddings (memory_id, embedding) VALUES (?, ?)",
                    (memory_id, embedding.tobytes())
                )
                
                memory_ids.append(memory_id)
            
            # Commit transaction
            self.conn.commit()
            return memory_ids
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise RuntimeError(f"Batch store failed: {str(e)}")

    def recompute_embeddings(self, context_id: str = None) -> int:
        """
        Recompute embeddings for existing memories.
        Useful when updating the embedding model or fixing corrupted embeddings.
        
        Args:
            context_id: Optional context ID to limit recomputation
            
        Returns:
            int: Number of embeddings recomputed
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        
        try:
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Get memories to recompute
            sql = "SELECT id, content FROM memories"
            params = []
            
            if context_id:
                sql += " WHERE context_id = ?"
                params.append(context_id)
            
            cursor.execute(sql, params)
            memories = cursor.fetchall()
            
            # Recompute embeddings
            count = 0
            for memory_id, content in memories:
                embedding = self.model.encode(content)
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (memory_id, embedding)
                    VALUES (?, ?)
                    """,
                    (memory_id, embedding.tobytes())
                )
                count += 1
            
            # Commit transaction
            self.conn.commit()
            return count
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise RuntimeError(f"Embedding recomputation failed: {str(e)}")

    def optimize_embeddings(self) -> None:
        """
        Optimize the embeddings table and clean up any orphaned embeddings.
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        
        try:
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Remove orphaned embeddings
            cursor.execute("""
                DELETE FROM embeddings 
                WHERE memory_id NOT IN (SELECT id FROM memories)
            """)
            
            # Optimize the database
            cursor.execute("VACUUM")
            
            # Commit transaction
            self.conn.commit()
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise RuntimeError(f"Embedding optimization failed: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Initialize embedding memory
    memory = EmbeddingMemory(
        db_path="memory.db",
        passphrase="my-secure-passphrase"
    )
    
    try:
        # Create a context
        context_id = memory.create_context(
            name="General Conversation",
            description="General chat context"
        )
        
        # Store some memories
        memory.store(
            content="The weather is nice today",
            context_id=context_id,
            importance=8,
            tags=["weather", "conversation"]
        )
        
        memory.store(
            content="I had a great lunch at the restaurant",
            context_id=context_id,
            importance=7,
            tags=["food", "restaurant"]
        )
        
        # Perform semantic search
        results = memory.semantic_search(
            query="How's the weather outside?",
            context_id=context_id,
            threshold=0.5
        )
        
        print("Semantic search results:")
        for result in results:
            print(f"Content: {result['content']}")
            print(f"Similarity: {result['similarity']:.3f}")
            print(f"Importance: {result['importance']}")
            print("---")
        
    finally:
        memory.close() 