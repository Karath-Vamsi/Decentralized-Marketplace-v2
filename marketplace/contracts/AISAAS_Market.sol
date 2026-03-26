// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract AISAAS_Market is Ownable {
    
    // --- Data Structures ---

    struct Agent {
        address developer;      // Who built it
        string name;           // Agent name
        string category;       // e.g., "travel", "writing", "legal"
        string agentCardURI;   // Link to the JSON Agent Card (IPFS or URL)
        uint256 baseFee;       // Price in Wei
        bool isActive;         // Status
    }

    enum JobStatus { Locked, Released, Refunded }

    struct Job {
        uint256 id;
        address executive;
        address worker;
        uint256 amount;
        JobStatus status;
    }

    // --- State Variables ---

    mapping(uint256 => Agent) public registry;
    uint256 public totalAgents;

    mapping(uint256 => Job) public jobs;
    uint256 public totalJobs;

    // --- Events ---

    event AgentRegistered(uint256 indexed agentId, string name, string category);
    event AgentUpdated(uint256 indexed agentId, bool isActive);
    event JobCreated(uint256 indexed jobId, address indexed executive, address indexed worker, uint256 amount);
    event PaymentReleased(uint256 indexed jobId);

    constructor() Ownable(msg.sender) {}

    // --- Agent Management Functions ---

    function registerAgent(
        string memory _name,
        string memory _category,
        string memory _cardURI,
        uint256 _baseFee
    ) public {
        totalAgents++;
        registry[totalAgents] = Agent({
            developer: msg.sender,
            name: _name,
            category: _category,
            agentCardURI: _cardURI,
            baseFee: _baseFee,
            isActive: true
        });

        emit AgentRegistered(totalAgents, _name, _category);
    }

    function toggleAgentStatus(uint256 _agentId) public {
        require(registry[_agentId].developer == msg.sender, "Only developer can edit");
        registry[_agentId].isActive = !registry[_agentId].isActive;
        emit AgentUpdated(_agentId, registry[_agentId].isActive);
    }

    function getAgentsByCategory(string memory _category) public view returns (uint256[] memory) {
        uint256 count = 0;
        for (uint256 i = 1; i <= totalAgents; i++) {
            if (keccak256(abi.encodePacked(registry[i].category)) == keccak256(abi.encodePacked(_category)) && registry[i].isActive) {
                count++;
            }
        }

        uint256[] memory result = new uint256[](count);
        uint256 index = 0;
        for (uint256 i = 1; i <= totalAgents; i++) {
            if (keccak256(abi.encodePacked(registry[i].category)) == keccak256(abi.encodePacked(_category)) && registry[i].isActive) {
                result[index] = i;
                index++;
            }
        }
        return result;
    }

    // --- Phase 4: Escrow & Payment Functions ---

    // 1. Executive locks funds here
    function createJob(uint256 _agentId) public payable returns (uint256) {
        Agent storage agent = registry[_agentId];
        require(agent.isActive, "Agent not active");
        require(msg.value >= agent.baseFee, "Insufficient payment");

        totalJobs++;
        jobs[totalJobs] = Job({
            id: totalJobs,
            executive: msg.sender,
            worker: agent.developer,
            amount: msg.value,
            status: JobStatus.Locked
        });

        emit JobCreated(totalJobs, msg.sender, agent.developer, msg.value);
        return totalJobs;
    }

    // 2. User releases payment from Dashboard
    function releasePayment(uint256 _jobId) public {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.Locked, "Job not in locked state");
        // Ensure only the executive/owner of the job can release it
        require(msg.sender == job.executive, "Only Executive can release");

        job.status = JobStatus.Released;
        
        // Transfer the locked ETH to the worker
        (bool success, ) = payable(job.worker).call{value: job.amount}("");
        require(success, "Transfer failed");

        emit PaymentReleased(_jobId);
    }
}