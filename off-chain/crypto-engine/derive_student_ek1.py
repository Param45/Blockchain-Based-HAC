# crypto-engine/derive_student_ek.py
"""
Stage 4D: Hierarchical EK Derivation + File Access
-------------------------------------------------
1. Derives symmetric keys along the chain: Director → Professor → Student
2. Decrypts the final student's EK
3. Uses that EK to decrypt the protected file encrypted by the Director
"""

import json, os
from ecc_elgamal import ecc_decrypt, load_private_from_scalar_hex
from key_manager import load_entity_keys
from aes_gcm import aes_gcm_decrypt, aes_gcm_encrypt


# ========== Utility ==========

def decrypt_edge(from_role, to_role, edge_file):
    """Decrypt EK for 'to_role' using private key of 'to_role'."""
    print(f"\n🔍 Decrypting edge {from_role} → {to_role}")

    # --- Load private key of recipient ---
    recipient_data = load_entity_keys(to_role)
    recipient_priv = load_private_from_scalar_hex(recipient_data["priv_scalar_hex"])

    # --- Load edge data ---
    with open(edge_file, "r") as f:
        edge = json.load(f)

    enc_bytes = bytes.fromhex(edge["enc_pk_to_hex"])
    eunder_bytes = bytes.fromhex(edge["e_under_hex"])

    pkg = {
        "ephemeral_pub": enc_bytes[:65],  # 04 + 32x + 32y
        "nonce": enc_bytes[65:77],
        "ciphertext": enc_bytes[77:]
    }

    try:
        ek_plain = ecc_decrypt(recipient_priv, pkg)
        print(f"✅ Decryption succeeded for {from_role}→{to_role}")
        print("   Recovered EK (hex):", ek_plain.hex())
        return ek_plain
    except Exception as e:
        print(f"❌ Decryption failed for {from_role}→{to_role}:", e)
        return None


def decrypt_protected_data(final_key):
    """Decrypt the protected report using the final derived EK."""
    print("\n🔐 Attempting to decrypt protected resource...")

    enc_path = "crypto-engine/protected/report.enc"
    if not os.path.exists(enc_path):
        print("⚠️ Encrypted report not found. Please run encrypt_protected.py first.")
        return

    try:
        with open(enc_path, "rb") as f:
            data = f.read()
        nonce, ciphertext = data[:12], data[12:]
        plaintext = aes_gcm_decrypt(final_key, nonce, ciphertext)
        print("✅ Access granted. Decrypted content:\n")
        print(plaintext.decode())
    except Exception as e:
        print("❌ Access denied:", e)


# ========== Main Hierarchical Flow ==========

def hierarchical_decrypt(chain):
    """
    chain = list of nodes from top (Director) to bottom (Student)
    Example: ["Director", "Professor1", "Student1"]
    """
    print(f"\n🚀 Starting hierarchical decryption for path: {' → '.join(chain)}")

    current_key = None

    for i in range(len(chain) - 1):
        from_role, to_role = chain[i], chain[i + 1]
        edge_file = f"crypto-engine/edge_{from_role}_{to_role}.json"

        if not os.path.exists(edge_file):
            print(f"❌ Missing edge file: {edge_file}")
            return None

        current_key = decrypt_edge(from_role, to_role, edge_file)
        if current_key is None:
            print(f"🛑 Stopping chain at {from_role} → {to_role}")
            return None

    print("\n✅ Final decrypted EK for deepest node:", current_key.hex())
    decrypt_protected_data(current_key)
    return current_key


if __name__ == "__main__":
    # Default chain (you can modify as needed)
    chain = ["Director", "Professor1", "Student1"]
    hierarchical_decrypt(chain)
