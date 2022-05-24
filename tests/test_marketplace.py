from scripts.helpful_scripts import (
    get_account,
    LOCAL_ENVIRONMENT
)
from pathlib import Path
from brownie import (
    ScribblesOffspring, 
    ArtMarketplace,
    exceptions,
    network, 
    project, 
    # config, 
    ERC721
)
from web3 import Web3
import pytest

LOYALTY_PERCENTAGE = 10

def test_setup():
    account = get_account()
    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)

    #deploy parent contract
    parent = ERC721.deploy("parent", "SCBP", {"from": account})
    print(f"parent details : {parent}")

    #mint a few parent scribbles
    parent._safeMint(minter1.address, 1, {"from": minter1})
    print(f"parent 1 minted by {minter1}")

    parent._safeMint(minter2.address, 2, {"from": minter2})
    print(f"parent 2 minted by {minter2}")

    parent._safeMint(minter3.address, 3, {"from": minter3})
    print(f"parent 3 minted by {minter3}")


    #deploy offspring contract with parent contract address
    scribbles = ScribblesOffspring.deploy(
        "scribbles offspring", 
        "SCBO", 
        "testing", 
        "testing", 
        parent.address, 
        {"from": account}
    )
    
    # minter 1 minting 1 owns index 1 renting index 2
    scribbles.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(1, "ether")})

    # minter 2 minting 2 owns index 2 renting index 1
    scribbles.mint(2, 2, 1, {"from": minter2, "value": Web3.toWei(2, "ether")})

    # minter 3 minting 1 owns index 3 renting index 2
    scribbles.mint(1, 3, 2, {"from": minter3, "value": Web3.toWei(1, "ether")})

    marketplace = ArtMarketplace.deploy(
        scribbles,
        parent.address,
        {"from": account}
    )

    print(f"marketplace address : {marketplace}")

def test_selling():
    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)

    scribbles = ScribblesOffspring[-1]
    marketplace = ArtMarketplace[-1]
    parent = ERC721[-1]

    # test selling parent without approval
    with pytest.raises(exceptions.VirtualMachineError):
        marketplace.putItemForSale(1, Web3.toWei(1, "ether"), True, {"from": minter1})

    scribbles.approve(marketplace, 1, {"from": minter1})
    parent.approve(marketplace, 1, {"from": minter1})

    # test selling parent from wrong account
    with pytest.raises(exceptions.VirtualMachineError):
        marketplace.putItemForSale(1, Web3.toWei(1, "ether"), True, {"from": minter2})
    
    # test selling offspring from wrong account
    with pytest.raises(exceptions.VirtualMachineError):
        marketplace.putItemForSale(1, Web3.toWei(1, "ether"), False, {"from": minter2})

    marketplace.putItemForSale(1, Web3.toWei(1, "ether"), True, {"from": minter1})
    marketplace.putItemForSale(1, Web3.toWei(1, "ether"), False, {"from": minter1})

    assert marketplace.totalItemsForSale() == 2

    scribbles.approve(marketplace, 4, {"from": minter3})
    parent.approve(marketplace, 3, {"from": minter3})

def test_buying():
    
    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)

    scribbles = ScribblesOffspring[-1]
    marketplace = ArtMarketplace[-1]
    parent = ERC721[-1]

    #test buying unlisted item
    with pytest.raises(exceptions.VirtualMachineError):
        marketplace.buyItem(2, {"from": minter3, "value": Web3.toWei(1, "ether")})
    
    #test buying with inadequate amount
    with pytest.raises(exceptions.VirtualMachineError):
        marketplace.buyItem(0, {"from": minter2, "value": Web3.toWei(0.5, "ether")})

    #test buying parent
    assert parent.balanceOf(minter2) == 1

    marketplace.buyItem(0, {"from": minter2, "value": Web3.toWei(1, "ether")})

    assert parent.balanceOf(minter2) == 2

    #test buying scribbles
    assert scribbles.balanceOf(minter2) == 2

    marketplace.buyItem(1, {"from": minter2, "value": Web3.toWei(1, "ether")})

    assert scribbles.balanceOf(minter2) == 3

def test_cancel():

    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)

    scribbles = ScribblesOffspring[-1]
    marketplace = ArtMarketplace[-1]
    parent = ERC721[-1]

    # putting item for sale on index 2
    parent.approve(marketplace, 3, {"from": minter3})
    marketplace.putItemForSale(3, Web3.toWei(1, "ether"), True, {"from": minter3})

    # putting item for sale on index 3
    scribbles.approve(marketplace, 4, {"from": minter3})
    marketplace.putItemForSale(4, Web3.toWei(1, "ether"), False, {"from": minter3})

    assert marketplace.totalItemsForSale() == 4
    assert marketplace.listingConcluded(2) is False

    marketplace.cancelListing(2, {"from": minter3})

    assert marketplace.listingConcluded(2) is True

    marketplace.putItemForSale(3, Web3.toWei(1, "ether"), True, {"from": minter3})













