"""
encryption.py - AES-GCM encryption implementation for secure memory storage

This module provides secure encryption utilities using AES-GCM (Galois/Counter Mode),
which provides both confidentiality and authenticity of the encrypted data.
"""

import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

def generate_key(passphrase: str = None, salt: bytes = None) -> Tuple[bytes, bytes]:
    """
    Generate a secure encryption key from a passphrase or random bytes.
    
    Args:
        passphrase: Optional passphrase to derive the key from
        salt: Optional salt for key derivation (if not provided, a random one will be generated)
        
    Returns:
        Tuple of (key, salt) where:
        - key: 32-byte key suitable for AES-GCM
        - salt: Salt used for key derivation (if using passphrase) or random bytes
    """
    if passphrase:
        # Generate a random salt if not provided
        if salt is None:
            salt = os.urandom(16)
            
        # Use PBKDF2 to derive a key from the passphrase
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,  # High iteration count for security
            backend=default_backend()
        )
        key = kdf.derive(passphrase.encode())
        return key, salt
    else:
        # Generate a random key and salt
        key = os.urandom(32)
        salt = os.urandom(16)
        return key, salt

def encrypt_with_key(data: str, key: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:
    """
    Encrypt data using AES-GCM.
    
    Args:
        data: String to encrypt
        key: 32-byte encryption key
        nonce: Optional nonce (if not provided, a random one will be generated)
        
    Returns:
        Tuple of (encrypted_data, nonce) where:
        - encrypted_data: The encrypted data as bytes
        - nonce: The nonce used for encryption
    """
    # Create AESGCM instance
    aesgcm = AESGCM(key)
    
    # Generate a random nonce if not provided
    if nonce is None:
        nonce = os.urandom(12)  # AESGCM requires a 12-byte nonce
    
    # Encrypt the data
    encrypted_data = aesgcm.encrypt(nonce, data.encode(), None)
    
    return encrypted_data, nonce

def decrypt_with_key(encrypted_data: bytes, key: bytes, nonce: bytes) -> str:
    """
    Decrypt data using AES-GCM.
    
    Args:
        encrypted_data: The encrypted data as bytes
        key: 32-byte encryption key
        nonce: The nonce used for encryption
        
    Returns:
        The decrypted data as string
        
    Raises:
        ValueError: If the data cannot be decrypted or authenticated
    """
    # Create AESGCM instance
    aesgcm = AESGCM(key)
    
    try:
        # Decrypt the data
        decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")

def key_to_string(key: bytes, salt: bytes) -> str:
    """
    Convert a key and salt to a base64-encoded string for storage.
    
    Args:
        key: The encryption key
        salt: The salt used for key derivation
        
    Returns:
        Base64-encoded string containing both key and salt
    """
    combined = key + salt
    return base64.b64encode(combined).decode('utf-8')

def string_to_key(key_string: str) -> Tuple[bytes, bytes]:
    """
    Convert a base64-encoded string back to a key and salt.
    
    Args:
        key_string: Base64-encoded string containing key and salt
        
    Returns:
        Tuple of (key, salt)
    """
    combined = base64.b64decode(key_string)
    return combined[:32], combined[32:]

# Example usage
if __name__ == "__main__":
    # Generate a key from a passphrase
    key, salt = generate_key("my-secure-passphrase")
    
    # Encrypt some data
    data = "This is a secret message"
    encrypted_data, nonce = encrypt_with_key(data, key)
    
    # Decrypt the data
    decrypted_data = decrypt_with_key(encrypted_data, key, nonce)
    
    print(f"Original data: {data}")
    print(f"Decrypted data: {decrypted_data}")
    print(f"Data matches: {data == decrypted_data}") 