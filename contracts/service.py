# service.py

from dotenv import load_dotenv
load_dotenv()  # charge automatiquement ton .env

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, calculate_group_id, wait_for_confirmation

app = FastAPI()

# ─── CONFIG via variables d’environnement ───────────────────────────────────────
ALGOD_ADDRESS     = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN       = os.getenv("ALGOD_TOKEN", "")
TREASURY_MNEMONIC = os.getenv("TREASURY_MNEMONIC")
ASSET_ID          = int(os.getenv("ASSET_ID"))
BURN_ADDR         = os.getenv("BURN_ADDR")
LP_ADDR           = os.getenv("LP_ADDR")
REWARDS_ADDR      = os.getenv("REWARDS_ADDR")

# Vérifie que tout est bien défini
if not all([ALGOD_ADDRESS, TREASURY_MNEMONIC, ASSET_ID, BURN_ADDR, LP_ADDR, REWARDS_ADDR]):
    raise RuntimeError("Merci de définir toutes les variables d’environnement dans .env")

# ─── INITIALISATION ALGOD & CLÉS ───────────────────────────────────────────────
client        = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
treasury_sk   = mnemonic.to_private_key(TREASURY_MNEMONIC)
treasury_addr = account.address_from_private_key(treasury_sk)
sp            = client.suggested_params()

# ─── Schéma de la requête ──────────────────────────────────────────────────────
class Distribution(BaseModel):
    burn:    conint(ge=0)
    lp:      conint(ge=0)
    rewards: conint(ge=0)

# ─── Endpoint pour récupérer le solde de la treasury ───────────────────────────
@app.get("/treasury-balance")
def get_treasury_balance():
    acct   = client.account_info(treasury_addr)
    assets = acct.get("assets", [])
    bal    = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)
    return {"treasury_balance": bal}

# ─── Endpoint de distribution manuelle ─────────────────────────────────────────
@app.post("/distribute-manual")
def distribute_manual(dist: Distribution):
    # 1) Lit le solde actuel de la treasury
    acct   = client.account_info(treasury_addr)
    assets = acct.get("assets", [])
    total  = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

    # 2) Validation
    requested = dist.burn + dist.lp + dist.rewards
    if requested > total:
        raise HTTPException(400, detail=f"Montant demandé ({requested}) > solde treasury ({total})")

    # 3) Création des transactions avec paramètres nommés
    tx1 = AssetTransferTxn(
        sender=treasury_addr,
        sp=sp,
        receiver=BURN_ADDR,
        amt=dist.burn,
        index=ASSET_ID,
    )
    tx2 = AssetTransferTxn(
        sender=treasury_addr,
        sp=sp,
        receiver=LP_ADDR,
        amt=dist.lp,
        index=ASSET_ID,
    )
    tx3 = AssetTransferTxn(
        sender=treasury_addr,
        sp=sp,
        receiver=REWARDS_ADDR,
        amt=dist.rewards,
        index=ASSET_ID,
    )

    txs = [tx1, tx2, tx3]
    gid = calculate_group_id(txs)
    for tx in txs:
        tx.group = gid

    # 4) Signature & envoi
    try:
        signed = [tx.sign(treasury_sk) for tx in txs]
        txid   = client.send_transactions(signed)
        wait_for_confirmation(client, txid, 4)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur Algod : {str(e)}")

    return {
        "status": "success",
        "txid": txid,
        "distributed": {
            "burn":    dist.burn,
            "lp":      dist.lp,
            "rewards": dist.rewards
        }
    }

# ─── Endpoint de redistribution automatique ───────────────────────────────────
@app.post("/distribute-all")
def distribute_all():
    # 1) Lire le solde actuel de la treasury
    acct   = client.account_info(treasury_addr)
    assets = acct.get("assets", [])
    total  = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

    # 2) Calcul des parts égales
    burn_amt    = total // 3
    rewards_amt = total // 3
    lp_amt      = total - burn_amt - rewards_amt

    # 3) Construire les 3 transactions groupées
    tx1 = AssetTransferTxn(
        sender=treasury_addr, sp=sp, receiver=BURN_ADDR,    amt=burn_amt,    index=ASSET_ID
    )
    tx2 = AssetTransferTxn(
        sender=treasury_addr, sp=sp, receiver=LP_ADDR,      amt=lp_amt,      index=ASSET_ID
    )
    tx3 = AssetTransferTxn(
        sender=treasury_addr, sp=sp, receiver=REWARDS_ADDR, amt=rewards_amt, index=ASSET_ID
    )

    txs = [tx1, tx2, tx3]
    gid = calculate_group_id(txs)
    for tx in txs:
        tx.group = gid

    # 4) Signer et envoyer
    try:
        signed = [tx.sign(treasury_sk) for tx in txs]
        txid   = client.send_transactions(signed)
        wait_for_confirmation(client, txid, 4)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur Algod : {str(e)}")

    # 5) Retourner le résultat à l’admin
    return {
        "status": "success",
        "txid": txid,
        "distributed": {
            "burn":    burn_amt,
            "lp":      lp_amt,
            "rewards": rewards_amt
        }
    }
