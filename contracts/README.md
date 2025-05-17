## Backend (contracts/)

A FastAPI service and a set of Python scripts to manage the Dumbly ASA treasury on Algorand.

### Prerequisites

* Python 3.8+ (tested on 3.10)
* `pip install python-dotenv algosdk fastapi pydantic uvicorn`


### Environment

In `contracts/.env`, define:

```ini
ALGOD_ADDRESS=https://testnet-api.4160.nodely.dev  # or your Algod endpoint
ALGOD_TOKEN=
ADMIN_MNEMONIC="<25-word admin mnemonic>"
TREASURY_MNEMONIC="<25-word treasury mnemonic>"
ASSET_ID=<your ASA id>
BURN_ADDR=<burn account address>
LP_ADDR=<LP account address>
REWARDS_ADDR=<rewards account address>
BURN_MNEMONIC="<burn mnemonic>"
LP_MNEMONIC="<lp mnemonic>"
REWARDS_MNEMONIC="<rewards mnemonic>"
APP_ID=<your app id>  # optional, used by tests
BUYER_MNEMONIC="<buyer mnemonic>"  # for test_tax.py
```

### Quickstart / Demo Flow

Run exactly these steps (as in `demo_mi_projet.sh`):

```bash
# 1) Create the ASA
cd contracts
python scripts/create_asa.py
# → note new ASSET_ID, update .env

# 2) Opt-in the targets
python scripts/optin_targets.py

# 3) Compile & deploy the stateful contract
python tax_token.py
python scripts/deploy.py
# → note new APP_ID, update .env

# 4) Test the 9% tax on-chain
python tests/test_tax.py

# 5) Check the treasury balance
curl http://127.0.0.1:8000/treasury-balance && echo

# 6) Manual distribution (example: 10/20/30)
curl -X POST http://127.0.0.1:8000/distribute-manual \
  -H "Content-Type: application/json" \
  -d '{"burn":10,"lp":20,"rewards":30}' && echo

# 7) Automatic distribution (1/3 each)
curl -X POST http://127.0.0.1:8000/distribute-all && echo
```

### Scripts

All scripts live under `contracts/` or `contracts/scripts/`:

* **scripts/create\_asa.py**: Create the Dumbly ASA and print `asset-id`.
* **scripts/optin\_targets.py**: Opt-in Burn, LP, and Rewards accounts.
* **tax\_token.py**: Generate `approval.teal` & `clear.teal` from PyTeal.
* **scripts/deploy.py**: Compile and deploy the application.
* **scripts/distribute.py**: Standalone equal-split distribution (useful outside FastAPI).
* **scripts/check\_balance.py**: Print current treasury balance.
* **contracts/check\_targets\_balance.py**: Print balances of Burn, LP, Rewards.

### API Server

* **service.py**: FastAPI app exposing:

  * `GET /treasury-balance`  → returns `{ "treasury_balance": <number> }`
  * `POST /distribute-manual` → accepts `{ burn, lp, rewards }`
  * `POST /distribute-all`    → splits entire balance 1/3 each

Start server:

```bash
uvicorn service:app --reload
```

### Tests

Pytest scripts under `contracts/tests/`:

* `test_tax.py`       → validates the 9% tax logic
* `test_fraction.py`  → checks fractional transfers
* `test_distribute_all.py` → end-to-end distribution via API


```



