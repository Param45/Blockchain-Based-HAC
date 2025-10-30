// transactions/rotateKey.js

const HACContract = require("../contracts/hac");

/**
 * Rotate an entity's public key on-chain
 * @param {string} role - Role of the sender (Director/Professor/Student)
 * @param {string} privateKey - Private key of the sender for signing
 * @param {string} newPubKeyHex - New public key in hex format
 * @param {number} newVersion - Monotonic version number for this rotation
 */
async function rotateKey(role, privateKey, newPubKeyHex, newVersion) {
    try {
        console.log(`[${role}] Connecting to blockchain...`);
        const hac = new HACContract(role, privateKey);

        console.log(`[${role}] Rotating key to new version ${newVersion}...`);
        const receipt = await hac.rotateKey(newPubKeyHex, newVersion);

        console.log(`[${role}] Key rotated successfully!`);
        console.log(`Transaction Hash: ${receipt.transactionHash}`);
        return receipt;
    } catch (err) {
        console.error(`[${role}] Failed to rotate key:`, err);
        throw err;
    }
}

/**
 * Example Usage:
 * node rotateKey.js Professor1 0x<PrivKey> <NewPubKeyHex> 2
 */
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length < 4) {
        console.error("Usage: node rotateKey.js <Role> <PrivateKey> <NewPubKeyHex> <NewVersion>");
        process.exit(1);
    }

    const [role, privateKey, newPubKeyHex, versionStr] = args;
    const newVersion = parseInt(versionStr, 10);

    rotateKey(role, privateKey, newPubKeyHex, newVersion);
}

module.exports = rotateKey;
