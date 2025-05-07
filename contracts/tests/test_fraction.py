from algosdk import mnemonic, account
from algosdk.v2client import algod
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation

# ─── CONFIGURATION ────────────────────────────────────────────────────────
ALGOD_ADDRESS   = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN     = ""

ADMIN_MNEMONIC  = (
    "fog shine vehicle endless online practice lion goat initial problem budget "
    "ring truly hybrid myth journey reward rug guilt body rotate bracket stomach above mad"
)
BUYER_MNEMONIC = (
    "still rookie taste false spice index cat oval manage minor dutch betray fringe "
    "gesture liar hip produce pony offer develop spoon obvious drama about tree"
)

ASSET_ID        = 738130308   # ASA Dumbly avec decimals=6
RECEIVER_ADDR   = "YOZSV3LLBPCJRSNR2DXZBNR3MHZ43USP4OCU3YK4W46FUUQBJF45OWLNPA"

# ─── INIT CLIENT & CLÉS ───────────────────────────────────────────────────
admin_sk   = mnemonic.to_private_key(ADMIN_MNEMONIC)
admin_addr = account.address_from_private_key(admin_sk)
client     = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp         = client.suggested_params()

# ─── OPT-IN (si pas déjà fait) ─────────────────────────────────────────────
# ─── OPT-IN (si pas déjà fait) ─────────────────────────────────────────────
receiver_sk = mnemonic.to_private_key(BUYER_MNEMONIC)   # ← utilise bien le mnemonic du RECEIVER
optin = AssetTransferTxn(
    sender=RECEIVER_ADDR,
    sp=sp,
    receiver=RECEIVER_ADDR,
    amt=0,
    index=ASSET_ID,
)
stx = optin.sign(receiver_sk)                          # ← signé par receiver_sk, pas admin_sk
txid = client.send_transaction(stx)
wait_for_confirmation(client, txid, 4)
print(f"✅ {RECEIVER_ADDR} opt-in OK (ASA {ASSET_ID})")


# ─── TRANSFERT FRACTIONNEL ────────────────────────────────────────────────
# 0.5 Dumbly = 0.5 * 10^6 = 500_000 unités
fraction_units = 500_000
txn = AssetTransferTxn(
    sender=admin_addr,
    sp=sp,
    receiver=RECEIVER_ADDR,
    amt=fraction_units,
    index=ASSET_ID
)
signed = txn.sign(admin_sk)
txid = client.send_transaction(signed)
wait_for_confirmation(client, txid, 4)
print(f"→ {fraction_units} unités (0.5 Dumbly) envoyées à {RECEIVER_ADDR} (txID={txid})")

# ─── VÉRIFICATION DU SOLDE ───────────────────────────────────────────────
acct = client.account_info(RECEIVER_ADDR)
balance = next(a["amount"] for a in acct["assets"] if a["asset-id"] == ASSET_ID)
print(f"✅ Solde {RECEIVER_ADDR} = {balance} unités (fractions OK)")
