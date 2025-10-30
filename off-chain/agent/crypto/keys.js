// crypto/keys.js
const { execSync } = require("child_process");

/**
 * Generate or load entity keys via the Python crypto engine
 * @param {string} entityId - Role or ID of the entity
 * @param {string} skiHex - Optional deterministic SKI
 * @returns {object} { privHex, pubHex, ekHex }
 */
function keygen(entityId, skiHex = null) {
    try {
        let cmd = `python3 ./agent/crypto_engine_wrapper.py keygen ${entityId}`;
        if (skiHex) cmd += ` ${skiHex}`;

        const output = execSync(cmd, { encoding: "utf-8" });
        return JSON.parse(output);
    } catch (err) {
        console.error(`[keys.js] Keygen failed for ${entityId}:`, err.message);
        throw err;
    }
}

/**
 * Export public key (passthrough)
 * @param {string} pubHex
 * @returns {string}
 */
function exportPubHex(pubHex) {
    return pubHex;
}

module.exports = {
    keygen,
    exportPubHex
};
