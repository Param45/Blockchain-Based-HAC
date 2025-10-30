// config/network.js

/**
 * Network configuration for Besu QBFT private network
 * Adjust RPC_URL based on the node where the agent is running
 */

// Contract address of the deployed HierarchicalAccessControl
const CONTRACT_ADDRESS = "0x5d678c356221B87105cB87150C8112bF59bB771b"; // Replace with actual deployed contract address

// Chain ID
const CHAIN_ID = 1337;

// RPC endpoints per role/node
const RPC_URLS = {
    Director: "http://127.0.0.1:8545",
    Professor1: "http://127.0.0.1:8546",
    Professor2: "http://127.0.0.1:8547",
    Student1: "http://127.0.0.1:8548",
    Student2: "http://127.0.0.1:8549",
    Student3: "http://127.0.0.1:8550"
};

// WebSocket endpoints (optional) per role/node for event subscriptions
const WS_URLS = {
    Director: "ws://127.0.0.1:9545",
    Professor1: "ws://127.0.0.1:9546",
    Professor2: "ws://127.0.0.1:9547",
    Student1: "ws://127.0.0.1:9548",
    Student2: "ws://127.0.0.1:9549",
    Student3: "ws://127.0.0.1:9550"
};

/**
 * Get the RPC HTTP URL for a given role
 * @param {string} role - e.g., "Director", "Professor1"
 */
function getRpcUrl(role) {
    return RPC_URLS[role] || null;
}

/**
 * Get the WebSocket URL for a given role
 * @param {string} role - e.g., "Director", "Professor1"
 */
function getWsUrl(role) {
    return WS_URLS[role] || null;
}

module.exports = {
    CONTRACT_ADDRESS,
    CHAIN_ID,
    RPC_URLS,
    WS_URLS,
    getRpcUrl,
    getWsUrl
};
