#!/usr/bin/env python3
"""
check_targets_balance.py

Fetches and displays the ASA balance for the Burn, LP, and Rewards accounts.

This helps verify that each target account holds the correct amount of the
configured Algorand Standard Asset (ASA).

Environment variables (.env required):
  ALGOD_ADDRESS   Algod API endpoint (e.g. https://testnet-api.algonode.cloud)
  ALGOD_TOKEN     Algod API token (may be empty)
  ASSET_ID        Numeric ID of the ASA (Dumbly token)
  BURN_ADDR       Address of the Burn account
  LP_ADDR         Address of the LP account
  REWARDS_ADDR    Address of the Rewards account

Usage:
  pip install python-dotenv py-algorand-sdk
  python check_targets_balance.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk.error import AlgodHTTPError

# Load environment settings
load_dotenv()

def get_env_var(name: str) -> str:
    """Return the value of the environment variable or exit if missing."""
    val = os.getenv(name)
    if not val:
        print(f"ERROR: Missing environment variable: {name}")
        sys.exit(1)
    return val

def init_algod_client() -> algod.AlgodClient:
    """Initialize and return the Algod client."""
    address = get_env_var("ALGOD_ADDRESS")
    token   = os.getenv("ALGOD_TOKEN", "")
    try:
        return algod.AlgodClient(token, address)
    except Exception as e:
        print(f"ERROR: Could not connect to Algod: {e}")
        sys.exit(1)

def fetch_asset_balance(client: algod.AlgodClient, address: str, asset_id: int) -> int:
    """
    Return the ASA balance for the given account address.
    Returns 0 if the account has not opted in or holds no tokens.
    """
    try:
        acct_info = client.account_info(address)
    except AlgodHTTPError as e:
        print(f"ERROR: Failed to fetch account info for {address}: {e}")
        return 0

    for asset in acct_info.get("assets", []):
        if asset.get("asset-id") == asset_id:
            return asset.get("amount", 0)
    return 0

def main():
    # Initialize client and read config
    client    = init_algod_client()
    asset_id  = int(get_env_var("ASSET_ID"))
    targets = {
        "Burn address":    get_env_var("BURN_ADDR"),
        "LP address":      get_env_var("LP_ADDR"),
        "Rewards address": get_env_var("REWARDS_ADDR"),
    }

    print(f"=== Balances for ASA {asset_id} ===")
    for name, addr in targets.items():
        bal = fetch_asset_balance(client, addr, asset_id)
        print(f"{name} ({addr}): {bal}")

if __name__ == "__main__":
    main()
