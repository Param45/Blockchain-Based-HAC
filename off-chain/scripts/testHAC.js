const hre = require("hardhat");
const { ethers } = hre;

// ----------------------------
// CONFIGURE THESE
// ----------------------------

// Replace with your deployer's private key (must have Ether on Besu)
const PRIVATE_KEY = "0x5ac1236830e93e924bec20f4bd885b2ebfd4a24e0458f4e3d2ad2642fdc7b523";

// Replace with your Besu RPC URL
const BESU_RPC_URL = "http://127.0.0.1:8545";

// Dummy second account public key (used for edges)
const USERB_ADDRESS = "0x8e6410e5c1c433d9c545025d7bd21f780605c81f"; // Replace with actual second account on Besu
const USERB_PRIVATE_KEY = "0xf68983bf4a0e7a92f8399de8c251ceabf7f9bd289d2dee24cc3659c9cd56090e"; // Optional if you want to send tx as userB

// ----------------------------
// SCRIPT
// ----------------------------

async function main() {
  const provider = new ethers.providers.JsonRpcProvider(BESU_RPC_URL);

  // Create deployer wallet
  const deployer = new ethers.Wallet(PRIVATE_KEY, provider);

  console.log("Deploying contracts with account:", deployer.address);

  const balance = await deployer.getBalance();
  console.log("Deployer balance:", ethers.utils.formatEther(balance));

  // Deploy HierarchicalAccessControl contract
  const HAC = await hre.ethers.getContractFactory("HierarchicalAccessControl");
  const hac = await HAC.connect(deployer).deploy();
  await hac.deployed();
  console.log("HierarchicalAccessControl deployed at:", hac.address);

  // -----------------------------
  // Step 1: Register public keys
  // -----------------------------
  console.log("\nRegistering public keys...");

  const pubKeyA = ethers.utils.toUtf8Bytes("pubkey-A"); // dummy bytes for deployer
  const tx1 = await hac.registerPublicKey(pubKeyA);
  await tx1.wait();
  console.log("Deployer registered pubkey:", pubKeyA);

  // If you want, register USERB pubkey
  const userBWallet = new ethers.Wallet(USERB_PRIVATE_KEY, provider);
  const pubKeyB = ethers.utils.toUtf8Bytes("pubkey-B"); // dummy bytes for userB
  const tx2 = await hac.connect(userBWallet).registerPublicKey(pubKeyB);
  await tx2.wait();
  console.log("UserB registered pubkey:", pubKeyB);

  // -----------------------------
  // Step 2: Publish an edge
  // -----------------------------
  console.log("\nPublishing edge from deployer -> userB...");
  const enc_pk_to = ethers.utils.toUtf8Bytes("encrypted-pk-to"); 
  const e_under = ethers.utils.toUtf8Bytes("encrypted-ek-under"); 
  const version = 1;

  const tx3 = await hac.publishEdge(USERB_ADDRESS, enc_pk_to, e_under, version);
  await tx3.wait();
  console.log("Edge published successfully!");

  // -----------------------------
  // Step 3: Query the latest edge
  // -----------------------------
  console.log("\nQuerying latest edge deployer -> userB...");
  const latestEdge = await hac.getLatestEdge(deployer.address, USERB_ADDRESS);

  console.log("Latest Edge:");
  console.log("from:", latestEdge.from_);
  console.log("to:", latestEdge.to_);
  console.log("enc_pk_to:", ethers.utils.toUtf8String(latestEdge.enc_pk_to));
  console.log("e_under:", ethers.utils.toUtf8String(latestEdge.e_under));
  console.log("version:", latestEdge.version.toString());
  console.log("timestamp:", latestEdge.timestamp.toString());
  console.log("deleted:", latestEdge.deleted);

  // -----------------------------
  // Step 4: Rotate deployer's key
  // -----------------------------
  console.log("\nRotating deployer's key...");
  const newPubKeyA = ethers.utils.toUtf8Bytes("pubkey-A-rotated");
  const newVersion = 2;

  const tx4 = await hac.rotateKey(newPubKeyA, newVersion);
  await tx4.wait();
  console.log("Key rotated successfully!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

