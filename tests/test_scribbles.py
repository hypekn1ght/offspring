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

LOYALTY_PERCENTAGE = 10

def test_deploy(minter1, minter2, minter3, parent, offspring):

    #mint a few parent offspring
    parent._safeMint(minter1.address, 1, {"from": minter1})
    print(f"parent 1 minted by {minter1}")

    parent._safeMint(minter2.address, 2, {"from": minter2})
    print(f"parent 2 minted by {minter2}")

    parent._safeMint(minter3.address, 3, {"from": minter3})
    print(f"parent 3 minted by {minter3}")

    print(f"offspring details : {offspring}")
    # test : initial supply = 0
    assert offspring.totalSupply() == 0
    

def test_ownership(admin, offspring):
    

    # test : shouldn't allow mint since message sender doesn't own either nft
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.mint(1, 1, 2, {"from": admin, "value": Web3.toWei(1, "ether")})


def test_mint_parameters(admin, minter1, minter2, minter3, parent, offspring):
     

    # test : minting should fail with only 0.9 ether
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(0.9, "ether")})
    
    # minter 1 minting 1 owns index 1 renting index 2
    offspring.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(1, "ether")})

    # minter 2 minting 2 owns index 2 renting index 1
    offspring.mint(2, 2, 1, {"from": minter2, "value": Web3.toWei(2, "ether")})

    # minter 3 minting 1 owns index 3 renting index 2
    offspring.mint(1, 3, 2, {"from": minter3, "value": Web3.toWei(1, "ether")})

    # test loyalty
    assert offspring.loyaltyLedger(2) == Web3.toWei(0.2, "ether")
    assert offspring.loyaltyLedger(1) == Web3.toWei(0.2, "ether")
    assert offspring.loyaltyLedger(3) == 0

    # test mint counter
    assert offspring.getMintCounter(1) == 1
    assert offspring.mintCounter(2) == 2
    assert offspring.mintCounter(3) == 1

    # test rent counter
    assert offspring.rentCounter(1) == 2
    assert offspring.rentCounter(2) == 2
    assert offspring.rentCounter(3) == 0

    # test loyalty percentage
    offspring.setParentLoyalty(15, {"from": admin})

    assert offspring.parentLoyaltyPercentage() == 15

    # test loyalty percentage
    offspring.setParentLoyalty(10, {"from": admin})

    assert offspring.parentLoyaltyPercentage() == 10


def test_withdraw(admin, minter1, minter2, offspring):
    
    totalLoyalty = offspring.getParentLoyalty(1) + offspring.getParentLoyalty(2)
    print(f"totalLoyalty: {totalLoyalty}")
    print(f"account: {admin.balance()}")
    print(f"contract: {offspring.balance()}")
    offspring.withdraw({"from": admin})
    print(f"account: {admin.balance()}")
    print(f"contract: {offspring.balance()}")
    assert offspring.balance() == totalLoyalty

    # test loyalty withdrawal
    # test invalid withdrawal based on ownership
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.loyaltyWithdraw(3, {"from": minter1})

    # test valid withdrawal
    preWithdrawBal = minter1.balance()
    loyalty1 = offspring.getParentLoyalty(1)
    contractLoyaltyBalance = offspring.balance()
    offspring.loyaltyWithdraw(1, {"from": minter1})

    # check parent owner balance
    assert minter1.balance() == preWithdrawBal + loyalty1

    # check contract balance
    assert offspring.balance() == contractLoyaltyBalance - loyalty1

    # test emptying contract
    preWithdrawBal = minter2.balance()
    loyalty2 = offspring.getParentLoyalty(2)
    tx = offspring.loyaltyWithdraw(2, {"from": minter2})
    print(f"tx info: {tx.info()}")

    # check parent owner balance
    assert minter2.balance() == preWithdrawBal + loyalty2

    # contract balance should be 0 
    assert offspring.balance() == 0

def test_mint_cost(admin, minter1, offspring):
    # change cost to 2 eth
    offspring.setCost(Web3.toWei(2, "ether"), {"from": admin})
    # test invalid cost
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(1, "ether")})
    # test valid mint @ 2eth
    initialBalance = offspring.balanceOf(minter1)
    offspring.mint(1, 1, 2, {"from": minter1, "value": Web3.toWei(2, "ether")})
    assert offspring.balanceOf(minter1) == initialBalance + 1
    # change cost back to 1
    offspring.setCost(Web3.toWei(1, "ether"), {"from": admin})

def test_caps(minter1, minter3, offspring):

    # test mint cap - should fail since tx would exceed mint cap
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.mint(4, 1, 3, {"from": minter1, "value": Web3.toWei(4, "ether")})

    # test rent cap - should fail since tx would exceed rent cap
    with pytest.raises(exceptions.VirtualMachineError):
        offspring.mint(3, 3, 2, {"from": minter3, "value": Web3.toWei(3, "ether")})

def test_burn(burner1, burner2, burner3, parent, offspring):
    # test mint, both parents owned *INDEX 4 & 5*
    parent._safeMint(burner1.address, 4, {"from": burner1})
    parent._safeMint(burner1.address, 5, {"from": burner1})

    offspring.mint(2, 4, 5, {"from": burner1, "value": Web3.toWei(2, "ether")})

    assert offspring.getMintCounter(4) == 2
    assert offspring.getMintCounter(5) == 2
    assert offspring.totalSupply() == 7

    # burn 
    offspring.burn(7, {"from": burner1})
    assert offspring.totalSupply() == 6

    # check mint and rent tally
    assert offspring.getMintCounter(4) == 1
    assert offspring.getMintCounter(5) == 1

    # test mint parent *INDEX 6* is owned, parent *INDEX 7* is rented 
    parent._safeMint(burner2.address, 6, {"from": burner2})
    parent._safeMint(burner1.address, 7, {"from": burner1})

    offspring.mint(1, 6, 7, {"from": burner2, "value": Web3.toWei(1, "ether")})
    assert offspring.totalSupply() == 7
    assert offspring.getMintCounter(6) == 1
    assert offspring.getRentCounter(7) == 1

    # burn 
    offspring.burn(7, {"from": burner2})
    assert offspring.totalSupply() == 6

    # check mint and rent tally
    assert offspring.getMintCounter(6) == 0
    assert offspring.getRentCounter(7) == 0

    # test mint parent *INDEX 9* is owned, parent *INDEX 8* is rented
    parent._safeMint(burner1.address, 8, {"from": burner1})
    parent._safeMint(burner3.address, 9, {"from": burner3})

    offspring.mint(2, 8, 9, {"from": burner3, "value": Web3.toWei(2, "ether")})
    assert offspring.totalSupply() == 8
    assert offspring.getMintCounter(9) == 2
    assert offspring.getRentCounter(8) == 2

    # burn 
    offspring.burn(7, {"from": burner3})
    assert offspring.totalSupply() == 7

    # check mint and rent tally
    assert offspring.getMintCounter(9) == 1
    assert offspring.getRentCounter(8) == 1
