#!/usr/bin/env python3
"""
deploy.py

This script compiles your approval and clear TEAL programs, then
creates a new Algorand application on TestNet or MainNet.

Before running:
  1) Make sure approval.teal and clear.teal are in the same folder.
  2) Copy .env.example → .env and fill in:
     - ALGOD_ADDRESS: your Algod API endpoint
     - ADMIN_MNEMONIC: the 25-word mnemonic of your admin account
     - TREASURY_ADDR: the address that will receive collected taxes
     (ALGOD_TOKEN and APP_ID are optional here.)

Install dependencies:
  pip install python-dotenv py-algorand-sdk

Run:
  python deploy.py
"""

import os
import sys
import base64
from dotenv import load_dotenv
from algosdk import mnemonic, account, transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address
from algosdk.error import AlgodHTTPError

# Load environment settings
load_dotenv()

ALGOD_ADDRESS  = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN    = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC = os.getenv("ADMIN_MNEMONIC")
TREASURY_ADDR  = os.getenv("TREASURY_ADDR")

# Basic validation
if not ALGOD_ADDRESS or not ADMIN_MNEMONIC or not TREASURY_ADDR:
    print("❌ Please set ALGOD_ADDRESS, ADMIN_MNEMONIC, and TREASURY_ADDR in your .env")
    sys.exit(1)

def init_client_and_keys():
    """Initialize Algod client and derive admin account keys."""
    try:
        admin_sk   = mnemonic.to_private_key(ADMIN_MNEMONIC)
        admin_addr = account.address_from_private_key(admin_sk)
        client     = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    except Exception as e:
        print(f"❌ Failed to set up Algod client or account keys: {e}")
        sys.exit(1)
    return client, admin_sk, admin_addr

def compile_teal_file(client, filename: str) -> bytes:
    """Compile a TEAL file and return the compiled bytes."""
    source = open(filename, "r").read()
    response = client.compile(source)
    return base64.b64decode(response["result"])

def main():
    client, admin_sk, admin_addr = init_client_and_keys()

    # Compile the Teal programs
    approval_program = compile_teal_file(client, "approval.teal")
    clear_program    = compile_teal_file(client, "clear.teal")

    # Define how much global and local state to allocate
    global_schema = transaction.StateSchema(num_uints=0, num_byte_slices=2)
    local_schema  = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    # Pass admin and treasury addresses as app arguments
    app_args = [
        decode_address(admin_addr),
        decode_address(TREASURY_ADDR),
    ]

    # Create the application
    txn = transaction.ApplicationCreateTxn(
        sender=admin_addr,
        sp=client.suggested_params(),
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=global_schema,
        local_schema=local_schema,
        app_args=app_args,
    )

    try:
        signed_txn = txn.sign(admin_sk)
        txid       = client.send_transaction(signed_txn)
        print(f"⏳ Waiting for confirmation – txID: {txid}")
        result = transaction.wait_for_confirmation(client, txid, 4)
        app_id = result["application-index"]
        print(f"✅ Application deployed! application-id = {app_id}")
    except AlgodHTTPError as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
