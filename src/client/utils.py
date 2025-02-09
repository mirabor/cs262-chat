import bcrypt

def hash_password(password):
    """Hash the password using bcrypt and return as a UTF-8 string."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")  # Convert bytes to string for JSON storage

def verify_password(plain_password, hashed_password):
    """Verify the plain password against the hashed one."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))