# crypto-engine/decrypt_file_with_derived_ek.py
"""
Director-side decryption
------------------------
Decrypts the student's encrypted file using the derived EK stored in derived_ek_<student>.bin
"""

import os
from aes_gcm import aes_gcm_decrypt

def decrypt_file_with_derived_ek(student_name, enc_file):
    key_path = f"crypto-engine/derived_ek_{student_name}.bin"
    if not os.path.exists(key_path):
        print(f"❌ Missing derived key file: {key_path}")
        return

    ek = open(key_path, "rb").read()
    with open(enc_file, "rb") as f:
        data = f.read()

    nonce, ciphertext = data[:12], data[12:]
    plaintext = aes_gcm_decrypt(ek, nonce, ciphertext)

    out_file = enc_file.replace(".enc", "_decrypted.txt")
    with open(out_file, "wb") as f:
        f.write(plaintext)

    print(f"✅ Decrypted {enc_file} → {out_file}")

if __name__ == "__main__":
    decrypt_file_with_derived_ek("Student1", "crypto-engine/student_files/student1_report.txt.enc")
