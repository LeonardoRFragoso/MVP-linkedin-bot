"""
Unit tests for EncryptionService.
Run with: pytest tests/test_encryption_service.py -v
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.encryption_service import (
    EncryptionService,
    EncryptionError,
    DecryptionError,
    get_encryption_service
)


class TestEncryptionService:
    """Tests for EncryptionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh EncryptionService with a test key."""
        test_key = EncryptionService.generate_key()
        return EncryptionService(encryption_key=test_key)
    
    @pytest.fixture
    def test_key(self):
        """Generate a test encryption key."""
        return EncryptionService.generate_key()
    
    # ==================== Key Generation Tests ====================
    
    def test_generate_key_returns_valid_key(self):
        """Test that generate_key returns a valid Fernet key."""
        key = EncryptionService.generate_key()
        assert key is not None
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 44 chars base64
    
    def test_generate_key_returns_unique_keys(self):
        """Test that each call to generate_key returns a unique key."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        assert key1 != key2
    
    def test_derive_key_from_password(self):
        """Test password-based key derivation."""
        password = "my-secret-password"
        key1, salt1 = EncryptionService.derive_key_from_password(password)
        
        assert key1 is not None
        assert salt1 is not None
        assert len(salt1) == 16
        
        # Same password + salt should give same key
        key2, _ = EncryptionService.derive_key_from_password(password, salt1)
        assert key1 == key2
        
        # Different salt should give different key
        key3, salt3 = EncryptionService.derive_key_from_password(password)
        assert key1 != key3
    
    # ==================== Initialization Tests ====================
    
    def test_init_with_valid_key(self, test_key):
        """Test initialization with a valid key."""
        service = EncryptionService(encryption_key=test_key)
        assert service is not None
    
    def test_init_with_invalid_key_raises_error(self):
        """Test that invalid key raises EncryptionError."""
        with pytest.raises(EncryptionError):
            EncryptionService(encryption_key="invalid-key")
    
    # ==================== Encryption Tests ====================
    
    def test_encrypt_string(self, service):
        """Test basic string encryption."""
        plaintext = "my-secret-password"
        encrypted = service.encrypt(plaintext)
        
        assert encrypted is not None
        assert encrypted != plaintext
        assert encrypted.startswith("enc:")
    
    def test_encrypt_empty_string_returns_empty(self, service):
        """Test that empty string returns empty string."""
        assert service.encrypt("") == ""
        assert service.encrypt(None) is None
    
    def test_encrypt_already_encrypted_returns_same(self, service):
        """Test that already encrypted value is not double-encrypted."""
        plaintext = "secret"
        encrypted = service.encrypt(plaintext)
        double_encrypted = service.encrypt(encrypted)
        
        assert encrypted == double_encrypted
    
    def test_encrypt_unicode(self, service):
        """Test encryption of unicode strings."""
        plaintext = "Senha secreta: 日本語 émojis 🔐"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_long_string(self, service):
        """Test encryption of long strings."""
        plaintext = "x" * 10000
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    # ==================== Decryption Tests ====================
    
    def test_decrypt_encrypted_string(self, service):
        """Test basic decryption."""
        plaintext = "my-secret-password"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_decrypt_unencrypted_string_returns_same(self, service):
        """Test that unencrypted string passes through."""
        plaintext = "not-encrypted"
        result = service.decrypt(plaintext)
        
        assert result == plaintext
    
    def test_decrypt_empty_string_returns_empty(self, service):
        """Test that empty string returns empty string."""
        assert service.decrypt("") == ""
        assert service.decrypt(None) is None
    
    def test_decrypt_with_wrong_key_raises_error(self, test_key):
        """Test that decryption with wrong key raises DecryptionError."""
        service1 = EncryptionService(encryption_key=test_key)
        encrypted = service1.encrypt("secret")
        
        # Create service with different key
        different_key = EncryptionService.generate_key()
        service2 = EncryptionService(encryption_key=different_key)
        
        with pytest.raises(DecryptionError):
            service2.decrypt(encrypted)
    
    def test_decrypt_tampered_data_raises_error(self, service):
        """Test that tampered data raises DecryptionError."""
        encrypted = service.encrypt("secret")
        tampered = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(DecryptionError):
            service.decrypt(tampered)
    
    # ==================== Dict Encryption Tests ====================
    
    def test_encrypt_dict_specific_keys(self, service):
        """Test dictionary encryption with specific keys."""
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "name": "John Doe"
        }
        
        encrypted = service.encrypt_dict(data, keys_to_encrypt=["password"])
        
        assert encrypted["email"] == "user@example.com"
        assert encrypted["password"].startswith("enc:")
        assert encrypted["name"] == "John Doe"
    
    def test_encrypt_dict_all_strings(self, service):
        """Test dictionary encryption of all string values."""
        data = {
            "field1": "value1",
            "field2": "value2",
            "number": 123  # Should not be encrypted
        }
        
        encrypted = service.encrypt_dict(data, keys_to_encrypt=None)
        
        assert encrypted["field1"].startswith("enc:")
        assert encrypted["field2"].startswith("enc:")
        assert encrypted["number"] == 123
    
    def test_encrypt_dict_nested(self, service):
        """Test encryption of nested dictionaries."""
        data = {
            "credentials": {
                "email": "user@example.com",
                "password": "secret"
            },
            "settings": {
                "api_key": "sk-12345"
            }
        }
        
        encrypted = service.encrypt_dict(data, keys_to_encrypt=["password", "api_key"])
        
        assert encrypted["credentials"]["email"] == "user@example.com"
        assert encrypted["credentials"]["password"].startswith("enc:")
        assert encrypted["settings"]["api_key"].startswith("enc:")
    
    def test_decrypt_dict_specific_keys(self, service):
        """Test dictionary decryption."""
        data = {
            "email": "user@example.com",
            "password": "secret123"
        }
        
        encrypted = service.encrypt_dict(data, keys_to_encrypt=["password"])
        decrypted = service.decrypt_dict(encrypted, keys_to_decrypt=["password"])
        
        assert decrypted == data
    
    def test_encrypt_decrypt_dict_roundtrip(self, service):
        """Test full roundtrip of dict encryption/decryption."""
        original = {
            "user": "admin",
            "password": "super-secret",
            "config": {
                "api_key": "key-123",
                "webhook_secret": "secret-456"
            }
        }
        
        keys = ["password", "api_key", "webhook_secret"]
        encrypted = service.encrypt_dict(original, keys_to_encrypt=keys)
        decrypted = service.decrypt_dict(encrypted, keys_to_decrypt=keys)
        
        assert decrypted == original
    
    # ==================== Credentials Tests ====================
    
    def test_encrypt_credentials(self, service):
        """Test credential encryption helper."""
        email = "user@linkedin.com"
        password = "linkedin-pass-123"
        
        credentials = service.encrypt_credentials(email, password)
        
        assert credentials["email"] == email
        assert credentials["password"].startswith("enc:")
    
    def test_decrypt_credentials(self, service):
        """Test credential decryption helper."""
        email = "user@linkedin.com"
        password = "linkedin-pass-123"
        
        encrypted = service.encrypt_credentials(email, password)
        decrypted_email, decrypted_password = service.decrypt_credentials(encrypted)
        
        assert decrypted_email == email
        assert decrypted_password == password
    
    # ==================== Utility Tests ====================
    
    def test_is_encrypted(self, service):
        """Test is_encrypted helper method."""
        plaintext = "not-encrypted"
        encrypted = service.encrypt("secret")
        
        assert service.is_encrypted(encrypted) is True
        assert service.is_encrypted(plaintext) is False
        assert service.is_encrypted("") is False
        assert service.is_encrypted(None) is False
    
    # ==================== Singleton Tests ====================
    
    def test_get_encryption_service_singleton(self):
        """Test that get_encryption_service returns singleton."""
        # Set environment for development mode
        os.environ['ENVIRONMENT'] = 'development'
        
        service1 = get_encryption_service()
        service2 = get_encryption_service()
        
        assert service1 is service2


