from brownie import (
    network, 
    config, 
    accounts, 
    Contract
)

DECIMALS = 8
STARTING_PRICE = 200000000000
FORKED_ENVIRONMENT = ["mainnet-for-dev", "harmony-fork"]
LOCAL_ENVIRONMENT = ["development"]

def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id: 
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_ENVIRONMENT 
        or network.show_active() in FORKED_ENVIRONMENT
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])

# contract_to_mock = {
#     "eth_price_feed": MockV3Aggregator, 
#     "vrf_coordinator": VRFCoordinatorMock,
#     "link_token": LinkToken
# }

# def get_contract(contract_name):
#     """

#     """
#     contract_type = contract_to_mock[contract_name]
#     if network.show_active() in LOCAL_ENVIRONMENT:
#         if len(contract_type) <=0:
#             deploy_mock()
#         contract = contract_type[-1]
#     else: 
#         contract_address = config["networks"][network.show_active()][contract_name]
#         contract = Contract.from_abi(
#             contract_type._name, contract_address, contract_type.abi
#         )
#     return contract

# def deploy_mock(decimals=DECIMALS, initial_value = STARTING_PRICE):
#     if len(MockV3Aggregator) >= 0:
#         print(f"the active network is {network.show_active()}")
#         print("Deploying mocks....")
#         account = get_account()
#         MockV3Aggregator.deploy(
#             decimals, initial_value, {"from": account}
#         )
#         link_token = LinkToken.deploy({"from": account})
#         VRFCoordinatorMock.deploy(link_token.address, {"from": account})
#         print("Mock deployed") 
    
# def fund_with_link(
#     contract_address, account=None, link_token=None, amount=100000000000000000
# ):
#     account = account if account else get_account()
#     link_token = link_token if link_token else get_contract("link_token")
#     tx = link_token.transfer(contract_address, amount, {"from": account})
#     # link_contract = interface.LinkTokenInterface(link_token.address)
#     # tx = link_contract.transfer(contract_address, amount, {"from": account})
#     tx.wait(1)
#     print("Fund contract!")
#     return tx