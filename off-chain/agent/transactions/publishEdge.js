// agent/transactions/publishEdge.js
const HACContract = require("../contracts/hac_full");
const dotenv = require("dotenv");
dotenv.config();

function normalizeHex(hexStr) {
  if (!hexStr) return "0x";
  // Remove unwanted ASCII hex prefixes like "3078..."
  // which represent literal "0x" in bytes
  if (hexStr.startsWith("3078")) {
    // decode the ASCII layer
    const asciiDecoded = Buffer.from(hexStr, "hex").toString("utf8");
    // strip the "0x" if present
    return asciiDecoded.replace(/^0x/, "0x");
  }
  // Otherwise ensure proper 0x prefix only once
  return hexStr.startsWith("0x") ? hexStr : "0x" + hexStr;
}

/**
 * Publish an EdgeLabel on-chain
 * @param {string} role - entity name (Director, Professor1, etc.)
 * @param {string} toAddress - recipient Ethereum address
 * @param {string} encPkToHex - hex of encrypted pk_to
 * @param {string} eUnderHex - hex of encrypted ek
 * @param {number} version - version number (default 1)
 */
async function publishEdge(role, toAddress, encPkToHex, eUnderHex, version = 1) {
  console.log(`\n🔗 Starting edge publication for ${role} → ${toAddress}`);

  const privKey = process.env[`${role.toUpperCase()}_PRIVATE_KEY`];
  if (!privKey) throw new Error(`❌ Missing ${role.toUpperCase()}_PRIVATE_KEY in .env`);

  const hac = new HACContract(role, privKey);

  // Normalize once
  const encHex = normalizeHex(encPkToHex);
  const eUnder = normalizeHex(eUnderHex);

  const tx = await hac.contract.publishEdge(toAddress, encHex, eUnder, version, {
    gasLimit: 800000,
    gasPrice: 0,
  });

  console.log(`⏳ TX sent: ${tx.hash}`);
  const receipt = await tx.wait();
  console.log(`✅ Edge published in block ${receipt.blockNumber}\n`);
  return receipt;
}

// CLI handler
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 4) {
    console.error("Usage: node agent/transactions/publishEdge.js <ROLE> <TO_ADDRESS> <ENC_PK_TO_HEX> <EUNDER_HEX> [version]");
    process.exit(1);
  }

  const [role, to, enc, eunder, versionStr] = args;
  const version = versionStr ? parseInt(versionStr, 10) : 1;

  publishEdge(role, to, enc, eunder, version)
    .catch(err => console.error("❌ Error in publishEdge:", err));
}

module.exports = publishEdge;
