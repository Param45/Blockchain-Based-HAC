# aes_gcm.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
from typing import Tuple

def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = None) -> Tuple[bytes, bytes]:
    """
    Returns (nonce || ciphertext || tag, nonce) or more clearly (ciphertext_bundle, nonce)
    We'll return (nonce, ciphertext) separately for easier packaging.
    """
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 128/192/256 bits")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ct

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes = None) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)
