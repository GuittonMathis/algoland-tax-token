# create_asa.py
import os
import sys
from dotenv import load_dotenv

from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
from algosdk.error import AlgodHTTPError

# ─── CHARGEMENT DES VARIABLES D’ENVIRONNEMENT ─────────────────────────────────
load_dotenv()

ALGOD_ADDRESS  = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN    = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC = os.getenv("ADMIN_MNEMONIC")
ASSET_ID_ENV   = os.getenv("ASSET_ID")  # pour override si on recrée

if not all([ALGOD_ADDRESS, ADMIN_MNEMONIC]):
    print("❌ Définis ALGOD_ADDRESS et ADMIN_MNEMONIC dans .env")
    sys.exit(1)

# ─── INITIALISATION CLÉS & CLIENT ───────────────────────────────────────────────
try:
    admin_sk   = mnemonic.to_private_key(ADMIN_MNEMONIC)
    admin_addr = account.address_from_private_key(admin_sk)
    client     = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
except Exception as e:
    print("❌ Erreur de configuration Algod :", e)
    sys.exit(1)

# ─── PARAMÈTRES DE L’ASA ────────────────────────────────────────────────────────
TOTAL_SUPPLY = 777_777_777
DECIMALS     = 6
ASSET_NAME   = "Dumbly"
UNIT_NAME    = "Dumbly"

# ─── CRÉATION DE L'ASA ──────────────────────────────────────────────────────────
params = client.suggested_params()
txn    = AssetConfigTxn(
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
    signed_txn = txn.sign(admin_sk)
    txid       = client.send_transaction(signed_txn)
    print("⏳ En attente de confirmation – txID :", txid)
    confirmed = wait_for_confirmation(client, txid, 4)
    print(f"✅ ASA créé ! asset-id = {confirmed['asset-index']}")
except AlgodHTTPError as e:
    print("❌ Erreur Algod lors de la création ASA :", e)
    sys.exit(1)
