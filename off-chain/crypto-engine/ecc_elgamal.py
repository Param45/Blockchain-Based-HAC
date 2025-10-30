# ecc_elgamal.py
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import constant_time
from cryptography.hazmat.backends import default_backend
from typing import Tuple
import os
from aes_gcm import aes_gcm_encrypt, aes_gcm_decrypt

# We'll use SECP256R1 by default (changeable)
CURVE = ec.SECP256R1()

def generate_keypair() -> Tuple[ec.EllipticCurvePrivateKey, bytes]:
    priv = ec.generate_private_key(CURVE, default_backend())
    pub_bytes = pubkey_bytes_from_private(priv)
    return priv, pub_bytes

def pubkey_bytes_from_private(priv: ec.EllipticCurvePrivateKey) -> bytes:
    pub = priv.public_key()
    return pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

def load_private_from_scalar_hex(ski_hex: str) -> ec.EllipticCurvePrivateKey:
    """
    Create an EC private key object from a user-supplied scalar (hex string).
    Warning: This assumes the scalar is valid for the chosen curve.
    """
    d = int(ski_hex, 16)
    # construct private numbers
    return ec.derive_private_key(d, CURVE, default_backend())

def load_public_from_bytes(pub_bytes: bytes) -> ec.EllipticCurvePublicKey:
    return ec.EllipticCurvePublicKey.from_encoded_point(CURVE, pub_bytes)

def _derive_symmetric_from_shared(shared: bytes, info: bytes = b"ecies-encryption", length: int = 32) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
        backend=default_backend()
    )
    return hkdf.derive(shared)

def ecc_encrypt(recipient_pub_bytes: bytes, plaintext: bytes, associated_data: bytes = None) -> dict:
    """
    ECIES-like encryption:
    - generate ephemeral privKey e
    - compute shared = ecdh(e, recipient_pub)
    - derive symmetric key K = HKDF(shared)
    - ciphertext = AES-GCM(K, plaintext)
    Return a dict: { 'ephemeral_pub': bytes, 'nonce': bytes, 'ciphertext': bytes }
    """
    recipient_pub = load_public_from_bytes(recipient_pub_bytes)
    eph_priv = ec.generate_private_key(CURVE, default_backend())
    shared = eph_priv.exchange(ec.ECDH(), recipient_pub)  # bytes
    sym = _derive_symmetric_from_shared(shared)
    nonce, ct = aes_gcm_encrypt(sym, plaintext, associated_data)
    eph_pub_bytes = pubkey_bytes_from_private(eph_priv)
    return {"ephemeral_pub": eph_pub_bytes, "nonce": nonce, "ciphertext": ct}

def ecc_decrypt(recipient_priv: ec.EllipticCurvePrivateKey, package: dict, associated_data: bytes = None) -> bytes:
    """
    package contains ephemeral_pub, nonce, ciphertext
    """
    eph_pub = load_public_from_bytes(package["ephemeral_pub"])
    shared = recipient_priv.exchange(ec.ECDH(), eph_pub)
    sym = _derive_symmetric_from_shared(shared)
    return aes_gcm_decrypt(sym, package["nonce"], package["ciphertext"], associated_data)
