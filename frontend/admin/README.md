## Frontend (frontend/admin/)

A React-based admin dashboard for viewing the treasury balance and triggering distributions.

### Prerequisites

* Node.js 16+ / npm or Yarn
* Backend running at `http://localhost:8000`

### Install & Run

```bash
cd frontend/admin
npm install    # or yarn install
npm start      # or yarn start
```

* Opens at `http://localhost:3000`
* Uses `proxy` in `package.json` to forward `/` requests to backend

### Build for Production

```bash
npm run build  # or yarn build
```

