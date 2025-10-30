// agent/transactions/registerKey.js
const { execSync } = require("child_process");
const { getRpcUrl } = require("../config/network");
const dotenv = require("dotenv");
dotenv.config();

async function registerKey() {
  const role = process.argv[2];
  if (!role) {
    console.error("❌ Usage: node agent/transactions/registerKey.js <RoleName>");
    process.exit(1);
  }

  const envKeyName = `${role.toUpperCase()}_PRIVATE_KEY`;
  const privateKey = process.env[envKeyName];
  if (!privateKey) {
    console.error(`❌ Missing private key for ${role} (${envKeyName})`);
    process.exit(1);
  }

  // --- Call Python to get the public key hex ---
  console.log(`🔑 Generating or loading public key for ${role}...`);
  let pubKeyHex;
  try {
    const output = execSync(`python3 crypto-engine/key_manager.py --entity ${role}`, {
      encoding: "utf8",
    });
    pubKeyHex = output.trim();
    if (!/^0[2345]/.test(pubKeyHex)) {
      throw new Error("Invalid pubkey output from Python");
    }
  } catch (err) {
    console.error("❌ Failed to get pubkey from Python:", err.message);
    process.exit(1);
  }

  // --- Register key on-chain ---
  console.log(`📡 Connecting ${role} node...`);
  const { ethers } = require("ethers");
  const { CONTRACT_ADDRESS } = require("../config/network");
  const fs = require("fs");
  const path = require("path");

  const ABI_PATH = path.join(
    __dirname,
    "../../artifacts/contracts/HierarchicalAccessControl.sol/HierarchicalAccessControl.json"
  );
  const abiJson = JSON.parse(fs.readFileSync(ABI_PATH, "utf8"));
  const CONTRACT_ABI = abiJson.abi;

  const provider = new ethers.providers.JsonRpcProvider(getRpcUrl(role), parseInt(process.env.CHAIN_ID));
  const wallet = new ethers.Wallet(privateKey, provider);
  const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, wallet);

  try {
    console.log(`📝 Registering key for ${role} (${pubKeyHex.slice(0, 16)}...)`);
    const tx = await contract.registerPublicKey("0x" + pubKeyHex, { gasLimit: 300000, gasPrice: 0 });
    console.log(`⏳ Sent TX: ${tx.hash}`);
    const receipt = await tx.wait();
    console.log(`✅ Key registered in block ${receipt.blockNumber}`);
  } catch (err) {
    console.error("❌ Error during registration:", err);
  }
}

registerKey();
