// Hardhat configuration for Hyperledger Besu QBFT private network

require("@nomiclabs/hardhat-ethers"); // Enables ethers.js plugin

// === Besu Network Configuration ===
// Replace the RPC URL if your Besu node runs on a different host or port.
const BESU_RPC_URL = "http://localhost:8545";

// Private key of the deployer (director in your genesis alloc)
const DEPLOYER_PRIVATE_KEY = "0x5ac1236830e93e924bec20f4bd885b2ebfd4a24e0458f4e3d2ad2642fdc7b523";

// QBFT network chain ID (from your genesis config)
const CHAIN_ID = 1337;

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  defaultNetwork: "besu",
  networks: {
    besu: {
      url: BESU_RPC_URL,
      chainId: CHAIN_ID,
      accounts: [DEPLOYER_PRIVATE_KEY],
      gasPrice: 0,           // Besu private networks often run with 0 gas price
      gas: "auto",           // let Hardhat estimate gas
      timeout: 200000,       // prevent deployment timeout
    },
  },
};

