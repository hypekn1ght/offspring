// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ScribblesOffspring.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";

contract ArtMarketplace {
    ScribblesOffspring private token;
    IERC721Enumerable private parent;

    struct ItemForSale {
        uint256 id;
        uint256 tokenId;
        address payable seller;
        uint256 price;
        // set to false when listing is initiated, true when listing is cancelled or sold
        bool isConcluded;
        bool isParent;
    }

    ItemForSale[] public itemsForSale;
    mapping(uint256 => bool) public activeScribblesItems; // tokenId => ativo?
    mapping(uint256 => bool) public activeParentItems;

    event itemAddedForSale(
        uint256 id,
        uint256 tokenId,
        uint256 price,
        bool isParent
    );
    event itemSold(uint256 id, address buyer, uint256 price, bool isParent);
    event saleCancelled(uint256 id, address seller, bool isParent);

    constructor(ScribblesOffspring _token, address _parentAddress) {
        token = _token;
        parent = IERC721Enumerable(_parentAddress);
    }

    modifier OnlyItemOwner(uint256 tokenId, bool isParent) {
        if (isParent) {
            require(
                parent.ownerOf(tokenId) == msg.sender,
                "Sender does not own the item"
            );
        } else {
            require(
                token.ownerOf(tokenId) == msg.sender,
                "Sender does not own the item"
            );
        }
        _;
    }

    modifier HasTransferApproval(uint256 tokenId, bool isParent) {
        if (isParent) {
            require(
                parent.getApproved(tokenId) == address(this),
                "Market is not approved"
            );
        } else {
            require(
                token.getApproved(tokenId) == address(this),
                "Market is not approved"
            );
        }

        _;
    }

    modifier ItemExists(uint256 id) {
        require(
            id < itemsForSale.length && itemsForSale[id].id == id,
            "Could not find item"
        );
        _;
    }

    modifier IsForSale(uint256 id) {
        require(!itemsForSale[id].isConcluded, "Item is already sold");
        _;
    }

    function putItemForSale(
        uint256 tokenId,
        uint256 price,
        bool isParent
    )
        external
        OnlyItemOwner(tokenId, isParent)
        HasTransferApproval(tokenId, isParent)
        returns (uint256)
    {
        if (isParent) {
            require(!activeParentItems[tokenId], "Item is already up for sale");
        } else {
            require(
                !activeScribblesItems[tokenId],
                "Item is already up for sale"
            );
        }

        uint256 newItemId = itemsForSale.length;
        itemsForSale.push(
            ItemForSale({
                id: newItemId,
                tokenId: tokenId,
                seller: payable(msg.sender),
                price: price,
                isConcluded: false,
                isParent: isParent
            })
        );
        if (isParent) {
            activeParentItems[tokenId] = true;
        } else {
            activeScribblesItems[tokenId] = true;
        }

        assert(itemsForSale[newItemId].id == newItemId);
        emit itemAddedForSale(newItemId, tokenId, price, isParent);
        return newItemId;
    }

    function cancelListing(uint256 id)
        external
        ItemExists(id)
        IsForSale(id)
        HasTransferApproval(itemsForSale[id].tokenId, itemsForSale[id].isParent)
    {
        require(msg.sender != itemsForSale[id].seller);
        itemsForSale[id].isConcluded = true;
        if (itemsForSale[id].isParent) {
            activeParentItems[itemsForSale[id].tokenId] = false;
        } else {
            activeScribblesItems[itemsForSale[id].tokenId] = false;
        }
        emit saleCancelled(id, msg.sender, itemsForSale[id].isParent);
    }

    function buyItem(uint256 id)
        external
        payable
        ItemExists(id)
        IsForSale(id)
        HasTransferApproval(itemsForSale[id].tokenId, itemsForSale[id].isParent)
    {
        require(msg.value >= itemsForSale[id].price, "Not enough funds sent");
        require(msg.sender != itemsForSale[id].seller);

        itemsForSale[id].isConcluded = true;

        if (itemsForSale[id].isParent) {
            activeParentItems[itemsForSale[id].tokenId] = false;
            parent.safeTransferFrom(
                itemsForSale[id].seller,
                msg.sender,
                itemsForSale[id].tokenId
            );
        } else {
            activeScribblesItems[itemsForSale[id].tokenId] = false;
            token.safeTransferFrom(
                itemsForSale[id].seller,
                msg.sender,
                itemsForSale[id].tokenId
            );
        }

        itemsForSale[id].seller.transfer(msg.value);

        emit itemSold(
            id,
            msg.sender,
            itemsForSale[id].price,
            itemsForSale[id].isParent
        );
    }

    function totalItemsForSale() external view returns (uint256) {
        return itemsForSale.length;
    }
}
