# crypto-engine/demo_hierarchy_decrypt.py
import json
from ecc_elgamal import ecc_decrypt, load_private_from_scalar_hex
from key_manager import load_entity_keys

def decrypt_edge(from_role, to_role):
    path = f"crypto-engine/edge_{from_role}_{to_role}.json"
    print(f"\n🔍 Decrypting edge {from_role} → {to_role}")

    with open(path, "r") as f:
        edge = json.load(f)

    enc_bytes = bytes.fromhex(edge["enc_pk_to_hex"])
    pkg = {
        "ephemeral_pub": enc_bytes[:65],
        "nonce": enc_bytes[65:77],
        "ciphertext": enc_bytes[77:],
    }

    recipient = load_entity_keys(to_role)
    priv_key = load_private_from_scalar_hex(recipient["priv_scalar_hex"])
    try:
        plaintext = ecc_decrypt(priv_key, pkg)
        print(f"✅ Decryption succeeded for {from_role}→{to_role}")
        print(f"   Recovered EK (hex): {plaintext.hex()}")
        return plaintext
    except Exception as e:
        print(f"❌ Decryption failed for {from_role}→{to_role}: {e}")
        return None

def hierarchical_decrypt(path_roles):
    print(f"\n🚀 Starting hierarchical decryption for path: {' → '.join(path_roles)}")
    current_key = None

    for i in range(len(path_roles) - 1):
        from_role = path_roles[i]
        to_role = path_roles[i + 1]
        ek = decrypt_edge(from_role, to_role)
        if ek is None:
            print(f"🛑 Stopping chain at {from_role} → {to_role}")
            return
        current_key = ek

    print("\n✅ Final decrypted EK for deepest node:", current_key.hex())

if __name__ == "__main__":
    hierarchical_decrypt(["Director", "Professor1", "Student3"])
