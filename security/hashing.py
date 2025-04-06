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

def generate_salt(size: int = 16) -> bytes:
    """
    Generate a secure random salt.
    
    Args:
        size: Size of the salt in bytes
        
    Returns:
        Random salt bytes
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
    hash_obj = argon2.using(
        salt=salt,
        memory_cost=65536,  # 64MB
        time_cost=3,        # 3 iterations
        parallelism=4,      # 4 parallel threads
        hash_len=32,        # 32 bytes output
        type='id'           # Use Argon2id
    )
    
    # Hash the password and get the full hash string
    full_hash = hash_obj.hash(password)
    
    # Return the hash string and salt
    return full_hash.encode(), salt

def verify_hash(password: str, hash_str: str) -> bool:
    """
    Verify a password against a hash string.
    
    Args:
        password: Password to verify
        hash_str: Hash string to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
        
    Raises:
        ValueError: If hash_str is None
    """
    if hash_str is None:
        raise ValueError("Hash string cannot be None")
    
    if not isinstance(hash_str, str):
        return False
    
    if not hash_str:
        return False
    
    try:
        # First try to verify using standard Argon2 format
        if hash_str.startswith('$argon2'):
            return argon2.verify(password, hash_str)
        
        # If not standard format, try our custom format
        try:
            hash_bytes, salt = string_to_hash(hash_str)
            if hash_bytes.startswith(b'$argon2'):
                return argon2.verify(password, hash_bytes.decode())
        except ValueError:
            pass
            
        # If all else fails, compute new hash with same salt and compare
        new_hash, _ = compute_hash(password, salt)
        new_hash_str = hash_to_string(new_hash, salt)
        return secure_compare(hash_str, new_hash_str)
        
    except Exception:
        # Any error in verification should result in failure
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
    except Exception as e:
        raise ValueError(f"Invalid hash string: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Hash a password
    password = "my-secure-password"
    hash_bytes, salt = compute_hash(password)
    
    # Convert to string
    hash_str = hash_to_string(hash_bytes, salt)
    print(f"Hash string: {hash_str}")
    
    # Verify password
    if verify_hash(password, hash_str):
        print("Password verified!")
    else:
        print("Password verification failed!") 