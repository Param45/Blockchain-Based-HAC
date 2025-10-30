// agent/transactions/verifyKey.js
const { ethers } = require("ethers");
const { getProvider, getContract } = require("../contracts/hac"); // ✅ use hac.js, not hac_full
const dotenv = require("dotenv");
const fs = require("fs");
dotenv.config();

async function verifyKey(entityName, address) {
  console.log(`🔍 Verifying on-chain public key for ${entityName}...`);

  // 1️⃣ Connect to provider + contract
  const provider = getProvider();
  const contract = getContract(provider);

  try {
    // 2️⃣ Fetch on-chain public key
    const keyBytes = await contract.getPubKey(address);
    if (!keyBytes || keyBytes.length === 0) {
      console.log(`❌ No public key found for ${entityName} (${address})`);
      return;
    }

    const pubKeyHex = Buffer.from(keyBytes).toString("hex");
    console.log(`✅ On-chain Public Key for ${entityName}:`);
    console.log(pubKeyHex);

    // 3️⃣ Compare with local file (optional)
    const path = `crypto-engine/keys/${entityName}.json`;
    if (fs.existsSync(path)) {
      const local = JSON.parse(fs.readFileSync(path, "utf8"));
      if (local.pub_hex.toLowerCase() === pubKeyHex.toLowerCase()) {
        console.log("🟩 Match confirmed with local file.\n");
      } else {
        console.log("🟥 Mismatch detected between on-chain and local pubkey.\n");
      }
    } else {
      console.log("⚠️ No local key file found for comparison.\n");
    }

  } catch (err) {
    console.error(`❌ Error verifying ${entityName}:`, err.message);
  }
}

async function main() {
  const entity = process.argv[2];
  if (!entity) {
    console.error("Usage: node agent/transactions/verifyKey.js <EntityName>");
    process.exit(1);
  }

  // Replace these with actual blockchain addresses for each entity
  const addressBook = {
    Director: "0x4BdbbFD674ee2ed57db4D058Ed5cA04B858EF461",
    Professor1: "0x8E6410E5c1c433D9C545025d7bD21F780605C81f",
    Professor2: "0x08F20e403B2813A326221781D4420242a5DB452b",
    Student1: "0x6681D6eB6128F6Ef8E0792Ca53271F7a5c84873B",
    Student2: "0x733123064C38bfB70F939f4763e359E0d512b9bA",
    Student3: "0xCf9d739f438C36bD6E769595cDF4794dc84996C3"
  };

  const address = addressBook[entity];
  if (!address) {
    console.error(`❌ No address found for ${entity}. Please update the addressBook.`);
    process.exit(1);
  }

  await verifyKey(entity, address);
}

main();
