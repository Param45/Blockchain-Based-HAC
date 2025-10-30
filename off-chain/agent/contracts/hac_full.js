// agent/contracts/hac.js
const { ethers } = require("ethers");
const { CONTRACT_ADDRESS, CHAIN_ID, getRpcUrl, getWsUrl } = require("../config/network");
const fs = require("fs");
const path = require("path");

// Load ABI
const ABI_PATH = path.join(__dirname, "../../artifacts/contracts/HierarchicalAccessControl.sol/HierarchicalAccessControl.json");
if (!fs.existsSync(ABI_PATH)) {
    throw new Error(`ABI not found at ${ABI_PATH}. Make sure you compiled the contract first.`);
}
const abiJson = JSON.parse(fs.readFileSync(ABI_PATH, "utf8"));
const CONTRACT_ABI = abiJson.abi;

/**
 * HierarchicalAccessControl Contract Wrapper Class
 */
class HACContract {
    /**
     * @param {string} role - Role name (Director, Professor1, Student1, etc.)
     * @param {string} privateKey - Private key for the role from .env
     */
    constructor(role, privateKey) {
        this.role = role;

        // Connect providers
        this.rpcUrl = getRpcUrl(role);
        this.wsUrl = getWsUrl(role);

        this.provider = new ethers.providers.JsonRpcProvider(this.rpcUrl, CHAIN_ID);
        this.wallet = new ethers.Wallet(privateKey, this.provider);
        this.contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wallet);

        // Optional WebSocket provider for event subscriptions
        this.wsProvider = new ethers.providers.WebSocketProvider(this.wsUrl, CHAIN_ID);
        this.wsContract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wsProvider);

        // Auto-reconnect WS if dropped
        this.wsProvider._websocket?.on("close", () => {
            console.log(`[${this.role}] WS connection closed. Reconnecting in 3s...`);
            setTimeout(() => {
                this.wsProvider = new ethers.providers.WebSocketProvider(this.wsUrl, CHAIN_ID);
                this.wsContract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wsProvider);
            }, 3000);
        });
    }

    /** -------------------------
     * Transaction Functions
     * ------------------------- */

    async registerKey(pubKeyHex) {
        const tx = await this.contract.registerPublicKey("0x" + pubKeyHex, {
            gasLimit: 300000,
            gasPrice: 0,
        });
        return tx.wait();
    }

    async publishEdge(toAddress, encPkToHex, eUnderHex, version) {
        const tx = await this.contract.publishEdge(
            toAddress,
            "0x" + encPkToHex,
            "0x" + eUnderHex,
            version,
            { gasLimit: 800000, gasPrice: 0 }
        );
        return tx.wait();
    }

    async deleteEdge(toAddress, version) {
        const tx = await this.contract.deleteEdge(toAddress, version, {
            gasLimit: 300000,
            gasPrice: 0,
        });
        return tx.wait();
    }

    async rotateKey(newPubKeyHex, newVersion) {
        const tx = await this.contract.rotateKey("0x" + newPubKeyHex, newVersion, {
            gasLimit: 300000,
            gasPrice: 0,
        });
        return tx.wait();
    }

    /** -------------------------
     * Read Functions
     * ------------------------- */

    async hasPubKey(address) {
        return await this.contract.hasPubKey(address);
    }

    async getPubKey(address) {
        const keyBytes = await this.contract.getPubKey(address);
        return Buffer.from(keyBytes).toString("hex");
    }

    async getEdgeCount(from, to) {
        return (await this.contract.getEdgeCount(from, to)).toNumber();
    }

    async getEdgeByIndex(from, to, index) {
        const el = await this.contract.getEdgeByIndex(from, to, index);
        return {
            from: el.from,
            to: el.to,
            enc_pk_to: Buffer.from(el.enc_pk_to).toString("hex"),
            e_under: Buffer.from(el.e_under).toString("hex"),
            version: el.version.toNumber(),
            timestamp: el.timestamp.toNumber(),
            deleted: el.deleted,
        };
    }

    async getLatestEdge(from, to) {
        const el = await this.contract.getLatestEdge(from, to);
        return {
            from: el.from,
            to: el.to,
            enc_pk_to: Buffer.from(el.enc_pk_to).toString("hex"),
            e_under: Buffer.from(el.e_under).toString("hex"),
            version: el.version.toNumber(),
            timestamp: el.timestamp.toNumber(),
            deleted: el.deleted,
        };
    }

    /** -------------------------
     * Event Listeners
     * ------------------------- */

    onKeyRegistered(callback) {
        this.wsContract.on("KeyRegistered", callback);
    }

    onEdgePublished(callback) {
        this.wsContract.on("EdgePublished", callback);
    }

    onEdgeDeleted(callback) {
        this.wsContract.on("EdgeDeleted", callback);
    }

    onKeyRotated(callback) {
        this.wsContract.on("KeyRotated", callback);
    }
}

module.exports = HACContract;
