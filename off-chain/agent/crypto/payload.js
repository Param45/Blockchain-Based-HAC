// crypto/payload.js
const { execSync } = require("child_process");

/**
 * Create edge payload (enc_pk_to, e_under) via Python crypto engine
 * @param {string} fromId - Publisher entity ID
 * @param {string} toPubHex - Recipient public key in hex
 * @param {string} ekFromHex - Publisher symmetric key in hex
 * @param {string} ekToHex - Recipient symmetric key in hex
 * @returns {object} { enc_pk_to, e_under } - JSON payload
 */
function makeEdgePayload(fromId, toPubHex, ekFromHex, ekToHex) {
    try {
        const cmd = `python3 ./agent/crypto_engine_wrapper.py make_payload ${fromId} ${toPubHex} ${ekFromHex} ${ekToHex}`;
        const output = execSync(cmd, { encoding: "utf-8" });
        return JSON.parse(output);
    } catch (err) {
        console.error(`[payload.js] makeEdgePayload failed:`, err.message);
        throw err;
    }
}

/**
 * Decode an edge payload for recipient using Python crypto engine
 * @param {string} recipientPrivHex - Recipient private key hex
 * @param {object} payload - JSON payload from makeEdgePayload
 * @returns {object} { ekFromHex, ekToHex }
 */
function decodeEdgePayload(recipientPrivHex, payload) {
    try {
        const payloadStr = JSON.stringify(payload).replace(/"/g, '\\"'); // escape quotes
        const cmd = `python3 ./agent/crypto_engine_wrapper.py decode_payload ${recipientPrivHex} "${payloadStr}"`;
        const output = execSync(cmd, { encoding: "utf-8" });
        return JSON.parse(output);
    } catch (err) {
        console.error(`[payload.js] decodeEdgePayload failed:`, err.message);
        throw err;
    }
}

module.exports = {
    makeEdgePayload,
    decodeEdgePayload
};
