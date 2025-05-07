# README.md

## 1. Prérequis

- Python 3.8+ et `pip`
- Un compte TestNet Algorand avec des fonds (pour payer les frais de transactions)

## 2. Installation

1. Clone du dépôt et positionnement :
   ```bash
   git clone <url-de-ton-repo>
   cd algoland-tax-token/contracts
   ```
2. Création d’un environnement virtuel et installation des dépendances :
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # ou .\.venv\Scripts\activate sur Windows
   pip install --upgrade pip
   pip install -r requirements.txt  # ou pip install fastapi uvicorn algosdk python-dotenv httpx pytest
   ```

## 3. Configuration (`.env`)

Crée un fichier `.env` à la racine de `contracts/` et renseigne :

```dotenv
ALGOD_ADDRESS=https://testnet-api.4160.nodely.dev
ALGOD_TOKEN=

ADMIN_MNEMONIC="..."
TREASURY_MNEMONIC="..."
ASSET_ID=         # mis à jour après création de l’ASA
APP_ID=           # mis à jour après déploiement du smart-contract

BURN_ADDR=...
LP_ADDR=...
REWARDS_ADDR=...

# Si nécessaire (mnemonics pour opt-in)
BURN_MNEMONIC="..."
LP_MNEMONIC="..."
REWARDS_MNEMONIC="..."
```

## 4. Création de l’ASA “Dumbly”

```bash
python create_asa.py
# → note l’ASSET_ID généré et mets-le dans .env
```

## 5. Déploiement du smart-contract (taxe 9 % on-chain)

```bash
# (Re)compiler le TEAL avec la logique taxe
python tax_token.py

# Déployer le contrat
python deploy.py
# → note l’APP_ID généré et mets-le dans .env
```

## 6. Lancer l’API FastAPI

```bash
uvicorn service:app --reload
```

L’API tournera par défaut sur [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 7. Endpoints disponibles

| Méthode | URL                  | Description                                                                                                |
| ------- | -------------------- | ---------------------------------------------------------------------------------------------------------- |
| GET     | `/treasury-balance`  | Récupère le solde actuel de la treasury                                                                    |
| POST    | `/distribute-manual` | Redistribue des montants manuels vers burn/LP/rewards. Corps JSON : `{ "burn": X, "lp": Y, "rewards": Z }` |
| POST    | `/distribute-all`    | Redistribue automatiquement **tout** le solde en 3 parts égales                                            |

### Exemples

```bash
# Voir solde\
curl http://127.0.0.1:8000/treasury-balance

# Redistribution manuelle (50,20,30)
curl -X POST http://127.0.0.1:8000/distribute-manual \
  -H "Content-Type: application/json" \
  -d '{"burn":50,"lp":20,"rewards":30}'

# Redistribution automatique
curl -X POST http://127.0.0.1:8000/distribute-all
```

## 8. Tests automatisés (pytest)

```bash
# Installer si nécessaire
pip install pytest httpx

# Lancer le test de distribute-all
pytest test_distribute_all.py -q
```


