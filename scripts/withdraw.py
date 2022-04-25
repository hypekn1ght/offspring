from brownie.network.main import gas_limit
from scripts.helpful_scripts import get_account
from brownie import ScribblesOffspring, network
from web3 import Web3

def main():
    withdraw()

def withdraw():
    account = get_account()
    scribbles = ScribblesOffspring.at("0x11c464f746D2F84023C8488D2b57473925FA7A07")
    scribbles.withdraw({ "from": account, "gas_price": "30 gwei" })
    print(f"scribbles details : {scribbles}")
