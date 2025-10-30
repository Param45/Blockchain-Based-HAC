# crypto-engine/director_decrypt_file.py
"""
Director-side decryption
------------------------
Uses the derived Student1 EK to decrypt the file encrypted by Student1.
"""

import os
from aes_gcm import aes_gcm_decrypt

def director_decrypt():
    derived_ek_path = "crypto-engine/derived_student1_ek.hex"
    enc_path = "crypto-engine/protected/student1_data.enc"

    if not os.path.exists(derived_ek_path):
        print("❌ Derived Student1 EK not found. Run derive_student_ek.py first.")
        return
    if not os.path.exists(enc_path):
        print("❌ Encrypted file not found. Run student_encrypt_file.py first.")
        return

    with open(derived_ek_path, "r") as f:
        ek_hex = f.read().strip()
    ek = bytes.fromhex(ek_hex)

    with open(enc_path, "rb") as f:
        data = f.read()
    nonce, ciphertext = data[:12], data[12:]

    try:
        plaintext = aes_gcm_decrypt(ek, nonce, ciphertext)
        print("✅ Director successfully decrypted Student1's file.")
        print("\n📄 File content:")
        print(plaintext.decode())
    except Exception as e:
        print("❌ Decryption failed:", e)

if __name__ == "__main__":
    director_decrypt()
