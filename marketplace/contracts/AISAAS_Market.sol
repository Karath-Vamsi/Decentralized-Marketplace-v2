// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract AISAAS_Market is Ownable {
    
    struct Agent {
        address developer;      // Who built it
        string name;           // Agent name
        string category;       // e.g., "travel", "writing", "legal"
        string agentCardURI;   // Link to the JSON Agent Card (IPFS or URL)
        uint256 baseFee;       // Price in Wei
        bool isActive;         // Status
    }

    // Mapping of Agent ID (incremental) to Agent details
    mapping(uint256 => Agent) public registry;
    uint256 public totalAgents;

    event AgentRegistered(uint256 indexed agentId, string name, string category);
    event AgentUpdated(uint256 indexed agentId, bool isActive);

    constructor() Ownable(msg.sender) {}

    // 1. Register a new Specialist Agent
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

    // 2. Update Agent Status (for developers to pause their service)
    function toggleAgentStatus(uint256 _agentId) public {
        require(registry[_agentId].developer == msg.sender, "Only developer can edit");
        registry[_agentId].isActive = !registry[_agentId].isActive;
        emit AgentUpdated(_agentId, registry[_agentId].isActive);
    }

    // 3. Get all active agents in a specific category
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
}