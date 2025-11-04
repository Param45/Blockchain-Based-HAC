# crypto-engine/encrypt_file_with_student_ek.py
"""
Student-side encryption
-----------------------
Encrypts a file using Student's ek_hex (from their local key file).
The ciphertext will be saved as <filename>.enc
"""

import os
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys

def encrypt_file_with_student_ek(student_name, input_file):
    student = load_entity_keys(student_name)
    ek = bytes.fromhex(student["ek_hex"])

    with open(input_file, "rb") as f:
        data = f.read()

    nonce, ciphertext = aes_gcm_encrypt(ek, data)

    out_path = input_file + ".enc"
    with open(out_path, "wb") as f:
        f.write(nonce + ciphertext)

    print(f"✅ Encrypted {input_file} → {out_path} using {student_name}'s EK")

if __name__ == "__main__":
    os.makedirs("crypto-engine/student_files", exist_ok=True)
    input_path = "crypto-engine/student_files/student1_report.txt"

    # Create a sample file
    with open(input_path, "w") as f:
        f.write("Hii. My name is Ankesh Mishra (202311010).")

    encrypt_file_with_student_ek("Student1", input_path)
