# test_crypto_verification.py
"""
Tests for verifying correctness of AES-GCM, ECC ElGamal, and hierarchical EdgeAdd encryption/decryption.
Run with:
    python3 test_crypto_verification.py
"""

from aes_gcm import aes_gcm_encrypt, aes_gcm_decrypt
from ecc_elgamal import generate_keypair, ecc_encrypt, ecc_decrypt
from edge_ops import make_edge_add_payload, decode_edge_add_payload_for_target
from cryptography.hazmat.primitives.asymmetric import ec
import os, binascii

def test_aes_gcm():
    print("=== AES-GCM TEST ===")
    key = os.urandom(32)
    plaintext = b"This is a test message for AES-GCM encryption"
    nonce, ciphertext = aes_gcm_encrypt(key, plaintext)
    recovered = aes_gcm_decrypt(key, nonce, ciphertext)
    assert recovered == plaintext, "AES-GCM decryption failed!"
    print("AES-GCM encryption/decryption successful.")
    print(f"Key: {key.hex()}")
    print(f"Nonce: {nonce.hex()}")
    print(f"Ciphertext: {ciphertext.hex()}\n")


def test_ecc_elgamal():
    print("=== ECC ELGAMAL (ECIES) TEST ===")
    priv_recipient, pub_recipient = generate_keypair()
    message = os.urandom(32)  # 256-bit message, e.g., a symmetric key
    print(f"Original message: {message.hex()}")

    package = ecc_encrypt(pub_recipient, message)
    print("Encrypted package:")
    print({
        "ephemeral_pub": package["ephemeral_pub"].hex(),
        "nonce": package["nonce"].hex(),
        "ciphertext": package["ciphertext"].hex()
    })

    recovered = ecc_decrypt(priv_recipient, package)
    assert recovered == message, "ECC decryption failed!"
    print("ECC encryption/decryption successful.\n")


def test_edge_add_flow():
    print("=== EDGEADD FLOW TEST (HIERARCHICAL) ===")
    # Simulate two entities: A (parent) and B (child)
    from key_manager import keygen_from_user_ski
    parent_priv, parent_pub, parent_ek = keygen_from_user_ski("parent")
    child_priv, child_pub, child_ek = keygen_from_user_ski("child")

    # Parent -> Child payload
    payload = make_edge_add_payload("parent", child_pub, parent_ek, child_ek)
    print("Generated EdgeAdd payload:")
    print(payload)

    # Child decrypts
    ek_from_parent, ek_to_child = decode_edge_add_payload_for_target(child_priv, payload)
    assert ek_from_parent == parent_ek, "Parent ek mismatch!"
    assert ek_to_child == child_ek, "Child ek mismatch!"
    print("EdgeAdd encryption/decryption successful.")
    print(f"Recovered parent_ek: {binascii.hexlify(ek_from_parent).decode()}")
    print(f"Recovered child_ek: {binascii.hexlify(ek_to_child).decode()}\n")


if __name__ == "__main__":
    print("Running cryptographic verification tests...\n")
    test_aes_gcm()
    test_ecc_elgamal()
    test_edge_add_flow()
    print("✅ All crypto tests passed successfully.")
