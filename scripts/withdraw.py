from brownie.network.main import gas_limit
from scripts.helpful_scripts import get_account
from brownie import ScribblesOffspring, network
from web3 import Web3

def main():
    withdraw()

def withdraw():
    account = get_account()
    scribbles = ScribblesOffspring[-1]
    scribbles.withdraw({ "from": account, "gas_price": "30 gwei" })
    print(f"scribbles details : {scribbles}")
