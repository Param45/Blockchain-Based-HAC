# edge_ops.py
import json
from ecc_elgamal import ecc_encrypt, ecc_decrypt
from aes_gcm import aes_gcm_encrypt, aes_gcm_decrypt
from typing import Dict

def make_edge_add_payload(entity_from_id: str, entity_to_pub_bytes: bytes, ek_from: bytes, ek_to: bytes):
    """
    Create the tuple described in paper:
    - Enc(pk_to, ek_from)        -> ECC encrypt ek_from under pk_to
    - E(ek_to, ek_from)          -> AES encrypt ek_to under ek_from
    We'll return a JSON-serializable dict with base hex strings.
    """
    # 1. Enc(pk_to, ek_from)
    enc_pk_to = ecc_encrypt(entity_to_pub_bytes, ek_from)
    # 2. E(ek_to, ek_from)  -> AES-GCM encrypt ek_to with ek_from as key
    nonce, ct = aes_gcm_encrypt(ek_from, ek_to)
    payload = {
        "from": entity_from_id,
        "enc_pk_to": {
            "ephemeral_pub_hex": enc_pk_to["ephemeral_pub"].hex(),
            "nonce_hex": enc_pk_to["nonce"].hex(),
            "ciphertext_hex": enc_pk_to["ciphertext"].hex()
        },
        "e_under": {
            "nonce_hex": nonce.hex(),
            "ciphertext_hex": ct.hex()
        }
    }
    return payload

def decode_edge_add_payload_for_target(recipient_priv_obj, payload: Dict):
    """
    Recipient (target) uses its private key to decrypt Enc(pk_to, ek_from)
    and obtains ek_from. Then can decrypt E(ek_to, ek_from) with ek_from to get ek_to.
    """
    enc_pk_to = {
        "ephemeral_pub": bytes.fromhex(payload["enc_pk_to"]["ephemeral_pub_hex"]),
        "nonce": bytes.fromhex(payload["enc_pk_to"]["nonce_hex"]),
        "ciphertext": bytes.fromhex(payload["enc_pk_to"]["ciphertext_hex"])
    }
    ek_from = ecc_decrypt(recipient_priv_obj, enc_pk_to)
    e_under_nonce = bytes.fromhex(payload["e_under"]["nonce_hex"])
    e_under_ct = bytes.fromhex(payload["e_under"]["ciphertext_hex"])
    ek_to = aes_gcm_decrypt(ek_from, e_under_nonce, e_under_ct)
    return ek_from, ek_to
