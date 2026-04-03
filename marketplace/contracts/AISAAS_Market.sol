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
        uint256 totalStars;    // Sum of all stars given
        uint256 jobsCompleted; // Total number of ratings received
    }

    enum JobStatus { Locked, Released, Refunded }

    struct Job {
        uint256 id;
        uint256 agentId;       // NEW: Directly links job to the specific Agent ID
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
    event ReputationUpdated(uint256 indexed agentId, uint256 newAverageRating, uint256 totalJobs);

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
            isActive: true,
            totalStars: 0,
            jobsCompleted: 0
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

    // --- Escrow & Reputation Functions ---

    // 1. Executive locks funds and creates an indexed job
    function createJob(uint256 _agentId) public payable returns (uint256) {
        Agent storage agent = registry[_agentId];
        require(agent.isActive, "Agent not active");
        require(msg.value >= agent.baseFee, "Insufficient payment");

        totalJobs++;
        jobs[totalJobs] = Job({
            id: totalJobs,
            agentId: _agentId, // Storing Agent ID for accurate reputation
            executive: msg.sender,
            worker: agent.developer,
            amount: msg.value,
            status: JobStatus.Locked
        });

        emit JobCreated(totalJobs, msg.sender, agent.developer, msg.value);
        return totalJobs;
    }

    // 2. Optimized: Direct credit to the specific Agent ID
    function releasePaymentWithRating(uint256 _jobId, uint256 _rating) public {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.Locked, "Job already settled");
        require(msg.sender == job.executive, "Only Executive can release");
        require(_rating >= 1 && _rating <= 5, "Rating must be 1-5");

        // Targeted Reputation Update
        uint256 targetId = job.agentId;
        registry[targetId].totalStars += _rating;
        registry[targetId].jobsCompleted += 1;
        
        // Scaled average (e.g. 4.5 is stored as 45)
        uint256 avg = (registry[targetId].totalStars * 10) / registry[targetId].jobsCompleted; 
        emit ReputationUpdated(targetId, avg, registry[targetId].jobsCompleted);

        // Finalize Transaction
        job.status = JobStatus.Released;
        (bool success, ) = payable(job.worker).call{value: job.amount}("");
        require(success, "Transfer failed");

        emit PaymentReleased(_jobId);
    }

    // Fallback: Release without rating
    function releasePayment(uint256 _jobId) public {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.Locked, "Job not in locked state");
        require(msg.sender == job.executive, "Only Executive can release");

        job.status = JobStatus.Released;
        (bool success, ) = payable(job.worker).call{value: job.amount}("");
        require(success, "Transfer failed");

        emit PaymentReleased(_jobId);
    }
}