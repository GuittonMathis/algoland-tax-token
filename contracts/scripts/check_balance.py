#!/usr/bin/env python3
"""
check_balance.py

Reads and prints the balance of the "Dumbly" ASA held by the Treasury account on Algorand.

Environment Variables (.env):
  ALGOD_ADDRESS     URL of the Algod API (e.g., https://testnet-api.algonode.cloud)
  ALGOD_TOKEN       API token (may be empty)
  TREASURY_MNEMONIC Mnemonic of the Treasury account
  ASSET_ID          Numeric ASA ID for "Dumbly"

Usage:
  pip install python-dotenv algosdk
  python check_balance.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.error import AlgodHTTPError

# Load .env variables into environment
load_dotenv()

def get_env_var(name: str) -> str:
    """
    Retrieve an environment variable or exit if it's missing.
    """
    value = os.getenv(name)
    if not value:
        print(f"ERROR: Missing environment variable: {name}")
        sys.exit(1)
    return value

def init_algod_client() -> algod.AlgodClient:
    """
    Initialize and return an Algod client using environment settings.
    """
    address = get_env_var("ALGOD_ADDRESS")
    token   = os.getenv("ALGOD_TOKEN", "")  # allow empty token
    try:
        return algod.AlgodClient(token, address)
    except Exception as e:
        print(f"ERROR: Failed to connect to Algod: {e}")
        sys.exit(1)

def get_treasury_address() -> str:
    """
    Convert the Treasury account's mnemonic into its public address.
    """
    mnem = get_env_var("TREASURY_MNEMONIC")
    try:
        private_key = mnemonic.to_private_key(mnem)
        return account.address_from_private_key(private_key)
    except Exception as e:
        print(f"ERROR: Failed to convert mnemonic to address: {e}")
        sys.exit(1)

def fetch_asset_balance(client: algod.AlgodClient, address: str, asset_id: int) -> int:
    """
    Return the balance of the given asset_id for the specified address.
    Returns 0 if the address has not opted in or the asset is not found.
    """
    try:
        info = client.account_info(address)
    except AlgodHTTPError as e:
        print(f"ERROR: HTTP error fetching account info: {e}")
        sys.exit(1)

    for asset in info.get("assets", []):
        if asset.get("asset-id") == asset_id:
            return asset.get("amount", 0)
    return 0

def main():
    # 1) Initialize client and parameters
    client       = init_algod_client()
    treasury_addr = get_treasury_address()
    asset_id     = int(get_env_var("ASSET_ID"))

    # 2) Fetch balance
    balance = fetch_asset_balance(client, treasury_addr, asset_id)

    # 3) Display result
    print(f"Treasury balance for ASA {asset_id} ({treasury_addr}): {balance} Dumbly")

if __name__ == "__main__":
    main()
