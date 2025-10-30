# crypto-engine/verify_phase1_and_prepare_phase2.py
"""
Usage:
  # Option A: verify using local phase1 file saved earlier
  python3 verify_phase1_and_prepare_phase2.py --file crypto-engine/edge_phase1_Professor1_Director.json

  # Option B: verify using on-chain saved edge (fetchLatestEdge.js -> crypto-engine/edge_data.json)
  python3 verify_phase1_and_prepare_phase2.py --onchain

Produces:
  crypto-engine/edge_phase2_<Parent>_<Child>.json
Fields:
  - enc_pk_to_hex: Enc(pk_child, ek_parent)  (the parent encrypted to child; keeps contract fields consistent)
  - e_under_hex: AES_GCM(ek_parent, ek_child)  (parent's symmetric encryption of child's ek)
"""

import argparse
from pathlib import Path
from ecc_elgamal import ecc_decrypt, ecc_encrypt
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys
from utils import load_json, save_json, hex_bytes

def read_phase1_from_file(path):
    return load_json(path)

def read_phase1_from_edge_data():
    p = Path("crypto-engine/edge_data.json")
    if not p.exists():
        raise FileNotFoundError("crypto-engine/edge_data.json not found. Run fetchLatestEdge.js first.")
    return load_json(p)

def clean_hex(h):
    # remove optional 0x
    return h[2:] if h.startswith("0x") else h

def decrypt_enc_pk_to(recipient_priv, enc_pk_to_hex):
    enc_bytes = bytes.fromhex(clean_hex(enc_pk_to_hex))
    pkg = {
        "ephemeral_pub": enc_bytes[:65],
        "nonce": enc_bytes[65:77],
        "ciphertext": enc_bytes[77:]
    }
    plaintext = ecc_decrypt(recipient_priv, pkg)
    return plaintext

def prepare_phase2(parent_role, child_role, ek_child_bytes):
    """
    parent_role: e.g., 'Director'
    child_role: e.g., 'Professor1'
    ek_child_bytes: recovered child's ek (bytes)
    """
    parent_data = load_entity_keys(parent_role)
    child_data = load_entity_keys(child_role)

    ek_parent = bytes.fromhex(parent_data["ek_hex"])
    pk_child = bytes.fromhex(child_data["pub_hex"])
    pk_parent = bytes.fromhex(parent_data["pub_hex"])

    # e_under_phase2 = AES_GCM(ek_parent, ek_child)
    nonce2, ciphertext2 = aes_gcm_encrypt(ek_parent, ek_child_bytes)
    e_under_phase2_hex = hex_bytes(nonce2 + ciphertext2)

    # enc_pk_to_for_phase2 = Enc(pk_child, ek_parent)   (so child can decrypt/verify optionally)
    ecc_pkg2 = ecc_encrypt(pk_child, ek_parent)
    enc_pk_to_phase2_hex = hex_bytes(ecc_pkg2["ephemeral_pub"] + ecc_pkg2["nonce"] + ecc_pkg2["ciphertext"])

    payload = {
        "from": parent_role,
        "to": child_role,
        "enc_pk_to_hex": enc_pk_to_phase2_hex,
        "e_under_hex": e_under_phase2_hex
    }
    out_path = f"crypto-engine/edge_phase2_{parent_role}_{child_role}.json"
    save_json(payload, out_path)
    print(f"✅ Phase-2 payload saved to: {out_path}")
    print(payload)
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to local phase1 JSON file")
    parser.add_argument("--onchain", action="store_true", help="Read phase1 from crypto-engine/edge_data.json (fetchLatestEdge.js output)")
    args = parser.parse_args()

    if not (args.file or args.onchain):
        print("Specify --file <path> or --onchain")
        return

    if args.file:
        p = Path(args.file)
        if not p.exists():
            raise FileNotFoundError(p)
        phase1 = read_phase1_from_file(str(p))
    else:
        phase1 = read_phase1_from_edge_data()

    child_role = phase1["from"]    # the lower node who originally published
    parent_role = phase1["to"]     # the higher node (this script runs as parent)
    print(f"🔍 Preparing Phase-2 as parent='{parent_role}' for child='{child_role}'")

    # load parent's private key object
    parent_data = load_entity_keys(parent_role)
    # parent_data["priv_scalar_hex"] -> convert to private key object using your helper
    from ecc_elgamal import load_private_from_scalar_hex
    parent_priv = load_private_from_scalar_hex(parent_data["priv_scalar_hex"])

    # Decrypt the enc_pk_to (child->parent) to recover ek_child
    ek_child = decrypt_enc_pk_to(parent_priv, phase1["enc_pk_to_hex"])
    print(f"✅ Recovered ek_child (hex): {ek_child.hex()}")

    # Optional sanity check: compare with child's local ek (if you have it)
    child_local = load_entity_keys(child_role)
    if child_local.get("ek_hex", "").lower() == ek_child.hex().lower():
        print("🟩 Recovered ek matches child's stored ek_hex (good).")
    else:
        print("⚠️ Recovered ek does NOT match child's stored ek_hex (maybe different derivation).")

    # Prepare Phase-2 payload to be published by parent
    out = prepare_phase2(parent_role, child_role, ek_child)
    print(f"📢 To publish Phase-2 (parent->child) run:")
    print(f"node agent/transactions/publishEdge.js {parent_role} <{child_role}_ADDRESS> \"<enc_pk_to_hex_from_{out}>\" \"<e_under_hex_from_{out}>\" 1")

if __name__ == "__main__":
    main()
