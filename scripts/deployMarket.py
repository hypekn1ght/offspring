from brownie.network.main import gas_limit
from scripts.helpful_scripts import get_account
from brownie import ArtMarketplace, ScribblesOffspring, network, Contract
from web3 import Web3

def main():
    deploy()

def deploy():
    account = get_account()
    scribbles = ScribblesOffspring.at("0x1E03ca2D54682ecdE845e5385f5AB8E0E62343C9")


    marketplace = ArtMarketplace.deploy(
        scribbles, 
        "0xDB18774dCa16F1c5C2F7Af640EBA3edb19343D7d",
        {"from": account, "gas_price": "35 gwei"}
    )

    print(f"market place address : {marketplace}")