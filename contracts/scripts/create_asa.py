#!/usr/bin/env python3
"""
create_asa.py

This script spins up a new Algorand Standard Asset (ASA) called “Dumbly.”
You’ll get back the new asset ID once it’s live on TestNet or MainNet.

Before running:
  1) Copy .env.example → .env and fill in ALGOD_ADDRESS, ADMIN_MNEMONIC.
  2) (Optional) Set ASSET_ID if you’re re-creating an existing asset.

Install dependencies:
  pip install python-dotenv py-algorand-sdk

Run:
  python create_asa.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk.error import AlgodHTTPError

# Load our .env values
load_dotenv()

ALGOD_ADDRESS  = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN    = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC = os.getenv("ADMIN_MNEMONIC")
ASSET_ID_ENV   = os.getenv("ASSET_ID")  # override if you want to reuse an asset ID

if not ALGOD_ADDRESS or not ADMIN_MNEMONIC:
    print("❌ Please set ALGOD_ADDRESS and ADMIN_MNEMONIC in your .env")
    sys.exit(1)

# Turn the mnemonic into a usable keypair
try:
    admin_sk   = mnemonic.to_private_key(ADMIN_MNEMONIC)
    admin_addr = account.address_from_private_key(admin_sk)
    client     = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
except Exception as e:
    print(f"❌ Could not set up Algod client or account: {e}")
    sys.exit(1)

# How many tokens in total, and precision
TOTAL_SUPPLY = 777_777_777
DECIMALS     = 6
ASSET_NAME   = "Dumbly"
UNIT_NAME    = "Dumbly"

def main():
    # Grab the current network params so our tx is valid
    params = client.suggested_params()

    # Build the transaction to create the ASA
    txn = AssetConfigTxn(
        sender=admin_addr,
        sp=params,
        total=TOTAL_SUPPLY,
        default_frozen=False,
        unit_name=UNIT_NAME,
        asset_name=ASSET_NAME,
        manager=admin_addr,
        reserve=admin_addr,
        freeze=admin_addr,
        clawback=admin_addr,
        decimals=DECIMALS,
    )

    try:
        # Sign and post the tx
        signed_txn = txn.sign(admin_sk)
        txid       = client.send_transaction(signed_txn)
        print(f"⏳ Waiting on txID {txid}...")
        result     = wait_for_confirmation(client, txid, 4)
        new_id     = result["asset-index"]
        print(f"✅ All done! New ASA ID is {new_id}")
    except AlgodHTTPError as e:
        print(f"❌ ASA creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
