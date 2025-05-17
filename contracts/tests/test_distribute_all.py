#!/usr/bin/env pytest
"""
test_distribute_all.py

End-to-end test for the `/distribute-all` endpoint of the FastAPI backend.

This test will:
  1. Top up the Treasury account by running the `test_tax.py` script.
  2. Verify the Treasury’s initial ASA balance is at least 3 units.
  3. Call the `/distribute-all` API and expect a successful response.
  4. Check that the sum of burn, lp, and rewards equals the initial balance.
  5. Confirm that the Treasury’s ASA balance is zero after distribution.
"""

import os
import subprocess
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from algosdk import mnemonic, account
from algosdk.v2client import algod

# Load environment variables from .env
load_dotenv()

from service import app, ASSET_ID, TREASURY_MNEMONIC

client_api = TestClient(app)

@pytest.fixture(scope="module")
def algod_client():
    """Returns an Algod client configured via environment variables."""
    token   = os.getenv("ALGOD_TOKEN", "")
    address = os.getenv("ALGOD_ADDRESS")
    return algod.AlgodClient(token, address)

@pytest.fixture(scope="module")
def treasury_sk():
    """Returns the private key of the Treasury account."""
    mnem = os.getenv("TREASURY_MNEMONIC")
    return mnemonic.to_private_key(mnem)

@pytest.fixture(scope="module")
def treasury_addr(treasury_sk):
    """Returns the public address of the Treasury account."""
    return account.address_from_private_key(treasury_sk)

def test_distribute_all(algod_client, treasury_sk, treasury_addr):
    # 1) Credit the Treasury by simulating a sale + tax
    subprocess.run(["python", "tests/test_tax.py"], check=True)

    # 2) Fetch the initial balance and ensure it's >= 3 units
    acct_info = algod_client.account_info(treasury_addr)
    initial_total = next(
        (a["amount"] for a in acct_info.get("assets", []) if a["asset-id"] == ASSET_ID),
        0
    )
    assert initial_total >= 3, f"Initial balance too low ({initial_total}) for testing distribute-all"

    # 3) Call the distribute-all endpoint
    response = client_api.post("/distribute-all")
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.json()
    assert data["status"] == "success", f"API returned failure: {data}"

    # 4) Check that burn + lp + rewards equals the initial balance
    burn, lp, rewards = (
        data["distributed"]["burn"],
        data["distributed"]["lp"],
        data["distributed"]["rewards"]
    )
    assert burn + lp + rewards == initial_total, (
        f"Distributed sum ({burn + lp + rewards}) does not match initial ({initial_total})"
    )

    # 5) Verify the Treasury is now empty
    acct_after = algod_client.account_info(treasury_addr)
    new_total = next(
        (a["amount"] for a in acct_after.get("assets", []) if a["asset-id"] == ASSET_ID),
        0
    )
    assert new_total == 0, f"Treasury not emptied, remaining balance: {new_total}"
