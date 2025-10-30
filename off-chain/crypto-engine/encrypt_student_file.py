# crypto-engine/encrypt_student_file.py
"""
Student encrypts a local file using their own EK.
Later, the Director (or superior) can derive this EK via hierarchy and decrypt it.
"""

import os
from aes_gcm import aes_gcm_encrypt
from key_manager import load_entity_keys

def encrypt_file(student_id, input_path, output_path):
    student = load_entity_keys(student_id)
    ek_student = bytes.fromhex(student["ek_hex"])

    with open(input_path, "rb") as f:
        plaintext = f.read()

    nonce, ciphertext = aes_gcm_encrypt(ek_student, plaintext)

    with open(output_path, "wb") as f:
        f.write(nonce + ciphertext)

    print(f"✅ File encrypted by {student_id} using their EK")
    print(f"📁 Saved to {output_path}")

if __name__ == "__main__":
    os.makedirs("crypto-engine/protected", exist_ok=True)

    student_id = "Student1"  # change as needed
    input_path = "crypto-engine/protected/student1_report.txt"
    output_path = "crypto-engine/protected/student1_report.enc"

    # create test file
    with open(input_path, "w") as f:
        f.write("Student1 confidential research data.")

    encrypt_file(student_id, input_path, output_path)
