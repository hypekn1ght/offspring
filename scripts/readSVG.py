import json
from brownie.network.main import gas_limit
from scripts.helpful_scripts import get_account
from brownie import network, interface, ERC721
from web3 import Web3


def main():
    write()


def write():
    account = get_account()
    parent = ERC721.at("0xDB18774dCa16F1c5C2F7Af640EBA3edb19343D7d")

    svgData = []
    supply = 1023
    i = 0
    while i <= supply:
        svgData.append(parent.tokenURI(i))
        i = i+1
        print(f"index : {i}")
    
    jsonString = json.dumps(svgData)

    jsonFile = open("data.json", "w")
    jsonFile.write(jsonString)
    jsonFile.close()
