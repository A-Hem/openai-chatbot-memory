"""
secure_memory.py - Secure memory storage system for AI chatbots

This module implements a secure, encrypted memory storage system using SQLite.
It provides end-to-end encryption, password protection, and advanced memory
management features while ensuring data privacy and security.
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from security.encryption import (
    generate_key,
    encrypt_with_key,
    decrypt_with_key,
    key_to_string,
    string_to_key
)
from security.hashing import (
    compute_hash,
    verify_hash,
    secure_compare
)
from Crypto.Cipher import AES

class SecureMemory:
    """
    Secure memory storage system with encryption and password protection.
    
    This class provides a secure way to store and retrieve memories using
    SQLite with end-to-end encryption and password protection.
    """
    
    def __init__(self, db_path: str, passphrase: str = None, key_path: str = None):
        """
        Initialize secure memory system.
        
        Args:
            db_path: Path to SQLite database file
            passphrase: Optional passphrase for encryption
            key_path: Optional path to encryption key file
        """
        self.db_path = db_path
        self.passphrase = passphrase
        self.key_path = key_path
        self.conn = None
        self.encryption_key = None
        self.initialized = False
        
        # Setup encryption key
        self._setup_encryption_key()
        
        # Initialize database
        self._initialize_database()
    
    def _setup_encryption_key(self) -> None:
        """Set up the encryption key using either the key file or passphrase."""
        if self.key_path and os.path.exists(self.key_path):
            # Load existing key from file
            with open(self.key_path, 'rb') as f:
                key_data = f.read()
                self.encryption_key, _ = string_to_key(key_data.decode())
        elif self.key_path:
            # Generate new key and save to file
            self.encryption_key, salt = generate_key()
            key_string = key_to_string(self.encryption_key, salt)
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, 'w') as f:
                f.write(key_string)
        elif self.passphrase:
            # Derive key from passphrase
            self.encryption_key, _ = generate_key(self.passphrase)
        else:
            # Generate random key
            self.encryption_key, _ = generate_key()
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create contexts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL,
                content BLOB NOT NULL,
                content_hash TEXT NOT NULL,
                importance INTEGER DEFAULT 5,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            )
        """)
        
        # Create meta table for system settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Initialize meta table if empty
        cursor.execute("SELECT COUNT(*) FROM meta")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO meta (key, value) VALUES
                ('version', '1.0'),
                ('encryption_version', 'aes-gcm'),
                ('hashing_version', 'argon2id')
            """)
        
        self.conn.commit()
        self.initialized = True
    
    def create_context(self, name: str, description: str = None) -> str:
        """
        Create a new conversation context.
        
        Args:
            name: Name of the context
            description: Optional description
            
        Returns:
            Context ID
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        context_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute(
            "INSERT INTO contexts (id, name, description) VALUES (?, ?, ?)",
            (context_id, name, description)
        )
        
        self.conn.commit()
        return context_id
    
    def store(self, content: str, context_id: str, 
              importance: int = 5, tags: List[str] = None) -> int:
        """
        Store a memory with encryption.
        
        Args:
            content: Content to store
            context_id: Context ID to associate with memory
            importance: Importance score (1-10)
            tags: Optional tags for categorization
            
        Returns:
            Memory ID
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        # Verify context exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM contexts WHERE id = ?", (context_id,))
        if not cursor.fetchone():
            raise ValueError(f"Context {context_id} doesn't exist")
        
        # Encrypt content
        encrypted_content, nonce = encrypt_with_key(content, self.encryption_key)
        
        # Store nonce with encrypted content
        combined_data = nonce + encrypted_content
        
        # Store tags as JSON
        tags_json = json.dumps(tags) if tags else None
        
        # Save to database
        cursor.execute(
            """
            INSERT INTO memories 
            (context_id, content, content_hash, importance, tags) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (context_id, combined_data, content, importance, tags_json)
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def retrieve(self, memory_id: int) -> Dict[str, Any]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Dictionary containing memory data
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT content, importance, tags, created_at
            FROM memories WHERE id = ?
            """,
            (memory_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Memory {memory_id} not found")
        
        # Extract nonce and encrypted content
        combined_data = row[0]
        nonce = combined_data[:12]  # First 12 bytes are nonce
        encrypted_content = combined_data[12:]
        
        # Decrypt content
        decrypted_content = decrypt_with_key(encrypted_content, self.encryption_key, nonce)
        
        # Parse tags
        tags = json.loads(row[2]) if row[2] else []
        
        return {
            'id': memory_id,
            'content': decrypted_content,
            'importance': row[1],
            'tags': tags,
            'created_at': row[3]
        }
    
    def search(self, query: str, context_id: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for memories using text matching.
        
        Args:
            query: Search query
            context_id: Optional context ID to search within
            tags: Optional list of tags to filter by
            
        Returns:
            List[Dict[str, Any]]: List of matching memories
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        
        # Build SQL query
        sql = "SELECT id, content, importance, tags, created_at FROM memories"
        params = []
        conditions = []
        
        if context_id:
            conditions.append("context_id = ?")
            params.append(context_id)
            
        if tags:
            for tag in tags:
                conditions.append("json_array_contains(tags, ?)")
                params.append(tag)
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            # Decrypt content
            try:
                decrypted_content = self._decrypt(row[1])
            except Exception as e:
                print(f"Warning: Failed to decrypt memory {row[0]}: {str(e)}")
                continue
            
            # Check if content matches query
            if query.lower() in decrypted_content.lower():
                results.append({
                    'id': row[0],
                    'content': decrypted_content,
                    'importance': row[2],
                    'tags': json.loads(row[3]),
                    'created_at': row[4]
                })
        
        return results
    
    def update_importance(self, memory_id: int, importance: int) -> None:
        """
        Update the importance score of a memory.
        
        Args:
            memory_id: ID of the memory to update
            importance: New importance score (1-10)
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE memories SET importance = ? WHERE id = ?",
            (importance, memory_id)
        )
        self.conn.commit()
    
    def add_tags(self, memory_id: int, tags: List[str]) -> None:
        """
        Add tags to a memory.
        
        Args:
            memory_id: ID of the memory to update
            tags: List of tags to add
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT tags FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Memory {memory_id} not found")
        
        current_tags = json.loads(row[0]) if row[0] else []
        new_tags = list(set(current_tags + tags))  # Remove duplicates
        
        cursor.execute(
            "UPDATE memories SET tags = ? WHERE id = ?",
            (json.dumps(new_tags), memory_id)
        )
        self.conn.commit()
    
    def delete_memory(self, memory_id: int) -> None:
        """
        Delete a memory.
        
        Args:
            memory_id: ID of the memory to delete
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.conn.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.initialized = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_contexts(self) -> List[Dict[str, Any]]:
        """
        Get all contexts.
        
        Returns:
            List[Dict[str, Any]]: List of context dictionaries
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, description FROM contexts")
        
        contexts = []
        for row in cursor.fetchall():
            contexts.append({
                'id': row[0],
                'name': row[1],
                'description': row[2]
            })
        
        return contexts

    def clear_context(self, context_id: str) -> None:
        """
        Clear all memories in a context.
        
        Args:
            context_id: ID of the context to clear
        """
        if not self.initialized:
            raise RuntimeError("Memory system not initialized")
            
        cursor = self.conn.cursor()
        
        # Get all memories in context
        cursor.execute("SELECT id FROM memories WHERE context_id = ?", (context_id,))
        memory_ids = [row[0] for row in cursor.fetchall()]
        
        # Delete each memory
        for memory_id in memory_ids:
            self.delete_memory(memory_id)
        
        # Delete the context
        cursor.execute("DELETE FROM contexts WHERE id = ?", (context_id,))
        self.conn.commit()

    def _decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt data using AES-GCM.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            
        Returns:
            str: Decrypted data as string
        """
        try:
            # Extract nonce and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            # Create cipher
            cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
            
            # Decrypt
            decrypted_data = cipher.decrypt(ciphertext)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def _encrypt(self, data: str) -> bytes:
        """
        Encrypt data using AES-GCM.
        
        Args:
            data: Data to encrypt
            
        Returns:
            bytes: Encrypted data
        """
        # Generate random nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
        
        # Encrypt
        ciphertext = cipher.encrypt(data.encode('utf-8'))
        
        # Combine nonce and ciphertext
        return nonce + ciphertext

# Example usage
if __name__ == "__main__":
    # Initialize secure memory
    memory = SecureMemory(
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
            content="User's message",
            context_id=context_id,
            importance=8,
            tags=["user_input", "conversation"]
        )
        
        memory.store(
            content="Assistant's response",
            context_id=context_id,
            importance=7,
            tags=["assistant", "response"]
        )
        
        # Search for memories
        results = memory.search("message", context_id=context_id)
        print("Search results:", results)
        
        # Retrieve a specific memory
        memory_data = memory.retrieve(1)
        print("Retrieved memory:", memory_data)
        
    finally:
        memory.close()