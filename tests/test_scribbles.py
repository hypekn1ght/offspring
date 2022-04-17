from scripts.helpful_scripts import (
    get_account,
    LOCAL_ENVIRONMENT
)
from pathlib import Path
from brownie import (
    ScribblesOffspring, 
    exceptions,
    network, 
    project, 
    # config, 
    ERC721
)
from web3 import Web3
import pytest

LOYALTY_PERCENTAGE = 20

def test_deploy():
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
    print(f"scribbles details : {scribbles}")
    # test : initial supply = 0
    assert scribbles.totalSupply() == 0
    

def test_ownership():
    account = get_account()
    parent = ERC721[-1]
    scribbles = ScribblesOffspring[-1]

    # test : shouldn't allow mint since message sender doesn't own either nft
    with pytest.raises(exceptions.VirtualMachineError):
        scribbles.mint(1, 1, 2, {"from": account, "value": Web3.toWei(1, "ether")})


def test_mint_parameters():
    account = get_account()
    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)
    parent = ERC721[-1]
    scribbles = ScribblesOffspring[-1]

    # test : minting should fail with only 0.9 ether
    with pytest.raises(exceptions.VirtualMachineError):
        scribbles.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(0.9, "ether")})
    
    # minter 1 minting 1 owns index 1 renting index 2
    scribbles.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(1, "ether")})

    # minter 2 minting 2 owns index 2 renting index 1
    scribbles.mint(2, 2, 1, {"from": minter2, "value": Web3.toWei(2, "ether")})

    # minter 3 minting 1 owns index 3 renting index 2
    scribbles.mint(1, 3, 2, {"from": minter3, "value": Web3.toWei(1, "ether")})

    # test loyalty
    assert scribbles.loyaltyLedger(2) == Web3.toWei(0.2, "ether")
    assert scribbles.loyaltyLedger(1) == Web3.toWei(0.2, "ether")
    assert scribbles.loyaltyLedger(3) == 0

    # test mint counter
    assert scribbles.mintCounter(1) == 1
    assert scribbles.getMintCounter(1) == 1
    assert scribbles.mintCounter(2) == 2
    assert scribbles.mintCounter(3) == 1

    # test rent counter
    assert scribbles.rentCounter(1) == 2
    assert scribbles.rentCounter(2) == 2
    assert scribbles.rentCounter(3) == 0

    # test loyalty percentage
    scribbles.setParentLoyalty(10, {"from": account})

    assert scribbles.parentLoyaltyPercentage() == 10

    # test loyalty percentage
    scribbles.setParentLoyalty(20, {"from": account})

    assert scribbles.parentLoyaltyPercentage() == 20



def test_caps():
    minter1 = get_account(index=1)
    minter2 = get_account(index=2)
    minter3 = get_account(index=3)

    scribbles = ScribblesOffspring[-1]

    # test mint cap - should fail since tx would exceed mint cap
    with pytest.raises(exceptions.VirtualMachineError):
        scribbles.mint(4, 1, 3, {"from": minter1, "value": Web3.toWei(4, "ether")})

    # test rent cap - should fail since tx would exceed rent cap
    with pytest.raises(exceptions.VirtualMachineError):
        scribbles.mint(3, 3, 2, {"from": minter3, "value": Web3.toWei(3, "ether")})
