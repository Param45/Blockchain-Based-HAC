// agent/listeners/events.js
const HACContract = require("../contracts/hac_full");
const dotenv = require("dotenv");
dotenv.config();

async function listenEvents() {
  console.log("🎧 Starting event listener...");

  // === Initialize all roles ===
  const roles = {
    Director: process.env.DIRECTOR_PRIVATE_KEY,
    Professor1: process.env.PROFESSOR1_PRIVATE_KEY,
    Professor2: process.env.PROFESSOR2_PRIVATE_KEY,
    Student1: process.env.STUDENT1_PRIVATE_KEY,
    Student2: process.env.STUDENT2_PRIVATE_KEY,
    Student3: process.env.STUDENT3_PRIVATE_KEY,
  };

  const agents = {};
  for (const [role, key] of Object.entries(roles)) {
    if (!key) {
      console.warn(`⚠️ Missing private key for ${role} in .env`);
      continue;
    }
    try {
      agents[role] = new HACContract(role, key);
      console.log(`✅ Connected: ${role}`);
    } catch (err) {
      console.error(`❌ Failed to init ${role}:`, err.message);
    }
  }

  console.log("🎯 Listening for contract events...");

  // === Subscribe to events for all roles ===
  Object.entries(agents).forEach(([role, contract]) => {
    // KeyRegistered
    contract.onKeyRegistered((who, pubKey, ts) => {
      console.log(
        `📢 [${role}] KeyRegistered | who=${who} | time=${new Date(ts * 1000).toISOString()}`
      );
    });

    // EdgePublished
    contract.onEdgePublished((from, to, enc_pk_to, e_under, version, ts) => {
      console.log(
        `📢 [${role}] EdgePublished | from=${from} -> to=${to} | v=${version} | t=${new Date(ts * 1000).toISOString()}`
      );
    });

    // EdgeDeleted
    contract.onEdgeDeleted((from, to, version, ts) => {
      console.log(
        `📢 [${role}] EdgeDeleted | from=${from} -> to=${to} | v=${version} | t=${new Date(ts * 1000).toISOString()}`
      );
    });

    // KeyRotated
    contract.onKeyRotated((who, newPubKey, version, ts) => {
      console.log(
        `📢 [${role}] KeyRotated | who=${who} | v=${version} | t=${new Date(ts * 1000).toISOString()}`
      );
    });
  });
}

// Run listener
listenEvents().catch((err) => {
  console.error("❌ Error in listener:", err);
});
