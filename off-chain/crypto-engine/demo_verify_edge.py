# crypto-engine/demo_verify_edge.py
import json
from ecc_elgamal import ecc_decrypt, load_private_from_scalar_hex
from key_manager import load_entity_keys
from pathlib import Path

def clean_hex_encoding(enc_hex: str) -> str:
    """
    Some encodings accidentally store ASCII for '0x04' -> '30783034...'
    This fixes it to the true binary form.
    """
    raw = bytes.fromhex(enc_hex)
    # Detect if string begins with ASCII '0x04'
    if raw.startswith(b"0x04"):
        # decode, then remove ASCII layer
        inner = raw.decode(errors="ignore")
        return inner.replace("0x", "").lstrip()
    return enc_hex

def main():
    print("🔍 Verifying a published edge (ECC decryption test)")

    # Change as needed
    recipient_role = "Student1"
    edge_file = Path("crypto-engine/edge_Professor1_Student1.json")

    if not edge_file.exists():
        raise FileNotFoundError(edge_file)

    recipient = load_entity_keys(recipient_role)
    priv_key = load_private_from_scalar_hex(recipient["priv_scalar_hex"])

    edge = json.loads(edge_file.read_text())
    enc_hex = clean_hex_encoding(edge["enc_pk_to_hex"]).replace("0x", "")
    eunder_hex = clean_hex_encoding(edge["e_under_hex"]).replace("0x", "")

    enc_bytes = bytes.fromhex(enc_hex)
    if len(enc_bytes) < 80:
        raise ValueError("Encoded edge payload too short; check file formatting.")

    pkg = {
        "ephemeral_pub": enc_bytes[:65],
        "nonce": enc_bytes[65:77],
        "ciphertext": enc_bytes[77:]
    }

    print(f"🧩 Parsed ECC package → eph_pub_len={len(pkg['ephemeral_pub'])}, nonce_len={len(pkg['nonce'])}, cipher_len={len(pkg['ciphertext'])}")
    print(f"🔹 eph_pub starts with: {pkg['ephemeral_pub'][:2].hex()}")

    try:
        plaintext = ecc_decrypt(priv_key, pkg)
        print("✅ ECC decryption succeeded!")
        print("Recovered plaintext (hex):", plaintext.hex())
    except Exception as e:
        print("❌ ECC decryption failed:", e)

if __name__ == "__main__":
    main()
