# Usage Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Authentication](#authentication)
5. [Payment Processing](#payment-processing)
6. [Admin Operations](#admin-operations)
7. [API Usage](#api-usage)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
- Python 3.9+ (Backend)
- Node.js 18+ (Frontend)
- PostgreSQL 12+ (Database)
- Git

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd demo_project
```

2. **Set up backend** (see [Backend Setup](#backend-setup))
3. **Set up frontend** (see [Frontend Setup](#frontend-setup))
4. **Start services**
```bash
# Backend
cd backend
python main.py

# Frontend (new terminal)
cd frontend
npm run dev
```

---

## Backend Setup

### 1. Environment Configuration

Create `.env` file in `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tourist_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Solana
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_NETWORK=mainnet-beta

# Encryption
ENCRYPTION_KEY=your-encryption-key-32-bytes

# Frontend URL
FRONTEND_URL=http://localhost:3000

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Data Retention (Optional)
RETENTION_BOOKING_DAYS=2555
RETENTION_PAYMENT_DAYS=2555
RETENTION_FEEDBACK_DAYS=365
```

### 2. Database Setup

**Option A: Using Docker Compose**
```bash
cd backend
docker-compose -f docker-compose.db.yml up -d
```

**Option B: Manual PostgreSQL Setup**
```bash
# Create database
createdb tourist_db

# Run migrations
cd backend
alembic upgrade head

# Or initialize database
python init_db.py
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Using CLI
python db_cli.py init

# Or using Python
python init_db.py
```

### 5. Seed Data (Optional)

```bash
python seed_data.py
```

### 6. Run Backend

```bash
# Development
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Setup

```bash
# Health check
curl http://localhost:8000/health

# API docs
# Visit http://localhost:8000/docs
```

---

## Frontend Setup

### 1. Environment Configuration

Create `.env.local` file in `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_SOLANA_NETWORK=devnet
```

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Run Development Server

```bash
npm run dev
```

### 4. Build for Production

```bash
npm run build
npm start
```

### 5. Verify Setup

Visit `http://localhost:3000` in your browser.

---

## Authentication

### User Registration

**API Endpoint**: `POST /auth/register`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "username": "johndoe"
}
```

**Response**:
```json
{
  "success": true,
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "role": "user"
  }
}
```

**Frontend Usage**:
```typescript
import { register } from '@/lib/auth'

const handleRegister = async (email: string, password: string) => {
  try {
    const response = await register(email, password)
    localStorage.setItem('token', response.access_token)
    // Redirect to dashboard
  } catch (error) {
    // Handle error
  }
}
```

### User Login

**API Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "user": { ... },
  "expires_at": "2024-01-01T00:00:00Z"
}
```

**MFA Flow**:
If MFA is enabled, response includes `mfa_required: true`. Use `/auth/login/mfa-verify` endpoint with the code.

### OAuth Login

**Google OAuth**:
1. Redirect user to `/auth/oauth/google/url`
2. User authorizes on Google
3. Redirect to `/auth/google/callback?code=...`
4. Receive token and redirect to frontend

**GitHub OAuth**:
1. Redirect user to `/auth/oauth/github/url`
2. User authorizes on GitHub
3. Redirect to `/auth/github/callback?code=...`
4. Receive token and redirect to frontend

### MFA Setup

**Step 1: Setup TOTP**
```bash
POST /auth/mfa/setup
{
  "device_name": "iPhone 12"
}

# Response includes QR code URL and secret
```

**Step 2: Verify and Enable**
```bash
POST /auth/mfa/verify-enable
{
  "code": "123456"
}
```

**Step 3: Login with MFA**
1. Login with email/password
2. Receive `mfa_required: true`
3. Submit MFA code to `/auth/login/mfa-verify`

### Session Management

**Get User Sessions**:
```bash
GET /auth/sessions
Authorization: Bearer <token>
```

**Revoke Session**:
```bash
POST /auth/sessions/revoke
{
  "session_id": 1
}
```

**Revoke All Sessions**:
```bash
POST /auth/sessions/revoke-all
```

---

## Payment Processing

### Stripe Payment (Card)

**Step 1: Create Payment Intent**
```bash
POST /payments/stripe/intent
{
  "tour_id": 1,
  "amount": 100.00,
  "currency": "usd",
  "user_email": "user@example.com"
}

# Response includes client_secret
```

**Step 2: Confirm Payment**
```bash
POST /payments/stripe/confirm
{
  "payment_intent_id": "pi_...",
  "tour_id": 1,
  "user_email": "user@example.com"
}
```

**Frontend Example**:
```typescript
import { loadStripe } from '@stripe/stripe-js'

const stripe = await loadStripe(STRIPE_PUBLISHABLE_KEY)
const { error } = await stripe.confirmCardPayment(clientSecret, {
  payment_method: {
    card: cardElement,
    billing_details: { email: userEmail }
  }
})
```

### Solana Payment

**Step 1: Get Payment Address**
```bash
GET /payments/address/solana

# Response includes Solana address
```

**Step 2: Send Transaction**
User sends SOL from their wallet to the payment address.

**Step 3: Verify Payment**
```bash
POST /payments/solana
{
  "tour_id": 1,
  "transaction_hash": "signature_here",
  "amount": 1.5,
  "currency": "solana",
  "public_key": "wallet_public_key",
  "user_email": "user@example.com"
}
```

**Step 4: Check Status**
```bash
GET /payments/solana/status/{signature}
```

**Frontend Example**:
```typescript
import { useWallet } from '@solana/wallet-adapter-react'

const { publicKey, sendTransaction } = useWallet()

// Get payment address from API
const { address } = await getPaymentAddress('solana')

// Create and send transaction
const transaction = new Transaction().add(
  SystemProgram.transfer({
    fromPubkey: publicKey,
    toPubkey: new PublicKey(address),
    lamports: amount * LAMPORTS_PER_SOL
  })
)

const signature = await sendTransaction(transaction, connection)
```

### Bitcoin/Ethereum Payment

**Step 1: Get Payment Address**
```bash
GET /payments/address/bitcoin
GET /payments/address/ethereum
```

**Step 2: Send Transaction**
User sends cryptocurrency to the payment address.

**Step 3: Verify Payment**
```bash
POST /payments/bitcoin
POST /payments/ethereum
{
  "tour_id": 1,
  "transaction_hash": "tx_hash",
  "amount": 0.001,
  "currency": "bitcoin",
  "user_email": "user@example.com"
}
```

### Payment Refund

**Stripe Refund**:
```bash
POST /payments/stripe/refund
{
  "payment_id": 1,
  "amount": 50.00  # Optional, full refund if omitted
}
```

---

## Admin Operations

### User Management

**List Users**:
```bash
GET /admin/users?skip=0&limit=100&search=email
Authorization: Bearer <admin_token>
```

**Get User**:
```bash
GET /admin/users/{user_id}
```

**Update User**:
```bash
PATCH /admin/users/{user_id}
{
  "role": "admin",
  "is_active": true
}
```

**Delete User**:
```bash
DELETE /admin/users/{user_id}
```

### Analytics

**Get Analytics**:
```bash
GET /admin/analytics
```

**Response includes**:
- Total users, bookings, revenue
- Active users (30 days)
- Revenue by month
- Top tours
- Recent activity

### Billing Summary

```bash
GET /admin/billing
```

**Response includes**:
- Total revenue
- Revenue this month/last month
- Pending/failed payments
- Revenue by payment method
- Invoice summary

### Audit Logs

```bash
GET /admin/audit-logs?user_id=1&action=user.update&limit=100
```

### System Health

```bash
GET /admin/health
```

**Response includes**:
- Database status
- API status
- Service health
- Connection pool stats

### Data Export (GDPR)

```bash
POST /security/data/export
{
  "user_id": 1,
  "format": "json"  # or "csv"
}
```

### Data Deletion (GDPR)

```bash
POST /security/data/delete
{
  "user_id": 1,
  "anonymize": true
}
```

### Backup Management

**Create Backup**:
```bash
POST /security/backup/create
{
  "backup_name": "backup_20240101",
  "encrypt": true
}
```

**List Backups**:
```bash
GET /security/backup/list
```

**Restore Backup**:
```bash
POST /security/backup/restore
{
  "backup_path": "backups/backup_20240101.sql",
  "drop_existing": false,
  "encrypted": true
}
```

---

## API Usage

### Authentication Headers

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

### Error Responses

**400 Bad Request**:
```json
{
  "detail": "Validation error message"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden**:
```json
{
  "detail": "Not enough permissions"
}
```

**404 Not Found**:
```json
{
  "detail": "Resource not found"
}
```

### Pagination

Many list endpoints support pagination:
```
GET /admin/users?skip=0&limit=100
```

### Filtering

Some endpoints support filtering:
```
GET /admin/audit-logs?user_id=1&action=user.update&start_date=2024-01-01
```

### API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Troubleshooting

### Backend Issues

**Database Connection Error**:
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check database credentials
- Test connection: `psql $DATABASE_URL`

**Migration Errors**:
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

**Port Already in Use**:
```bash
# Change port in uvicorn command
uvicorn main:app --port 8001
```

### Frontend Issues

**API Connection Error**:
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS settings in backend
- Verify backend is running

**Build Errors**:
```bash
# Clear cache and rebuild
rm -rf .next
npm run build
```

**TypeScript Errors**:
```bash
# Check types
npm run type-check
```

### Payment Issues

**Stripe Payment Fails**:
- Verify Stripe keys in `.env`
- Check webhook endpoint configuration
- Review Stripe dashboard for errors

**Solana Payment Not Verified**:
- Check RPC endpoint connectivity
- Verify transaction signature
- Check network (mainnet vs devnet)

**Crypto Payment Timeout**:
- Increase timeout in API calls
- Check blockchain explorer for transaction status
- Verify payment address is correct

### Authentication Issues

**Token Expired**:
- Use refresh token endpoint
- Re-authenticate if refresh fails
- Check token expiration settings

**MFA Not Working**:
- Verify TOTP secret is correct
- Check device time synchronization
- Regenerate backup codes if needed

**OAuth Callback Fails**:
- Verify OAuth credentials
- Check redirect URLs in provider settings
- Review callback endpoint logs

### Database Issues

**Connection Pool Exhausted**:
- Increase pool size in `database.py`
- Check for connection leaks
- Review connection timeout settings

**Migration Conflicts**:
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Review and edit migration file
# Apply migration
alembic upgrade head
```

**Backup/Restore Fails**:
- Verify backup file exists
- Check file permissions
- Verify encryption key if encrypted
- Check disk space

---

## Best Practices

### Security
- Never commit `.env` files
- Use strong JWT secret keys
- Enable MFA for admin accounts
- Regularly rotate encryption keys
- Monitor audit logs

### Performance
- Use connection pooling
- Implement caching where appropriate
- Optimize database queries
- Use pagination for large datasets
- Monitor API response times

### Development
- Use environment variables for configuration
- Write tests for critical paths
- Document API changes
- Follow code style guidelines
- Use version control

### Deployment
- Use HTTPS in production
- Set up monitoring and alerts
- Configure automated backups
- Use Docker for consistent environments
- Implement CI/CD pipelines

---

## Additional Resources

- **API Documentation**: `http://localhost:8000/docs`
- **Backend Documentation**: See `backend/CORE_LOGIC.md`
- **Frontend Documentation**: See `frontend/CORE_LOGIC.md`
- **Technical Terms**: See `TECHNICAL_TERMS.md`

