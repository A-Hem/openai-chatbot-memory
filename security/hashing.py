"""
hashing.py - Secure password hashing utilities

This module provides secure password hashing and verification using Argon2,
which is the winner of the 2015 Password Hashing Competition and is considered
one of the most secure password hashing algorithms available.
"""

import os
import hashlib
import base64
from typing import Tuple, Optional
from passlib.hash import argon2

def generate_salt() -> bytes:
    """
    Generate a secure random salt.
    
    Returns:
        Random bytes for use as a salt
    """
    return os.urandom(16)

def compute_hash(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """
    Compute Argon2 hash of a password.
    
    Args:
        password: Password to hash
        salt: Optional salt to use (if None, generates new salt)
        
    Returns:
        Tuple[bytes, bytes]: Tuple of (hash, salt)
    """
    if salt is None:
        salt = generate_salt()
    
    # Use Argon2id with recommended parameters
    hash_str = argon2.using(
        salt=salt,
        memory_cost=65536,  # 64MB
        time_cost=3,        # 3 iterations
        parallelism=4,      # 4 parallel threads
        hash_len=32,        # 32 bytes output
        type='id'           # Use Argon2id
    ).hash(password)
    
    return hash_str.encode(), salt

def verify_hash(password: str, hash_str: str) -> bool:
    """
    Verify a password against a hash string.
    
    Args:
        password: Password to verify
        hash_str: Hash string to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    try:
        return argon2.verify(hash_str, password)
    except Exception:
        return False

def secure_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time.
    
    Args:
        a: First string to compare
        b: Second string to compare
        
    Returns:
        bool: True if strings are equal, False otherwise
    """
    try:
        return hashlib.compare_digest(a.encode(), b.encode())
    except AttributeError:
        # Fallback for older Python versions (not timing-safe!)
        if len(a) != len(b):
            return False
        return a == b

def hash_to_string(hash_bytes: bytes, salt: bytes) -> str:
    """
    Convert hash and salt to string format.
    
    Args:
        hash_bytes: Hash bytes
        salt: Salt bytes
        
    Returns:
        str: String representation of hash and salt
    """
    # Combine hash and salt with a separator
    combined = hash_bytes + b":" + salt
    return base64.b64encode(combined).decode('utf-8')

def string_to_hash(hash_str: str) -> Tuple[bytes, bytes]:
    """
    Convert hash string back to hash and salt.
    
    Args:
        hash_str: String representation of hash and salt
        
    Returns:
        Tuple[bytes, bytes]: Tuple of (hash, salt)
    """
    try:
        # Decode base64 string
        combined = base64.b64decode(hash_str.encode('utf-8'))
        
        # Split hash and salt
        parts = combined.split(b":")
        if len(parts) != 2:
            raise ValueError("Invalid hash string format")
            
        return parts[0], parts[1]
    except Exception:
        raise ValueError("Invalid hash string")

# Example usage
if __name__ == "__main__":
    # Test password hashing
    password = "my-secure-password"
    
    # Compute hash
    hash_str, salt = compute_hash(password)
    print(f"Generated hash: {hash_str}")
    print(f"Generated salt: {salt.hex()}")
    
    # Verify password
    is_valid = verify_hash(password, hash_str)
    print(f"Password valid: {is_valid}")
    
    # Test with wrong password
    wrong_password = "wrong-password"
    is_valid = verify_hash(wrong_password, hash_str)
    print(f"Wrong password valid: {is_valid}")
    
    # Test secure comparison
    str1 = "secret"
    str2 = "secret"
    str3 = "different"
    
    print(f"Secure compare (same): {secure_compare(str1, str2)}")
    print(f"Secure compare (different): {secure_compare(str1, str3)}") 