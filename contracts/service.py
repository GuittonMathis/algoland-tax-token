#!/usr/bin/env python3
"""
service.py

FastAPI backend for the Dumbly token treasury.  
Provides endpoints to:
  • GET  /treasury-balance       ⇒ returns current ASA balance in treasury  
  • POST /distribute-manual      ⇒ distribute custom amounts to Burn, LP, Rewards  
  • POST /distribute-all         ⇒ split entire balance evenly (1/3 each)

Environment variables (.env):
  ALGOD_ADDRESS     Algod API endpoint (e.g. https://testnet-api.algonode.cloud)
  ALGOD_TOKEN       Algod API token (may be empty)
  TREASURY_MNEMONIC 25-word mnemonic of the Treasury account
  ASSET_ID          Numeric ASA ID for Dumbly
  BURN_ADDR         Burn account address
  LP_ADDR           LP account address
  REWARDS_ADDR      Rewards account address

Install dependencies:
  pip install python-dotenv fastapi uvicorn algosdk pydantic
Run:
  uvicorn service:app --reload
"""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, calculate_group_id, wait_for_confirmation
from algosdk.error import AlgodHTTPError

# ─── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

def get_env_var(name: str) -> str:
    """Return an env var or exit if missing."""
    val = os.getenv(name)
    if not val:
        print(f"ERROR: Missing environment variable: {name}")
        sys.exit(1)
    return val

# Read and validate config
ALGOD_ADDRESS     = get_env_var("ALGOD_ADDRESS")
ALGOD_TOKEN       = os.getenv("ALGOD_TOKEN", "")
TREASURY_MNEMONIC = get_env_var("TREASURY_MNEMONIC")
ASSET_ID          = int(get_env_var("ASSET_ID"))
BURN_ADDR         = get_env_var("BURN_ADDR")
LP_ADDR           = get_env_var("LP_ADDR")
REWARDS_ADDR      = get_env_var("REWARDS_ADDR")

# ─── FastAPI setup ─────────────────────────────────────────────────────────────
app = FastAPI()

# Allow only local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize Algod client & Treasury keys ───────────────────────────────────
try:
    client        = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    treasury_sk   = mnemonic.to_private_key(TREASURY_MNEMONIC)
    treasury_addr = account.address_from_private_key(treasury_sk)
except Exception as e:
    print(f"ERROR: Failed to initialize Algod client or keys: {e}")
    sys.exit(1)

# ─── Request model for manual distribution ──────────────────────────────────────
class Distribution(BaseModel):
    burn:    conint(ge=0)
    lp:      conint(ge=0)
    rewards: conint(ge=0)

# ─── Endpoint: Get treasury balance ────────────────────────────────────────────
@app.get("/treasury-balance")
def get_treasury_balance():
    """Return the current Dumbly ASA balance in the treasury account."""
    acct_info = client.account_info(treasury_addr)
    assets    = acct_info.get("assets", [])
    bal       = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)
    return {"treasury_balance": bal}

# ─── Endpoint: Manual distribution ─────────────────────────────────────────────
@app.post("/distribute-manual")
def distribute_manual(dist: Distribution):
    """
    Distribute specified amounts of Dumbly from treasury to Burn, LP, Rewards.
    Validates that total requested ≤ current balance.
    """
    # Fetch current balance
    acct_info = client.account_info(treasury_addr)
    assets    = acct_info.get("assets", [])
    total     = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

    requested = dist.burn + dist.lp + dist.rewards
    if requested > total:
        raise HTTPException(400, detail=f"Requested ({requested}) > balance ({total})")

    # Build and group transactions
    sp = client.suggested_params()
    txs = [
        AssetTransferTxn(treasury_addr, sp, BURN_ADDR,    dist.burn,    ASSET_ID),
        AssetTransferTxn(treasury_addr, sp, LP_ADDR,      dist.lp,      ASSET_ID),
        AssetTransferTxn(treasury_addr, sp, REWARDS_ADDR, dist.rewards, ASSET_ID),
    ]
    gid = calculate_group_id(txs)
    for tx in txs:
        tx.group = gid

    # Sign & send
    try:
        signed = [tx.sign(treasury_sk) for tx in txs]
        txid   = client.send_transactions(signed)
        wait_for_confirmation(client, txid, 4)
    except AlgodHTTPError as e:
        raise HTTPException(500, detail=f"Algod error: {e}")

    return {
        "status": "success",
        "txid": txid,
        "distributed": {"burn": dist.burn, "lp": dist.lp, "rewards": dist.rewards}
    }

# ─── Endpoint: Automatic distribution ──────────────────────────────────────────
@app.post("/distribute-all")
def distribute_all():
    """
    Split the entire treasury balance evenly into three parts:
    Burn, LP, and Rewards (floor division for two parts, remainder to LP).
    """
    acct_info = client.account_info(treasury_addr)
    assets    = acct_info.get("assets", [])
    total     = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

    burn_amt    = total // 3
    rewards_amt = total // 3
    lp_amt      = total - burn_amt - rewards_amt

    sp = client.suggested_params()
    txs = [
        AssetTransferTxn(treasury_addr, sp, BURN_ADDR,    burn_amt,    ASSET_ID),
        AssetTransferTxn(treasury_addr, sp, LP_ADDR,      lp_amt,      ASSET_ID),
        AssetTransferTxn(treasury_addr, sp, REWARDS_ADDR, rewards_amt, ASSET_ID),
    ]
    gid = calculate_group_id(txs)
    for tx in txs:
        tx.group = gid

    try:
        signed = [tx.sign(treasury_sk) for tx in txs]
        txid   = client.send_transactions(signed)
        wait_for_confirmation(client, txid, 4)
    except AlgodHTTPError as e:
        raise HTTPException(500, detail=f"Algod error: {e}")

    return {
        "status": "success",
        "txid": txid,
        "distributed": {"burn": burn_amt, "lp": lp_amt, "rewards": rewards_amt}
    }
