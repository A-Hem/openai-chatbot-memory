"""
Debug script for hashing module
"""

import base64
from security.hashing import (
    generate_salt,
    compute_hash,
    verify_hash,
    hash_to_string,
    string_to_hash
)

def main():
    """Test the hashing module directly"""
    print("Debugging hashing module...")
    
    # Test with password
    password = "test-password"
    print(f"Test password: {password}")
    
    # Generate hash
    hash_bytes, salt = compute_hash(password)
    print(f"Generated hash bytes: {hash_bytes[:20]}...")
    print(f"Generated salt: {salt.hex()}")
    
    # Create hash string
    hash_str = hash_to_string(hash_bytes, salt)
    print(f"Hash string: {hash_str}")
    
    # Verify with correct password
    result = verify_hash(password, hash_str)
    print(f"Verify correct password: {result}")
    
    # Verify with wrong password
    wrong_result = verify_hash("wrong-password", hash_str)
    print(f"Verify wrong password: {wrong_result}")
    
    # Try extracting the hash and salt
    try:
        extracted_hash, extracted_salt = string_to_hash(hash_str)
        print(f"Extracted hash bytes: {extracted_hash[:20]}...")
        print(f"Extracted salt: {extracted_salt.hex()}")
        print(f"Salt matches: {salt == extracted_salt}")
    except Exception as e:
        print(f"Error extracting hash: {e}")
    
    # Try direct argon2 verification
    if hash_bytes.startswith(b'$argon2'):
        print("Hash appears to be in argon2 format")
        try:
            from passlib.hash import argon2
            argon2_verify = argon2.verify(password, hash_bytes.decode())
            print(f"Direct argon2 verification: {argon2_verify}")
        except Exception as e:
            print(f"Error with direct argon2 verification: {e}")
    else:
        print("Hash is not in argon2 format")
    
    # Test verify_hash with None
    try:
        verify_hash(password, None)
        print("verify_hash with None did not raise an exception!")
    except ValueError as e:
        print(f"Good: verify_hash with None raised ValueError: {e}")
    except Exception as e:
        print(f"Unexpected exception: {e}")
    
    # Test from test case
    test_password = "test-password"
    test_hash_bytes, test_salt = compute_hash(test_password)
    test_hash_str = hash_to_string(test_hash_bytes, test_salt)
    
    print(f"\nTest case hash string: {test_hash_str}")
    verify_result = verify_hash(test_password, test_hash_str)
    print(f"Test case verification: {verify_result}")

if __name__ == "__main__":
    main() 