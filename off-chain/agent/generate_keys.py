import sys, binascii
sys.path.insert(0, "../crypto-engine")

from ecc_elgamal import generate_keypair

# Generate a new keypair
priv_obj, pub_bytes = generate_keypair()

# Convert private scalar (d) to hex
priv_numbers = priv_obj.private_numbers()
ski_hex = format(priv_numbers.private_value, 'x')

# Convert public key bytes to hex (uncompressed form)
pub_hex = pub_bytes.hex()

print("\n✅ ECC Key Pair Generated")
print("Private Key (save securely):", ski_hex)
print("Public Key (register on-chain):", pub_hex)

# Optionally save them to files
with open("../crypto-engine/keys/generated_priv.txt", "w") as f:
    f.write(ski_hex)
with open("../crypto-engine/keys/generated_pub.txt", "w") as f:
    f.write(pub_hex)
print("\nSaved to crypto-engine/keys/")
