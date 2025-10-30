# hash_module.py
import hashlib

def sha256(data: bytes) -> bytes:
    """
    Return SHA-256 digest of data.
    """
    return hashlib.sha256(data).digest()

def sha256_hex(data: bytes) -> str:
    return sha256(data).hex()
