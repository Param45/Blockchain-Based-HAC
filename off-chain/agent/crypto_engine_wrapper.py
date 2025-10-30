#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

# Add the crypto-engine directory to the import path
CURRENT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = CURRENT_DIR.parent / "crypto-engine"
sys.path.insert(0, str(ENGINE_DIR))

# Import your crypto-engine modules
from key_manager import generate_ecc_keypair, load_public_key, load_private_key
from aes_gcm import aes_encrypt, aes_decrypt
from ecc_elgamal import ecc_encrypt, ecc_decrypt
from edge_ops import create_edge_payload, recover_edge_keys

def print_usage():
    print("""
Usage:
  python3 crypto_engine_wrapper.py <command> [args...]

Commands:
  genkeys <role>                      Generate ECC keypair for given role
  catpub <path_to_pubkey>             Output public key as hex string (no 0x)
  makepayload <from_priv> <to_pub>    Create encrypted edge payload
  decodepayload <to_priv> <payload_json>  Decrypt edge payload JSON and recover keys
""")

# Utility: convert bytes → hex (no 0x prefix)
def to_hex(b: bytes) -> str:
    return b.hex()

# Utility: convert hex → bytes (handles 0x prefix if present)
def from_hex(h: str) -> bytes:
    h = h.strip()
    return bytes.fromhex(h[2:] if h.startswith("0x") else h)

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    # 1️⃣ Generate ECC keypair
    if cmd == "genkeys":
        if len(sys.argv) < 3:
            print("Usage: genkeys <role>")
            sys.exit(1)
        role = sys.argv[2]
        priv_path = ENGINE_DIR / f"keys/{role}_priv.pem"
        pub_path = ENGINE_DIR / f"keys/{role}_pub.pem"
        os.makedirs(priv_path.parent, exist_ok=True)
        generate_ecc_keypair(priv_path, pub_path)
        print(f"✅ Keys generated for {role}")
        print(f"Private: {priv_path}")
        print(f"Public:  {pub_path}")

    # 2️⃣ Output public key as hex string (no 0x)
    elif cmd == "catpub":
        if len(sys.argv) < 3:
            print("Usage: catpub <path_to_pubkey>")
            sys.exit(1)
        pubkey_path = Path(sys.argv[2])
        pubkey = load_public_key(pubkey_path)
        pub_bytes = pubkey.public_bytes(encoding='X962', format='UncompressedPoint')
        print(to_hex(pub_bytes))  # no 0x prefix

    # 3️⃣ Create encrypted edge payload (Director → Professor, etc.)
    elif cmd == "makepayload":
        if len(sys.argv) < 4:
            print("Usage: makepayload <from_priv> <to_pub>")
            sys.exit(1)
        from_priv_path = Path(sys.argv[2])
        to_pub_path = Path(sys.argv[3])
        payload = create_edge_payload(from_priv_path, to_pub_path)
        print(json.dumps(payload, indent=2))

    # 4️⃣ Decode payload (Professor or Student receives it)
    elif cmd == "decodepayload":
        if len(sys.argv) < 4:
            print("Usage: decodepayload <to_priv> <payload_json>")
            sys.exit(1)
        to_priv_path = Path(sys.argv[2])
        payload_json_path = Path(sys.argv[3])
        payload = json.loads(open(payload_json_path).read())
        recovered = recover_edge_keys(to_priv_path, payload)
        print(json.dumps(recovered, indent=2))

    else:
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()
