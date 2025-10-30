// agent/transactions/fetchLatestEdge.js
require("dotenv").config();
const fs = require("fs");
const { getProvider, getContract } = require("../contracts/hac");

async function fetchLatestEdge(fromAddr, toAddr, outPath = "crypto-engine/edge_data.json") {
  const provider = getProvider();
  const contract = getContract(provider);

  try {
    const el = await contract.getLatestEdge(fromAddr, toAddr);
    // el = [from, to, enc_pk_to (bytes), e_under (bytes), version, timestamp, deleted]

    // ethers.js returns bytes as hex strings ("0x..."), not Buffers.
    const enc_pk_to = el[2].startsWith("0x") ? el[2].slice(2) : el[2];
    const e_under = el[3].startsWith("0x") ? el[3].slice(2) : el[3];

    const payload = {
      from: el[0],
      to: el[1],
      enc_pk_to_hex: enc_pk_to,
      e_under_hex: e_under,
      version: el[4].toString(),
      timestamp: el[5].toString(),
      deleted: el[6],
    };

    fs.writeFileSync(outPath, JSON.stringify(payload, null, 2));
    console.log("✅ Saved edge to", outPath);
    console.log(payload);
  } catch (e) {
    console.error("❌ Failed to fetch edge:", e);
  }
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node agent/transactions/fetchLatestEdge.js <fromAddr> <toAddr> [outPath]");
    process.exit(1);
  }
  fetchLatestEdge(args[0], args[1], args[2]);
}
