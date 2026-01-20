# User Management & Authentication Documentation

This document describes the comprehensive authentication and user management features implemented in the application.

## Table of Contents

1. [Social Login (OAuth 2.0)](#social-login-oauth-20)
2. [SAML/OIDC SSO](#samloidc-sso)
3. [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)
4. [Session Management](#session-management)
5. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
6. [Invitation & Onboarding](#invitation--onboarding)
7. [API Endpoints](#api-endpoints)

## Social Login (OAuth 2.0)

The application supports OAuth 2.0 authentication with multiple providers:

### Supported Providers

- **Google** - Google Sign-In
- **GitHub** - GitHub OAuth
- **Facebook** - Facebook Login (configured but not fully implemented)
- **Apple** - Apple Sign-In (configured but not fully implemented)

### Configuration

Set up OAuth credentials in your `.env` file:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### Usage

**Get OAuth URL:**
```bash
GET /auth/oauth/{provider}/url
```

**Handle OAuth Callback:**
```bash
GET /auth/{provider}/callback?code={authorization_code}
```

**Verify OAuth Token:**
```bash
POST /auth/oauth/token
{
  "token": "oauth_access_token",
  "provider": "google"
}
```

## SAML/OIDC SSO

### SAML 2.0

SAML 2.0 support for enterprise SSO integration.

**Configuration:**
- Configure SAML providers in the database via `SAMLProvider` model
- Requires X.509 certificate from identity provider
- Supports both SSO and Single Logout (SLO)

**Endpoints:**
- `POST /auth/saml/initiate` - Initiate SAML SSO
- `GET /auth/saml/metadata/{provider_id}` - Get SAML metadata

**Setup:**
1. Create SAML provider record in database
2. Configure entity ID, SSO URL, and X.509 certificate
3. Share SP metadata with identity provider

### OpenID Connect (OIDC)

OIDC support for modern identity providers.

**Configuration:**
- Configure OIDC providers via `OIDCProvider` model
- Requires issuer URL, client ID, and client secret
- Supports standard OIDC flows

**Endpoints:**
- `POST /auth/oidc/initiate` - Get authorization URL
- `GET /auth/oidc/{provider_id}/callback` - Handle OIDC callback

**Setup:**
1. Create OIDC provider record in database
2. Configure issuer, endpoints, and client credentials
3. Set up redirect URI in identity provider

## Multi-Factor Authentication (MFA)

### TOTP (Time-based One-Time Password)

Users can enable TOTP using authenticator apps like Google Authenticator, Authy, etc.

**Setup Flow:**
1. User requests MFA setup: `POST /auth/mfa/setup`
2. System generates QR code and secret
3. User scans QR code with authenticator app
4. User verifies with a code: `POST /auth/mfa/verify-enable`
5. System enables MFA and generates backup codes

**Endpoints:**
- `POST /auth/mfa/setup` - Setup TOTP (returns QR code)
- `POST /auth/mfa/verify-enable` - Verify and enable MFA
- `POST /auth/mfa/verify` - Verify MFA code during login
- `POST /auth/mfa/disable` - Disable MFA (requires password)
- `POST /auth/mfa/regenerate-backup-codes` - Generate new backup codes
- `GET /auth/mfa/devices` - List MFA devices

**Backup Codes:**
- Generated when MFA is enabled
- Can be used if authenticator device is lost
- Single-use codes
- Can be regenerated

**Configuration:**
```env
MFA_ISSUER_NAME=Tourist App
```

### Login with MFA

When MFA is enabled:
1. User logs in with email/password
2. System returns `mfa_required: true`
3. User provides MFA code via `POST /auth/login/mfa-verify`
4. System creates session and returns tokens

## Session Management

Comprehensive session management with refresh tokens and device tracking.

### Features

- **Session Tokens**: Secure session identifiers
- **Refresh Tokens**: Long-lived tokens for refreshing access tokens
- **Device Tracking**: Track devices and IP addresses
- **Session Limits**: Configurable maximum sessions per user
- **Session Revocation**: Revoke individual or all sessions

### Configuration

```env
SESSION_EXPIRY_HOURS=24
REFRESH_TOKEN_EXPIRY_DAYS=30
MAX_SESSIONS_PER_USER=10
```

### Endpoints

- `POST /auth/sessions/refresh` - Refresh access token
- `GET /auth/sessions` - List all user sessions
- `POST /auth/sessions/revoke` - Revoke a specific session
- `POST /auth/sessions/revoke-all` - Revoke all sessions

### Session Lifecycle

1. **Login**: Creates new session with access and refresh tokens
2. **Token Refresh**: Use refresh token to get new access token
3. **Session Expiry**: Sessions expire after configured time
4. **Session Revocation**: User or admin can revoke sessions

## Role-Based Access Control (RBAC)

Granular permission system with role-based and user-specific permissions.

### Roles

- **USER**: Standard user with basic permissions
- **MODERATOR**: Extended permissions for content moderation
- **ADMIN**: Full access to all features

### Permission Structure

Permissions follow the format: `{resource}.{action}`

Examples:
- `tours.view` - View tours
- `tours.create` - Create tours
- `bookings.view_own` - View own bookings
- `users.view` - View users (moderator/admin)

### Default Permissions

**USER:**
- `bookings.view_own`
- `bookings.create`
- `tours.view`
- `profile.view_own`
- `profile.update_own`
- `invoices.view_own`
- `feedback.create`

**MODERATOR:**
- All USER permissions plus:
- `bookings.view`
- `bookings.update`
- `tours.update`
- `users.view`
- `feedback.view`
- `feedback.update`

**ADMIN:**
- All permissions (`*`)

### Endpoints

- `GET /auth/permissions` - Get user's permissions
- `POST /auth/permissions/grant` - Grant permission to user (Admin)
- `POST /auth/permissions/revoke` - Revoke permission from user (Admin)
- `POST /auth/permissions/create` - Create new permission (Admin)
- `POST /auth/permissions/initialize` - Initialize default permissions (Admin)

### Usage in Code

```python
from services.rbac_service import RBACService

rbac = RBACService()

# Check permission
if await rbac.check_permission(user, "tours.create", db):
    # User can create tours
    pass

# Require permission (raises exception if not granted)
await rbac.require_permission(user, "tours.create", db)
```

## Invitation & Onboarding

User invitation system for controlled onboarding.

### Features

- **Email Invitations**: Send invitations via email
- **Role Assignment**: Assign roles during invitation
- **Token-based**: Secure invitation tokens
- **Expiry Management**: Configurable invitation expiry
- **Status Tracking**: Track invitation status (pending, accepted, expired, cancelled)

### Configuration

```env
INVITATION_EXPIRY_DAYS=7
FRONTEND_URL=http://localhost:3000
```

### Endpoints

- `POST /auth/invitations` - Create invitation (Admin)
- `GET /auth/invitations` - List invitations
- `POST /auth/invitations/accept` - Accept invitation and create account
- `POST /auth/invitations/{id}/cancel` - Cancel invitation
- `POST /auth/invitations/{id}/resend` - Resend invitation

### Invitation Flow

1. **Admin creates invitation**: Provides email and role
2. **System generates token**: Secure token with expiry
3. **User receives invitation**: Email with invitation link
4. **User accepts**: Creates account with provided password
5. **Account created**: User is automatically verified

## API Endpoints

### Authentication

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/register` | POST | Register new user | None |
| `/auth/login` | POST | Login with email/password | None |
| `/auth/login/mfa-verify` | POST | Verify MFA after login | None |
| `/auth/oauth/token` | POST | Verify OAuth token | None |
| `/auth/oauth/{provider}/url` | GET | Get OAuth URL | None |
| `/auth/{provider}/callback` | GET | OAuth callback | None |
| `/auth/me` | GET | Get current user | User |
| `/auth/refresh` | POST | Refresh token | User |

### MFA

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/mfa/setup` | POST | Setup TOTP | User |
| `/auth/mfa/verify-enable` | POST | Verify and enable MFA | User |
| `/auth/mfa/verify` | POST | Verify MFA code | User |
| `/auth/mfa/disable` | POST | Disable MFA | User |
| `/auth/mfa/regenerate-backup-codes` | POST | Regenerate backup codes | User |
| `/auth/mfa/devices` | GET | List MFA devices | User |

### Sessions

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/sessions/refresh` | POST | Refresh access token | None |
| `/auth/sessions` | GET | List user sessions | User |
| `/auth/sessions/revoke` | POST | Revoke session | User |
| `/auth/sessions/revoke-all` | POST | Revoke all sessions | User |

### Invitations

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/invitations` | POST | Create invitation | Admin |
| `/auth/invitations` | GET | List invitations | User |
| `/auth/invitations/accept` | POST | Accept invitation | None |
| `/auth/invitations/{id}/cancel` | POST | Cancel invitation | User |
| `/auth/invitations/{id}/resend` | POST | Resend invitation | User |

### SAML/OIDC

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/saml/initiate` | POST | Initiate SAML SSO | None |
| `/auth/saml/metadata/{id}` | GET | Get SAML metadata | None |
| `/auth/oidc/initiate` | POST | Get OIDC auth URL | None |
| `/auth/oidc/{id}/callback` | GET | OIDC callback | None |

### RBAC

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/permissions` | GET | Get user permissions | User |
| `/auth/permissions/grant` | POST | Grant permission | Admin |
| `/auth/permissions/revoke` | POST | Revoke permission | Admin |
| `/auth/permissions/create` | POST | Create permission | Admin |
| `/auth/permissions/initialize` | POST | Initialize defaults | Admin |

## Database Models

### User
- Extended with MFA fields (`mfa_enabled`, `mfa_secret`, `backup_codes`)
- Relationships to sessions, MFA devices, invitations, permissions

### UserSession
- Session tokens and refresh tokens
- Device tracking (IP, user agent)
- Expiry management

### MFADevice
- TOTP device registration
- Device name and verification status

### Invitation
- Email, token, role
- Status and expiry tracking

### Permission
- Granular permissions (resource.action)
- Role and user assignments

### SAMLProvider / OIDCProvider
- Identity provider configuration
- SSO endpoint URLs and certificates

## Security Best Practices

1. **MFA**: Encourage users to enable MFA
2. **Session Management**: Regularly review and revoke old sessions
3. **Permissions**: Follow principle of least privilege
4. **Invitations**: Use invitations for controlled onboarding
5. **OAuth/SAML**: Use for enterprise SSO when available
6. **Token Security**: Store tokens securely, use HTTPS
7. **Backup Codes**: Store backup codes securely

## Troubleshooting

### MFA Issues
- Ensure authenticator app time is synchronized
- Check MFA secret is correct
- Use backup codes if device is lost

### Session Issues
- Check session expiry settings
- Verify refresh token is valid
- Check session limit configuration

### Permission Issues
- Verify user role
- Check permission exists
- Review user-specific overrides

### OAuth/SAML Issues
- Verify provider configuration
- Check redirect URIs match
- Review provider logs

## Support

For authentication-related issues:
- Check API documentation at `/docs`
- Review service logs
- Verify environment configuration
- Test with provided endpoints

