import pytest

from brownie import (
    ScribblesOffspring, 
    exceptions,
    network, 
    project, 
    ERC721
)

from scripts.helpful_scripts import (
    get_account
)

@pytest.fixture (scope="session")
def admin():
    yield get_account()

@pytest.fixture (scope="session")
def minter1():
    yield get_account(index=1)

@pytest.fixture (scope="session")
def minter2():
    yield get_account(index=2)

@pytest.fixture (scope="session")
def minter3():
    yield get_account(index=3)

@pytest.fixture (scope="session")
def burner1():
    yield get_account(index=4)

@pytest.fixture (scope="session")
def burner2():
    yield get_account(index=5)

@pytest.fixture (scope="session")
def burner3():
    yield get_account(index=6)
    
@pytest.fixture (scope="session")
def parent(admin):
    parent = ERC721.deploy("parent", "SCBP", {"from": admin})
    yield parent

@pytest.fixture (scope="session")
def offspring(admin, parent):
    offspring = ScribblesOffspring.deploy(
        "scribbles offspring", 
        "SCBO", 
        "testing", 
        "testing", 
        parent.address, 
        {"from": admin}
    )
    yield offspring

