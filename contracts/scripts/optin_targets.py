# optin_targets.py
import os
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation

load_dotenv()

ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
ASSET_ID      = int(os.getenv("ASSET_ID"))

# Charge les clés depuis les mnémos
def load_sk(env_key):
    sk = mnemonic.to_private_key(os.getenv(env_key))
    addr = account.address_from_private_key(sk)
    return addr, sk

burn_addr,   burn_sk   = load_sk("BURN_MNEMONIC")
lp_addr,     lp_sk     = load_sk("LP_MNEMONIC")
rewards_addr,rew_sk    = load_sk("REWARDS_MNEMONIC")

client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp     = client.suggested_params()

for addr, sk in [(burn_addr, burn_sk), (lp_addr, lp_sk), (rewards_addr, rew_sk)]:
    try:
        tx = AssetTransferTxn(sender=addr, sp=sp, receiver=addr, amt=0, index=ASSET_ID)
        stx = tx.sign(sk)
        txid = client.send_transaction(stx)
        wait_for_confirmation(client, txid, 4)
        print(f"✅ Opt-in réussi pour {addr}")
    except Exception as e:
        print(f"⚠️ Opt-in déjà fait ou erreur pour {addr} :", e)
