# AISAAS 2.0: System Startup & Deployment Guide

This document outlines the sequential process to initialize the **AISAAS 2.0** ecosystem. Follow these steps in order to ensure the local blockchain, AI models, and agent infrastructure communicate correctly.

-----

## Phase 1: Core Infrastructure

*The "Brain" and the "Ledger" must be active before any other services can connect.*

### 1\. Launch the Local LLM (The Brain)

Navigate to the models folder and start the Llamafile server. This provides the intelligence for your Digital Twin.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\sovereign_executive\models"
.\Llama-3.2-3B-Instruct-Q6_K.llamafile.exe --server --host 127.0.0.1 --port 8090 --nobrowser
```

> **Note:** We are using port **8090** to avoid conflicts. Keep this terminal open.

### 2\. Start the Local Blockchain (The Ledger)

Open a new terminal to host the local Ethereum network where your contracts will live.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\marketplace"
npx hardhat node
```

> **Warning:** Restarting this node wipes all previous deployment data. You will need to redeploy contracts and reset your MetaMask account (clear activity tab) if the node is restarted.

-----

## Phase 2: Smart Contract Deployment

*Deploying the "Rules of the Game" to the local network.*

### 3\. Deploy the Marketplace Contract

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\marketplace"
npx hardhat run scripts/deploy_market.ts --network localhost
```

  * **Action Required:** Copy the resulting address and update `MARKETPLACE_ADDRESS` in your `.env` file.

### 4\. Deploy the Executive NFT Contract

```powershell
npx hardhat ignition deploy ./ignition/modules/ExecutiveNFT.ts --network localhost
```

  * **Action Required:** Copy the address for `ExecutiveNFTModule#ExecutiveNFT` and update `CONTRACT_ADDRESS` in your `.env` file.

-----

## Phase 3: Identity & Core Logic

*Establishing your presence as a "Sovereign Executive" in the system.*

### 5\. Mint your Executive Identity

This grants your wallet the necessary NFT to bypass the Gatekeeper.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2"
python mint_nft.py
```

### 6\. Start the Sovereign Executive Server

This is the main Python backend that orchestrates RAG and Agent-to-Agent (A2A) calls.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\sovereign_executive\src"
python .\server.py
```

### 7\. Run the Gatekeeper Test

Verify that the backend correctly recognizes your NFT and denies unauthorized wallets.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2"
python .\test_gatekeeper.py
```

-----

## Phase 4: Populating the Marketplace

*Registering specialized worker agents to handle external tasks.*

### 8\. Register Specialized Agents

Run the registration script for each core agent category.

```powershell
# Example for Crypto Agent
cd "AISAAS 2.0\Decentralized-Marketplace-v2\marketplace\agents\crypto_agent"
python .\register_crypto.py

# Repeat the process for:
# - Security Agent
# - Travel Agent
# - Humanizer Agent
```

### 9\. Seed Shadow Agents

Populate the marketplace with simulated agents to test discovery and variety.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\marketplace\scripts"
python .\seed_marketplace.py
```

### 10\. Start Worker Agent Servers

Each specialized agent needs its own server running to listen for tasks from the Sovereign Executive.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\marketplace\agents"
python <agent_name>/server.py
```

-----

## Phase 5: The User Interface

### 11\. Launch the Next.js Dashboard

Finally, start the frontend to interact with your Digital Twin through the browser.

```powershell
cd "AISAAS 2.0\Decentralized-Marketplace-v2\dashboard"
npm run dev
```

  * **URL:** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000)

-----
