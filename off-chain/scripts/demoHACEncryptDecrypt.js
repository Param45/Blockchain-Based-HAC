const hre = require("hardhat");
const { ethers } = hre;
const crypto = require("crypto");

// ----------------------------
// CONFIGURE THESE
// ----------------------------
const BESU_RPC_URL = "http://127.0.0.1:8545";

// Replace with private keys of the accounts (must have some ETH on Besu)
const STUD3_PRIVATE_KEY = "0x829938e39c710ecc837a7e7bc5f0bd69278ba36fc7afa34e55b4f8c0660b7538";
const DIRECTOR_PRIVATE_KEY = "0x5ac1236830e93e924bec20f4bd885b2ebfd4a24e0458f4e3d2ad2642fdc7b523";

// HAC contract address (already deployed)
const HAC_ADDRESS = "0x2ED168cbB2DdB083D27988Ae7Aeb800c0C5a2c26";

// For demonstration
const PLAINTEXT = "Hello Director! This is secret from stud3.";

// ----------------------------
// HELPER FUNCTIONS
// ----------------------------

// AES-GCM encryption
function aesEncrypt(plaintext, key) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, encrypted]); // store IV+TAG+CIPHERTEXT
}

// AES-GCM decryption
function aesDecrypt(cipherBytes, key) {
  const iv = cipherBytes.slice(0, 12);
  const tag = cipherBytes.slice(12, 28);
  const encrypted = cipherBytes.slice(28);
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  const decrypted = decipher.update(encrypted).toString("utf8") + decipher.final("utf8");
  return decrypted;
}

// ECIES-style encryption (simplified using public key + crypto module)
function eciesEncrypt(symKey, pubKey) {
  // For demonstration, we just use AES + random key to simulate "enc_pk_to"
  // In production, replace with proper ECIES encryption
  return Buffer.from(symKey).toString("hex"); // store as hex string
}

// ECIES-style decryption
function eciesDecrypt(encSymKey, privKey) {
  // For demonstration, just convert back from hex
  return Buffer.from(encSymKey, "hex");
}

// ----------------------------
// MAIN SCRIPT
// ----------------------------
async function main() {
  const provider = new ethers.providers.JsonRpcProvider(BESU_RPC_URL);
  const stud3 = new ethers.Wallet(STUD3_PRIVATE_KEY, provider);
  const director = new ethers.Wallet(DIRECTOR_PRIVATE_KEY, provider);

  console.log("STUD3:", stud3.address);
  console.log("DIRECTOR:", director.address);

  // Connect to HAC
  const HAC = await hre.ethers.getContractFactory("HierarchicalAccessControl");
  const hac = HAC.attach(HAC_ADDRESS);

  // -----------------------------
  // Step 0: Ensure both have registered public keys
  // -----------------------------
  const stud3PubKey = ethers.utils.toUtf8Bytes("stud3-pubkey"); // dummy
  const directorPubKey = ethers.utils.toUtf8Bytes("director-pubkey"); // dummy

  let tx = await hac.connect(stud3).registerPublicKey(stud3PubKey);
  await tx.wait();
  console.log("STUD3 registered pubkey");

  tx = await hac.connect(director).registerPublicKey(directorPubKey);
  await tx.wait();
  console.log("DIRECTOR registered pubkey");

  // -----------------------------
  // Step 1: STUD3 encrypts plaintext
  // -----------------------------
  console.log("\nSTUD3 encrypting plaintext...");
  const symmetricKey = crypto.randomBytes(32); // AES-256 key
  const e_under = aesEncrypt(PLAINTEXT, symmetricKey); // encrypt plaintext
  const enc_pk_to = eciesEncrypt(symmetricKey, directorPubKey); // encrypt key for director

  console.log("Encrypted symmetric key (enc_pk_to):", enc_pk_to);
  console.log("Encrypted payload (e_under):", e_under.toString("hex"));

  // -----------------------------
  // Step 2: Publish edge to HAC
  // -----------------------------
  console.log("\nPublishing edge STUD3 -> DIRECTOR...");
  tx = await hac.connect(stud3).publishEdge(
    director.address,
    enc_pk_to,
    e_under,
    1
  );
  await tx.wait();
  console.log("Edge published successfully!");

  // -----------------------------
  // Step 3: DIRECTOR retrieves and decrypts
  // -----------------------------
  console.log("\nDIRECTOR retrieving and decrypting...");
  const latestEdge = await hac.getLatestEdge(stud3.address, director.address);
  const encSymKey = latestEdge.enc_pk_to;
  const cipherPayload = latestEdge.e_under;

  const decryptedSymKey = eciesDecrypt(encSymKey, director.privateKey);
  const recoveredPlaintext = aesDecrypt(Buffer.from(cipherPayload), decryptedSymKey);

  console.log("\nRecovered plaintext:", recoveredPlaintext);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

