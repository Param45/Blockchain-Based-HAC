# Edge Computing enabled Blockchain Based Hierarchical Access Control System (HBEC)

This repository contains the implementation of a novel **Hybrid Blockchain-based Edge Computing (HBEC)** framework. The project demonstrates a decentralized, dynamic hierarchical access control scheme where computations are performed securely over mutually distrustful edge devices without needing a centralized controller.

## 📖 Abstract
Traditional hierarchical access control systems rely heavily on central authorities, creating single points of failure and trust bottlenecks. By utilizing blockchain technology alongside edge computing, this framework eliminates centralized control. **Blockchain** provides structural transparency and trustless decentralization, while **Edge Computing** ensures that sensitive data stays off-chain and computational overhead (like key derivation and cryptographic operations) is kept low.

## ✨ Key Features
- **Fully Decentralized Architecture**: No central node for key generation, distribution, or hierarchy management.
- **Dynamic Hierarchy Updates**: Supports adding and deleting nodes/edges in a Directed Acyclic Graph (DAG) hierarchy, with built-in mechanisms for forward and backward secrecy.
- **Cryptographic Independence**: Uses ECC-based ElGamal encryption and AES-GCM to securely manage keys across different levels of the hierarchy. Nodes perform their own encryptions/decryptions.
- **Hyperledger Besu & Smart Contracts**: State transitions and access rules are verified and logged onto a distributed ledger utilizing Quorum Byzantine Fault Tolerance (QBFT) consensus.

## 🏗️ System Architecture

### 1. Blockchain Layer (`/Blockchain`)
- Driven by **Hyperledger Besu**.
- Configured with the **QBFT consensus mechanism** to provide immediate transaction finality. 
- Encompasses several initialized validator nodes representing hierarchical roles (e.g., `director`, `prof1`, `prof2`, `stud1`, `stud2`, `stud3c`).
- Acts as the immutable storage for edge labels, public keys, and validation logic.

### 2. Edge Layer & Off-Chain Logic (`/off-chain`)
- Built using **Hardhat**, **Ethers.js**, and **Node.js**.
- Integrates a custom crypto-engine (Python & cryptography libraries) to manage edge-device computations locally.
- Smart contracts govern hierarchy alterations (Adding/Deleting Edges) directly from the command line/scripts without centralized APIs.

## 📁 Repository Structure
```
Blockchain-Based-HAC/
├── Blockchain/              # Hyperledger Besu local network setup and validators
│   ├── genesis.json         # Blockchain custom genesis configuration
│   ├── qbftConfigFile.json  # QBFT consensus parameters
│   └── [node directories]   # Configuration and local state for each simulated node
└── off-chain/               # Smart contracts, edge computations, and deployment scripts 
    ├── contracts/           # Solidity smart contracts for access control 
    ├── scripts/             # Deployment and interaction scripts
    ├── crypto-engine/       # Cryptographic module for key derivation and AES/ECC operations
    ├── hardhat.config.js    # Hardhat Environment Configuration
    └── package.json         # Node.js dependencies
```

## 🛠️ Prerequisites
- **Node.js** (v16+ recommended)
- **Hardhat**
- **Hyperledger Besu** (v25.9.0)
- **Python 3** (v3.12.3) with `cryptography` package
- Ubuntu 24.04 (or environments running WSL/Windows) for executing the network

## 🚀 Setup & Execution

### 1. Start the Blockchain Network
Navigate to the `Blockchain` folder and launch your Hyperledger Besu nodes. Ensure you have properly synced the custom `genesis.json` among the nodes. Each node acts as a validator in the QBFT network.

### 2. Configure the Off-Chain Environment
Install the Node.js dependencies:
```bash
cd off-chain
npm install
```

Ensure your `hardhat.config.js` points to the Local Besu RPC endpoints of your started nodes. 

### 3. Deploy Smart Contracts
You can compile and deploy the required smart contracts using Hardhat:
```bash
npx hardhat compile
npx hardhat run scripts/deploy.js --network [your_network_name]
```

## 🔐 Workflow (Access Control)
Detailed workflow actions—such as Initial Registration, Add Edge, Delete Edge, and Key Derivation—are processed in the `/off-chain` environment. Each edge node computes its secrets locally via the Python crypto-engine. When an operation triggers modifying the graph, an update consists of submitting re-encrypted labels to the blockchain transparently.