class TestEncryptionServiceIntegration:
    """Integration tests for EncryptionService."""
    
    def test_encrypt_linkedin_credentials_workflow(self):
        """Test complete workflow for LinkedIn credentials."""
        # Setup
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)
        
        # User provides credentials
        email = "leonardorfragoso@gmail.com"
        password = "MySecretPassword123!"
        
        # Encrypt for storage
        stored_credentials = service.encrypt_credentials(email, password)
        
        # Verify password is encrypted
        assert "enc:" in stored_credentials["password"]
        assert password not in str(stored_credentials)
        
        # Retrieve and decrypt for use
        retrieved_email, retrieved_password = service.decrypt_credentials(stored_credentials)
        
        assert retrieved_email == email
        assert retrieved_password == password
    
    def test_config_migration_workflow(self):
        """Test workflow for migrating config files."""
        key = EncryptionService.generate_key()
        service = EncryptionService(encryption_key=key)
        
        # Simulated config from personals.py
        config = {
            "first_name": "Leonardo",
            "last_name": "Fragoso",
            "phone": "21980292791",
            "linkedin": {
                "email": "leonardorfragoso@gmail.com",
                "password": "Valentina@2308@@"  # Sensitive!
            },
            "ai_keys": {
                "openai_key": "sk-fake-key-123",
                "deepseek_key": "ds-fake-key-456"
            }
        }
        
        # Encrypt sensitive fields
        sensitive_keys = ["password", "openai_key", "deepseek_key"]
        encrypted_config = service.encrypt_dict(config, keys_to_encrypt=sensitive_keys)
        
        # Verify sensitive data is encrypted
        assert encrypted_config["linkedin"]["password"].startswith("enc:")
        assert encrypted_config["ai_keys"]["openai_key"].startswith("enc:")
        assert "Valentina" not in str(encrypted_config)
        
        # Non-sensitive data unchanged
        assert encrypted_config["first_name"] == "Leonardo"
        assert encrypted_config["phone"] == "21980292791"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
