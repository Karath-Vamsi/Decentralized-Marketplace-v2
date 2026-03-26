import { network } from "hardhat";

async function main() {
  console.log(" Initializing AISAAS Marketplace Deployment...");

  // In Hardhat 3, we explicitly connect to the network to get ethers
  // This 'connection' object contains the initialized ethers plugin
  const connection = await (network as any).connect();
  const { ethers } = connection;

  if (!ethers) {
    throw new Error(" Ethers not found on the connection. Ensure hardhat-toolbox-mocha-ethers is working.");
  }

  // 1. Get the signer (Account #0)
  const [deployer] = await ethers.getSigners();
  console.log(" Deploying with account:", deployer.address);

  // 2. Get the Contract Factory
  const Market = await ethers.getContractFactory("AISAAS_Market");
  
  // 3. Deploy
  const market = await Market.deploy();

  console.log(" Waiting for deployment confirmation...");
  await market.waitForDeployment();

  const marketAddress = await market.getAddress();
  
  console.log("--------------------------------------------------");
  console.log(" Marketplace successfully deployed to:", marketAddress);
  console.log("--------------------------------------------------");
  console.log(" Copy this address to your .env as MARKETPLACE_ADDRESS");
}

main().catch((error) => {
  console.error(" Deployment failed:", error);
  process.exitCode = 1;
});