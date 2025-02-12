import hashlib

def hash_password(password):
    """Hash the password using SHA-256 (unsalted)."""
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()
    
    # Update the hash object with the password (encoded as UTF-8)
    sha256_hash.update(password.encode("utf-8"))
    
    # Get the hexadecimal representation of the hash
    hashed_password = sha256_hash.hexdigest()
    
    return hashed_password

# def verify_password(plain_password, hashed_password):
#     """Verify the plain password against the hashed one."""
#     # Hash the plain password and compare it to the stored hash
#     return hash_password(plain_password) == hashed_password