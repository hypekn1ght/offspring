// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

/// @title Contract to Mint Reveal and Maintain an NFT contract
/// @author Juan Asher
/// @notice All contract is deployed, tested and run on Rinkeby network.
/**
@dev
NFT project owners can deploy this contract to maintain NFT assets including the asset json, pre-reveal hidden image. This contract will also manage the reveal process.
Before the reveal, all images are pointed to a hidden image to protect the NFT assets from being copied or users hand-picking which one to mint.
During the reveal, the meta data, returned by tokenURI function start to point to the real NFT assets. This is the designated function opensea use to link token id to the underlying art.
A random number is drawn using Chainlink VRF oracle to shift the NFT token <> art match so there is no chance for either owner or user to exploit rarity before the reveal.

NFT minters can use this contract to mint NFTs at a cost set by the owner. Owner can mint their NFT for free. Owner can also withdraw the ether paid by users.
 */

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract ScribblesOffspring is ERC721Enumerable, Ownable, ReentrancyGuard {
    using Strings for uint256;

    string baseURI; // this is the URI pointing to the real NFT arts on IPFS
    string public baseExtension = ".json";
    uint256 public cost = 1 ether; // This is the initial price set by the owner to mint each NFT.
    uint256 public maxSupply = 4096; // Total number of NFT that are available to mint.
    uint256 public maxMintAmount = 3; // The max amount of NFTs that can be mint at a time.
    bool public paused = false; // circuit breaker. The owner can pause the contract from executing important functions during emergency.
    bool public revealed = false; // if the NFT project has been revealed.
    string public notRevealedUri; // this is the boilerplate image the token point to before the reveal after the mint.
    bool public whitelistOnly = true;
    address[] public whitelistedAddresses;
    uint256 public parentMintCap = 4;
    uint256 public parentRentCap = 4;
    uint256 public parentLoyaltyPercentage = 10;
    uint256 public ownerBalance;
    mapping(uint256 => uint256) public mintCounter;
    mapping(uint256 => uint256) public rentCounter;
    mapping(uint256 => uint256) public loyaltyLedger; // loyalty ledger for each NFT (in GWEI)
    address public parentContractAddress;
    IERC721Enumerable public parentContract;

    struct OffspringData {
        uint256 ownedParent; // always owned
        uint256 spareParent; // could be owned or rented
        bool rented; // true if parent2 is rented
    }

    mapping(uint256 => OffspringData) public offspringDatabase;

    constructor(
        string memory _name,
        string memory _symbol,
        string memory _initBaseURI,
        string memory _initNotRevealedUri,
        address contractAddress
    ) ERC721(_name, _symbol) {
        parentContract = IERC721Enumerable(contractAddress);
        setBaseURI(_initBaseURI);
        setNotRevealedURI(_initNotRevealedUri);
    }

    // public
    function mint(
        uint256 _mintAmount,
        uint256 _scribblesIndex1,
        uint256 _scribblesIndex2
    ) public payable {
        uint256 supply = totalSupply();
        bool scribbleIndex1IsOwned;
        bool scribbleIndex2IsOwned;
        uint256 totalLoyalty = (msg.value * parentLoyaltyPercentage) / 100;

        require(!paused);
        require(_mintAmount > 0);
        require(_mintAmount <= maxMintAmount);
        require(supply + _mintAmount <= maxSupply);

        // //check if we're in whitelist phase or not, error out accordingly
        // if (whitelistOnly) {
        //     require(isWhitelisted(msg.sender), "Address is not on whitelist");
        // }

        require(
            _scribblesIndex1 != _scribblesIndex2,
            "both parents can't be the same NFT"
        );

        // check if address owns each NFT parent

        scribbleIndex1IsOwned =
            parentContract.ownerOf(_scribblesIndex1) == msg.sender;
        scribbleIndex2IsOwned =
            parentContract.ownerOf(_scribblesIndex2) == msg.sender;

        require(
            scribbleIndex1IsOwned || scribbleIndex2IsOwned,
            "must own at least one of the NFTs to be mixed"
        );

        // check if mint or rent operation is under the cap, if yes, proceed
        if (scribbleIndex1IsOwned) {
            require(
                mintCounter[_scribblesIndex1] + _mintAmount <= parentMintCap,
                "after tx, mint capacity is exceeded for Parent 1"
            );
        } else {
            require(
                rentCounter[_scribblesIndex1] + _mintAmount <= parentRentCap,
                "after tx, rent capacity is exceeded for Parent 1"
            );
        }

        if (scribbleIndex2IsOwned) {
            require(
                mintCounter[_scribblesIndex2] + _mintAmount <= parentMintCap,
                "after tx, mint capacity is exceeded for Parent 2"
            );
        } else {
            require(
                rentCounter[_scribblesIndex2] + _mintAmount <= parentRentCap,
                "after tx, rent capacity is exceeded for Parent 2"
            );
        }

        // mint cost check
        if (msg.sender != owner()) {
            require(
                msg.value >= cost * _mintAmount,
                "Need to attach sufficient funds"
            );
        }
        // mint according to _mintAmount
        for (uint256 i = 1; i <= _mintAmount; i++) {
            _safeMint(msg.sender, supply + i);
            offspringDatabase[supply + i] = OffspringData(
                scribbleIndex1IsOwned ? _scribblesIndex1 : _scribblesIndex2,
                scribbleIndex1IsOwned ? _scribblesIndex2 : _scribblesIndex1,
                !(scribbleIndex1IsOwned && scribbleIndex2IsOwned)
            );
        }

        // set mint/rent counter for first scribble parent
        if (scribbleIndex1IsOwned && scribbleIndex2IsOwned) {
            mintCounter[_scribblesIndex1] += _mintAmount;
            mintCounter[_scribblesIndex2] += _mintAmount;
            ownerBalance += msg.value;
        } else if (scribbleIndex1IsOwned || scribbleIndex2IsOwned) {
            if (scribbleIndex1IsOwned) {
                mintCounter[_scribblesIndex1] += _mintAmount;
                rentCounter[_scribblesIndex2] += _mintAmount;
                loyaltyLedger[_scribblesIndex2] += totalLoyalty;
            } else {
                mintCounter[_scribblesIndex2] += _mintAmount;
                rentCounter[_scribblesIndex1] += _mintAmount;
                loyaltyLedger[_scribblesIndex1] += totalLoyalty;
            }
            ownerBalance += (msg.value - totalLoyalty);
        }
    }

    // this function map the TokenId to the art assets on IPFS. This is the designated way
    function tokenURI(uint256 tokenId)
        public
        view
        virtual
        override
        returns (string memory)
    {
        require(
            _exists(tokenId),
            "ERC721Metadata: URI query for nonexistent token (It's not minted yet)"
        );

        if (revealed == false) {
            return notRevealedUri;
        }

        return
            bytes(baseURI).length > 0
                ? string(
                    abi.encodePacked(baseURI, tokenId.toString(), baseExtension)
                )
                : "";
    }

    //change the status from hidden to reveal. This is a one way function, meaning it can't go from revealed to hidden again.
    function reveal() public onlyOwner {
        revealed = true;
    }

    // Owner can change the minting cost
    function setCost(uint256 _newCost) public onlyOwner {
        cost = _newCost;
    }

    // Owner can change the max amount of NFTs being minted at a time.
    function setmaxMintAmount(uint256 _newmaxMintAmount) public onlyOwner {
        maxMintAmount = _newmaxMintAmount;
    }

    // set the URI of the not revealed art asset.
    function setNotRevealedURI(string memory _notRevealedURI) public onlyOwner {
        notRevealedUri = _notRevealedURI;
    }

    // set the URI of the not revealed art
    function setBaseURI(string memory _newBaseURI) public onlyOwner {
        baseURI = _newBaseURI;
    }

    function setBaseExtension(string memory _newBaseExtension)
        public
        onlyOwner
    {
        baseExtension = _newBaseExtension;
    }

    // Toggle pause
    function pause(bool _state) public onlyOwner {
        paused = _state;
    }

    function whiteListUsers(address[] calldata _users) public onlyOwner {
        delete whitelistedAddresses;
        whitelistedAddresses = _users;
    }

    function isWhitelisted(address _user) public view returns (bool) {
        for (uint256 i; i < whitelistedAddresses.length; i++) {
            if (whitelistedAddresses[i] == _user) {
                return true;
            }
        }
        return false;
    }

    function setRentCap(uint256 _rentCap) public onlyOwner {
        parentRentCap = _rentCap;
    }

    function setMintCap(uint256 _mintCap) public onlyOwner {
        parentMintCap = _mintCap;
    }

    function getMintCounter(uint256 _index) public view returns (uint256) {
        return mintCounter[_index];
    }

    function getRentCounter(uint256 _index) public view returns (uint256) {
        return rentCounter[_index];
    }

    function getParentLoyalty(uint256 _index) public view returns (uint256) {
        return loyaltyLedger[_index];
    }

    function setParentLoyalty(uint256 _loyaltyPercentage) public onlyOwner {
        parentLoyaltyPercentage = _loyaltyPercentage;
    }

    function getData(uint256 tokenID) public returns (uint256, uint256, bool) {
      return (offspringDatabase[tokenID].ownedParent, offspringDatabase[tokenID].spareParent, offspringDatabase[tokenID].rented);
    }

    function setPublicMint() public onlyOwner {
        require(whitelistOnly, "minting is already public!");
        whitelistOnly = false;
    }

    //after the mint, the owner can call this function to collect funds.
    function withdraw() public payable onlyOwner nonReentrant {
        (bool os, ) = payable(owner()).call{value: ownerBalance}("");
        require(os);
        ownerBalance = 0;
    }

    function loyaltyWithdraw(uint256 _index) public payable nonReentrant {
        require(
            parentContract.ownerOf(_index) == msg.sender,
            "message sender doesn't own selected NFT"
        );
        (bool os, ) = payable(msg.sender).call{value: loyaltyLedger[_index]}(
            ""
        );
        require(os);
        loyaltyLedger[_index] = 0;
    }

    function burn(uint256 tokenId) public virtual nonReentrant {
        //solhint-disable-next-line max-line-length
        require(
            _isApprovedOrOwner(_msgSender(), tokenId),
            "ERC721Burnable: caller is not owner nor approved"
        );
        _burn(tokenId);

        OffspringData memory data =  offspringDatabase[tokenId];
        mintCounter[data.ownedParent] -= 1;
        if (data.rented) {
          rentCounter[data.spareParent] -= 1;
        } else {
          mintCounter[data.spareParent] -= 1;
        }
    }
}
