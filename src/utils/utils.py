import bcrypt

def hash_password(password):
    """Hash a password for secure storage."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed

def verify_password(plain_password, hashed_password):
    """Verify a plain password against the hashed one."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)