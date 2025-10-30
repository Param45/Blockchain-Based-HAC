# crypto-engine/generate_phase1.py
"""
Usage:
  python3 generate_phase1.py <SenderRole> <RecipientRole>

Example:
  python3 generate_phase1.py Professor1 Director
Produces: crypto-engine/edge_phase1_Professor1_Director.json
Fields:
  - enc_pk_to_hex : Enc(pk_recipient, ek_sender)  (ephemeral_pub || nonce || ciphertext)
  - e_under_hex   : AES_GCM(ek_sender, ek_sender) (nonce || ciphertext) [local symmetric copy]
"""

import sys
from ecc_elgamal import ecc_encrypt
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys
from utils import save_json, hex_bytes

def generate_phase1(sender, recipient):
    sender_data = load_entity_keys(sender)
    recipient_data = load_entity_keys(recipient)

    ek_sender = bytes.fromhex(sender_data["ek_hex"])
    recipient_pub = bytes.fromhex(recipient_data["pub_hex"])

    # Enc(pk_recipient, ek_sender) -> ECIES-like package
    ecc_pkg = ecc_encrypt(recipient_pub, ek_sender)
    # concatenated bytes (ephemeral_pub || nonce || ciphertext)
    enc_pk_to_bytes = ecc_pkg["ephemeral_pub"] + ecc_pkg["nonce"] + ecc_pkg["ciphertext"]
    enc_pk_to_hex = hex_bytes(enc_pk_to_bytes)

    # local symmetric copy: AES-GCM(ek_sender, ek_sender)
    nonce, ciphertext = aes_gcm_encrypt(ek_sender, ek_sender)
    e_under_hex = hex_bytes(nonce + ciphertext)

    payload = {
        "from": sender,
        "to": recipient,
        "enc_pk_to_hex": enc_pk_to_hex,
        "e_under_hex": e_under_hex
    }

    out_path = f"crypto-engine/edge_phase1_{sender}_{recipient}.json"
    save_json(payload, out_path)
    print(f"✅ Phase-1 edge file saved to: {out_path}")
    print(payload)
    return out_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_phase1.py <SenderRole> <RecipientRole>")
        sys.exit(1)
    generate_phase1(sys.argv[1], sys.argv[2])
