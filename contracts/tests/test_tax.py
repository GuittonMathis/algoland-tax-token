# test_tax.py
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

# ─── CHARGEMENT DES VARIABLES D’ENVIRONNEMENT ─────────────────────────────────
load_dotenv()

ALGOD_ADDRESS     = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN       = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC    = os.getenv("ADMIN_MNEMONIC")
BUYER_MNEMONIC    = os.getenv("BUYER_MNEMONIC")
TREASURY_MNEMONIC = os.getenv("TREASURY_MNEMONIC")
APP_ID            = int(os.getenv("APP_ID", "0"))
ASSET_ID          = int(os.getenv("ASSET_ID", "0"))

if not all([ALGOD_ADDRESS, ADMIN_MNEMONIC, BUYER_MNEMONIC, TREASURY_MNEMONIC, APP_ID, ASSET_ID]):
    print("❌ Variables manquantes dans .env")
    sys.exit(1)

# ─── INIT CLÉS & CLIENT ─────────────────────────────────────────────────────────
client       = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp           = client.suggested_params()
admin_sk     = mnemonic.to_private_key(ADMIN_MNEMONIC)
admin_addr   = account.address_from_private_key(admin_sk)
buyer_sk     = mnemonic.to_private_key(BUYER_MNEMONIC)
buyer_addr   = account.address_from_private_key(buyer_sk)
treas_sk     = mnemonic.to_private_key(TREASURY_MNEMONIC)
treas_addr   = account.address_from_private_key(treas_sk)

# ─── OPT-IN Buyer & Treasury ──────────────────────────────────────────────────
for addr, sk in [(buyer_addr, buyer_sk), (treas_addr, treas_sk)]:
    try:
        opt = AssetTransferTxn(sender=addr, sp=sp, receiver=addr, amt=0, index=ASSET_ID)
        stx = opt.sign(sk)
        client.send_transaction(stx)
        wait_for_confirmation(client, stx.get_txid(), 4)
        print(f"✅ {addr} opt-in OK (ASA {ASSET_ID})")
    except AlgodHTTPError as e:
        print("⚠️ Opt-in déjà réalisé ou erreur :", e)

# ─── SOLDE INITIAL DE LA TREASURY ─────────────────────────────────────────────
acct            = client.account_info(treas_addr)
initial_balance = next(
    (a["amount"] for a in acct.get("assets", []) if a["asset-id"] == ASSET_ID),
    0
)
print(f"ℹ️ Treasury solde initial = {initial_balance} Dumbly")

# ─── SIMULATION DE VENTE + TAXE ───────────────────────────────────────────────
AMOUNT     = 1_000
net_amount = AMOUNT * 91 // 100
tax_amount = AMOUNT - net_amount

tx1 = AssetTransferTxn(sender=admin_addr, sp=sp, receiver=buyer_addr, amt=net_amount, index=ASSET_ID)
tx2 = AssetTransferTxn(sender=admin_addr, sp=sp, receiver=treas_addr, amt=tax_amount, index=ASSET_ID)
tx3 = ApplicationNoOpTxn(sender=admin_addr, sp=sp, index=APP_ID, app_args=[b"tax"])

# Groupe les 3 txns
gid = calculate_group_id([tx1, tx2, tx3])
for tx in (tx1, tx2, tx3):
    tx.group = gid

signed = [tx1.sign(admin_sk), tx2.sign(admin_sk), tx3.sign(admin_sk)]
try:
    txid = client.send_transactions(signed)
    print("⏳ Groupe tx envoyé, txID :", txid)
    wait_for_confirmation(client, txid, 4)
except AlgodHTTPError as e:
    print("❌ Erreur Algod pendant test_tax :", e)
    sys.exit(1)

# ─── VÉRIFICATION DE LA TAXE ───────────────────────────────────────────────────
acct_after  = client.account_info(treas_addr)
new_balance = next(
    (a["amount"] for a in acct_after.get("assets", []) if a["asset-id"] == ASSET_ID),
    0
)
delta = new_balance - initial_balance
print(f"✅ Treasury solde final = {new_balance} Dumbly  (delta = {delta}, attendu = {tax_amount})")
assert delta == tax_amount, "❌ Taxe incorrecte"
