"""
Encryption Service for LinkedIn Bot White Label MVP.
Handles encryption/decryption of sensitive data like LinkedIn credentials.

Uses Fernet symmetric encryption from the cryptography library.
"""

import os
import json
import base64
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption-related errors."""
    pass


class DecryptionError(Exception):
    """Custom exception for decryption-related errors."""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    
    Uses Fernet symmetric encryption which provides:
    - AES-128-CBC encryption
    - HMAC-SHA256 authentication
    - Automatic IV generation
    
    Usage:
        service = EncryptionService()
        encrypted = service.encrypt("my-secret-password")
        decrypted = service.decrypt(encrypted)
    """
    
    # Prefix for identifying encrypted values
    ENCRYPTED_PREFIX = "enc:"
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the encryption service.
        
        Args:
            encryption_key: Base64-encoded Fernet key. If not provided,
                           will try to load from ENCRYPTION_KEY env var.
                           In development mode, generates a new key if none exists.
        """
        self._key = self._get_or_generate_key(encryption_key)
        self._fernet = Fernet(self._key)
    
    def _get_or_generate_key(self, provided_key: Optional[str] = None) -> bytes:
        """
        Get encryption key from various sources or generate a new one.
        
        Priority:
        1. Provided key parameter
        2. ENCRYPTION_KEY environment variable
        3. Generate new key (development only)
        
        Args:
            provided_key: Optionally provided encryption key
            
        Returns:
            bytes: Valid Fernet key
            
        Raises:
            EncryptionError: If no key available and not in development mode
        """
        # 1. Try provided key
        if provided_key:
            try:
                key = provided_key.encode() if isinstance(provided_key, str) else provided_key
                Fernet(key)  # Validate key format
                return key
            except Exception as e:
                raise EncryptionError(f"Invalid provided encryption key: {e}")
        
        # 2. Try environment variable
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            try:
                key = env_key.encode() if isinstance(env_key, str) else env_key
                Fernet(key)  # Validate key format
                return key
            except Exception as e:
                raise EncryptionError(f"Invalid ENCRYPTION_KEY in environment: {e}")
        
        # 3. Development mode: generate key and warn
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'development':
            logger.warning(
                "⚠️  No ENCRYPTION_KEY found. Generating temporary key for development. "
                "DO NOT USE IN PRODUCTION! Set ENCRYPTION_KEY in .env file."
            )
            new_key = Fernet.generate_key()
            
            # Save to .env file if it exists
            self._save_key_to_env(new_key.decode())
            
            return new_key
        
        raise EncryptionError(
            "No encryption key available. Set ENCRYPTION_KEY environment variable. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    
    def _save_key_to_env(self, key: str) -> None:
        """
        Save generated key to .env file for persistence in development.
        
        Args:
            key: The encryption key to save
        """
        try:
            env_path = Path(__file__).parent.parent / '.env'
            
            if env_path.exists():
                content = env_path.read_text()
                if 'ENCRYPTION_KEY=' in content:
                    # Update existing key
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('ENCRYPTION_KEY='):
                            lines[i] = f'ENCRYPTION_KEY={key}'
                            break
                    env_path.write_text('\n'.join(lines))
                else:
                    # Append new key
                    with open(env_path, 'a') as f:
                        f.write(f'\nENCRYPTION_KEY={key}\n')
                logger.info(f"Encryption key saved to {env_path}")
            else:
                # Create new .env file
                env_path.write_text(f'ENCRYPTION_KEY={key}\n')
                logger.info(f"Created {env_path} with encryption key")
                
        except Exception as e:
            logger.warning(f"Could not save encryption key to .env: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            str: Base64-encoded Fernet key
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Derive a Fernet key from a password using PBKDF2.
        
        Useful for user-specific encryption where each user has their own password.
        
        Args:
            password: User password or passphrase
            salt: Optional salt bytes. If not provided, generates random salt.
            
        Returns:
            tuple: (base64-encoded key, salt bytes)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            str: Encrypted string with 'enc:' prefix
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return plaintext
        
        # Already encrypted
        if isinstance(plaintext, str) and plaintext.startswith(self.ENCRYPTED_PREFIX):
            return plaintext
        
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return f"{self.ENCRYPTED_PREFIX}{encrypted_bytes.decode('utf-8')}"
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string value.
        
        Args:
            ciphertext: The encrypted string (with or without 'enc:' prefix)
            
        Returns:
            str: Decrypted plaintext
            
        Raises:
            DecryptionError: If decryption fails
        """
        if not ciphertext:
            return ciphertext
        
        # Not encrypted
        if not ciphertext.startswith(self.ENCRYPTED_PREFIX):
            return ciphertext
        
        try:
            # Remove prefix
            encrypted_data = ciphertext[len(self.ENCRYPTED_PREFIX):]
            decrypted_bytes = self._fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            raise DecryptionError("Invalid encryption token. Key may have changed.")
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt data: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any], keys_to_encrypt: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Encrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary containing data to encrypt
            keys_to_encrypt: List of keys whose values should be encrypted.
                            If None, encrypts all string values.
                            
        Returns:
            dict: New dictionary with encrypted values
            
        Example:
            data = {"username": "user@email.com", "password": "secret123"}
            encrypted = service.encrypt_dict(data, keys_to_encrypt=["password"])
            # Result: {"username": "user@email.com", "password": "enc:gAAA..."}
        """
        result = data.copy()
        
        for key, value in result.items():
            if isinstance(value, dict):
                # Always recursively process nested dicts to find keys to encrypt
                result[key] = self.encrypt_dict(value, keys_to_encrypt)
            elif isinstance(value, str) and value:
                # Encrypt if key matches or if encrypting all strings
                if keys_to_encrypt is None or key in keys_to_encrypt:
                    result[key] = self.encrypt(value)
        
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], keys_to_decrypt: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Decrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            keys_to_decrypt: List of keys whose values should be decrypted.
                            If None, decrypts all encrypted string values.
                            
        Returns:
            dict: New dictionary with decrypted values
        """
        result = data.copy()
        
        for key, value in result.items():
            if isinstance(value, dict):
                # Always recursively process nested dicts to find keys to decrypt
                result[key] = self.decrypt_dict(value, keys_to_decrypt)
            elif isinstance(value, str) and value.startswith(self.ENCRYPTED_PREFIX):
                # Decrypt if key matches or if decrypting all encrypted values
                if keys_to_decrypt is None or key in keys_to_decrypt:
                    result[key] = self.decrypt(value)
        
        return result
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value is encrypted.
        
        Args:
            value: String to check
            
        Returns:
            bool: True if value appears to be encrypted
        """
        return isinstance(value, str) and value.startswith(self.ENCRYPTED_PREFIX)
    
    def encrypt_credentials(self, email: str, password: str) -> Dict[str, str]:
        """
        Convenience method to encrypt LinkedIn credentials.
        
        Args:
            email: LinkedIn email/username
            password: LinkedIn password
            
        Returns:
            dict: {"email": "...", "password": "enc:..."}
        """
        return {
            "email": email,  # Email typically doesn't need encryption
            "password": self.encrypt(password)
        }
    
    def decrypt_credentials(self, credentials: Dict[str, str]) -> tuple[str, str]:
        """
        Convenience method to decrypt LinkedIn credentials.
        
        Args:
            credentials: Dict with email and encrypted password
            
        Returns:
            tuple: (email, password)
        """
        email = credentials.get('email', '')
        password = self.decrypt(credentials.get('password', ''))
        return email, password


# Singleton instance for convenience
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the global encryption service instance (singleton).
    
    Returns:
        EncryptionService: Global instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


if __name__ == "__main__":
    # Quick test
    print("Testing EncryptionService...")
    
    # Generate a test key
    test_key = EncryptionService.generate_key()
    print(f"Generated key: {test_key[:20]}...")
    
    # Test encryption/decryption
    service = EncryptionService(encryption_key=test_key)
    
    original = "my-secret-password-123"
    encrypted = service.encrypt(original)
    decrypted = service.decrypt(encrypted)
    
    print(f"Original:  {original}")
    print(f"Encrypted: {encrypted[:50]}...")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {original == decrypted}")
    
    # Test dict encryption
    data = {
        "email": "user@example.com",
        "password": "secret123",
        "nested": {
            "api_key": "sk-12345"
        }
    }
    
    encrypted_dict = service.encrypt_dict(data, keys_to_encrypt=["password", "api_key"])
    print(f"\nEncrypted dict: {json.dumps(encrypted_dict, indent=2)}")
    
    decrypted_dict = service.decrypt_dict(encrypted_dict)
    print(f"\nDecrypted dict: {json.dumps(decrypted_dict, indent=2)}")
