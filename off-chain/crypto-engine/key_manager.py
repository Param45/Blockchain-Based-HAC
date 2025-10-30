# key_manager.py
import os, json
from typing import Tuple
from hash_module import sha256
from ecc_elgamal import generate_keypair, pubkey_bytes_from_private, load_private_from_scalar_hex
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# === CONFIG ===
KEYSTORE_DIR = "keys"

# Optional: map role → Ethereum address for convenience
ROLE_TO_ADDR = {
    "Director": "0x4BdbbFD674ee2ed57db4D058Ed5cA04B858EF461",
    "Professor1": "0x8E6410E5c1c433D9C545025d7bD21F780605C81f",
    "Professor2": "0x08F20e403B2813A326221781D4420242a5DB452b",
    "Student1": "0x6681D6eB6128F6Ef8E0792Ca53271F7a5c84873B",
    "Student2": "0x733123064C38bfB70F939f4763e359E0d512b9bA",
    "Student3": "0xCf9d739f438C36bD6E769595cDF4794dc84996C3"
}

# === CORE HELPERS ===

def ensure_keystore_dir():
    os.makedirs(KEYSTORE_DIR, exist_ok=True)

def resolve_entity_filename(entity_id: str) -> str:
    """
    Determine which keystore file to load:
    - If entity_id is a role name, use ROLE_TO_ADDR mapping.
    - If entity_id is already an Ethereum address (starts with 0x), use directly.
    """
    if not entity_id.startswith("0x"):
        # convert role name to its Ethereum address
        addr = ROLE_TO_ADDR.get(entity_id)
        if not addr:
            raise FileNotFoundError(f"No address mapping found for entity '{entity_id}' in ROLE_TO_ADDR")
        filename = f"{addr}.json"
    else:
        filename = f"{entity_id}.json"

    return os.path.join(KEYSTORE_DIR, filename)

def save_entity_keys(entity_id: str, priv_obj, pub_bytes: bytes, ek: bytes):
    ensure_keystore_dir()
    path = resolve_entity_filename(entity_id)
    priv_num = priv_obj.private_numbers().private_value
    data = {
        "entity_id": entity_id,
        "priv_scalar_hex": format(priv_num, "x"),
        "pub_hex": pub_bytes.hex(),
        "ek_hex": ek.hex()
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved keys for {entity_id} → {path}")

def load_entity_keys(entity_id: str):
    path = resolve_entity_filename(entity_id)
    with open(path, "r") as f:
        data = json.load(f)
    return data

def derive_ek_from_ski(ski_hex: str, entity_id: str, length: int = 32) -> bytes:
    d = int(ski_hex, 16)
    raw = d.to_bytes((d.bit_length() + 7) // 8, byteorder="big")
    info = entity_id.encode() + b":ek"
    hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info)
    return hkdf.derive(raw)

def keygen_from_user_ski(entity_id: str, ski_hex: str = None) -> Tuple:
    if ski_hex:
        priv = load_private_from_scalar_hex(ski_hex)
        pub_bytes = pubkey_bytes_from_private(priv)
        ek = derive_ek_from_ski(ski_hex, entity_id)
    else:
        priv, pub_bytes = generate_keypair()
        ek = os.urandom(32)
    return priv, pub_bytes, ek

def export_pub_hex(pub_bytes: bytes) -> str:
    return pub_bytes.hex()


if __name__ == "__main__":
    import argparse, sys
    parser = argparse.ArgumentParser(description="Return public key hex for an entity")
    parser.add_argument("--entity", required=True, help="Entity ID (role name or Ethereum address)")
    parser.add_argument("--ski", help="Optional SKI hex to deterministically derive key")
    args = parser.parse_args()

    try:
        priv, pub_bytes, ek = keygen_from_user_ski(args.entity, args.ski)
        save_entity_keys(args.entity, priv, pub_bytes, ek)
        print(pub_bytes.hex())
    except Exception as e:
        print(f"❌ error: {e}", file=sys.stderr)
        sys.exit(1)
