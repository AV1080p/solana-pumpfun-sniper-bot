# Backend Core Logic Documentation

## Table of Contents
1. [Authentication & Authorization](#authentication--authorization)
2. [Payment Processing](#payment-processing)
3. [Database Management](#database-management)
4. [Security & Compliance](#security--compliance)
5. [Communication Services](#communication-services)
6. [Session Management](#session-management)
7. [Role-Based Access Control](#role-based-access-control)

---

## Authentication & Authorization

### Overview
The authentication system supports multiple authentication methods including email/password, OAuth (Google, GitHub), SAML, and OIDC. It includes Multi-Factor Authentication (MFA) and session management.

### Core Components

#### AuthService (`services/auth_service.py`)
**Purpose**: Handles user registration, login, and OAuth provider integration.

**Key Methods**:
- `register_user()`: Creates new user accounts with password hashing
- `login_user()`: Authenticates users and returns tokens
- `verify_google_token()`: Validates Google OAuth tokens
- `verify_github_token()`: Validates GitHub OAuth tokens
- `handle_oauth_callback()`: Processes OAuth callbacks

**Logic Flow**:
1. User registration: Email validation → Password hashing (bcrypt) → User creation → Token generation
2. Login: Email lookup → Password verification → MFA check → Session creation → Token return
3. OAuth: Token validation → User lookup/creation → Session creation → Token return

#### JWT Token Management (`auth.py`)
**Purpose**: Manages JWT token creation, validation, and user authentication.

**Key Functions**:
- `create_access_token()`: Generates JWT tokens with expiration (30 days default)
- `decode_access_token()`: Validates and decodes JWT tokens
- `get_current_user()`: Extracts user from JWT token in requests
- `get_current_admin_user()`: Validates admin role

**Token Structure**:
```python
{
    "sub": user_id,
    "email": user_email,
    "exp": expiration_timestamp,
    "iat": issued_at_timestamp
}
```

#### MFA Service (`services/mfa_service.py`)
**Purpose**: Implements Time-based One-Time Password (TOTP) for two-factor authentication.

**Key Methods**:
- `setup_totp()`: Generates TOTP secret and QR code
- `verify_mfa()`: Validates TOTP codes
- `regenerate_backup_codes()`: Creates new backup codes

**Logic Flow**:
1. Setup: Generate secret → Create QR code → Store encrypted secret
2. Verification: Get secret → Generate expected code → Compare with input
3. Backup codes: Generate 10 random codes → Hash and store

---

## Payment Processing

### Overview
The payment system supports multiple payment methods: Stripe (debit/credit cards), Solana, Bitcoin, and Ethereum. Each method has its own verification and processing logic.

### Core Components

#### PaymentService (`services/payment_service.py`)
**Purpose**: Handles Stripe payment processing.

**Key Methods**:
- `create_payment_intent()`: Creates Stripe payment intent
- `process_stripe_payment()`: Processes card payments
- `confirm_payment_intent()`: Confirms payment completion
- `refund_payment()`: Processes refunds
- `handle_webhook()`: Processes Stripe webhook events

**Logic Flow**:
1. Payment Intent Creation: Amount validation → Stripe API call → Client secret return
2. Payment Processing: Payment method attachment → Confirmation → Booking creation → Invoice generation
3. Webhook Handling: Signature verification → Event processing → Status updates

#### SolanaService (`services/solana_service.py`)
**Purpose**: Handles Solana blockchain payments.

**Key Methods**:
- `get_payment_address()`: Generates Solana wallet address
- `verify_solana_payment()`: Verifies transaction on Solana blockchain
- `check_payment_status()`: Checks transaction confirmation status

**Logic Flow**:
1. Address Generation: Create wallet → Return public address
2. Payment Verification: Transaction signature → Blockchain query → Amount verification → Status update
3. Status Check: Transaction lookup → Confirmation count → Status determination

#### CryptoService (`services/crypto_service.py`)
**Purpose**: Handles Bitcoin and Ethereum payments.

**Key Methods**:
- `get_bitcoin_payment_address()`: Generates Bitcoin address
- `get_ethereum_payment_address()`: Generates Ethereum address
- `verify_bitcoin_payment()`: Verifies Bitcoin transactions
- `verify_ethereum_payment()`: Verifies Ethereum transactions
- `check_crypto_payment_status()`: Checks transaction status

**Logic Flow**:
1. Address Generation: Create wallet → Return address
2. Payment Verification: Transaction hash → Blockchain API call → Amount verification → Status update
3. Status Check: Transaction lookup → Block confirmations → Status determination

### Payment States
- `pending`: Payment initiated but not confirmed
- `processing`: Payment being processed
- `completed`: Payment successfully completed
- `failed`: Payment failed
- `refunded`: Payment refunded
- `cancelled`: Payment cancelled

---

## Database Management

### Overview
The database layer uses SQLAlchemy ORM with PostgreSQL. It includes connection pooling, migrations (Alembic), backup/restore, and health monitoring.

### Core Components

#### Database Connection (`database.py`)
**Purpose**: Manages database connections and session lifecycle.

**Key Features**:
- Connection pooling (default: 10 connections, max overflow: 20)
- Automatic connection health checks (`pool_pre_ping=True`)
- Session dependency injection for FastAPI
- Context manager for non-FastAPI contexts

**Connection Pool Configuration**:
```python
pool_size = 10
max_overflow = 20
pool_timeout = 30 seconds
pool_recycle = 3600 seconds (1 hour)
```

#### DatabaseManager (`db_utils.py`)
**Purpose**: Provides database utilities for initialization, backups, and statistics.

**Key Methods**:
- `initialize_database()`: Creates all tables
- `backup_database()`: Creates encrypted database backups
- `restore_database()`: Restores from backup
- `get_table_stats()`: Returns table statistics
- `get_connection_pool_stats()`: Returns pool statistics

**Backup Logic**:
1. Create backup directory
2. Generate backup filename with timestamp
3. Execute `pg_dump` (PostgreSQL) or SQLite backup
4. Encrypt backup if requested
5. Store backup record in database
6. Return backup path and metadata

### Models Architecture (`models.py`)

#### Core Models
- **User**: User accounts with authentication info
- **Tour**: Tour listings
- **Booking**: Tour bookings
- **Payment**: Payment records
- **Invoice**: Invoice generation

#### Authentication Models
- **UserSession**: Active user sessions
- **MFADevice**: MFA device registrations
- **Invitation**: User invitations
- **Permission**: RBAC permissions
- **RolePermission**: Role-permission mappings
- **UserPermission**: User-specific permissions

#### Communication Models
- **ChatRoom**: Chat rooms
- **Message**: Chat messages
- **AIConversation**: AI chatbot conversations
- **CallSession**: Voice/video calls
- **BroadcastAlert**: System announcements
- **ForumPost/ForumReply**: Forum posts and replies

#### Compliance Models
- **DataConsent**: GDPR consent tracking
- **DataRetentionLog**: Retention policy logs
- **BackupRecord**: Backup tracking
- **AuditLog**: System audit trail

---

## Security & Compliance

### Overview
The system implements GDPR/CCPA compliance features including data export, deletion, consent management, and data retention policies.

### Core Components

#### ComplianceService (`services/compliance_service.py`)
**Purpose**: Handles GDPR/CCPA compliance operations.

**Key Methods**:
- `export_user_data()`: Exports all user data (Right to Access)
- `delete_user_data()`: Deletes or anonymizes user data (Right to be Forgotten)
- `get_consent_status()`: Retrieves user consent status
- `update_consent()`: Updates consent preferences

**Data Export Logic**:
1. Query all user-related data (bookings, payments, invoices, feedback)
2. Format data as JSON or CSV
3. Encrypt sensitive fields
4. Return downloadable file

**Data Deletion Logic**:
1. Check if anonymization is requested
2. Anonymize or delete user data
3. Update related records
4. Log deletion action
5. Return confirmation

#### RetentionService (`services/retention_service.py`)
**Purpose**: Manages data retention policies.

**Key Methods**:
- `add_policy()`: Adds retention policy
- `apply_retention_policy()`: Applies policy to data type
- `apply_all_policies()`: Applies all policies

**Default Policies**:
- Bookings: 7 years (anonymize)
- Payments: 7 years (anonymize)
- Invoices: 7 years (anonymize)
- Feedback: 1 year (delete)
- Users: 10 years inactive (anonymize)

**Retention Logic**:
1. Calculate cutoff date (current date - retention days)
2. Query records older than cutoff
3. Apply action (delete or anonymize)
4. Log actions in DataRetentionLog
5. Return statistics

#### EncryptionService (`services/encryption_service.py`)
**Purpose**: Provides encryption/decryption for sensitive data.

**Key Methods**:
- `encrypt()`: Encrypts data using AES-256
- `decrypt()`: Decrypts encrypted data
- `generate_encryption_key()`: Generates new encryption key

**Encryption Algorithm**: AES-256-GCM (Galois/Counter Mode)

---

## Communication Services

### Overview
The communication system provides chat, AI chatbot, translation, voice/video calls, forums, and broadcast alerts.

### Core Components

#### CommunicationService (`services/communication_service.py`)
**Purpose**: Handles all communication features.

**Key Methods**:
- `create_chat_room()`: Creates chat rooms
- `send_message()`: Sends messages with optional translation
- `get_messages()`: Retrieves chat messages
- `send_ai_message()`: Processes AI chatbot messages
- `translate_text()`: Translates text between languages
- `initiate_call()`: Starts voice/video calls
- `create_broadcast()`: Creates system announcements
- `create_forum_post()`: Creates forum posts

**Chat Logic**:
1. Room Creation: Validate participants → Create room → Add participants
2. Message Sending: Validate room access → Create message → Optional translation → Store
3. Translation: Detect language → Translate → Store both versions

**AI Chatbot Logic**:
1. Create/retrieve conversation session
2. Store user message
3. Call AI API (OpenAI compatible)
4. Store AI response
5. Return conversation

**Translation Logic**:
1. Detect source language (if not provided)
2. Call translation API
3. Return translated text

---

## Session Management

### Overview
The session management system tracks user sessions across devices, supports refresh tokens, and provides session revocation.

### Core Components

#### SessionService (`services/session_service.py`)
**Purpose**: Manages user sessions and refresh tokens.

**Key Methods**:
- `create_session()`: Creates new user session
- `refresh_session()`: Refreshes access token using refresh token
- `get_user_sessions()`: Lists all user sessions
- `revoke_session()`: Revokes specific session
- `revoke_all_sessions()`: Revokes all user sessions

**Session Creation Logic**:
1. Generate session token (UUID)
2. Generate refresh token (UUID)
3. Store device info and IP address
4. Set expiration (30 days)
5. Create UserSession record
6. Return tokens

**Token Refresh Logic**:
1. Validate refresh token
2. Check session status (active)
3. Check expiration
4. Generate new access token
5. Update last activity
6. Return new token

**Session States**:
- `active`: Session is active
- `expired`: Session expired
- `revoked`: Session manually revoked

---

## Role-Based Access Control

### Overview
The RBAC system provides granular permissions beyond simple role checks. It supports role-based permissions and user-specific overrides.

### Core Components

#### RBACService (`services/rbac_service.py`)
**Purpose**: Manages permissions and access control.

**Key Methods**:
- `check_permission()`: Checks if user has permission
- `grant_permission()`: Grants permission to user
- `revoke_permission()`: Revokes permission from user
- `create_permission()`: Creates new permission
- `initialize_default_permissions()`: Sets up default permissions

**Permission Check Logic**:
1. Admin check: Admins have all permissions (`*`)
2. User-specific check: Check UserPermission table (overrides)
3. Role check: Check RolePermission table
4. Return boolean result

**Default Permissions**:
- **USER**: View own bookings, create bookings, view tours, manage profile, view own invoices, create feedback
- **MODERATOR**: View/update bookings, view/update tours, view users, view/update feedback
- **ADMIN**: All permissions (`*`)

**Permission Format**: `resource.action` (e.g., `bookings.create`, `tours.view`)

---

## API Endpoint Organization

### Endpoint Groups

1. **Authentication** (`/auth/*`): Registration, login, OAuth, MFA
2. **Tours** (`/tours/*`): Tour CRUD operations
3. **Bookings** (`/bookings/*`): Booking management
4. **Payments** (`/payments/*`): Payment processing
5. **Dashboard** (`/dashboard/*`): User dashboard data
6. **Admin** (`/admin/*`): Admin operations
7. **Security** (`/security/*`): Compliance and security
8. **Communication** (`/communication/*`): Chat, AI, calls, forums

### Request Flow
1. Request received by FastAPI
2. Authentication middleware checks JWT token
3. Dependency injection provides database session
4. Route handler processes request
5. Service layer executes business logic
6. Database operations via SQLAlchemy ORM
7. Response serialized via Pydantic schemas
8. Response returned to client

---

## Background Services

### SchedulerService (`services/scheduler_service.py`)
**Purpose**: Runs scheduled tasks for data retention and backups.

**Scheduled Tasks**:
- Daily retention policy execution (2:00 AM)
- Periodic backup creation (configurable)

**Implementation**: Uses `schedule` library with background thread

---

## Error Handling

### HTTP Exception Codes
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

### Error Response Format
```json
{
    "detail": "Error message"
}
```

---

## Logging

### Log Levels
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `DEBUG`: Debug information (development only)

### Logged Events
- Authentication attempts
- Payment processing
- Database operations
- Security events
- Service errors

