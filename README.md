# Tourist App - Crypto & Payment Integration

A modern tourist application with cryptocurrency and debit card payment integration, featuring Solana DEX integration, AWS deployment, React/Next.js frontend, and Python backend.

## Features

- 🏖️ Tourist booking and tour management
- 💳 Debit card payment integration (Stripe)
- 🪙 Cryptocurrency payments (Solana)
- 🔄 Solana DEX integration for token swaps
- ☁️ AWS cloud deployment ready
- 🎨 Modern React/Next.js frontend
- 🐍 Python FastAPI backend

## Project Structure

```
.
├── frontend/          # Next.js React application
├── backend/           # Python FastAPI backend
├── aws/              # AWS deployment configurations
└── docs/             # Documentation
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- AWS Account (for deployment)
- Solana wallet

### Installation

1. Install all dependencies:
```bash
npm run install-all
```

2. Set up environment variables:
- Copy `frontend/.env.example` to `frontend/.env.local`
- Copy `backend/.env.example` to `backend/.env`

3. Run the development servers:

Frontend:
```bash
npm run dev
```

Backend:
```bash
npm run backend
```

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy
- **Blockchain**: Solana Web3.js, Jupiter DEX API
- **Payments**: Stripe, Solana Wallet Adapter
- **Cloud**: AWS (EC2, RDS, S3, Lambda)

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOLANA_NETWORK=devnet
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_key
```

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost/tourist_db
SOLANA_RPC_URL=https://api.devnet.solana.com
JUPITER_API_URL=https://quote-api.jup.ag/v6
STRIPE_SECRET_KEY=your_stripe_secret
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

## License

MIT

