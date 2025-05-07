from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import (
    AssetTransferTxn,
    calculate_group_id,
    wait_for_confirmation,
)

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────
ALGOD_ADDRESS = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN   = ""

# Mnemonic du compte Treasury TestNet (celui qui détient réellement les fonds)
TREASURY_MNEMONIC = (
    "rent arctic mean fluid goose moon surface valid index refuse arrive fury useless "
    "filter track write marine original broken middle recipe sister absurd above beauty"
)

# Identifiant de l’ASA “Dumbly”
ASSET_ID = 738130308

# Adresses de destination (TestNet)
BURN_ADDR    = "G7HVTZD2MIVTN5QTN7VL5GHDMZP2B4ZSVHJJ5G6FLZAOGKITEXIOKXFJ7I"
REWARDS_ADDR = "AWM4UNTYTHULCN4MG4LE7NXFPX2HYPNQTCYMFLT64ZCXB3TUCI4O5Q4O5I"
LP_ADDR      = "GTD2JLI6UBVE3A6EXIOVJYNKFBEQ64SCH3HXAMZWAACBAZZJKPG6S33W5A"

# ─── INITIALISATION CLÉS & CLIENT ALGOD ─────────────────────────────────────────
treasury_sk   = mnemonic.to_private_key(TREASURY_MNEMONIC)
treasury_addr = account.address_from_private_key(treasury_sk)

client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp     = client.suggested_params()

# ─── LECTURE DYNAMIQUE DU SOLDE DE LA TREASURY ─────────────────────────────────
acct    = client.account_info(treasury_addr)
assets  = acct.get("assets", [])
TOTAL   = next((a["amount"] for a in assets if a["asset-id"] == ASSET_ID), 0)

print(f"ℹ️ Treasury solde actuel = {TOTAL} Dumbly")
if TOTAL <= 0:
    print("ℹ️ Aucun Dumbly à distribuer. Fin du script.")
    exit(0)

# ─── CALCUL DES PARTS ÉGALES ────────────────────────────────────────────────────
burn_amt    = TOTAL // 3
rewards_amt = TOTAL // 3
lp_amt      = TOTAL - burn_amt - rewards_amt

print(f"ℹ️ Distribution calculée : burn={burn_amt}, rewards={rewards_amt}, lp={lp_amt}")

# ─── CONSTRUCTION DU GROUPE DE TRANSACTIONS ─────────────────────────────────────
tx1 = AssetTransferTxn(
    sender=treasury_addr, sp=sp,
    receiver=BURN_ADDR,    amt=burn_amt,    index=ASSET_ID
)
tx2 = AssetTransferTxn(
    sender=treasury_addr, sp=sp,
    receiver=REWARDS_ADDR, amt=rewards_amt, index=ASSET_ID
)
tx3 = AssetTransferTxn(
    sender=treasury_addr, sp=sp,
    receiver=LP_ADDR,      amt=lp_amt,      index=ASSET_ID
)

txs = [tx1, tx2, tx3]
gid = calculate_group_id(txs)
for tx in txs:
    tx.group = gid

signed_txs = [tx.sign(treasury_sk) for tx in txs]

# ─── ENVOI & CONFIRMATION ───────────────────────────────────────────────────────
txid = client.send_transactions(signed_txs)
print("⏳ Groupe tx envoyé, txID :", txid)
wait_for_confirmation(client, txid, 4)

print("✅ Redistribution terminée avec succès.")
print(f"   • {burn_amt} Dumbly → Burn")
print(f"   • {rewards_amt} Dumbly → Rewards")
print(f"   • {lp_amt} Dumbly → LP")
