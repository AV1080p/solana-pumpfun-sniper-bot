# Frontend Core Logic Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Authentication Flow](#authentication-flow)
3. [State Management](#state-management)
4. [Payment Integration](#payment-integration)
5. [Component Architecture](#component-architecture)
6. [API Communication](#api-communication)
7. [Routing & Navigation](#routing--navigation)

---

## Architecture Overview

### Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Payment**: Stripe.js, Solana Web3.js
- **UI Notifications**: React Hot Toast

### Project Structure
```
frontend/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # User dashboard
│   ├── admin/             # Admin panel
│   └── ...
├── components/            # Reusable React components
├── contexts/              # React contexts
├── lib/                   # API clients and utilities
└── ...
```

---

## Authentication Flow

### Overview
The frontend implements JWT-based authentication with support for multiple auth providers (email/password, OAuth, MFA).

### Core Components

#### AuthContext (`contexts/AuthContext.tsx`)
**Purpose**: Manages global authentication state and provides auth methods.

**Key Features**:
- User state management
- Token storage (localStorage)
- Login/logout functions
- Token refresh logic
- Protected route checking

**State Structure**:
```typescript
{
  user: User | null
  token: string | null
  loading: boolean
  isAuthenticated: boolean
}
```

**Key Methods**:
- `login()`: Authenticates user and stores token
- `logout()`: Clears authentication state
- `register()`: Registers new user
- `refreshToken()`: Refreshes access token
- `checkAuth()`: Validates current token

**Authentication Flow**:
1. User submits credentials
2. API call to `/auth/login`
3. Receive JWT token and user data
4. Store token in localStorage
5. Update AuthContext state
6. Redirect to dashboard

#### ProtectedRoute Component (`components/ProtectedRoute.tsx`)
**Purpose**: Protects routes requiring authentication.

**Logic**:
1. Check AuthContext for authentication status
2. If not authenticated, redirect to login
3. If authenticated, render protected content
4. Optional role checking for admin routes

---

## State Management

### Zustand Store
**Purpose**: Global state management for application data.

**Store Structure**:
- User state (from AuthContext)
- Tour listings
- Booking data
- Payment state
- UI state (modals, notifications)

**Benefits**:
- Lightweight alternative to Redux
- Simple API
- TypeScript support
- No boilerplate

### Context Providers

#### WalletProvider (`components/WalletProvider.tsx`)
**Purpose**: Manages Solana wallet connections.

**Features**:
- Wallet adapter setup
- Wallet connection/disconnection
- Transaction signing
- Balance checking

**Supported Wallets**:
- Phantom
- Solflare
- Other Solana wallet adapters

---

## Payment Integration

### Overview
The frontend integrates with multiple payment methods: Stripe (cards), Solana, Bitcoin, and Ethereum.

### Core Components

#### PaymentModal (`components/PaymentModal.tsx`)
**Purpose**: Unified payment interface for all payment methods.

**Payment Methods**:
1. **Stripe (Card)**:
   - Uses Stripe Elements
   - Creates payment intent
   - Confirms payment
   - Handles 3D Secure

2. **Solana**:
   - Connects wallet
   - Gets payment address
   - Signs transaction
   - Verifies payment

3. **Bitcoin/Ethereum**:
   - Gets payment address
   - Displays QR code
   - Monitors transaction
   - Verifies payment

**Payment Flow**:
1. User selects payment method
2. Initialize payment method SDK
3. Collect payment details
4. Create payment intent/address
5. Process payment
6. Verify payment status
7. Update booking status
8. Show confirmation

#### Stripe Integration (`lib/api.ts`)
**Purpose**: Stripe payment processing.

**Key Functions**:
- `createPaymentIntent()`: Creates Stripe payment intent
- `confirmPayment()`: Confirms Stripe payment
- `processStripePayment()`: Complete Stripe payment flow

**Stripe Elements**:
- CardElement for card input
- PaymentElement for full payment form
- Automatic validation
- 3D Secure support

#### Solana Integration (`lib/solana.ts`)
**Purpose**: Solana blockchain payment processing.

**Key Functions**:
- `connectWallet()`: Connects Solana wallet
- `getPaymentAddress()`: Gets payment address
- `sendTransaction()`: Sends Solana transaction
- `verifyPayment()`: Verifies transaction

**Solana Web3.js**:
- Connection to Solana network
- Transaction creation
- Signature handling
- Balance checking

---

## Component Architecture

### Component Hierarchy

#### Layout Components
- **RootLayout**: App-wide layout with providers
- **Page Layouts**: Page-specific layouts

#### Feature Components

**TourCard** (`components/TourCard.tsx`):
- Displays tour information
- Handles tour selection
- Shows pricing (USD and SOL)
- Booking button

**ChatInterface** (`components/ChatInterface.tsx`):
- Real-time messaging
- Message history
- Translation support
- File attachments

**AIChatbot** (`components/AIChatbot.tsx`):
- AI conversation interface
- Message history
- Context management
- Response streaming

**CallInterface** (`components/CallInterface.tsx`):
- Voice/video call UI
- WebRTC integration
- Call controls
- Status indicators

**BroadcastAlerts** (`components/BroadcastAlerts.tsx`):
- System announcements
- Alert types (emergency, info)
- Dismissal handling
- Priority display

### Component Patterns

**Controlled Components**:
- Form inputs use controlled state
- Validation on change
- Error display

**Uncontrolled Components**:
- File inputs
- Third-party integrations

**Compound Components**:
- PaymentModal with method selection
- ChatInterface with message list

---

## API Communication

### API Client (`lib/api.ts`)
**Purpose**: Centralized API communication layer.

**Features**:
- Axios instance configuration
- Request interceptors (add auth token)
- Response interceptors (handle errors)
- Base URL configuration
- Error handling

**Request Interceptor**:
```typescript
// Adds Authorization header with JWT token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**Response Interceptor**:
```typescript
// Handles 401 errors (token expired)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error)
  }
)
```

### API Modules

**auth.ts**: Authentication endpoints
- Login, register, logout
- Token refresh
- OAuth callbacks

**adminApi.ts**: Admin endpoints
- User management
- Analytics
- System settings

**communicationApi.ts**: Communication endpoints
- Chat messages
- AI conversations
- Calls
- Forums

### Error Handling

**Error Types**:
- Network errors
- Validation errors (400)
- Authentication errors (401)
- Authorization errors (403)
- Not found errors (404)
- Server errors (500)

**Error Display**:
- Toast notifications (React Hot Toast)
- Inline form errors
- Error boundaries for React errors

---

## Routing & Navigation

### Next.js App Router

**Route Structure**:
- `/`: Home page
- `/auth/login`: Login page
- `/auth/register`: Registration page
- `/dashboard`: User dashboard
- `/bookings`: Bookings list
- `/admin`: Admin panel
- `/communication`: Communication hub

### Navigation Patterns

**Client-Side Navigation**:
- Next.js `Link` component
- `useRouter` hook for programmatic navigation
- Shallow routing for query params

**Route Protection**:
- `ProtectedRoute` wrapper component
- Middleware for route guards
- Redirect on unauthorized access

**Dynamic Routes**:
- `/tours/[id]`: Tour detail page
- `/bookings/[id]`: Booking detail page

---

## Data Fetching

### Server-Side Rendering (SSR)
- `getServerSideProps` for dynamic data
- Server components in App Router

### Client-Side Fetching
- `useEffect` hooks
- React Query (if implemented)
- SWR (if implemented)

### Data Flow
1. Component mounts
2. Check cache/localStorage
3. Fetch from API if needed
4. Update state
5. Re-render component

---

## Form Handling

### Form Patterns

**Controlled Forms**:
- React state for form values
- `onChange` handlers
- Validation on submit/blur

**Form Validation**:
- Client-side validation
- API validation feedback
- Error message display

**Form Libraries**:
- React Hook Form (if implemented)
- Formik (if implemented)
- Native React state

---

## UI/UX Patterns

### Loading States
- Skeleton loaders
- Spinner components
- Progress indicators

### Error States
- Error boundaries
- Fallback UI
- Retry mechanisms

### Success States
- Toast notifications
- Success messages
- Confirmation dialogs

### Responsive Design
- Tailwind CSS breakpoints
- Mobile-first approach
- Adaptive layouts

---

## Performance Optimization

### Code Splitting
- Dynamic imports
- Route-based code splitting
- Component lazy loading

### Image Optimization
- Next.js Image component
- Lazy loading
- Responsive images

### Caching Strategies
- localStorage for tokens
- API response caching
- Static asset caching

---

## Security Considerations

### Token Storage
- JWT tokens in localStorage
- Refresh token rotation
- Token expiration handling

### XSS Prevention
- React's built-in escaping
- Sanitize user input
- Content Security Policy

### CSRF Protection
- SameSite cookies
- CSRF tokens (if implemented)

---

## Testing Considerations

### Component Testing
- React Testing Library
- Jest for unit tests
- Component snapshots

### Integration Testing
- API mocking
- User flow testing
- E2E testing (if implemented)

---

## Build & Deployment

### Build Process
- `npm run build`: Production build
- `npm run dev`: Development server
- `npm run lint`: Code linting

### Environment Variables
- `.env.local`: Local development
- `.env.production`: Production config
- API URLs, keys, etc.

### Deployment
- Static export (if configured)
- Server-side rendering
- Docker containerization

