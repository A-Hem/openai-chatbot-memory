"""
Test suite for the hashing module.
"""

import pytest
from security.hashing import (
    generate_salt,
    compute_hash,
    verify_hash,
    secure_compare,
    hash_to_string,
    string_to_hash
)

def test_salt_generation():
    """Test that salt generation produces unique values."""
    salt1 = generate_salt()
    salt2 = generate_salt()
    
    assert len(salt1) == 16
    assert len(salt2) == 16
    assert salt1 != salt2

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test-password"
    
    # Test with generated salt
    hash_str, salt = compute_hash(password)
    assert verify_hash(password, hash_str)
    assert not verify_hash("wrong-password", hash_str)
    
    # Test with provided salt
    hash_str2, salt2 = compute_hash(password, salt)
    assert verify_hash(password, hash_str2)
    assert hash_str != hash_str2  # Different hashes due to different salts

def test_secure_comparison():
    """Test secure string comparison."""
    # Test equal strings
    assert secure_compare("secret", "secret")
    
    # Test different strings
    assert not secure_compare("secret", "different")
    
    # Test empty strings
    assert secure_compare("", "")
    
    # Test case sensitivity
    assert not secure_compare("Secret", "secret")

def test_hash_string_conversion():
    """Test conversion between hash/salt and string representation."""
    password = "test-password"
    hash_str, salt = compute_hash(password)
    
    # Convert to string
    hash_string = hash_to_string(hash_str, salt)
    
    # Convert back
    recovered_hash, recovered_salt = string_to_hash(hash_string)
    
    # Verify
    assert recovered_hash == hash_str
    assert recovered_salt == salt
    
    # Verify the recovered hash still works
    assert verify_hash(password, recovered_hash)

def test_hash_parameters():
    """Test that hash parameters are properly set."""
    password = "test-password"
    hash_str, salt = compute_hash(password)
    
    # Verify hash format (Argon2 hash string)
    assert hash_str.startswith("$argon2id$")
    assert "m=65536,t=3,p=4" in hash_str  # Check memory, time, and parallelism parameters

def test_invalid_hash_verification():
    """Test handling of invalid hash strings."""
    # Test with malformed hash string
    assert not verify_hash("password", "invalid-hash-string")
    
    # Test with empty hash string
    assert not verify_hash("password", "")
    
    # Test with None values
    assert not verify_hash(None, "hash")  # type: ignore
    assert not verify_hash("password", None)  # type: ignore 