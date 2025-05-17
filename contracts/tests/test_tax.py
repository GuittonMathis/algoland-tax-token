#!/usr/bin/env python3
"""
test_tax.py

Simulates a token sale with a 9% tax and verifies that the Treasury account
receives exactly the tax amount.

Steps:
  1. Opt-in both Buyer and Treasury accounts to the ASA.
  2. Record the Treasury’s initial balance.
  3. Create and send a 3-transaction atomic group:
       a. Transfer net amount (91%) to Buyer.
       b. Transfer tax amount (9%) to Treasury.
       c. Call the smart contract to enforce the tax.
  4. Confirm the group and check that the Treasury’s balance increased by the expected tax.

Environment variables (.env):
  ALGOD_ADDRESS     Algod API endpoint (e.g. https://testnet-api.algonode.cloud)
  ALGOD_TOKEN       Algod API token (may be empty)
  ADMIN_MNEMONIC    Admin account mnemonic
  BUYER_MNEMONIC    Buyer account mnemonic
  TREASURY_MNEMONIC Treasury account mnemonic
  APP_ID            Deployed application ID
  ASSET_ID          ASA ID for the token

Usage:
  pip install python-dotenv py-algorand-sdk
  python test_tax.py
"""

import os
import sys
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import (
    AssetTransferTxn,
    ApplicationNoOpTxn,
    calculate_group_id,
    wait_for_confirmation,
)
from algosdk.error import AlgodHTTPError

load_dotenv()

def get_env_var(name: str) -> str:
    """Retrieve an environment variable or exit if missing."""
    val = os.getenv(name)
    if not val:
        print(f"ERROR: Missing environment variable: {name}")
        sys.exit(1)
    return val

def init_client() -> algod.AlgodClient:
    """Initialize and return an Algod client."""
    address = get_env_var("ALGOD_ADDRESS")
    token   = os.getenv("ALGOD_TOKEN", "")
    try:
        return algod.AlgodClient(token, address)
    except Exception as e:
        print(f"ERROR: Failed to connect to Algod: {e}")
        sys.exit(1)

def load_keypair(env_key: str):
    """Convert a mnemonic env var to (private_key, address)."""
    m = get_env_var(env_key)
    sk = mnemonic.to_private_key(m)
    addr = account.address_from_private_key(sk)
    return sk, addr

def opt_in_accounts(client, sp, accounts, asset_id):
    """Opt-in each account in the list to the given ASA."""
    for sk, addr in accounts:
        try:
            txn = AssetTransferTxn(sender=addr, sp=sp, receiver=addr, amt=0, index=asset_id)
            stx = txn.sign(sk)
            txid = client.send_transaction(stx)
            wait_for_confirmation(client, txid, 4)
            print(f"✅ {addr} opt-in OK (ASA {asset_id})")
        except AlgodHTTPError as e:
            print(f"⚠️ Opt-in failed or already done for {addr}: {e}")

def main():
    client = init_client()
    sp = client.suggested_params()

    # Load keypairs
    admin_sk, admin_addr       = load_keypair("ADMIN_MNEMONIC")
    buyer_sk, buyer_addr       = load_keypair("BUYER_MNEMONIC")
    treas_sk, treas_addr       = load_keypair("TREASURY_MNEMONIC")
    app_id  = int(get_env_var("APP_ID"))
    asset_id= int(get_env_var("ASSET_ID"))

    # 1) Opt-in Buyer & Treasury
    opt_in_accounts(client, sp, [(buyer_sk, buyer_addr), (treas_sk, treas_addr)], asset_id)

    # 2) Record initial Treasury balance
    acct = client.account_info(treas_addr)
    initial_balance = next(
        (a["amount"] for a in acct.get("assets", []) if a["asset-id"] == asset_id),
        0
    )
    print(f"ℹ️ Initial Treasury balance = {initial_balance} Dumbly")

    # 3) Simulate sale + tax
    amount     = 1_000
    net_amount = amount * 91 // 100
    tax_amount = amount - net_amount

    txn1 = AssetTransferTxn(sender=admin_addr, sp=sp, receiver=buyer_addr, amt=net_amount, index=asset_id)
    txn2 = AssetTransferTxn(sender=admin_addr, sp=sp, receiver=treas_addr, amt=tax_amount, index=asset_id)
    txn3 = ApplicationNoOpTxn(sender=admin_addr, sp=sp, index=app_id, app_args=[b"tax"])

    group = [txn1, txn2, txn3]
    gid = calculate_group_id(group)
    for tx in group:
        tx.group = gid

    signed_group = [txn1.sign(admin_sk), txn2.sign(admin_sk), txn3.sign(admin_sk)]

    try:
        txid = client.send_transactions(signed_group)
        print(f"⏳ Group tx sent, txID: {txid}")
        wait_for_confirmation(client, txid, 4)
    except AlgodHTTPError as e:
        print(f"ERROR: Failed during test_tax group send: {e}")
        sys.exit(1)

    # 4) Verify the tax landed correctly
    acct_after = client.account_info(treas_addr)
    new_balance = next(
        (a["amount"] for a in acct_after.get("assets", []) if a["asset-id"] == asset_id),
        0
    )
    delta = new_balance - initial_balance
    print(f"✅ Final Treasury balance = {new_balance} Dumbly  (delta = {delta}, expected = {tax_amount})")

    assert delta == tax_amount, "ERROR: Tax amount incorrect"

if __name__ == "__main__":
    main()
