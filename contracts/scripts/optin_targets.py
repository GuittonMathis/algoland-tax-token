#!/usr/bin/env python3
"""
optin_targets.py

Opt-in the Burn, LP, and Rewards accounts to the Dumbly ASA on Algorand.
Each account sends a zero-amount AssetTransferTxn to itself, which enables
it to hold the ASA.

Environment variables (in .env):
  ALGOD_ADDRESS     Algod API endpoint (e.g. https://testnet-api.algonode.cloud)
  ALGOD_TOKEN       Algod API token (may be empty)
  ASSET_ID          Numeric ASA ID for Dumbly
  BURN_MNEMONIC     Mnemonic for the Burn account
  LP_MNEMONIC       Mnemonic for the LP account
  REWARDS_MNEMONIC  Mnemonic for the Rewards account

Usage:
  pip install python-dotenv py-algorand-sdk
  python optin_targets.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
from algosdk.error import AlgodHTTPError

load_dotenv()  # load variables from .env

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: Missing environment variable {name}")
        sys.exit(1)
    return value

def init_client() -> algod.AlgodClient:
    """Initialize the Algod client."""
    address = get_env_var("ALGOD_ADDRESS")
    token   = os.getenv("ALGOD_TOKEN", "")
    try:
        return algod.AlgodClient(token, address)
    except Exception as e:
        print(f"ERROR: Could not connect to Algod: {e}")
        sys.exit(1)

def load_account(env_key: str):
    """
    Load private key and address from the mnemonic stored in env_key.
    Returns (address, private_key).
    """
    mnem = get_env_var(env_key)
    try:
        sk   = mnemonic.to_private_key(mnem)
        addr = account.address_from_private_key(sk)
        return addr, sk
    except Exception as e:
        print(f"ERROR: Invalid mnemonic in {env_key}: {e}")
        sys.exit(1)

def main():
    client = init_client()
    sp     = client.suggested_params()
    asset_id = int(get_env_var("ASSET_ID"))

    # Load each target account
    accounts = [
        ("Burn",    "BURN_MNEMONIC"),
        ("LP",      "LP_MNEMONIC"),
        ("Rewards","REWARDS_MNEMONIC"),
    ]

    for name, key in accounts:
        addr, sk = load_account(key)
        try:
            # Zero-amount transfer to self = opt-in
            txn   = AssetTransferTxn(sender=addr, sp=sp, receiver=addr, amt=0, index=asset_id)
            stxn  = txn.sign(sk)
            txid  = client.send_transaction(stxn)
            wait_for_confirmation(client, txid, 4)
            print(f"✅ Opt-in successful for {name} account ({addr})")
        except AlgodHTTPError as e:
            print(f"⚠️{name} opt-in failed or already done: {e}")

if __name__ == "__main__":
    main()
