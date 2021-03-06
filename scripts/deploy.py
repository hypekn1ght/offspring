from brownie.network.main import gas_limit
from scripts.helpful_scripts import get_account
from brownie import ScribblesOffspring, network
from web3 import Web3

def main():
    deploy()

def deploy():
    account = get_account()
    scribbles = ScribblesOffspring.deploy(
        "blergy", "BGH", "testing", "testing", "0xDB18774dCa16F1c5C2F7Af640EBA3edb19343D7d", 
        {"from": account, "gas_price": "30 gwei"}
    )
    print(f"scribbles details : {scribbles}")
