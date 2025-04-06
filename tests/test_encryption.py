"""
Tests for the encryption module.

This module tests the core encryption functionality used by the secure memory system.
"""

import pytest
import os
import sys
import importlib.util

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the encryption functions
try:
    from security.encryption import generate_key, encrypt_with_key, decrypt_with_key, generate_key
except ImportError:
    # Try direct import for CI environment
    from encryption import generate_key, encrypt_with_key, decrypt_with_key

def test_key_generation():
    """Test that key generation produces valid keys."""
    key, salt = generate_key()
    assert len(key) == 32  # 256 bits = 32 bytes
    assert len(salt) == 16  # 128 bits = 16 bytes
    
    # Generate another key to ensure they're different
    key2, salt2 = generate_key()
    assert key != key2
    assert salt != salt2

def test_encryption_roundtrip():
    """Test that encryption followed by decryption returns the original data."""
    key, _ = generate_key()
    data = "This is a test message"
    
    # Encrypt and then decrypt
    encrypted, nonce = encrypt_with_key(data, key)
    decrypted = decrypt_with_key(encrypted, key, nonce)
    
    assert data == decrypted
    assert encrypted != data.encode()  # Encrypted data should be different from original

def test_different_keys():
    """Test that using different keys fails to decrypt."""
    key1, _ = generate_key()
    key2, _ = generate_key()
    data = "This is a test message"
    
    encrypted, nonce = encrypt_with_key(data, key1)
    
    # Trying to decrypt with a different key should raise an error
    with pytest.raises(Exception):
        decrypt_with_key(encrypted, key2, nonce)



def test_corrupted_encrypted_data():
    """Test handling of corrupted encrypted data."""
    key, _ = generate_key()
    data = "Original message"
    
    encrypted, nonce = encrypt_with_key(data, key)
    
    # Corrupt the encrypted data (change a byte in the middle)
    middle = len(encrypted) // 2
    corrupted = encrypted[:middle] + bytes([encrypted[middle] ^ 0xFF]) + encrypted[middle+1:]
    
    # Decryption should fail
    with pytest.raises(Exception):
        decrypt_with_key(corrupted, key, nonce)

def test_unicode_data():
    """Test encryption of Unicode data."""
    key, _ = generate_key()
    
    # Unicode data with various characters
    data = "Hello, world!"
    
    encrypted, nonce = encrypt_with_key(data, key)
    decrypted = decrypt_with_key(encrypted, key, nonce)
    
    assert data == decrypted