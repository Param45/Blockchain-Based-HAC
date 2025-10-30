# crypto-engine/encrypt_protected.py
import os
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys

def encrypt_file(input_path, output_path):
    director = load_entity_keys("Director")
    ek = bytes.fromhex(director["ek_hex"])

    with open(input_path, "rb") as f:
        plaintext = f.read()

    nonce, ciphertext = aes_gcm_encrypt(ek, plaintext)

    with open(output_path, "wb") as f:
        f.write(nonce + ciphertext)

    print(f"✅ File encrypted with Director's EK and saved as {output_path}")

if __name__ == "__main__":
    os.makedirs("crypto-engine/protected", exist_ok=True)
    # Create a test file
    with open("crypto-engine/protected/report.txt", "w") as f:
        f.write("Confidential performance report for authorized users only.")

    encrypt_file("crypto-engine/protected/report.txt", "crypto-engine/protected/report.enc")
