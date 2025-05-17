#!/usr/bin/env python3
"""
distribute.py

Evenly splits the entire Treasury’s Dumbly balance into three parts:
  - Burn address
  - Rewards address
  - LP address

This script groups the three AssetTransfer transactions atomically,
so they either all succeed or all fail together.

Dependencies:
  pip install py-algorand-sdk

Usage:
  python distribute.py
"""

from dotenv import load_dotenv
import os
import sys

from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, calculate_group_id, wait_for_confirmation

# Load environment variables from .env
load_dotenv()

# Algod network settings
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.4160.nodely.dev")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")

# Treasury account mnemonic (holds the funds to distribute)
TREASURY_MNEMONIC = os.getenv("TREASURY_MNEMONIC")
if not TREASURY_MNEMONIC:
    print("ERROR: TREASURY_MNEMONIC not set in .env")
    sys.exit(1)

# ASA ID of the "Dumbly" token
ASSET_ID = int(os.getenv("ASSET_ID", 0))
if ASSET_ID == 0:
    print("ERROR: ASSET_ID not set or invalid in .env")
    sys.exit(1)

# Destination addresses
BURN_ADDR    = os.getenv("BURN_ADDR")
REWARDS_ADDR = os.getenv("REWARDS_ADDR")
LP_ADDR      = os.getenv("LP_ADDR")
if not all([BURN_ADDR, REWARDS_ADDR, LP_ADDR]):
    print("ERROR: BURN_ADDR, REWARDS_ADDR, and LP_ADDR must be set in .env")
    sys.exit(1)

# Initialize Algod client and Treasury account keys
treasury_sk   = mnemonic.to_private_key(TREASURY_MNEMONIC)
treasury_addr = account.address_from_private_key(treasury_sk)
client        = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp            = client.suggested_params()

def main():
    # Fetch current Treasury balance for the ASA
    acct   = client.account_info(treasury_addr)
    assets = acct.get("assets", [])
    total  = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

    print(f"ℹ️ Current Treasury balance: {total} Dumbly")
    if total <= 0:
        print("ℹ️ Nothing to distribute. Exiting.")
        return

    # Calculate equal shares
    burn_amt    = total // 3
    rewards_amt = total // 3
    lp_amt      = total - burn_amt - rewards_amt
    print(f"ℹ️ Splitting into burn={burn_amt}, rewards={rewards_amt}, lp={lp_amt}")

    # Build the three transfer transactions
    tx1 = AssetTransferTxn(sender=treasury_addr, sp=sp, receiver=BURN_ADDR,    amt=burn_amt,    index=ASSET_ID)
    tx2 = AssetTransferTxn(sender=treasury_addr, sp=sp, receiver=REWARDS_ADDR, amt=rewards_amt, index=ASSET_ID)
    tx3 = AssetTransferTxn(sender=treasury_addr, sp=sp, receiver=LP_ADDR,      amt=lp_amt,      index=ASSET_ID)

    # Group them atomically
    txs = [tx1, tx2, tx3]
    gid = calculate_group_id(txs)
    for tx in txs:
        tx.group = gid

    # Sign and send
    signed_txs = [tx.sign(treasury_sk) for tx in txs]
    try:
        txid = client.send_transactions(signed_txs)
        print(f"⏳ Group transaction sent, txID: {txid}")
        wait_for_confirmation(client, txid, 4)
    except Exception as e:
        print(f"ERROR: Failed to send or confirm group transaction: {e}")
        sys.exit(1)

    # Success message
    print("✅ Distribution complete:")
    print(f"   • {burn_amt} Dumbly → Burn")
    print(f"   • {rewards_amt} Dumbly → Rewards")
    print(f"   • {lp_amt} Dumbly → LP")

if __name__ == "__main__":
    main()
