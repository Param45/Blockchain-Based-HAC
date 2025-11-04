import json
import sys
from pathlib import Path
from collections import deque
from key_manager import load_entity_keys
from aes_gcm import aes_gcm_decrypt
from cryptography.exceptions import InvalidTag

CRYPTO_DIR = Path("crypto-engine")

def load_edge(path):
    return json.loads(Path(path).read_text())

def is_ascii_hex_bytes(b: bytes) -> bool:
    if not b:
        return False
    try:
        s = b.decode('ascii')
    except Exception:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in s)

def decrypt_e_under(e_under_hex, key_bytes):
    h = e_under_hex.lower().removeprefix("0x")
    b = bytes.fromhex(h)
    if len(b) < 29:
        raise ValueError(f"e_under too short ({len(b)} bytes)")

    nonce, ciphertext = b[:12], b[12:]
    try:
        return aes_gcm_decrypt(key_bytes, nonce, ciphertext)
    except InvalidTag:
        if is_ascii_hex_bytes(key_bytes):
            try:
                decoded_key = bytes.fromhex(key_bytes.decode('ascii'))
                return aes_gcm_decrypt(decoded_key, nonce, ciphertext)
            except Exception:
                pass
    raise InvalidTag("AES-GCM tag verification failed.")

def build_graph():
    """Builds mapping of parent->child relationships from edge JSON filenames."""
    files = list(CRYPTO_DIR.glob("edge_phase2_*.json"))
    graph = {}
    edge_files = {}

    # Load simple entity_keys.json (name -> address)
    ek_data = json.loads(Path(CRYPTO_DIR / "entity_keys.json").read_text())
    name_to_addr = {k: v.lower() for k, v in ek_data.items()}
    addr_to_name = {v: k for k, v in name_to_addr.items()}

    for f in files:
        parts = f.stem.split("_")
        if len(parts) < 4:
            continue
        parent_addr = parts[-2].lower()
        child_addr = parts[-1].lower()
        parent = addr_to_name.get(parent_addr)
        child = addr_to_name.get(child_addr)
        if parent and child:
            graph.setdefault(parent, []).append(child)
            edge_files[(parent, child)] = str(f)
    return graph, edge_files

def find_path(graph, start, target):
    """BFS to find shortest path between start and target in graph."""
    q = deque([[start]])
    visited = set()
    while q:
        path = q.popleft()
        node = path[-1]
        if node == target:
            return path
        if node in visited:
            continue
        visited.add(node)
        for neigh in graph.get(node, []):
            q.append(path + [neigh])
    return None

def derive_along_path(path_roles, edge_files):
    root = path_roles[0]
    root_data = load_entity_keys(root)
    ek_current = bytes.fromhex(root_data["ek_hex"])
    print(f"[start] root='{root}', ek_root={ek_current.hex()}")

    for i in range(len(path_roles) - 1):
        parent, child = path_roles[i], path_roles[i + 1]
        edge_file = edge_files.get((parent, child))
        if not edge_file:
            raise FileNotFoundError(f"No edge file for {parent}->{child}")

        edge = load_edge(edge_file)
        e_under_hex = edge.get("e_under_hex") or edge.get("e_under")
        print(f"[step] Decrypting {parent}->{child} using ek_{parent} from {edge_file}")
        ek_child = decrypt_e_under(e_under_hex, ek_current)

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
    if len(sys.argv) != 2:
        print("Usage: python3 derive_student_ek_auto.py <Root,Target>")
        sys.exit(1)

    root, target = [x.strip() for x in sys.argv[1].split(",")]
    graph, edge_files = build_graph()

    print(f"🔍 Building graph with {len(edge_files)} edges...")
    path = find_path(graph, root, target)
    if not path:
        print(f"❌ No path found between {root} and {target}")
        sys.exit(1)

    print(f"🧭 Found path: {' -> '.join(path)}")
    final = derive_along_path(path, edge_files)

    # Save final derived EK to binary file
    output_path = CRYPTO_DIR / f"derived_ek_{target}.bin"
    with open(output_path, "wb") as f:
        f.write(final)
    print(f"\n✅ Final decrypted EK for deepest node: {final.hex()}")
    print(f"💾 Saved derived key to: {output_path}")
