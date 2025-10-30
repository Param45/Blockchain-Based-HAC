# crypto-engine/derive_student_ek.py
import json
import sys
from pathlib import Path
from key_manager import load_entity_keys
from aes_gcm import aes_gcm_decrypt
from cryptography.exceptions import InvalidTag

def load_edge(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Edge file not found: {path}")
    return json.loads(p.read_text())

def is_ascii_hex_bytes(b: bytes) -> bool:
    """Return True if b is an ASCII hex string (only 0-9a-fA-F characters)."""
    if not b:
        return False
    try:
        s = b.decode('ascii')
    except Exception:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in s)

def decrypt_e_under(e_under_hex, key_bytes):
    """Decrypt nonce||ciphertext||tag using AES-GCM and key."""
    h = e_under_hex.lower().removeprefix("0x")
    b = bytes.fromhex(h)
    if len(b) < 29:
        raise ValueError(f"e_under too short ({len(b)} bytes) in value: {e_under_hex[:80]}...")
    nonce, ciphertext = b[:12], b[12:]

    # try direct
    try:
        return aes_gcm_decrypt(key_bytes, nonce, ciphertext)
    except InvalidTag:
        if is_ascii_hex_bytes(key_bytes):
            try:
                decoded_key = bytes.fromhex(key_bytes.decode('ascii'))
                return aes_gcm_decrypt(decoded_key, nonce, ciphertext)
            except Exception:
                pass
    raise InvalidTag("AES-GCM tag verification failed (InvalidTag).")

def derive_along_path(path_roles, edge_paths):
    """
    path_roles: ["Director", "Professor2", "Student3"]
    edge_paths: dict mapping (parent,child) -> JSON path.
    """
    if not path_roles or len(path_roles) < 2:
        raise ValueError("Need at least two roles.")

    root = path_roles[0]
    root_data = load_entity_keys(root)
    ek_current = bytes.fromhex(root_data["ek_hex"])
    print(f"[start] root='{root}', ek_root={ek_current.hex()}")

    for i in range(len(path_roles) - 1):
        parent, child = path_roles[i], path_roles[i + 1]
        edge_file = edge_paths.get((parent, child))
        if not edge_file or not Path(edge_file).exists():
            raise FileNotFoundError(f"Missing edge file for {parent}->{child}: {edge_file}")

        edge = load_edge(edge_file)
        e_under_hex = edge.get("e_under_hex") or edge.get("e_under")
        if not e_under_hex:
            raise ValueError(f"No e_under field in {edge_file}")

        print(f"[step] Decrypting {parent}->{child} using ek_{parent} from {edge_file}")
        ek_child = decrypt_e_under(e_under_hex, ek_current)

        # Convert ASCII-hex plaintexts to raw bytes (only if looks like hex text)
        if is_ascii_hex_bytes(ek_child) and len(ek_child) in (64, 96, 128):
            try:
                ek_child = bytes.fromhex(ek_child.decode('ascii'))
                print(f"[info] Converted ek_{child} from ASCII-hex to raw bytes.")
            except Exception:
                pass

        print(f"🔓 Decrypted {parent}->{child}: ek_{child} = {ek_child.hex()}")
        ek_current = ek_child

    return ek_current

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 derive_student_ek.py <CommaSeparatedPathRoles>")
        sys.exit(1)
    roles = [r.strip() for r in sys.argv[1].split(",") if r.strip()]

    # 🔧 You must provide the mapping manually here
    edge_paths = {
        ("Director", "Professor2"):
            "crypto-engine/edge_phase2_0x4BdbbFD674ee2ed57db4D058Ed5cA04B858EF461_0x08F20e403B2813A326221781D4420242a5DB452b.json",
        ("Professor2", "Student2"):
            "crypto-engine/edge_phase2_0x08F20e403B2813A326221781D4420242a5DB452b_0x733123064C38bfB70F939f4763e359E0d512b9bA.json",
    }

    final = derive_along_path(roles, edge_paths)
    print("\n✅ Final decrypted EK for deepest node:", final.hex())
