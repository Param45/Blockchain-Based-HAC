# crypto-engine/student_encrypt_file.py
"""
Student-side file encryption
----------------------------
Encrypts a file using Student1's own EK (from keys/Student1.json)
and saves ciphertext to crypto-engine/protected/student1_data.enc
"""

import os
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys

def student_encrypt():
    os.makedirs("crypto-engine/protected", exist_ok=True)

    # Load Student1’s EK
    student = load_entity_keys("Student1")
    ek = bytes.fromhex(student["ek_hex"])

    # Prepare a sample file
    input_path = "crypto-engine/protected/student1_data.txt"
    with open(input_path, "w") as f:
        f.write("This is Student1’s confidential research submission to the Director.")

    # Encrypt file
    with open(input_path, "rb") as f:
        plaintext = f.read()

    nonce, ciphertext = aes_gcm_encrypt(ek, plaintext)
    output_path = "crypto-engine/protected/student1_data.enc"
    with open(output_path, "wb") as f:
        f.write(nonce + ciphertext)

    print(f"✅ Student1 encrypted file using their EK.")
    print(f"   Encrypted file saved at: {output_path}")
    print(f"   Nonce: {nonce.hex()}")
    print(f"   Ciphertext length: {len(ciphertext)} bytes")

if __name__ == "__main__":
    student_encrypt()
