# crypto-engine/demo_generate_edge.py
import json
from ecc_elgamal import ecc_encrypt
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys
from pathlib import Path

def generate_edge_payload(sender_id, recipient_id):
    sender = load_entity_keys(sender_id)
    recipient = load_entity_keys(recipient_id)

    ek_sender = bytes.fromhex(sender["ek_hex"])

    # --- ECC encrypt sender's ek under recipient's pubkey ---
    ecc_pkg = ecc_encrypt(bytes.fromhex(recipient["pub_hex"]), ek_sender)

    # Confirm proper binary 0x04 prefix
    eph_pub = ecc_pkg["ephemeral_pub"]
    if eph_pub[0] != 0x04:
        raise ValueError("Ephemeral pubkey not in uncompressed form (should start with 0x04)")

    # Combine all parts to form enc_pk_to
    enc_pk_to_hex = (
        eph_pub.hex() +
        ecc_pkg["nonce"].hex() +
        ecc_pkg["ciphertext"].hex()
    )

    # --- Encrypt ek_sender under itself (AES-GCM) ---
    nonce, ciphertext = aes_gcm_encrypt(ek_sender, ek_sender)
    e_under_hex = nonce.hex() + ciphertext.hex()

    payload = {
        "from": sender_id,
        "to": recipient_id,
        "enc_pk_to_hex": enc_pk_to_hex,
        "e_under_hex": e_under_hex
    }

    # Save to specific JSON file
    out_file = Path(f"crypto-engine/edge_{sender_id}_{recipient_id}.json")
    out_file.write_text(json.dumps(payload, indent=2))
    print(f"✅ Saved edge file: {out_file}")
    print(json.dumps(payload, indent=2))
    return payload

if __name__ == "__main__":
    generate_edge_payload("Professor2", "Student3")
