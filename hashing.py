from passlib.context import CryptContext

# Argon2 does not have the 72-byte limit
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against an Argon2 hash.
    """
    return pwd_context.verify(plain_password, hashed_password)