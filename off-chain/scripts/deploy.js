// scripts/deploy.js
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  const balance = await deployer.getBalance();
  console.log("Deployer balance:", balance.toString());

  const HAC = await ethers.getContractFactory("HierarchicalAccessControl");
  const hac = await HAC.deploy();
  console.log("Transaction hash:", hac.deployTransaction.hash);

  await hac.deployed();
  console.log("HierarchicalAccessControl deployed at:", hac.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

