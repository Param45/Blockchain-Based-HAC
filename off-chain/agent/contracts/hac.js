// agent/contracts/hac_utils.js
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const { CONTRACT_ADDRESS, getRpcUrl } = require("../config/network");
dotenv.config();

// Load ABI
const ABI_PATH = path.join(
  __dirname,
  "../../artifacts/contracts/HierarchicalAccessControl.sol/HierarchicalAccessControl.json"
);

if (!fs.existsSync(ABI_PATH)) {
  throw new Error(`ABI not found at ${ABI_PATH}. Run 'npx hardhat compile' first.`);
}

const abiJson = JSON.parse(fs.readFileSync(ABI_PATH, "utf8"));
const CONTRACT_ABI = abiJson.abi;

/**
 * Returns a JSON-RPC provider for a given role
 */
function getProvider(role = "Director") {
  const rpcUrl = getRpcUrl(role);
  if (!rpcUrl) throw new Error(`RPC URL not found for role: ${role}`);
  return new ethers.providers.JsonRpcProvider(rpcUrl);
}

/**
 * Returns a wallet instance for a given role
 */
function getWallet(role) {
  const keyEnv = `${role.toUpperCase()}_PRIVATE_KEY`;
  const privateKey = process.env[keyEnv];
  if (!privateKey) throw new Error(`Missing private key for ${role} in .env`);
  return new ethers.Wallet(privateKey, getProvider(role));
}

/**
 * Returns a contract instance (connected either to signer or provider)
 */
function getContract(signerOrProvider) {
  return new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, signerOrProvider);
}

module.exports = {
  getProvider,
  getWallet,
  getContract,
};
