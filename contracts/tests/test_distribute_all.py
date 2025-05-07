import os
import subprocess
import pytest
from fastapi.testclient import TestClient
from algosdk import mnemonic, account
from algosdk.v2client import algod
from service import app, ASSET_ID, TREASURY_MNEMONIC

client_api = TestClient(app)

@pytest.fixture(scope="module")
def algod_client():
    return algod.AlgodClient(os.getenv("ALGOD_TOKEN",""), os.getenv("ALGOD_ADDRESS"))

@pytest.fixture(scope="module")
def treasury_sk():
    return mnemonic.to_private_key(TREASURY_MNEMONIC)

@pytest.fixture(scope="module")
def treasury_addr(treasury_sk):
    return account.address_from_private_key(treasury_sk)

def test_distribute_all(algod_client, treasury_sk, treasury_addr):
    # 1) On crédite la treasury en lançant le script test_tax.py
    subprocess.run(["python", "tests/test_tax.py"], check=True)


    # 2) Vérifier le solde initial (>= 3)
    acct = algod_client.account_info(treasury_addr)
    total = next((a["amount"] for a in acct.get("assets", []) if a["asset-id"] == ASSET_ID), 0)
    assert total >= 3, f"Solde trop faible ({total}) pour tester distribute-all"

    # 3) Appel de l’API distribute-all
    resp = client_api.post("/distribute-all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

    # 4) Vérifier que burn + lp + rewards = total initial
    burn = data["distributed"]["burn"]
    lp = data["distributed"]["lp"]
    rewards = data["distributed"]["rewards"]
    assert burn + lp + rewards == total

    # 5) Vérifier que la treasury est vidée
    acct_after = algod_client.account_info(treasury_addr)
    new_total = next((a["amount"] for a in acct_after.get("assets", []) if a["asset-id"] == ASSET_ID), 0)
    assert new_total == 0
