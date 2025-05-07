# deploy.py
import os
import base64
import sys
from dotenv import load_dotenv

from algosdk import mnemonic, account
from algosdk import transaction
from algosdk.encoding import decode_address
from algosdk.v2client import algod
from algosdk.error import AlgodHTTPError

# ─── CHARGEMENT DES VARIABLES D’ENVIRONNEMENT ─────────────────────────────────
load_dotenv()  # lit automatiquement .env à la racine de contracts/

ALGOD_ADDRESS  = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN    = os.getenv("ALGOD_TOKEN", "")
ADMIN_MNEMONIC = os.getenv("ADMIN_MNEMONIC")
TREASURY_ADDR  = os.getenv("TREASURY_ADDR")
APP_ID         = os.getenv("APP_ID")  # non utilisé ici mais peut servir

if not all([ALGOD_ADDRESS, ADMIN_MNEMONIC, TREASURY_ADDR]):
    print("❌ Définis ALGOD_ADDRESS, ADMIN_MNEMONIC et TREASURY_ADDR dans .env")
    sys.exit(1)

# ─── INITIALISATION CLIENT & CLÉS ────────────────────────────────────────────────
try:
    admin_sk   = mnemonic.to_private_key(ADMIN_MNEMONIC)
    admin_addr = account.address_from_private_key(admin_sk)
    client     = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
except Exception as e:
    print("❌ Erreur de configuration ou de connexion Algod :", e)
    sys.exit(1)

def compile_teal(path: str) -> bytes:
    """Compile un fichier TEAL et retourne le binaire."""
    source = open(path, "r").read()
    res    = client.compile(source)
    return base64.b64decode(res["result"])

# ─── COMPILATION DES PROGRAMMES TEAL ─────────────────────────────────────────────
approval_program = compile_teal("approval.teal")
clear_program    = compile_teal("clear.teal")

# ─── CONSTRUCTION DE LA TRANSACTION DE CRÉATION D’APPLICATION ─────────────────────
global_schema = transaction.StateSchema(num_uints=0, num_byte_slices=2)
local_schema  = transaction.StateSchema(num_uints=0, num_byte_slices=0)

app_args = [
    decode_address(admin_addr),
    decode_address(TREASURY_ADDR),
]

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

# ─── SIGNATURE & ENVOI ───────────────────────────────────────────────────────────
try:
    signed_txn = txn.sign(admin_sk)
    txid       = client.send_transaction(signed_txn)
    print("⏳ En attente de confirmation – txID :", txid)
    res        = transaction.wait_for_confirmation(client, txid, 4)
    print(f"✅ Contrat déployé ! application-id = {res['application-index']}")
except AlgodHTTPError as e:
    print("❌ Erreur Algod lors du déploiement :", e)
    sys.exit(1)
