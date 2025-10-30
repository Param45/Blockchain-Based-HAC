// crypto/signing.js
const { ethers } = require("ethers");

/**
 * Sign an Ethereum transaction using a private key
 * @param {object} tx - Transaction object
 * @param {string} privateKey - Hex string
 * @returns {string} - Signed transaction serialized
 */
function signTransaction(tx, privateKey) {
    const wallet = new ethers.Wallet(privateKey);
    return wallet.signTransaction(tx);
}

module.exports = {
    signTransaction
};
