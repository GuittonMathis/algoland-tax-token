A PyTEAL smart contract paired with a React admin interface to manage a tax token on Algorand.

## Project Structure

```
algoland-tax-token/
├── contracts/            # Python backend
│   ├── scripts/          # CLI scripts: deploy, create_asa, opt-in, distribute, check_balance
│   ├── tests/            # PyTest unit tests
│   ├── service.py        # Helper functions: compile, deploy, transactions
│   └── tax_token.py      # Smart contract logic in PyTEAL
├── frontend/             # React frontend
│   └── admin/
│       ├── public/       # Static files
│       ├── src/          # React components and WalletContext
│       └── package.json  # Frontend dependencies
└── .gitignore
```

## Prerequisites

* Python 3.8+ and pip
* Node.js 18+ and npm (or yarn)
* Access to an Algorand node (TestNet, Sandbox, or third-party service)

## Installation

### Backend

```bash
cd contracts
# (Optional) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install py-algorand-sdk pyteal python-dotenv pytest
```

### Frontend

```bash
cd frontend/admin
npm install   # or yarn install
```

## Usage

1. **Deploy the smart contract**:

   ```bash
   cd contracts
   source .venv/bin/activate
   python scripts/deploy.py
   ```
2. **Create the ASA (tax-token)**:

   ```bash
   python scripts/create_asa.py
   ```
3. **Opt-in target accounts**:

   ```bash
   python scripts/optin_targets.py
   ```
4. **Distribute tokens**:

   ```bash
   python scripts/distribute.py
   ```
5. **Check balances**:

   ```bash
   python scripts/check_balance.py
   ```

To launch the React interface:

```bash
cd frontend/admin
npm start
```

Then open[ ](http://localhost:3000)[http://localhost:3000](http://localhost:3000).

##
