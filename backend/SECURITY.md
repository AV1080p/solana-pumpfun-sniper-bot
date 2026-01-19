# Security & Compliance Documentation

This document describes the security features and compliance tools implemented in the application.

## Table of Contents

1. [Encryption](#encryption)
2. [GDPR/CCPA Compliance](#gdprccpa-compliance)
3. [Data Export/Import](#data-exportimport)
4. [Data Retention Policies](#data-retention-policies)
5. [Backup & Recovery](#backup--recovery)
6. [API Endpoints](#api-endpoints)

## Encryption

### Encryption at Rest

The application uses **AES-256-GCM** (Galois/Counter Mode) for encrypting sensitive data at rest. This provides:
- Strong encryption (256-bit key)
- Authenticated encryption (prevents tampering)
- Secure random nonce generation

#### Setup

1. Generate an encryption key:
```bash
python -c "from cryptography.fernet import Fernet; import base64; print(base64.b64encode(Fernet.generate_key()).decode())"
```

2. Add to your `.env` file:
```
ENCRYPTION_KEY=your_base64_encoded_key_here
```

#### Usage

The `EncryptionService` provides methods for encrypting/decrypting data:

```python
from services.encryption_service import get_encryption_service

encryption_service = get_encryption_service()
encrypted = encryption_service.encrypt("sensitive data")
decrypted = encryption_service.decrypt(encrypted)
```

### Encryption in Transit

For production deployments, enable HTTPS/TLS:

1. Obtain SSL certificates
2. Configure your reverse proxy (nginx, Apache) or use uvicorn with SSL:
```python
uvicorn.run(app, host="0.0.0.0", port=443, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
```

3. Set environment variables:
```
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

## GDPR/CCPA Compliance

### Right to Access (Data Export)

Users can export all their personal data in JSON or CSV format.

**Endpoint:** `POST /security/data/export`

**Request:**
```json
{
  "user_id": 1,
  "format": "json"  // or "csv"
}
```

**Response:** File download with all user data including:
- Profile information
- Bookings
- Payments
- Invoices
- Feedback

### Right to be Forgotten (Data Deletion)

Users can request deletion or anonymization of their data.

**Endpoint:** `POST /security/data/delete`

**Request:**
```json
{
  "user_id": 1,
  "anonymize": true  // If true, anonymize instead of delete
}
```

### Consent Management

Track and manage user consent for data processing.

**Get Consent:** `GET /security/data/consent/{user_id}`
**Update Consent:** `POST /security/data/consent/{user_id}`

**Request:**
```json
{
  "consent_type": "marketing",  // data_processing, marketing, analytics, third_party_sharing
  "granted": true
}
```

## Data Export/Import

### Export Formats

- **JSON**: Complete structured data export
- **CSV**: Simplified tabular format

### Encryption

All exported data can be encrypted before transmission. The encryption service handles this automatically.

## Data Retention Policies

Automated data retention policies ensure compliance with legal requirements and reduce data storage costs.

### Default Policies

| Data Type | Retention Period | Action |
|-----------|----------------|--------|
| Bookings | 7 years (2555 days) | Anonymize |
| Payments | 7 years (2555 days) | Anonymize |
| Invoices | 7 years (2555 days) | Anonymize |
| Feedback | 1 year (365 days) | Delete |
| Inactive Users | 10 years (3650 days) | Anonymize |

### Configuration

Set retention policies via environment variables:

```env
RETENTION_BOOKING_DAYS=2555
RETENTION_PAYMENT_DAYS=2555
RETENTION_INVOICE_DAYS=2555
RETENTION_FEEDBACK_DAYS=365
RETENTION_USER_DAYS=3650

RETENTION_BOOKING_ACTION=anonymize
RETENTION_PAYMENT_ACTION=anonymize
RETENTION_INVOICE_ACTION=anonymize
RETENTION_FEEDBACK_ACTION=delete
RETENTION_USER_ACTION=anonymize
```

### Automated Execution

Retention policies run automatically daily at 2:00 AM via the scheduler service.

**Manual Execution:**

**Endpoint:** `POST /security/retention/apply`

**Request:**
```json
{
  "data_type": "booking",  // Optional: if omitted, applies all policies
  "dry_run": false  // If true, only reports what would be done
}
```

## Backup & Recovery

### Encrypted Backups

All database backups are encrypted by default using AES-256-GCM.

**Create Backup:** `POST /security/backup/create`

**Request:**
```json
{
  "backup_name": "backup_20240101",
  "encrypt": true
}
```

**Response:**
```json
{
  "success": true,
  "backup_path": "backups/backup_20240101.encrypted",
  "file_size": 1048576,
  "file_size_mb": 1.0,
  "encrypted": true
}
```

### Restore Backup

**Endpoint:** `POST /security/backup/restore`

**Request:**
```json
{
  "backup_path": "backups/backup_20240101.encrypted",
  "drop_existing": false,
  "encrypted": true
}
```

### List Backups

**Endpoint:** `GET /security/backup/list`

Returns list of all backups with metadata.

## API Endpoints

### Security & Compliance Endpoints

All security endpoints require admin authentication except:
- Data export (users can export their own data)
- Consent management (users can manage their own consent)

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/security/data/export` | POST | Export user data | User/Admin |
| `/security/data/delete` | POST | Delete/anonymize user data | Admin |
| `/security/data/consent/{user_id}` | GET | Get consent status | User/Admin |
| `/security/data/consent/{user_id}` | POST | Update consent | User/Admin |
| `/security/retention/policy` | POST | Create retention policy | Admin |
| `/security/retention/apply` | POST | Apply retention policies | Admin |
| `/security/retention/policies` | GET | List all policies | Admin |
| `/security/backup/create` | POST | Create encrypted backup | Admin |
| `/security/backup/restore` | POST | Restore from backup | Admin |
| `/security/backup/list` | GET | List all backups | Admin |
| `/security/encryption/key/generate` | GET | Generate encryption key | Admin |

## Best Practices

1. **Key Management**
   - Rotate encryption keys regularly
   - Store keys securely (use secret management services in production)
   - Never commit keys to version control

2. **Backup Strategy**
   - Create backups regularly (daily recommended)
   - Store backups in secure, off-site locations
   - Test restore procedures regularly
   - Encrypt all backups

3. **Retention Policies**
   - Review and update policies based on legal requirements
   - Document retention periods and rationale
   - Monitor retention policy execution logs

4. **Compliance**
   - Document all data processing activities
   - Maintain audit logs of data access and modifications
   - Respond to data subject requests promptly (GDPR: 30 days)

5. **Security**
   - Enable HTTPS/TLS in production
   - Use strong encryption keys
   - Regularly update dependencies
   - Monitor for security vulnerabilities

## Database Models

### DataConsent
Tracks user consent for various data processing activities.

### DataRetentionLog
Audit log of all retention policy actions.

### BackupRecord
Metadata about database backups.

## Scheduler Service

The scheduler service runs automated tasks:
- **Daily at 2:00 AM**: Apply all retention policies

To start the scheduler manually:
```python
from services.scheduler_service import get_scheduler_service
scheduler = get_scheduler_service()
scheduler.start()
```

## Troubleshooting

### Encryption Errors
- Ensure `ENCRYPTION_KEY` is set in environment
- Verify key is base64 encoded
- Check key length (should be 32 bytes for AES-256)

### Backup Issues
- Verify PostgreSQL client tools are installed (`pg_dump`, `pg_restore`)
- Check file permissions for backup directory
- Ensure sufficient disk space

### Retention Policy Issues
- Check database connection
- Verify retention policy configuration
- Review logs for specific errors

## Support

For security-related issues or questions, contact the security team or refer to the main project documentation.

