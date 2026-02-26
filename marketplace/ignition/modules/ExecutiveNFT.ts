import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const ExecutiveNFTModule = buildModule("ExecutiveNFTModule", (m) => {
  // This tells Hardhat to deploy the contract named "ExecutiveNFT"
  const nft = m.contract("ExecutiveNFT");

  return { nft };
});

export default ExecutiveNFTModule;