# crypto-engine/decrypt_file_hierarchy.py
"""
Director decrypts a student's file via hierarchical EK derivation.
"""

import os, json
from ecc_elgamal import ecc_decrypt, load_private_from_scalar_hex
from key_manager import load_entity_keys
from aes_gcm import aes_gcm_decrypt

def decrypt_edge(from_role, to_role, edge_file):
    """Decrypt EK for 'to_role' using private key of 'to_role'."""
    print(f"\n🔍 Decrypting edge {from_role} → {to_role}")

    recipient_data = load_entity_keys(to_role)
    recipient_priv = load_private_from_scalar_hex(recipient_data["priv_scalar_hex"])

    with open(edge_file, "r") as f:
        edge = json.load(f)

    enc_bytes = bytes.fromhex(edge["enc_pk_to_hex"])
    pkg = {
        "ephemeral_pub": enc_bytes[:65],
        "nonce": enc_bytes[65:77],
        "ciphertext": enc_bytes[77:]
    }

    ek_plain = ecc_decrypt(recipient_priv, pkg)
    print(f"✅ Decryption succeeded for {from_role}→{to_role}")
    print("   Recovered EK:", ek_plain.hex())
    return ek_plain


def hierarchical_derive(chain):
    """Derive EK for the deepest node following the hierarchy chain."""
    print(f"\n🚀 Starting hierarchical EK derivation for path: {' → '.join(chain)}")

    current_key = None
    for i in range(len(chain) - 1):
        from_role, to_role = chain[i], chain[i + 1]
        edge_file = f"crypto-engine/edge_{from_role}_{to_role}.json"
        current_key = decrypt_edge(from_role, to_role, edge_file)

    print(f"\n✅ Final derived EK for {chain[-1]} = {current_key.hex()}")
    return current_key


def decrypt_student_file(final_key, student_id):
    """Decrypt the file encrypted by the student using their EK."""
    enc_path = f"crypto-engine/protected/{student_id.lower()}_report.enc"
    if not os.path.exists(enc_path):
        print(f"⚠️ Encrypted file for {student_id} not found.")
        return

    with open(enc_path, "rb") as f:
        data = f.read()

    nonce, ciphertext = data[:12], data[12:]
    plaintext = aes_gcm_decrypt(final_key, nonce, ciphertext)

    print(f"\n📖 Decrypted content from {student_id}'s file:")
    print("-----------------------------------------")
    print(plaintext.decode())
    print("-----------------------------------------")


if __name__ == "__main__":
    chain = ["Director", "Professor1", "Student1"]  # adjust as needed
    final_ek = hierarchical_derive(chain)
    decrypt_student_file(final_ek, "Student1")
