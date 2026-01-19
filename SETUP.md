# Setup Instructions

## Quick Start

### 1. Install Dependencies

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

Or use the convenience script:
```bash
npm run install-all
```

### 2. Set Up Environment Variables

**Frontend:**
```bash
cd frontend
cp env.example .env.local
# Edit .env.local with your actual values
```

**Backend:**
```bash
cd backend
cp env.example .env
# Edit .env with your actual values
```

### 3. Set Up Database

For local development with SQLite (default):
```bash
# Database will be created automatically
```

For PostgreSQL:
1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE tourist_db;
   ```
3. Update `DATABASE_URL` in `backend/.env`

### 4. Seed Initial Data

```bash
cd backend
python seed_data.py
```

This will create sample tours in the database.

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Configuration

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the dashboard
3. Add them to your environment variables:
   - `STRIPE_SECRET_KEY` (backend)
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (frontend)

### Solana Setup

1. The app uses Solana devnet by default
2. For mainnet, update `NEXT_PUBLIC_SOLANA_NETWORK=mainnet-beta`
3. Set your payment wallet address in environment variables

### Jupiter DEX Integration

The app uses Jupiter Aggregator API for token swaps. No additional setup needed, but you can customize:
- `NEXT_PUBLIC_JUPITER_API_URL` (default: https://quote-api.jup.ag/v6)

## Testing Payments

### Test Stripe Cards

Use Stripe test cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

### Test Solana Payments

1. Install Phantom or Solflare wallet
2. Connect to Solana devnet
3. Get test SOL from https://faucet.solana.com
4. Make a test payment

## Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are in use:
- Frontend: Change port in `package.json` scripts
- Backend: Change port in `uvicorn` command

### Database Connection Issues

- Check `DATABASE_URL` format
- Ensure PostgreSQL is running (if using PostgreSQL)
- Check database credentials

### Wallet Connection Issues

- Ensure you're using a compatible wallet (Phantom, Solflare)
- Check network settings (devnet vs mainnet)
- Clear browser cache if issues persist

## Production Deployment

See `aws/README.md` for AWS deployment instructions.

