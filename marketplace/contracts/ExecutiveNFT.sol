// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ExecutiveNFT is ERC721, Ownable {
    uint256 private _nextTokenId;

    // Passing msg.sender to Ownable sets YOU as the admin
    constructor() ERC721("AISAAS Sovereign Executive", "ASE") Ownable(msg.sender) {}

    function mintTwin() public {
        uint256 tokenId = _nextTokenId++;
        _safeMint(msg.sender, tokenId);
    }

    function hasActiveTwin(address user) public view returns (bool) {
        return balanceOf(user) > 0;
    }
}