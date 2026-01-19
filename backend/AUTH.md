# Authentication System Documentation

This document describes the comprehensive authentication system implemented for the Tourist App.

## Overview

The authentication system supports multiple login methods:
- **Email/Password** - Traditional authentication
- **Google OAuth2** - Gmail sign-in
- **GitHub OAuth2** - GitHub sign-in
- **Facebook OAuth2** (optional)
- **Apple OAuth2** (optional)

## Features

- JWT-based authentication
- Multiple OAuth2 providers
- User roles (User, Admin, Moderator)
- Protected routes with role-based access control
- Token refresh mechanism
- User profile management

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "username": "johndoe"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user",
    "avatar_url": null,
    "is_verified": false,
    "auth_provider": "email"
  }
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Get OAuth URL
```http
GET /auth/oauth/{provider}/url
```

**Example:**
```http
GET /auth/oauth/google/url
```

**Response:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "provider": "google"
}
```

#### Verify OAuth Token
```http
POST /auth/oauth/token
Content-Type: application/json

{
  "token": "oauth_access_token_from_provider",
  "provider": "google"  // or "github"
}
```

#### OAuth Callback
```http
GET /auth/{provider}/callback?code=AUTHORIZATION_CODE
```

This endpoint handles the OAuth callback and redirects to the frontend with the JWT token.

#### Get Current User
```http
GET /auth/me
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "avatar_url": "https://...",
  "is_verified": true,
  "auth_provider": "google"
}
```

#### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer {jwt_token}
```

## Protected Routes

### User Authentication Required

Some endpoints require authentication. Include the JWT token in the Authorization header:

```http
Authorization: Bearer {jwt_token}
```

### Admin-Only Routes

The following routes require admin privileges:
- `POST /tours` - Create tour
- `PUT /tours/{tour_id}` - Update tour
- `DELETE /tours/{tour_id}` - Delete tour
- `PATCH /bookings/{booking_id}` - Update booking

### Optional Authentication

Some routes work with or without authentication:
- `GET /bookings` - Can filter by current user if authenticated
- `POST /bookings` - Links booking to user if authenticated

## Frontend Integration

### Storing Token

After successful authentication, store the token:

```typescript
// After login/register
const response = await fetch('/auth/login', { ... });
const data = await response.json();
localStorage.setItem('auth_token', data.access_token);
```

### Using Token in Requests

The frontend API client should automatically include the token:

```typescript
// lib/api.ts
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Google OAuth Flow

1. **Get OAuth URL:**
   ```typescript
   const response = await fetch('/auth/oauth/google/url');
   const { url } = await response.json();
   window.location.href = url;
   ```

2. **Handle Callback:**
   The backend redirects to `/auth/callback?token={jwt_token}&success=true`
   
   ```typescript
   // In your callback page
   const params = new URLSearchParams(window.location.search);
   const token = params.get('token');
   if (token) {
     localStorage.setItem('auth_token', token);
     // Redirect to dashboard
   }
   ```

### Alternative: Direct Token Verification

If you're using a frontend OAuth library (like `@react-oauth/google`):

```typescript
// Get token from Google
const response = google.accounts.oauth2.initTokenClient({
  client_id: GOOGLE_CLIENT_ID,
  scope: 'email profile',
  callback: async (tokenResponse) => {
    // Verify token with backend
    const res = await fetch('/auth/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: tokenResponse.access_token,
        provider: 'google'
      })
    });
    const data = await res.json();
    localStorage.setItem('auth_token', data.access_token);
  }
});
response.requestAccessToken();
```

## Environment Variables

Add these to your `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Application URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Google OAuth2
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth2
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

## Setting Up OAuth Providers

### Google OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure consent screen
6. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
7. Copy Client ID and Client Secret

### GitHub OAuth2 Setup

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/auth/github/callback`
4. Copy Client ID and Client Secret

## User Model

The User model includes:
- `id` - Primary key
- `uuid` - Unique identifier
- `email` - Unique email address
- `username` - Optional unique username
- `full_name` - User's full name
- `hashed_password` - Bcrypt hashed password (nullable for OAuth users)
- `auth_provider` - Provider used (email, google, github, etc.)
- `provider_id` - OAuth provider's user ID
- `role` - User role (user, admin, moderator)
- `is_active` - Account active status
- `is_verified` - Email verification status
- `avatar_url` - Profile picture URL
- `created_at`, `updated_at`, `last_login` - Timestamps

## Security Best Practices

1. **JWT Secret Key**: Use a strong, random secret key in production
   ```bash
   openssl rand -hex 32
   ```

2. **HTTPS**: Always use HTTPS in production

3. **Token Expiration**: Tokens expire after 30 days (configurable)

4. **Password Requirements**: Implement strong password requirements on frontend

5. **Rate Limiting**: Consider adding rate limiting to auth endpoints

6. **Email Verification**: Implement email verification for email/password users

## Database Migration

Run the migration to create the users table:

```bash
# Create migration
alembic revision --autogenerate -m "Add user model"

# Apply migration
alembic upgrade head
```

Or use the initialization script:

```bash
python init_db.py
```

## Testing Authentication

### Test Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### Test Protected Route
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### "Could not validate credentials"
- Check if token is expired
- Verify token is included in Authorization header
- Ensure JWT_SECRET_KEY matches between token creation and verification

### "OAuth not configured"
- Ensure OAuth client ID and secret are set in environment variables
- Check that provider name matches exactly (case-sensitive)

### "Email already registered"
- User with that email already exists
- Try logging in instead, or use OAuth if account was created via OAuth

## Future Enhancements

- Email verification system
- Password reset functionality
- Two-factor authentication (2FA)
- Social login with more providers (Facebook, Apple, etc.)
- Account linking (link multiple OAuth providers to one account)
- Session management
- Refresh token rotation

