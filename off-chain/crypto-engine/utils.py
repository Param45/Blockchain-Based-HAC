# crypto-engine/utils.py
import json
from pathlib import Path

def save_json(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2))

def load_json(path):
    return json.loads(Path(path).read_text())

def hex_bytes(b: bytes) -> str:
    return b.hex()
