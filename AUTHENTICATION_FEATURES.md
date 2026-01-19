# User Management & Authentication Features

This document describes the comprehensive authentication and user management system that has been implemented.

## ✅ Implemented Features

### 1. SSO & Identity Management
- **Social Login**: Google, GitHub (with support for Facebook, Apple)
- **SAML 2.0**: Full SAML SSO support with metadata generation
- **OpenID Connect (OIDC)**: Complete OIDC authentication flow
- **Multiple Auth Providers**: Users can authenticate via email, OAuth, SAML, or OIDC

### 2. Multi-Factor Authentication (MFA)
- **TOTP Support**: Time-based one-time passwords via authenticator apps
- **QR Code Generation**: Automatic QR code generation for easy setup
- **Backup Codes**: 10 backup codes generated for account recovery
- **MFA Device Management**: Track and manage multiple MFA devices
- **MFA Verification**: Required during login when enabled

### 3. Session Management
- **Refresh Tokens**: Long-lived refresh tokens for session renewal
- **Device Tracking**: Track devices, IP addresses, and user agents
- **Session Limits**: Configurable maximum sessions per user
- **Session Revocation**: Users can revoke individual or all sessions
- **Automatic Cleanup**: Expired sessions are automatically marked

### 4. Role-Based Access Control (RBAC)
- **Granular Permissions**: Fine-grained permission system
- **Role Permissions**: Default permissions for User, Moderator, Admin roles
- **User-Specific Permissions**: Override permissions for individual users
- **Permission Checking**: API endpoints for permission verification
- **Permission Management**: Admin endpoints to grant/revoke permissions

### 5. Invitation & Onboarding Workflows
- **User Invitations**: Admin can invite users with specific roles
- **Invitation Tokens**: Secure token-based invitation system
- **Invitation Expiry**: Configurable expiration (default 7 days)
- **Invitation Management**: List, cancel, and resend invitations
- **Onboarding Flow**: Accept invitation and create account

## 📁 Backend Structure

### New Database Models
- `UserSession`: Session tracking with refresh tokens
- `MFADevice`: MFA device registration
- `Invitation`: User invitation system
- `Permission`: Granular permissions
- `RolePermission`: Role-to-permission mapping
- `UserPermission`: User-specific permission overrides
- `SAMLProvider`: SAML identity provider configuration
- `OIDCProvider`: OpenID Connect provider configuration

### New Services
- `mfa_service.py`: MFA management (TOTP, backup codes)
- `session_service.py`: Session management
- `invitation_service.py`: Invitation workflows
- `saml_service.py`: SAML 2.0 authentication
- `oidc_service.py`: OpenID Connect authentication
- `rbac_service.py`: Role-based access control

### API Endpoints

#### Authentication
- `POST /auth/login` - Login with email/password (supports MFA)
- `POST /auth/login/mfa-verify` - Verify MFA code after login
- `POST /auth/register` - Register new user
- `POST /auth/refresh` - Refresh access token (legacy)
- `POST /auth/sessions/refresh` - Refresh using refresh token

#### MFA
- `POST /auth/mfa/setup` - Setup TOTP MFA
- `POST /auth/mfa/verify-enable` - Verify and enable MFA
- `POST /auth/mfa/verify` - Verify MFA code
- `POST /auth/mfa/disable` - Disable MFA
- `POST /auth/mfa/regenerate-backup-codes` - Regenerate backup codes
- `GET /auth/mfa/devices` - List MFA devices

#### Sessions
- `GET /auth/sessions` - List user sessions
- `POST /auth/sessions/revoke` - Revoke a session
- `POST /auth/sessions/revoke-all` - Revoke all sessions

#### Invitations
- `POST /auth/invitations` - Create invitation (Admin)
- `GET /auth/invitations` - List invitations
- `POST /auth/invitations/accept` - Accept invitation
- `POST /auth/invitations/{id}/cancel` - Cancel invitation
- `POST /auth/invitations/{id}/resend` - Resend invitation

#### SAML/OIDC
- `POST /auth/saml/initiate` - Initiate SAML SSO
- `GET /auth/saml/metadata/{provider_id}` - Get SAML metadata
- `POST /auth/oidc/initiate` - Initiate OIDC SSO
- `GET /auth/oidc/{provider_id}/callback` - OIDC callback

#### RBAC
- `GET /auth/permissions` - Get user permissions
- `POST /auth/permissions/grant` - Grant permission (Admin)
- `POST /auth/permissions/revoke` - Revoke permission (Admin)
- `POST /auth/permissions/create` - Create permission (Admin)
- `POST /auth/permissions/initialize` - Initialize default permissions (Admin)

## 📁 Frontend Structure

### New Components
- `contexts/AuthContext.tsx`: Authentication context provider
- `components/ProtectedRoute.tsx`: Route protection component
- `app/auth/login/page.tsx`: Login page with MFA support
- `app/auth/register/page.tsx`: Registration page

### New Utilities
- `lib/auth.ts`: Authentication API client and utilities

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# MFA Configuration
MFA_ISSUER_NAME=Tourist App

# Session Configuration
SESSION_EXPIRY_HOURS=24
REFRESH_TOKEN_EXPIRY_DAYS=30
MAX_SESSIONS_PER_USER=10

# Invitation Configuration
INVITATION_EXPIRY_DAYS=7
```

## 🚀 Usage Examples

### Setting Up MFA

1. User calls `POST /auth/mfa/setup` with device name
2. Backend returns QR code and secret
3. User scans QR code with authenticator app
4. User calls `POST /auth/mfa/verify-enable` with code
5. MFA is enabled, backup codes are returned

### Using Invitations

1. Admin calls `POST /auth/invitations` with email and role
2. Invitation token is generated
3. User receives invitation link
4. User calls `POST /auth/invitations/accept` with token and password
5. Account is created and user is logged in

### Checking Permissions

```python
from services.rbac_service import RBACService

rbac_service = RBACService()
has_permission = await rbac_service.check_permission(user, "tours.create", db)
```

### Using Protected Routes

```tsx
import { ProtectedRoute } from '@/components/ProtectedRoute'

<ProtectedRoute requireRole={['admin', 'moderator']}>
  <AdminPanel />
</ProtectedRoute>
```

## 📝 Database Migration

After adding the new models, run:

```bash
# Create migration
alembic revision --autogenerate -m "Add auth features: MFA, sessions, invitations, RBAC"

# Apply migration
alembic upgrade head
```

## 🔐 Security Features

1. **Password Hashing**: Bcrypt with salt
2. **JWT Tokens**: Secure token-based authentication
3. **Refresh Tokens**: Long-lived tokens for session renewal
4. **MFA**: TOTP with backup codes
5. **Session Tracking**: Device and IP tracking
6. **Permission System**: Granular access control
7. **Invitation Tokens**: Cryptographically secure tokens

## 🎯 Next Steps

1. Run database migrations to create new tables
2. Initialize default permissions: `POST /auth/permissions/initialize`
3. Configure OAuth providers (Google, GitHub) in `.env`
4. Set up SAML/OIDC providers if needed
5. Test authentication flows
6. Configure frontend API URL in `frontend/.env.local`

## 📚 Additional Notes

- MFA is optional but recommended for admin accounts
- Sessions are automatically cleaned up when expired
- Invitations expire after 7 days by default
- Admin role has all permissions by default
- OAuth users don't need passwords
- SAML/OIDC require additional provider configuration

