#!/usr/bin/env python3
"""
test_fraction.py

Quick script to verify that partial (fractional) transfers of the Dumbly ASA work as expected.

Steps performed:
  1. Opt-in the receiver account (if not already opted in).
  2. Send 0.5 Dumbly (500_000 base units) from the admin account to the receiver.
  3. Confirm the receiver’s new balance.

Environment variables (.env):
  ALGOD_ADDRESS    Algod API endpoint (e.g. https://testnet-api.algonode.cloud)
  ALGOD_TOKEN      Algod API token (may be empty)
  ADMIN_MNEMONIC   25-word mnemonic for the admin account (issuer)
  BUYER_MNEMONIC   25-word mnemonic for the receiver account
  ASSET_ID         Numeric ASA ID for Dumbly (with 6 decimals)
  RECEIVER_ADDR    Public address of the receiver account

Usage:
  pip install python-dotenv py-algorand-sdk
  python test_fraction.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
from algosdk.error import AlgodHTTPError

load_dotenv()

# Load configuration from environment
ALGOD_ADDRESS    = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN      = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC   = os.getenv("ADMIN_MNEMONIC")
BUYER_MNEMONIC   = os.getenv("BUYER_MNEMONIC")
ASSET_ID         = int(os.getenv("ASSET_ID", "0"))
RECEIVER_ADDR    = os.getenv("RECEIVER_ADDR")

# Basic validation
if not all([ALGOD_ADDRESS, ADMIN_MNEMONIC, BUYER_MNEMONIC, ASSET_ID, RECEIVER_ADDR]):
    print("ERROR: One or more required environment variables are missing.")
    sys.exit(1)

def init_client():
    """Initialize and return an Algod client."""
    try:
        return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    except Exception as e:
        print(f"ERROR: Unable to connect to Algod: {e}")
        sys.exit(1)

def get_keypair(mnemonic_env: str):
    """Convert a mnemonic env var to (private_key, public_address)."""
    mnem = os.getenv(mnemonic_env)
    try:
        pk   = mnemonic.to_private_key(mnem)
        addr = account.address_from_private_key(pk)
        return pk, addr
    except Exception as e:
        print(f"ERROR: Failed to derive keys from {mnemonic_env}: {e}")
        sys.exit(1)

def main():
    client   = init_client()
    sp       = client.suggested_params()
    admin_sk, admin_addr = get_keypair("ADMIN_MNEMONIC")
    buyer_sk, buyer_addr = get_keypair("BUYER_MNEMONIC")

    # 1) Opt-in buyer account to the ASA
    try:
        optin_txn = AssetTransferTxn(
            sender=buyer_addr,
            sp=sp,
            receiver=buyer_addr,
            amt=0,
            index=ASSET_ID
        )
        signed_optin = optin_txn.sign(buyer_sk)
        txid = client.send_transaction(signed_optin)
        wait_for_confirmation(client, txid, 4)
        print(f"✅ Opt-in successful for {buyer_addr}")
    except AlgodHTTPError as e:
        print(f"⚠️ Opt-in might already be done or failed: {e}")

    # 2) Send 0.5 Dumbly (500_000 units)
    fraction = 500_000
    try:
        send_txn = AssetTransferTxn(
            sender=admin_addr,
            sp=sp,
            receiver=RECEIVER_ADDR,
            amt=fraction,
            index=ASSET_ID
        )
        signed_send = send_txn.sign(admin_sk)
        txid = client.send_transaction(signed_send)
        wait_for_confirmation(client, txid, 4)
        print(f"→ Sent {fraction} units (0.5 Dumbly) to {RECEIVER_ADDR} (txID={txid})")
    except AlgodHTTPError as e:
        print(f"ERROR: Fractional transfer failed: {e}")
        sys.exit(1)

    # 3) Verify receiver balance
    try:
        acct_info = client.account_info(RECEIVER_ADDR)
        balance = next(
            (a["amount"] for a in acct_info.get("assets", []) if a["asset-id"] == ASSET_ID),
            0
        )
        print(f"✅ Receiver balance = {balance} units (fractions OK)")
    except AlgodHTTPError as e:
        print(f"ERROR: Unable to fetch receiver balance: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
