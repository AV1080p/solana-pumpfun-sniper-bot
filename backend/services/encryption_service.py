"""
Encryption Service for Data at Rest

Provides encryption/decryption capabilities for sensitive data storage.
Uses AES-256-GCM for authenticated encryption.
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data at rest"""
    
    def __init__(self):
        # Get encryption key from environment or generate one
        self.encryption_key = self._get_or_create_key()
        self.aesgcm = self._init_aesgcm()
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate a new one"""
        key_env = os.getenv("ENCRYPTION_KEY")
        
        if key_env:
            try:
                # Try to decode as base64
                return base64.b64decode(key_env)
            except Exception:
                # If not base64, use as-is (not recommended for production)
                logger.warning("ENCRYPTION_KEY should be base64 encoded")
                return key_env.encode() if isinstance(key_env, str) else key_env
        
        # Generate a new key (for development only)
        logger.warning("ENCRYPTION_KEY not set. Generating a new key. This should be set in production!")
        key = Fernet.generate_key()
        logger.info(f"Generated encryption key: {base64.b64encode(key).decode()}")
        logger.info("Add this to your .env file: ENCRYPTION_KEY=" + base64.b64encode(key).decode())
        return base64.b64decode(base64.b64encode(key))
    
    def _init_aesgcm(self) -> AESGCM:
        """Initialize AES-GCM cipher"""
        # Use first 32 bytes of key for AES-256
        key = self.encryption_key[:32] if len(self.encryption_key) >= 32 else self.encryption_key.ljust(32, b'0')
        return AESGCM(key)
    
    def encrypt(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt plaintext data using AES-256-GCM
        
        Args:
            plaintext: The data to encrypt (string)
            associated_data: Optional associated data for authentication
            
        Returns:
            Base64-encoded encrypted data with nonce
        """
        try:
            if not plaintext:
                return ""
            
            # Generate a random nonce (96 bits for GCM)
            nonce = os.urandom(12)
            
            # Encrypt the data
            plaintext_bytes = plaintext.encode('utf-8')
            ciphertext = self.aesgcm.encrypt(nonce, plaintext_bytes, associated_data)
            
            # Combine nonce and ciphertext, then encode
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")
    
    def encrypt_bytes(self, plaintext_bytes: bytes, associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt binary data using AES-256-GCM
        
        Args:
            plaintext_bytes: The binary data to encrypt
            associated_data: Optional associated data for authentication
            
        Returns:
            Base64-encoded encrypted data with nonce
        """
        try:
            if not plaintext_bytes:
                return ""
            
            # Generate a random nonce (96 bits for GCM)
            nonce = os.urandom(12)
            
            # Encrypt the data
            ciphertext = self.aesgcm.encrypt(nonce, plaintext_bytes, associated_data)
            
            # Combine nonce and ciphertext, then encode
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt(self, encrypted_data: str, associated_data: Optional[bytes] = None) -> str:
        """
        Decrypt encrypted data using AES-256-GCM
        
        Args:
            encrypted_data: Base64-encoded encrypted data with nonce
            associated_data: Optional associated data for authentication
            
        Returns:
            Decrypted plaintext string
        """
        try:
            if not encrypted_data:
                return ""
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Decrypt the data
            plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def decrypt_bytes(self, encrypted_data: str, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt encrypted data to binary using AES-256-GCM
        
        Args:
            encrypted_data: Base64-encoded encrypted data with nonce
            associated_data: Optional associated data for authentication
            
        Returns:
            Decrypted binary data
        """
        try:
            if not encrypted_data:
                return b""
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Decrypt the data
            plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext_bytes
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_field(self, value: Optional[str]) -> Optional[str]:
        """Encrypt a field value, handling None"""
        if value is None:
            return None
        return self.encrypt(value)
    
    def decrypt_field(self, value: Optional[str]) -> Optional[str]:
        """Decrypt a field value, handling None"""
        if value is None:
            return None
        try:
            return self.decrypt(value)
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy data)
            logger.warning("Decryption failed, returning value as-is")
            return value
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Hash sensitive data for one-way storage (e.g., for search/indexing)
        Uses SHA-256
        """
        from hashlib import sha256
        return sha256(data.encode('utf-8')).hexdigest()
    
    def generate_encryption_key(self) -> str:
        """Generate a new encryption key (for setup)"""
        key = Fernet.generate_key()
        return base64.b64encode(key).decode('utf-8')


# Singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create encryption service singleton"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

