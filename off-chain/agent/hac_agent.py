#!/usr/bin/env python3
# hac_agent.py
import os, sys, json, time
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from pathlib import Path

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = Web3.toChecksumAddress(os.getenv("CONTRACT_ADDRESS"))
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1337"))
ABI_PATH = os.getenv("ABI_PATH")
CRYPTO_ENGINE_PATH = os.getenv("CRYPTO_ENGINE_PATH", "../crypto-engine")

if not (RPC_URL and CONTRACT_ADDRESS and DEPLOYER_PRIVATE_KEY and ABI_PATH):
    print("Missing required environment variables in .env. Please set RPC_URL, CONTRACT_ADDRESS, DEPLOYER_PRIVATE_KEY, ABI_PATH")
    sys.exit(1)

# Add crypto_engine path so we can import modules
sys.path.insert(0, CRYPTO_ENGINE_PATH)

# Import your crypto engine helpers
from edge_ops import decode_edge_add_payload_for_target  # uses ecc_decrypt + aes_gcm_decrypt
# key_manager (optional) import if needed:
# from key_manager import load_entity_keys

# Load ABI
with open(ABI_PATH, "r") as f:
    abi_json = json.load(f)
    abi = abi_json["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
acct = Account.from_key(DEPLOYER_PRIVATE_KEY)
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def build_and_send_tx(fn_call):
    """Helper to build, sign, and send tx. fn_call is contract.functions.X(...)"""
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = fn_call.build_transaction({
        "from": acct.address,
        "nonce": nonce,
        "gas": 800000,
        "gasPrice": 0  # change if your network requires nonzero gas
    })
    signed = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print("Sent tx:", tx_hash.hex())
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print("Receipt status:", receipt.status)
    return receipt

# ---------- ACTION: register public key ----------
def register_public_key(pubkey_hex):
    """
    pubkey_hex: hex string of the public key bytes (no 0x prefix required).
    On-chain we pass bytes, so convert to bytes.
    """
    pub_bytes = bytes.fromhex(pubkey_hex if not pubkey_hex.startswith("0x") else pubkey_hex[2:])
    fn = contract.functions.registerPublicKey(pub_bytes)
    receipt = build_and_send_tx(fn)
    return receipt

# ---------- ACTION: publish edge ----------
def publish_edge(to_address, payload_json_path, version):
    """
    payload_json_path: path to JSON payload produced by crypto_engine.make_edge_add_payload(...)
    The JSON contains fields: enc_pk_to.{ephemeral_pub_hex, nonce_hex, ciphertext_hex}, e_under.{nonce_hex, ciphertext_hex}
    We must pack enc_pk_to as bytes and e_under as bytes to match smart contract storage.
    Packing convention used here:
      enc_pk_to_bytes = ephemeral_pub || nonce || ciphertext
      e_under_bytes   = nonce || ciphertext
    (That mirrors how we encoded payload earlier.)
    """
    to = Web3.toChecksumAddress(to_address)
    with open(payload_json_path, "r") as f:
        payload = json.load(f)
    # build enc_pk_to bytes
    epub = payload["enc_pk_to"]["ephemeral_pub_hex"]
    enc_nonce = payload["enc_pk_to"]["nonce_hex"]
    enc_cipher = payload["enc_pk_to"]["ciphertext_hex"]
    enc_pk_to_bytes = bytes.fromhex(epub + enc_nonce + enc_cipher)
    # build e_under bytes
    e_under_nonce = payload["e_under"]["nonce_hex"]
    e_under_cipher = payload["e_under"]["ciphertext_hex"]
    e_under_bytes = bytes.fromhex(e_under_nonce + e_under_cipher)

    fn = contract.functions.publishEdge(to, enc_pk_to_bytes, e_under_bytes, int(version))
    receipt = build_and_send_tx(fn)
    return receipt

# ---------- ACTION: listen & attempt decrypt ----------
def listen_and_decrypt(entity_privkey_hex=None, entity_address=None):
    """
    Listens for EdgePublished events. If an incoming event is addressed to entity_address,
    it reconstructs the payload as expected by decode_edge_add_payload_for_target and tries to decrypt it.
    entity_privkey_hex: optional hex of ECC private scalar for target (if provided, we use it to decrypt)
    If you keep ECC private in your crypto_engine keystore file, load it instead and pass here accordingly.
    """
    print("Listening for EdgePublished events... ctrl-c to exit")
    event_filter = contract.events.EdgePublished.createFilter(fromBlock="latest")

    # If user provided an ECC private scalar, load it into a private key object using key_manager/ecc_elgamal
    ecc_priv_obj = None
    if entity_privkey_hex:
        # dynamic import to avoid circular issues
        from ecc_elgamal import load_private_from_scalar_hex
        ecc_priv_obj = load_private_from_scalar_hex(entity_privkey_hex)

    while True:
        try:
            for ev in event_filter.get_new_entries():
                ev_args = ev["args"]
                ev_from = ev_args["from"]
                ev_to = ev_args["to"]
                print(f"Event: EdgePublished from={ev_from} to={ev_to} version={ev_args['version']}")

                # Check if this event is for our entity_address
                if entity_address and Web3.toChecksumAddress(ev_to) != Web3.toChecksumAddress(entity_address):
                    print("  -> not addressed to this entity, skipping.")
                    continue

                enc_pk_to_bytes = ev_args["enc_pk_to"]
                e_under_bytes = ev_args["e_under"]

                # Parse enc_pk_to: ephemeral_pub (65 bytes uncompressed) || nonce (12 bytes) || ciphertext (rest)
                # NOTE: this parsing assumes standard sizes — if your encoding differs, adapt accordingly.
                enc_bytes = bytes(enc_pk_to_bytes)
                if len(enc_bytes) < 65 + 12 + 16:
                    print("  -> enc_pk_to too short, skipping")
                    continue
                ephemeral_pub = enc_bytes[:65]
                nonce_enc = enc_bytes[65:65+12]
                ciphertext_enc = enc_bytes[65+12:]

                e_under_b = bytes(e_under_bytes)
                if len(e_under_b) < 12 + 16:
                    print("  -> e_under too short, skipping")
                    continue
                nonce_under = e_under_b[:12]
                ciphertext_under = e_under_b[12:]

                # Reconstruct payload dict matching what decode_edge_add_payload_for_target expects
                payload = {
                    "enc_pk_to": {
                        "ephemeral_pub_hex": ephemeral_pub.hex(),
                        "nonce_hex": nonce_enc.hex(),
                        "ciphertext_hex": ciphertext_enc.hex()
                    },
                    "e_under": {
                        "nonce_hex": nonce_under.hex(),
                        "ciphertext_hex": ciphertext_under.hex()
                    }
                }

                # If we have ECC private, attempt decryption
                if ecc_priv_obj:
                    try:
                        ek_from, ek_to = decode_edge_add_payload_for_target(ecc_priv_obj, payload)
                        print("  -> Decryption success. ek_from (hex):", ek_from.hex())
                        print("  -> ek_to   (hex):", ek_to.hex())
                    except Exception as e:
                        print("  -> Decrypt failed:", str(e))
                else:
                    print("  -> No ECC private provided to decrypt. Provide ECC scalar to attempt decryption.")

            time.sleep(2)
        except KeyboardInterrupt:
            print("Listener stopped.")
            break
        except Exception as e:
            print("Listener error:", str(e))
            time.sleep(5)

# ---------- CLI entrypoint ----------
def print_usage():
    print("Usage:")
    print("  python hac_agent.py register-key <pubkey_hex>")
    print("  python hac_agent.py publish-edge <to_address> <payload_json_path> <version>")
    print("  python hac_agent.py listen <entity_priv_scalar_hex_or_empty> <entity_address_optional>")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    cmd = sys.argv[1]

    if cmd == "register-key":
        if len(sys.argv) != 3:
            print("register-key requires pubkey_hex")
            sys.exit(1)
        pubkey_hex = sys.argv[2]
        register_public_key(pubkey_hex)
    elif cmd == "publish-edge":
        if len(sys.argv) != 5:
            print("publish-edge requires: <to_address> <payload_json_path> <version>")
            sys.exit(1)
        to_addr = sys.argv[2]
        payload_path = sys.argv[3]
        version = sys.argv[4]
        publish_edge(to_addr, payload_path, version)
    elif cmd == "listen":
        # allow passing empty string for no privkey
        if len(sys.argv) >= 3:
            priv = sys.argv[2] if sys.argv[2] != "none" else None
        else:
            priv = None
        ent_addr = sys.argv[3] if len(sys.argv) >= 4 else None
        listen_and_decrypt(priv, ent_addr)
    else:
        print_usage()
