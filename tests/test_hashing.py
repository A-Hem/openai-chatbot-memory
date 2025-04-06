"""
Test suite for the security hashing module.
"""

import pytest
import base64
from security.hashing import (
    generate_salt,
    compute_hash,
    verify_hash,
    secure_compare,
    hash_to_string,
    string_to_hash
)

def test_salt_generation():
    """Test that salt generation works properly."""
    # Generate multiple salts
    salt1 = generate_salt()
    salt2 = generate_salt()
    
    # Verify salts are not the same
    assert salt1 != salt2
    
    # Verify salt length is correct
    assert len(salt1) == 16  # 16 bytes

def test_password_hashing():
    """Test that password hashing works properly."""
    # With generated salt
    password = "test-password"
    hash_bytes, salt = compute_hash(password)
    
    # Verify hash is not the same as password
    assert hash_bytes != password.encode()
    
    # Create hash string for verification
    hash_str = hash_to_string(hash_bytes, salt)
    
    # Verify password
    assert verify_hash(password, hash_str)
    assert not verify_hash("wrong-password", hash_str)
    
    # With provided salt
    salt = generate_salt()
    hash_bytes, salt2 = compute_hash(password, salt)
    
    # Verify salt is the same
    assert salt == salt2
    
    # Create hash string
    hash_str = hash_to_string(hash_bytes, salt)
    
    # Verify password
    assert verify_hash(password, hash_str)
    assert not verify_hash("wrong-password", hash_str)

def test_secure_comparison():
    """Test secure string comparison."""
    # Equal strings
    assert secure_compare("test-string", "test-string")
    
    # Different strings
    assert not secure_compare("test-string", "other-string")
    
    # Different length strings
    assert not secure_compare("test-string", "test-string-extra")
    
    # Case sensitivity
    assert not secure_compare("Test-String", "test-string")

def test_hash_string_conversion():
    """Test hash and salt to string conversion."""
    # Generate hash
    password = "test-password"
    hash_bytes, salt = compute_hash(password)
    
    # Convert to string
    hash_str = hash_to_string(hash_bytes, salt)
    
    # Convert back to hash and salt
    recovered_hash, recovered_salt = string_to_hash(hash_str)
    
    # Verify hash and salt are the same
    assert hash_bytes == recovered_hash
    assert salt == recovered_salt
    
    # Verify password still works
    assert verify_hash(password, hash_str)

def test_hash_parameters():
    """Test that hash parameters are correct."""
    # Generate hash
    password = "test-password"
    hash_bytes, salt = compute_hash(password)
    
    # Convert to string
    hash_str = hash_to_string(hash_bytes, salt)
    
    # Verify hash string format
    decoded = base64.b64decode(hash_str)
    assert b":" in decoded  # Should contain separator

def test_invalid_hash_verification():
    """Test handling invalid hash strings."""
    # Test with invalid hash format
    assert not verify_hash("password", "invalid-hash")
    
    # Test with empty hash
    assert not verify_hash("password", "")
    
    # Test with None hash
    with pytest.raises(Exception):
        verify_hash("password", None) 