# check_balance.py
from dotenv import load_dotenv
load_dotenv()

import os
from algosdk import mnemonic, account
from algosdk.v2client import algod

# Initialisation
client        = algod.AlgodClient(os.getenv("ALGOD_TOKEN",""), os.getenv("ALGOD_ADDRESS"))
treasury_sk   = mnemonic.to_private_key(os.getenv("TREASURY_MNEMONIC"))
treasury_addr = account.address_from_private_key(treasury_sk)

# Lecture du compte
acct = client.account_info(treasury_addr)
bal = next(
    (a["amount"] for a in acct.get("assets", []) if a["asset-id"] == int(os.getenv("ASSET_ID"))),
    0
)
print("Solde treasury =", bal, "Dumbly")
