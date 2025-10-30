// agent/index.js

const HACContract = require("../contracts/hac");
const listenEvents = require("../listeners/events");
const { makeEdgePayload } = require("../crypto/payload");
const { keygen, exportPubHex } = require("../crypto/keys");
const deleteEdge = require("../transactions/deleteEdge");
const rotateKey = require("../transactions/rotateKey");
const publishEdgeTx = require("../transactions/publishEdge");

/** 
 * Initialize an agent
 * @param {string} role - Agent role (Director, Professor1, Student1, etc.)
 * @param {string} skiHex - Optional deterministic SKI for reproducible keys
 */
async function initAgent(role, skiHex = null) {
    console.log(`[${role}] Initializing agent...`);

    // 1️⃣ Generate or load keys using crypto_engine_wrapper
    const { privHex, pubHex, ekHex } = keygen(role, skiHex);
    console.log(`[${role}] Keys loaded. Public key: ${pubHex}`);

    // 2️⃣ Initialize smart contract handler
    const hac = new HACContract(role, privHex);

    // 3️⃣ Register public key if not already on-chain
    const hasKey = await hac.hasPubKey(hac.getSignerAddress());
    if (!hasKey) {
        console.log(`[${role}] Registering public key on-chain...`);
        const receipt = await hac.registerKey(pubHex);
        console.log(`[${role}] Key registered. TxHash: ${receipt.transactionHash}`);
    } else {
        console.log(`[${role}] Public key already registered.`);
    }

    // 4️⃣ Start listening to contract events
    listenEvents(role, privHex);

    // 5️⃣ Return agent API
    return {
        role,
        privHex,
        pubHex,
        ekHex,

        /**
         * Publish an edge to another entity
         * @param {string} toPubHex - Recipient public key in hex
         * @param {string} toAddress - Ethereum address of recipient
         * @param {string} version - Version number for the edge
         */
        publishEdge: async (toPubHex, toAddress, version) => {
            const payload = makeEdgePayload(role, toPubHex, ekHex, ekHex);
            return await publishEdgeTx(role, privHex, toAddress, payload.enc_pk_to, payload.e_under, version);
        },

        /**
         * Soft-delete an edge
         * @param {string} toAddress
         * @param {number} version
         */
        deleteEdge: async (toAddress, version) => {
            return await deleteEdge(role, privHex, toAddress, version);
        },

        /**
         * Rotate public key
         * @param {string} newPubHex
         * @param {number} newVersion
         */
        rotateKey: async (newPubHex, newVersion) => {
            return await rotateKey(role, privHex, newPubHex, newVersion);
        }
    };
}

// -------------------------
// CLI Support
// -------------------------
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error("Usage: node index.js <Role> [<SKI_Hex>]");
        process.exit(1);
    }
    const [role, skiHex] = args;

    initAgent(role, skiHex)
        .then(agent => console.log(`[${role}] Agent initialized successfully.`))
        .catch(err => console.error(`[${role}] Agent initialization failed:`, err));
}

module.exports = initAgent;
