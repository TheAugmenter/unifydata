"""
Encryption Service for OAuth Tokens
Uses Fernet (symmetric encryption) to encrypt/decrypt sensitive data
"""
from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import hashlib


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data like OAuth tokens
    """

    def __init__(self):
        """Initialize encryption service with key from settings"""
        # Derive a Fernet key from SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string

        Args:
            data: Plain text string to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""

        encrypted_bytes = self.cipher.encrypt(data.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string

        Args:
            encrypted_data: Encrypted string (base64 encoded)

        Returns:
            Decrypted plain text string
        """
        if not encrypted_data:
            return ""

        decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()


# Global instance
encryption_service = EncryptionService()
