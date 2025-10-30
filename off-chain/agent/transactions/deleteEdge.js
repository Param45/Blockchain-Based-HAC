// agent/transactions/deleteEdge.js
const { getWallet, getContract } = require("../contracts/hac");

/**
 * Soft-delete edge by publisher
 * @param {string} privateKey - 0x private key
 * @param {string} toAddress - recipient address
 * @param {number} versionOrMax - version number to delete, or -1 to delete latest
 */
async function deleteEdge(privateKey, toAddress, versionOrMax = -1) {
  if (!privateKey || !toAddress) throw new Error("deleteEdge requires (privateKey, toAddress, versionOrMax)");
  const wallet = getWallet(privateKey);
  const contract = getContract(wallet);
  let version;
  if (versionOrMax === -1) version = BigInt("0xffffffffffffffff"); // Solidity type(uint64).max
  else version = parseInt(versionOrMax, 10);
  const tx = await contract.deleteEdge(toAddress, version, { gasLimit: 300000, gasPrice: 0 });
  console.log("deleteEdge tx:", tx.hash);
  const receipt = await tx.wait();
  console.log("deleteEdge mined. status:", receipt.status, "blockNumber:", receipt.blockNumber);
  return receipt;
}

// CLI
if (require.main === module) {
  const argv = process.argv.slice(2);
  if (argv.length < 2) {
    console.error("Usage: node deleteEdge.js <PRIVATE_KEY> <TO_ADDRESS> [version|latest]");
    process.exit(1);
  }
  const [privateKey, toAddress, versionArg] = argv;
  const versionOrMax = (versionArg && versionArg !== "latest") ? parseInt(versionArg, 10) : -1;
  deleteEdge(privateKey, toAddress, versionOrMax).catch(e => { console.error(e); process.exit(1); });
}

module.exports = deleteEdge;
